"""SpaceCDF -- Constraint Propagation Engine.

Maps ALL design point interconnections across the tool and provides:
1. Violation detection: which budgets/constraints are violated?
2. Root cause analysis: which parameters drive the violation?
3. Downstream impact: what else does this affect?
4. Resolution options: what can be changed to fix it, with cross-budget impact?

This is the core concurrent engineering intelligence that makes a CDF tool
useful beyond simple calculation -- it REASONS about what to do when
constraints conflict.

Design Point Interconnection Map:
  Every design parameter affects multiple budgets/constraints simultaneously.
  When one changes, cascading effects propagate through the system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DesignConstraint:
    """A constraint that can be violated."""
    id: str
    name: str
    budget_type: str  # mass, power, link, pointing, volume, deltav, data, cost, thermal
    parameter_id: str
    operator: str  # <=, >=, ==
    limit_value: float
    current_value: float
    unit: str
    status: str = "ok"  # ok, warning, violated
    margin_pct: float = 0.0


@dataclass
class DesignImpact:
    """Impact of changing one parameter on another."""
    source_param: str
    target_param: str
    target_budget: str
    relationship: str  # "increases", "decreases", "constrains"
    sensitivity: float  # approximate: delta_target per unit delta_source
    description: str


@dataclass
class Resolution:
    """A suggested resolution for a constraint violation."""
    id: str
    description: str
    parameter_to_change: str
    direction: str  # "increase" or "decrease"
    estimated_change: float
    unit: str
    impacts: list[DesignImpact] = field(default_factory=list)
    trade_off: str = ""  # human-readable trade-off description


@dataclass
class ConstraintViolation:
    """A detected constraint violation with analysis."""
    constraint: DesignConstraint
    root_causes: list[str]
    downstream_impacts: list[DesignImpact]
    resolutions: list[Resolution]


# ===========================================================================
# MASTER INTERCONNECTION MAP (187 connections from exhaustive research)
# ===========================================================================
# Import the full 187-connection map auto-generated from CDF research
from .interconnection_data import FULL_INTERCONNECTION_MAP

# Use full map as primary; legacy 50-connection map below as fallback
INTERCONNECTION_MAP = FULL_INTERCONNECTION_MAP

# Legacy map (original 50 connections) — kept as subset for quick checks
_LEGACY_MAP: list[dict[str, Any]] = []
# Every row: when SOURCE changes, it affects TARGET in TARGET_BUDGET
# This is the complete dependency graph of a CubeSat design

INTERCONNECTION_MAP: list[dict[str, Any]] = [
    # --- ORBIT affects everything ---
    {"source": "orbit.altitude_km", "target": "link.fspl_db", "budget": "link", "rel": "increases", "sens": 0.01, "desc": "Higher altitude = longer range = more path loss"},
    {"source": "orbit.altitude_km", "target": "debris.lifetime_years", "budget": "mass", "rel": "increases", "sens": 10, "desc": "Higher altitude = longer natural lifetime (may need propulsion)"},
    {"source": "orbit.altitude_km", "target": "payload.gsd_m", "budget": "pointing", "rel": "increases", "sens": 0.02, "desc": "Higher altitude = worse GSD (need larger aperture)"},
    {"source": "orbit.altitude_km", "target": "power.eclipse_fraction", "budget": "power", "rel": "decreases", "sens": -0.0001, "desc": "Higher altitude = slightly shorter eclipse"},
    {"source": "orbit.altitude_km", "target": "radiation.tid_krad", "budget": "mass", "rel": "increases", "sens": 0.01, "desc": "Higher altitude = more radiation (above 600km)"},
    {"source": "orbit.altitude_km", "target": "thermal.max_temp_c", "budget": "thermal", "rel": "varies", "sens": 0, "desc": "Altitude affects thermal environment (albedo, IR)"},

    # --- PAYLOAD drives power, data, pointing, mass ---
    {"source": "payload.power_w", "target": "power.total_demand_w", "budget": "power", "rel": "increases", "sens": 1.0, "desc": "More payload power = more SA/battery needed"},
    {"source": "payload.power_w", "target": "thermal.dissipation_w", "budget": "thermal", "rel": "increases", "sens": 0.8, "desc": "More payload power = more waste heat to reject"},
    {"source": "payload.mass_kg", "target": "mass.dry_mass_kg", "budget": "mass", "rel": "increases", "sens": 1.0, "desc": "Heavier payload = less margin for bus"},
    {"source": "payload.data_rate_mbps", "target": "data.generation_gb_day", "budget": "data", "rel": "increases", "sens": 0.01, "desc": "Higher data rate = more storage + downlink needed"},
    {"source": "payload.data_rate_mbps", "target": "link.required_rate_mbps", "budget": "link", "rel": "increases", "sens": 1.0, "desc": "More payload data = need higher link capacity"},
    {"source": "payload.pointing_accuracy_deg", "target": "aocs.pointing_req_deg", "budget": "pointing", "rel": "constrains", "sens": 1.0, "desc": "Tighter payload pointing = more capable AOCS needed"},
    {"source": "payload.duty_cycle_pct", "target": "power.orbit_avg_w", "budget": "power", "rel": "increases", "sens": 0.01, "desc": "Higher duty cycle = higher orbit-average power"},
    {"source": "payload.duty_cycle_pct", "target": "data.generation_gb_day", "budget": "data", "rel": "increases", "sens": 0.1, "desc": "Higher duty cycle = more data generated per orbit"},

    # --- POWER (SA/battery) interacts with mass, volume, thermal ---
    {"source": "power.sa_area_m2", "target": "mass.eps_mass_kg", "budget": "mass", "rel": "increases", "sens": 2.5, "desc": "Larger SA = heavier (2.5 kg/m2 body-mount, 1.5 deployable)"},
    {"source": "power.sa_area_m2", "target": "volume.sa_volume_cm3", "budget": "volume", "rel": "increases", "sens": 1000, "desc": "Larger SA panels consume volume (stowed)"},
    {"source": "power.sa_area_m2", "target": "thermal.radiator_competition", "budget": "thermal", "rel": "constrains", "sens": 1.0, "desc": "SA area competes with radiator area on external surfaces"},
    {"source": "power.battery_capacity_wh", "target": "mass.battery_mass_kg", "budget": "mass", "rel": "increases", "sens": 0.0067, "desc": "Bigger battery = heavier (150 Wh/kg)"},
    {"source": "power.battery_capacity_wh", "target": "volume.battery_volume_cm3", "budget": "volume", "rel": "increases", "sens": 3.0, "desc": "Bigger battery takes more volume"},

    # --- AOCS complexity drives mass, power, cost ---
    {"source": "aocs.pointing_accuracy_deg", "target": "aocs.mass_kg", "budget": "mass", "rel": "decreases", "sens": -5.0, "desc": "Tighter pointing = heavier AOCS (more hardware: RW, ST)"},
    {"source": "aocs.pointing_accuracy_deg", "target": "aocs.power_w", "budget": "power", "rel": "decreases", "sens": -30, "desc": "Tighter pointing = more AOCS power (reaction wheels active)"},
    {"source": "aocs.pointing_accuracy_deg", "target": "aocs.cost_keur", "budget": "cost", "rel": "decreases", "sens": -200, "desc": "Tighter pointing = more expensive AOCS hardware"},
    {"source": "aocs.num_wheels", "target": "aocs.vibration_arcsec", "budget": "pointing", "rel": "increases", "sens": 2, "desc": "More wheels = more vibration sources affecting payload"},
    {"source": "aocs.num_wheels", "target": "mass.aocs_mass_kg", "budget": "mass", "rel": "increases", "sens": 0.12, "desc": "Each additional wheel adds ~120g"},

    # --- LINK (TX power/antenna) drives power, mass, thermal ---
    {"source": "link.tx_power_w", "target": "link.margin_db", "budget": "link", "rel": "increases", "sens": 3.0, "desc": "Doubling TX power adds 3dB link margin"},
    {"source": "link.tx_power_w", "target": "power.ttc_power_w", "budget": "power", "rel": "increases", "sens": 3.3, "desc": "Higher TX RF power = higher DC power (30% PA efficiency)"},
    {"source": "link.tx_power_w", "target": "thermal.ttc_dissipation_w", "budget": "thermal", "rel": "increases", "sens": 2.3, "desc": "70% of TX DC power becomes heat"},
    {"source": "link.tx_power_w", "target": "mass.ttc_mass_kg", "budget": "mass", "rel": "increases", "sens": 0.05, "desc": "Higher power TX = heavier amplifier"},
    {"source": "link.antenna_gain_dbi", "target": "link.margin_db", "budget": "link", "rel": "increases", "sens": 1.0, "desc": "Higher gain antenna improves link directly"},
    {"source": "link.antenna_gain_dbi", "target": "aocs.pointing_req_deg", "budget": "pointing", "rel": "decreases", "sens": -0.5, "desc": "Higher gain antenna = narrower beam = tighter pointing needed"},
    {"source": "link.antenna_gain_dbi", "target": "mass.antenna_mass_kg", "budget": "mass", "rel": "increases", "sens": 0.02, "desc": "Higher gain = larger/heavier antenna"},
    {"source": "link.data_rate_mbps", "target": "link.margin_db", "budget": "link", "rel": "decreases", "sens": -0.3, "desc": "Higher data rate requires more Eb/N0 (reduces margin)"},
    {"source": "link.frequency_ghz", "target": "link.fspl_db", "budget": "link", "rel": "increases", "sens": 6.0, "desc": "Doubling frequency adds 6dB path loss"},
    {"source": "link.frequency_ghz", "target": "link.antenna_size_m", "budget": "volume", "rel": "decreases", "sens": -0.1, "desc": "Higher frequency = smaller antenna for same gain"},

    # --- STRUCTURE (form factor) constrains volume ---
    {"source": "structure.form_factor_u", "target": "volume.available_cm3", "budget": "volume", "rel": "increases", "sens": 1000, "desc": "Each U = 1000 cm3 internal volume"},
    {"source": "structure.form_factor_u", "target": "mass.allocation_kg", "budget": "mass", "rel": "increases", "sens": 2.0, "desc": "CDS limit: ~2 kg per U"},
    {"source": "structure.form_factor_u", "target": "power.sa_area_available_m2", "budget": "power", "rel": "increases", "sens": 0.01, "desc": "Larger form factor = more body area for SA"},
    {"source": "structure.form_factor_u", "target": "cost.launch_keur", "budget": "cost", "rel": "increases", "sens": 50, "desc": "Larger form factor = more expensive launch slot"},

    # --- PROPULSION drives mass, volume, cost ---
    {"source": "propulsion.delta_v_ms", "target": "propulsion.propellant_mass_kg", "budget": "mass", "rel": "increases", "sens": 0.01, "desc": "More dV = more propellant (Tsiolkovsky)"},
    {"source": "propulsion.delta_v_ms", "target": "propulsion.tank_volume_cm3", "budget": "volume", "rel": "increases", "sens": 5.0, "desc": "More propellant = larger tank"},
    {"source": "propulsion.isp_s", "target": "propulsion.propellant_mass_kg", "budget": "mass", "rel": "decreases", "sens": -0.001, "desc": "Higher Isp = less propellant for same dV"},
    {"source": "propulsion.type", "target": "propulsion.power_w", "budget": "power", "rel": "varies", "sens": 0, "desc": "Electric propulsion needs 10-50W; cold gas needs ~0W"},

    # --- THERMAL drives mass, power ---
    {"source": "thermal.radiator_area_m2", "target": "thermal.max_temp_c", "budget": "thermal", "rel": "decreases", "sens": -100, "desc": "Larger radiator = lower hot-case temperature"},
    {"source": "thermal.radiator_area_m2", "target": "mass.thermal_mass_kg", "budget": "mass", "rel": "increases", "sens": 0.5, "desc": "Radiator panels add mass"},
    {"source": "thermal.heater_power_w", "target": "power.eclipse_demand_w", "budget": "power", "rel": "increases", "sens": 1.0, "desc": "Eclipse heaters consume battery power"},
    {"source": "thermal.heater_power_w", "target": "power.battery_capacity_wh", "budget": "power", "rel": "increases", "sens": 0.6, "desc": "More heater power = bigger battery needed for eclipse"},

    # --- COST cascades ---
    {"source": "mass.dry_mass_kg", "target": "cost.launch_keur", "budget": "cost", "rel": "increases", "sens": 7.0, "desc": "Heavier spacecraft = more expensive launch ($7K/kg rideshare)"},
    {"source": "aocs.cost_keur", "target": "cost.total_keur", "budget": "cost", "rel": "increases", "sens": 1.0, "desc": "AOCS hardware cost contributes directly"},
    {"source": "mission.duration_years", "target": "cost.operations_keur", "budget": "cost", "rel": "increases", "sens": 100, "desc": "Longer mission = more operations cost"},
    {"source": "mission.duration_years", "target": "power.sa_degradation_pct", "budget": "power", "rel": "increases", "sens": 2.5, "desc": "Longer mission = more SA degradation (2.5%/yr)"},
    {"source": "mission.duration_years", "target": "radiation.tid_krad", "budget": "mass", "rel": "increases", "sens": 5, "desc": "Longer mission = more radiation dose"},

    # --- DATA budget cascades ---
    {"source": "data.storage_gb", "target": "mass.obc_mass_kg", "budget": "mass", "rel": "increases", "sens": 0.001, "desc": "More storage = heavier memory modules"},
    {"source": "data.storage_gb", "target": "volume.obc_volume_cm3", "budget": "volume", "rel": "increases", "sens": 0.5, "desc": "More storage takes volume"},
    {"source": "link.contact_min_per_day", "target": "data.downlink_gb_day", "budget": "data", "rel": "increases", "sens": 0.01, "desc": "More contact time = more data downlinked per day"},
    {"source": "ground.num_stations", "target": "link.contact_min_per_day", "budget": "data", "rel": "increases", "sens": 15, "desc": "More ground stations = more passes = more contact time"},
    {"source": "ground.num_stations", "target": "cost.ground_keur", "budget": "cost", "rel": "increases", "sens": 50, "desc": "More stations = higher ground segment cost"},
]


# ===========================================================================
# RESOLUTION RULES
# ===========================================================================
# For each budget type that can be violated, define resolution options

RESOLUTION_RULES: dict[str, list[dict[str, Any]]] = {
    "mass_exceeded": [
        {"desc": "Reduce payload mass (de-scope instrument)", "param": "payload.mass_kg", "dir": "decrease", "impacts": ["performance"]},
        {"desc": "Use lighter AOCS (coarser pointing, fewer wheels)", "param": "aocs.mass_kg", "dir": "decrease", "impacts": ["pointing", "performance"]},
        {"desc": "Remove propulsion (accept natural deorbit)", "param": "propulsion.total_mass_kg", "dir": "decrease", "impacts": ["deltav", "compliance"]},
        {"desc": "Use larger form factor (more mass allocation)", "param": "structure.form_factor_u", "dir": "increase", "impacts": ["volume", "cost"]},
        {"desc": "Use lighter structure material", "param": "structure.mass_kg", "dir": "decrease", "impacts": ["cost"]},
        {"desc": "Reduce battery capacity (accept reduced eclipse operations)", "param": "power.battery_capacity_wh", "dir": "decrease", "impacts": ["power"]},
    ],
    "power_exceeded": [
        {"desc": "Reduce payload duty cycle", "param": "payload.duty_cycle_pct", "dir": "decrease", "impacts": ["data", "performance"]},
        {"desc": "Add deployable solar panels", "param": "power.sa_area_m2", "dir": "increase", "impacts": ["mass", "volume", "cost"]},
        {"desc": "Reduce TX power (accept lower link margin)", "param": "link.tx_power_w", "dir": "decrease", "impacts": ["link"]},
        {"desc": "Use coarser AOCS (less power for wheels)", "param": "aocs.pointing_accuracy_deg", "dir": "increase", "impacts": ["pointing", "mass"]},
        {"desc": "Reduce heater power (accept colder cold case)", "param": "thermal.heater_power_w", "dir": "decrease", "impacts": ["thermal"]},
        {"desc": "Use larger form factor (more SA area)", "param": "structure.form_factor_u", "dir": "increase", "impacts": ["mass", "volume", "cost"]},
    ],
    "link_violated": [
        {"desc": "Increase TX power", "param": "link.tx_power_w", "dir": "increase", "impacts": ["power", "thermal", "mass"]},
        {"desc": "Use higher-gain antenna", "param": "link.antenna_gain_dbi", "dir": "increase", "impacts": ["mass", "pointing", "volume"]},
        {"desc": "Reduce data rate (accept longer download time)", "param": "link.data_rate_mbps", "dir": "decrease", "impacts": ["data"]},
        {"desc": "Use lower frequency band (less FSPL)", "param": "link.frequency_ghz", "dir": "decrease", "impacts": ["volume", "data"]},
        {"desc": "Add ground stations (more contact time)", "param": "ground.num_stations", "dir": "increase", "impacts": ["cost", "data"]},
        {"desc": "Use more powerful coding (lower Eb/N0 threshold)", "param": "link.coding_gain_db", "dir": "increase", "impacts": []},
    ],
    "pointing_violated": [
        {"desc": "Add star tracker (finer attitude knowledge)", "param": "aocs.sensor_accuracy_arcsec", "dir": "decrease", "impacts": ["mass", "power", "cost"]},
        {"desc": "Add reaction wheels (finer control)", "param": "aocs.num_wheels", "dir": "increase", "impacts": ["mass", "power", "cost"]},
        {"desc": "Improve mechanical alignment (tighter tolerances)", "param": "aocs.alignment_deg", "dir": "decrease", "impacts": ["cost"]},
        {"desc": "Add vibration isolators (reduce jitter)", "param": "aocs.jitter_arcsec", "dir": "decrease", "impacts": ["mass", "cost"]},
        {"desc": "Relax pointing requirement (accept coarser)", "param": "payload.pointing_accuracy_deg", "dir": "increase", "impacts": ["performance"]},
    ],
    "volume_exceeded": [
        {"desc": "Use larger form factor", "param": "structure.form_factor_u", "dir": "increase", "impacts": ["mass", "cost"]},
        {"desc": "Remove propulsion system", "param": "propulsion.total_mass_kg", "dir": "decrease", "impacts": ["deltav", "mass"]},
        {"desc": "Use more compact components", "param": "volume.utilisation_pct", "dir": "decrease", "impacts": ["cost"]},
        {"desc": "Use deployable SA instead of body-mounted (frees body volume)", "param": "power.sa_type", "dir": "change", "impacts": ["mass", "cost"]},
    ],
    "data_imbalanced": [
        {"desc": "Increase downlink data rate", "param": "link.data_rate_mbps", "dir": "increase", "impacts": ["link", "power"]},
        {"desc": "Add ground stations for more contact time", "param": "ground.num_stations", "dir": "increase", "impacts": ["cost"]},
        {"desc": "Reduce payload duty cycle (generate less data)", "param": "payload.duty_cycle_pct", "dir": "decrease", "impacts": ["performance"]},
        {"desc": "Add on-board data compression", "param": "data.compression_ratio", "dir": "increase", "impacts": ["power"]},
        {"desc": "Increase onboard storage (buffer more orbits)", "param": "data.storage_gb", "dir": "increase", "impacts": ["mass", "volume"]},
    ],
    "thermal_exceeded": [
        {"desc": "Increase radiator area", "param": "thermal.radiator_area_m2", "dir": "increase", "impacts": ["mass", "power"]},
        {"desc": "Reduce payload duty cycle (less waste heat)", "param": "payload.duty_cycle_pct", "dir": "decrease", "impacts": ["data", "performance"]},
        {"desc": "Reduce TX power (less PA waste heat)", "param": "link.tx_power_w", "dir": "decrease", "impacts": ["link"]},
        {"desc": "Change orbit (reduce solar exposure)", "param": "orbit.altitude_km", "dir": "varies", "impacts": ["link", "mass"]},
    ],
    "cost_exceeded": [
        {"desc": "Use simpler AOCS (coarser pointing)", "param": "aocs.pointing_accuracy_deg", "dir": "increase", "impacts": ["pointing", "performance"]},
        {"desc": "Use amateur band (free licensing)", "param": "link.license_type", "dir": "change", "impacts": ["link", "data"]},
        {"desc": "Remove propulsion", "param": "propulsion.total_mass_kg", "dir": "decrease", "impacts": ["deltav", "mass"]},
        {"desc": "Use smaller form factor (cheaper launch)", "param": "structure.form_factor_u", "dir": "decrease", "impacts": ["volume", "mass"]},
        {"desc": "Reduce mission duration (less operations cost)", "param": "mission.duration_years", "dir": "decrease", "impacts": ["data"]},
        {"desc": "Use COTS components exclusively (no custom development)", "param": "cost.nre_fraction", "dir": "decrease", "impacts": []},
    ],
}


def analyze_violations(design_params: dict[str, float], constraints: dict[str, float]) -> list[ConstraintViolation]:
    """Analyze all constraint violations and provide resolution options.

    Args:
        design_params: Current design parameter values
        constraints: Budget allocations/limits

    Returns:
        List of violations with root causes, impacts, and resolutions
    """
    violations = []

    # Check each budget type
    checks = [
        ("mass_exceeded", "mass.dry_mass_kg", "<=", constraints.get("mass_allocation_kg", 6)),
        ("power_exceeded", "power.total_demand_w", "<=", constraints.get("power_available_w", 15)),
        ("link_violated", "link.margin_db", ">=", 3.0),
        ("volume_exceeded", "volume.utilisation_pct", "<=", 85),
        ("data_imbalanced", "data.balance_gb", ">=", 0),
        ("cost_exceeded", "cost.total_keur", "<=", constraints.get("cost_ceiling_keur", 5000)),
    ]

    for violation_type, param_id, op, limit in checks:
        value = design_params.get(param_id, 0)
        violated = (op == "<=" and value > limit) or (op == ">=" and value < limit)

        if violated:
            # Find root causes from interconnection map
            root_causes = []
            for conn in INTERCONNECTION_MAP:
                if conn["target"] == param_id or param_id.startswith(conn["target"].split(".")[0]):
                    root_causes.append(f"{conn['source']}: {conn['desc']}")

            # Find downstream impacts
            impacts = []
            for conn in INTERCONNECTION_MAP:
                if conn["source"] == param_id or param_id.startswith(conn["source"].split(".")[0]):
                    impacts.append(DesignImpact(
                        source_param=param_id,
                        target_param=conn["target"],
                        target_budget=conn["budget"],
                        relationship=conn["rel"],
                        sensitivity=conn["sens"],
                        description=conn["desc"],
                    ))

            # Get resolution options
            resolutions = []
            for rule in RESOLUTION_RULES.get(violation_type, []):
                resolutions.append(Resolution(
                    id=f"res-{violation_type}-{rule['param']}",
                    description=rule["desc"],
                    parameter_to_change=rule["param"],
                    direction=rule["dir"],
                    estimated_change=0,
                    unit="",
                    trade_off=f"Affects: {', '.join(rule['impacts'])}" if rule["impacts"] else "No other budget impact",
                ))

            constraint = DesignConstraint(
                id=violation_type, name=violation_type.replace("_", " ").title(),
                budget_type=violation_type.split("_")[0], parameter_id=param_id,
                operator=op, limit_value=limit, current_value=value, unit="",
                status="violated", margin_pct=((limit - value) / max(abs(limit), 0.01)) * 100,
            )

            violations.append(ConstraintViolation(
                constraint=constraint,
                root_causes=root_causes[:5],
                downstream_impacts=impacts[:5],
                resolutions=resolutions,
            ))

    return violations


def get_interconnection_map() -> list[dict[str, Any]]:
    """Return the full interconnection map for UI visualization."""
    return INTERCONNECTION_MAP


def get_resolution_options(violation_type: str) -> list[dict[str, Any]]:
    """Get resolution options for a specific violation type."""
    return RESOLUTION_RULES.get(violation_type, [])


# ===========================================================================
# REQUIREMENT COMPLIANCE CASCADE
# ===========================================================================
# When a parameter changes, trace UP through the requirement hierarchy
# to determine if mission/system requirements are still met.

def check_requirement_compliance(
    changed_param: str,
    new_value: float,
    requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Check if a parameter change violates any requirements at any level.

    Traces upward: subsystem requirement → system requirement → mission requirement.
    Returns violations at the HIGHEST level affected.

    Args:
        changed_param: The parameter ID that changed
        new_value: Its new value
        requirements: List of requirements with {id, level, text, threshold, operator, parameter_id}
    """
    violations = []

    for req in requirements:
        # Check if this requirement references the changed parameter
        param_ids = req.get("parameter_ids", [])
        req_param = req.get("parameter_id", "")
        if changed_param not in param_ids and changed_param != req_param:
            # Check if the parameter domain matches
            changed_domain = changed_param.split(".")[0]
            req_domain = req.get("domain", "")
            if changed_domain != req_domain:
                continue

        threshold = req.get("threshold")
        operator = req.get("operator", "<=")
        if threshold is None:
            continue

        # Check compliance
        compliant = True
        if operator == "<=" and new_value > threshold:
            compliant = False
        elif operator == ">=" and new_value < threshold:
            compliant = False
        elif operator == "==" and abs(new_value - threshold) > threshold * 0.1:
            compliant = False

        if not compliant:
            violations.append({
                "requirement_id": req.get("id", ""),
                "requirement_text": req.get("text", ""),
                "level": req.get("level", "subsystem"),
                "threshold": threshold,
                "operator": operator,
                "achieved_value": new_value,
                "parameter": changed_param,
                "compliance": "VIOLATED",
                "parent_requirement": req.get("parent_id"),
            })

    # Sort by level priority: mission > system > subsystem
    level_order = {"mission": 0, "system": 1, "subsystem": 2}
    violations.sort(key=lambda v: level_order.get(v["level"], 3))

    return violations


