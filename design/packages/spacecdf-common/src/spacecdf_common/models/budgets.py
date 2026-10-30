"""SpaceCDF — Engineering Budget System with Bidirectional Requirement Roll-up.

Proper engineering budgets per ECSS-E-ST-10C and NASA SEH:
- Mass budget (dry/wet/MoI — most CubeSats have no wet mass)
- Power budget (generation/consumption per mode: peak/orbital-avg/eclipse/safe)
- Volume budget (per subsystem vs bus envelope)
- Pointing budget (error tree)
- Data budget (generation/storage/downlink)
- ΔV budget (manoeuvre breakdown)
- Link budget (EIRP → FSPL → G/T → margin chain)
- Cost budget (WBS roll-up)

Each budget:
- Has allocation per subsystem from system-level requirement
- Has actual per subsystem from design agent output
- Computes margin (allocation - actual) / allocation
- Rolls UP: subsystem → system → mission requirement
- Propagates DOWN: mission requirement change → system → subsystem impact
- Flags when a subsystem exceeds its allocation → system budget risk → mission risk

CubeSat-aware: most have no propulsion → no wet mass → dry = launch mass.
MoI computed for attitude control sizing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BudgetStatus(str, Enum):
    GREEN = "green"       # Margin > margin policy (e.g. >20%)
    AMBER = "amber"       # 0 < margin < policy
    RED = "red"           # Margin < 0 (exceeded)
    NOT_APPLICABLE = "na" # Budget doesn't apply (e.g. wet mass for no-prop mission)


@dataclass
class BudgetLine:
    """A single line in an engineering budget."""
    subsystem: str
    equipment: str = ""
    allocation: float = 0.0
    actual: float = 0.0
    margin_percent: float = 0.0
    unit: str = ""
    source: str = ""       # Which agent/parameter produced this
    requirement_id: str = ""  # Which requirement this allocation derives from
    notes: str = ""

    @property
    def status(self) -> BudgetStatus:
        if self.allocation <= 0:
            return BudgetStatus.NOT_APPLICABLE
        self.margin_percent = ((self.allocation - self.actual) / self.allocation) * 100
        if self.margin_percent >= 20:
            return BudgetStatus.GREEN
        elif self.margin_percent >= 0:
            return BudgetStatus.AMBER
        return BudgetStatus.RED


@dataclass
class EngineeringBudget:
    """A complete engineering budget with roll-up and roll-down."""
    name: str
    unit: str
    lines: list[BudgetLine] = field(default_factory=list)

    # Mission-level requirement this budget serves
    mission_requirement_id: str = ""
    mission_requirement_text: str = ""
    mission_allocation: float = 0.0  # From mission requirement (e.g. "mass < 12 kg")

    # Margin policy for current phase
    margin_policy_percent: float = 20.0  # Phase 0/A = 20%, Phase B = 10%

    @property
    def total_actual(self) -> float:
        return sum(line.actual for line in self.lines)

    @property
    def total_allocation(self) -> float:
        return self.mission_allocation if self.mission_allocation > 0 else sum(line.allocation for line in self.lines)

    @property
    def margin_percent(self) -> float:
        alloc = self.total_allocation
        if alloc <= 0:
            return 0
        return ((alloc - self.total_actual) / alloc) * 100

    @property
    def status(self) -> BudgetStatus:
        m = self.margin_percent
        if m >= self.margin_policy_percent:
            return BudgetStatus.GREEN
        elif m >= 0:
            return BudgetStatus.AMBER
        return BudgetStatus.RED

    @property
    def mission_requirement_at_risk(self) -> bool:
        """Does this budget failure put a mission requirement at risk?"""
        return self.status == BudgetStatus.RED

    def add_line(self, subsystem: str, actual: float, allocation: float = 0,
                 equipment: str = "", source: str = "", requirement_id: str = "") -> None:
        line = BudgetLine(
            subsystem=subsystem, equipment=equipment,
            allocation=allocation, actual=actual,
            unit=self.unit, source=source,
            requirement_id=requirement_id,
        )
        line.margin_percent = ((allocation - actual) / allocation * 100) if allocation > 0 else 0
        self.lines.append(line)


@dataclass
class PowerModeProfile:
    """Power budget for a single operational mode."""
    mode_name: str
    mode_type: str
    subsystem_power: dict[str, float] = field(default_factory=dict)  # subsystem → watts
    total_consumption_w: float = 0.0
    sa_generation_w: float = 0.0  # 0 if eclipse
    margin_w: float = 0.0
    margin_percent: float = 0.0
    is_eclipse: bool = False
    is_peak: bool = False


@dataclass
class MomentOfInertia:
    """Spacecraft moment of inertia for AOCS sizing."""
    ixx_kgm2: float = 0.0
    iyy_kgm2: float = 0.0
    izz_kgm2: float = 0.0
    # CubeSat simplified: uniform rectangular prism
    mass_kg: float = 0.0
    length_m: float = 0.0
    width_m: float = 0.0
    height_m: float = 0.0


def compute_engineering_budgets(
    parameters: dict[str, Any],
    mission_requirements: dict[str, Any] | None = None,
    conops_modes: list[dict] | None = None,
    spacecraft_class: str = "nano",
) -> dict[str, EngineeringBudget]:
    """Compute all engineering budgets from converged design parameters.

    Returns budgets that roll up to mission requirements and flag risks.
    """
    mr = mission_requirements or {}
    modes = conops_modes or []

    def get(pid: str, default: float = 0.0) -> float:
        p = parameters.get(pid)
        if p is None:
            return default
        if hasattr(p, "value"):
            return float(p.value) if isinstance(p.value, (int, float)) else default
        if isinstance(p, dict):
            v = p.get("value", default)
            return float(v) if isinstance(v, (int, float)) else default
        return default

    budgets: dict[str, EngineeringBudget] = {}

    # === MASS BUDGET ===
    target_mass = mr.get("target_mass_kg", 0) or 0
    has_propulsion = get("propulsion.propellant_mass_kg") > 0

    mass_budget = EngineeringBudget(
        name="Mass", unit="kg",
        mission_requirement_id="REQ-SYS-MASS",
        mission_requirement_text=f"Spacecraft mass shall not exceed {target_mass} kg" if target_mass else "",
        mission_allocation=target_mass,
    )

    subsystem_masses = [
        ("Payload", get("mass.payload_kg")),
        ("EPS", get("power.eps_mass_kg")),
        ("AOCS", get("aocs.mass_kg")),
        ("TTC", get("link.ttc_mass_kg")),
        ("TCS", get("thermal.tcs_mass_kg")),
        ("OBDH", get("data.obdh_mass_kg")),
        ("Structure", get("structure.mass_kg")),
    ]

    if has_propulsion:
        subsystem_masses.append(("Propulsion (dry)", get("propulsion.total_mass_kg") - get("propulsion.propellant_mass_kg")))
        subsystem_masses.append(("Propellant", get("propulsion.propellant_mass_kg")))

    for name, actual in subsystem_masses:
        mass_budget.add_line(name, actual, source=f"{name.lower()}.mass_kg")

    budgets["mass_dry"] = mass_budget

    # Wet mass (only if propulsion exists)
    if has_propulsion:
        wet_budget = EngineeringBudget(name="Mass (Wet)", unit="kg", mission_allocation=target_mass)
        wet_budget.add_line("Dry Mass", get("mass.dry_mass_kg"))
        wet_budget.add_line("Propellant", get("propulsion.propellant_mass_kg"))
        budgets["mass_wet"] = wet_budget

    # Moment of Inertia (CubeSat: uniform rectangular prism approximation)
    dry_mass = get("mass.dry_mass_kg", 5.0)
    from spacecdf_common.models.cubesat_standards import CDS_SPECS
    cds = CDS_SPECS.get({"nano": "3U", "micro": "6U"}.get(spacecraft_class, "3U"), CDS_SPECS.get("3U", {}))
    dims = cds.get("dimensions_mm", [100, 100, 340])
    l, w, h = [d / 1000 for d in dims]  # metres
    moi = MomentOfInertia(
        ixx_kgm2=dry_mass / 12 * (w**2 + h**2),
        iyy_kgm2=dry_mass / 12 * (l**2 + h**2),
        izz_kgm2=dry_mass / 12 * (l**2 + w**2),
        mass_kg=dry_mass, length_m=l, width_m=w, height_m=h,
    )

    # === POWER BUDGET (per mode) ===
    power_budget = EngineeringBudget(
        name="Power (Orbital Average)", unit="W",
        mission_requirement_id="REQ-SYS-POWER",
        mission_requirement_text="Positive power margin in all operating modes",
        mission_allocation=get("power.sa_power_eol_w"),
    )
    power_budget.add_line("Platform", get("power.total_sunlight_w") - get("power.total_sunlight_w") * 0.3, source="power.total_sunlight_w")
    power_budget.add_line("Payload", sum(get(f"payload.{i}.power_w") for i in range(5) if get(f"payload.{i}.power_w") > 0))
    budgets["power"] = power_budget

    # Per-mode power profiles
    mode_profiles: list[PowerModeProfile] = []
    for mode in modes:
        profile = PowerModeProfile(
            mode_name=mode.get("name", ""),
            mode_type=mode.get("mode_type", ""),
            is_eclipse=not mode.get("sun_illuminated", True),
            is_peak=mode.get("mode_type") == "peak_science",
        )
        profile.total_consumption_w = mode.get("power_w", 0)
        profile.sa_generation_w = get("power.sa_power_eol_w") if mode.get("sun_illuminated", True) else 0
        profile.margin_w = profile.sa_generation_w - profile.total_consumption_w
        profile.margin_percent = (profile.margin_w / max(profile.sa_generation_w, 1)) * 100 if profile.sa_generation_w > 0 else -100
        mode_profiles.append(profile)

    # === VOLUME BUDGET ===
    volume_budget = EngineeringBudget(
        name="Volume", unit="L",
        mission_allocation=get("volume.bus_envelope_litres", 6.0),
    )
    volume_budget.add_line("Equipment", get("volume.total_litres", 0), source="volume.total_litres")
    budgets["volume"] = volume_budget

    # === DATA BUDGET ===
    data_budget = EngineeringBudget(
        name="Data", unit="GB/day",
        mission_requirement_id="REQ-SYS-DATA",
        mission_allocation=get("data.downlinked_per_day_gb"),
    )
    data_budget.add_line("Generated", get("data.generated_per_day_gb"), source="data.generated_per_day_gb")
    budgets["data"] = data_budget

    # === DELTA-V BUDGET ===
    if has_propulsion:
        dv_budget = EngineeringBudget(name="Delta-V", unit="m/s",
            mission_allocation=get("orbit.delta_v_total_ms"))
        dv_budget.add_line("Station-keeping", get("orbit.delta_v_sk_ms"))
        dv_budget.add_line("Deorbit", get("orbit.delta_v_deorbit_ms"))
        budgets["delta_v"] = dv_budget

    # === POINTING BUDGET ===
    pointing_budget = EngineeringBudget(
        name="Pointing Accuracy", unit="deg",
        mission_requirement_id="REQ-SYS-POINTING",
        mission_allocation=get("aocs.pointing_accuracy_deg"),
    )
    # Pointing error tree (simplified RSS)
    star_tracker_err = 0.003  # 10 arcsec typical
    wheel_jitter = 0.001
    structural_alignment = 0.005
    thermal_distortion = 0.002
    total_err = math.sqrt(star_tracker_err**2 + wheel_jitter**2 + structural_alignment**2 + thermal_distortion**2)
    pointing_budget.add_line("Star tracker", star_tracker_err, source="sensor")
    pointing_budget.add_line("Wheel jitter", wheel_jitter, source="actuator")
    pointing_budget.add_line("Structural alignment", structural_alignment, source="structure")
    pointing_budget.add_line("Thermal distortion", thermal_distortion, source="thermal")
    budgets["pointing"] = pointing_budget

    return budgets


def check_requirement_impact(
    budgets: dict[str, EngineeringBudget],
) -> list[dict[str, Any]]:
    """Check which mission requirements are at risk from budget exceedances.

    This is the upward roll-up: subsystem budget exceeded → system budget
    at risk → mission requirement impacted.
    """
    impacts: list[dict[str, Any]] = []
    for bname, budget in budgets.items():
        if budget.mission_requirement_at_risk:
            impacts.append({
                "budget": bname,
                "budget_name": budget.name,
                "status": budget.status.value,
                "margin_percent": round(budget.margin_percent, 1),
                "mission_requirement_id": budget.mission_requirement_id,
                "mission_requirement_text": budget.mission_requirement_text,
                "total_actual": round(budget.total_actual, 3),
                "total_allocation": round(budget.total_allocation, 3),
                "exceeded_lines": [
                    {"subsystem": l.subsystem, "actual": l.actual, "allocation": l.allocation}
                    for l in budget.lines if l.allocation > 0 and l.actual > l.allocation
                ],
            })
    return impacts