def detect_circular_dependencies(
    starting_param: str,
    resolution_param: str,
) -> list[list[str]]:
    """Detect if resolving a violation creates a circular dependency.

    A circular dependency occurs when:
    - Fixing budget A requires changing parameter X
    - Changing X affects budget B
    - Budget B was already tight
    - Fixing B requires changing parameter Y
    - Changing Y affects budget A again

    Returns list of detected cycles (each cycle = list of param IDs in the loop).
    """
    cycles = []
    visited = set()
    path = []

    def _dfs(param: str, depth: int = 0):
        if depth > 6:  # Max depth to prevent infinite recursion
            return
        if param in visited:
            # Found a cycle
            cycle_start = path.index(param) if param in path else -1
            if cycle_start >= 0:
                cycles.append(path[cycle_start:] + [param])
            return

        visited.add(param)
        path.append(param)

        # Find what this parameter affects
        for conn in INTERCONNECTION_MAP:
            if conn["source"] == param or param.startswith(conn["source"].split(".")[0]):
                _dfs(conn["target"], depth + 1)

        path.pop()
        visited.discard(param)

    _dfs(resolution_param)

    # Filter to only cycles that include the starting parameter
    relevant_cycles = [c for c in cycles if starting_param in c or any(starting_param.startswith(p.split(".")[0]) for p in c)]

    return relevant_cycles[:3]  # Return top 3 cycles found
