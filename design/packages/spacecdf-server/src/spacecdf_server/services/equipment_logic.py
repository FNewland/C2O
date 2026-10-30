"""SpaceCDF — Equipment Compatibility & Requirement-Driven Selection Logic.

Determines:
  1. Which equipment categories are NEEDED for a given design
  2. Which components are COMPATIBLE with each other (frequency, interface, voltage)
  3. What quantity of each component type is needed
  4. Live budget impact of selections (mass, power, volume roll-up)
  5. Which optimizer variables/objectives are relevant

References:
  - CubeSat Design Specification (Cal Poly CDS Rev 14) for interface standards
  - ECSS-E-ST-20C for power bus compatibility
  - ECSS-E-ST-50-05C for RF chain compatibility
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Equipment need rules: what a mission REQUIRES
# ---------------------------------------------------------------------------

@dataclass
class EquipmentNeed:
    """A category of equipment the mission needs."""
    category: str
    reason: str
    quantity: int = 1
    required: bool = True  # False = optional/nice-to-have
    notes: str = ""


def determine_equipment_needs(
    mission_type: str = "earth_observation",
    pointing_accuracy_deg: float = 1.0,
    has_propulsion: bool = False,
    orbit_type: str = "sso",
    altitude_km: float = 500,
    data_rate_mbps: float = 10,
    bus_form_factor: str = "3U",
    mission_duration_years: float = 3.0,
) -> list[EquipmentNeed]:
    """Determine which equipment categories are needed based on requirements.

    Returns a list of EquipmentNeed, each with category, quantity, and rationale.
    """
    needs: list[EquipmentNeed] = []

    # --- Always needed ---
    needs.append(EquipmentNeed("eps_boards", "Every mission needs power management", 1))
    needs.append(EquipmentNeed("batteries", "Energy storage for eclipse and peak loads", 1))
    needs.append(EquipmentNeed("solar_panels", "Primary power generation", 1,
                               notes="Body-mounted or deployable depending on power demand"))
    needs.append(EquipmentNeed("obcs", "Flight computer for ADCS, data handling, TTC", 1))
    needs.append(EquipmentNeed("cubesat_structures", f"Primary structure ({bus_form_factor})", 1))
    needs.append(EquipmentNeed("deployers", "Launch vehicle interface", 1))

    # --- TTC (always needed, but band depends on data rate) ---
    if data_rate_mbps > 50:
        needs.append(EquipmentNeed("transponders", "High-rate X-band or S-band downlink required", 1,
                                   notes="X-band recommended for >50 Mbps"))
        needs.append(EquipmentNeed("antennas", "Directional antenna for high data rate", 1,
                                   notes="Patch or horn antenna for X-band"))
    else:
        needs.append(EquipmentNeed("transponders", "TTC transponder for commanding and telemetry", 1,
                                   notes="UHF or S-band typical for CubeSat"))
        needs.append(EquipmentNeed("antennas", "TTC antenna (dipole or patch)", 1))

    # --- AOCS: driven by pointing requirement ---
    if pointing_accuracy_deg <= 0.1:
        # Fine pointing: star tracker + reaction wheels
        needs.append(EquipmentNeed("star_trackers", "Fine pointing requires star tracker", 1,
                                   notes=f"Pointing req: {pointing_accuracy_deg}° needs stellar reference"))
        needs.append(EquipmentNeed("reaction_wheels", "3-axis fine pointing", 4,
                                   notes="4 wheels (3+1 redundant) for fine pointing"))
        needs.append(EquipmentNeed("magnetorquers", "Momentum dumping", 3))
        needs.append(EquipmentNeed("sun_sensors", "Safe mode attitude reference", 2, required=False))
    elif pointing_accuracy_deg <= 2.0:
        # Medium pointing: sun sensors + reaction wheels (no star tracker)
        needs.append(EquipmentNeed("reaction_wheels", "Medium pointing control", 3,
                                   notes=f"Pointing req: {pointing_accuracy_deg}° — reaction wheels sufficient"))
        needs.append(EquipmentNeed("magnetorquers", "Momentum dumping + coarse control", 3))
        needs.append(EquipmentNeed("sun_sensors", "Attitude reference", 2))
        needs.append(EquipmentNeed("star_trackers", "Could improve pointing margin", 1, required=False,
                                   notes="Optional: would give margin on pointing"))
    else:
        # Coarse pointing: magnetorquers only
        needs.append(EquipmentNeed("magnetorquers", "Coarse attitude control", 3,
                                   notes=f"Pointing req: {pointing_accuracy_deg}° — magnetorquers sufficient"))
        needs.append(EquipmentNeed("sun_sensors", "Basic attitude reference", 2))

    # --- GPS: needed for precise orbit knowledge ---
    if orbit_type in ("sso", "leo") and altitude_km < 2000:
        if pointing_accuracy_deg <= 1.0 or mission_type in ("earth_observation", "sar"):
            needs.append(EquipmentNeed("gps_receivers", "Precise orbit determination for geolocation", 1))
        else:
            needs.append(EquipmentNeed("gps_receivers", "Orbit knowledge", 1, required=False,
                                       notes="Optional: ground-based orbit determination may suffice"))

    # --- Propulsion ---
    if has_propulsion:
        needs.append(EquipmentNeed("thrusters", "Orbit maintenance / deorbit", 1,
                                   notes="Cold gas, electric, or chemical depending on ΔV need"))
    elif altitude_km > 600 and mission_duration_years > 2:
        needs.append(EquipmentNeed("thrusters", "May need propulsion for 25-year deorbit rule", 1,
                                   required=False, notes="Consider drag augmentation as alternative"))

    return needs


# ---------------------------------------------------------------------------
# RF compatibility checking
# ---------------------------------------------------------------------------

# Frequency band ranges (MHz)
RF_BANDS = {
    "UHF": (300, 3000),
    "VHF": (30, 300),
    "S": (2000, 4000),
    "X": (8000, 12000),
    "Ka": (26500, 40000),
    "L": (1000, 2000),
}


def check_rf_compatibility(
    transponder: dict[str, Any],
    antenna: dict[str, Any],
) -> dict[str, Any]:
    """Check if a transponder and antenna are frequency-compatible.

    Returns {compatible: bool, reason: str, details: str}.
    """
    # Extract frequency info
    tx_band = _get_band(transponder)
    ant_band = _get_band(antenna)

    if not tx_band or not ant_band:
        return {"compatible": True, "reason": "unknown", "details": "Cannot determine frequency bands — manual check needed"}

    if tx_band == ant_band:
        return {"compatible": True, "reason": "match", "details": f"Both operate in {tx_band}-band"}

    # Check if bands overlap
    tx_range = RF_BANDS.get(tx_band)
    ant_range = RF_BANDS.get(ant_band)
    if tx_range and ant_range:
        overlap = max(0, min(tx_range[1], ant_range[1]) - max(tx_range[0], ant_range[0]))
        if overlap > 0:
            return {"compatible": True, "reason": "overlap", "details": f"{tx_band} and {ant_band} bands overlap"}

    return {
        "compatible": False,
        "reason": "band_mismatch",
        "details": f"Transponder is {tx_band}-band but antenna is {ant_band}-band — incompatible RF chain",
    }


def _get_band(component: dict) -> str | None:
    """Extract RF band from a component's metadata."""
    for key in ("frequency_band", "band", "rf_band"):
        val = component.get(key)
        if val:
            return val.upper().replace("-BAND", "").strip()
    # Try to infer from frequency
    perf = component.get("performance", {})
    freq_mhz = component.get("frequency_mhz") or perf.get("frequency_mhz") or perf.get("center_frequency_mhz")
    if freq_mhz:
        for band, (lo, hi) in RF_BANDS.items():
            if lo <= freq_mhz <= hi:
                return band
    # Try name
    name = (component.get("name", "") + " " + component.get("description", "")).upper()
    for band in ("UHF", "VHF", "S-BAND", "X-BAND", "KA-BAND", "L-BAND"):
        if band in name:
            return band.replace("-BAND", "")
    return None


# ---------------------------------------------------------------------------
# Interface compatibility
# ---------------------------------------------------------------------------

def check_interface_compatibility(
    component_a: dict[str, Any],
    component_b: dict[str, Any],
) -> dict[str, Any]:
    """Check if two components share a compatible digital interface."""
    ifaces_a = set(_get_interfaces(component_a))
    ifaces_b = set(_get_interfaces(component_b))

    common = ifaces_a & ifaces_b
    if common:
        return {"compatible": True, "shared_interfaces": sorted(common)}
    if not ifaces_a or not ifaces_b:
        return {"compatible": True, "shared_interfaces": [], "note": "Interface data missing — manual check needed"}
    return {"compatible": False, "shared_interfaces": [],
            "note": f"No common interface: {sorted(ifaces_a)} vs {sorted(ifaces_b)}"}


def _get_interfaces(comp: dict) -> list[str]:
    """Extract interface list from component."""
    ifaces = comp.get("interfaces", [])
    if isinstance(ifaces, list):
        return [i.upper() for i in ifaces if isinstance(i, str)]
    return []


# ---------------------------------------------------------------------------
# Live budget impact calculator
# ---------------------------------------------------------------------------

@dataclass
class BudgetImpact:
    """Impact of current equipment selections on system budgets."""
    total_mass_kg: float = 0.0
    total_power_w: float = 0.0
    total_cost_keur: float = 0.0
    total_volume_litres: float = 0.0
    items: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def compute_selection_budget(
    selections: list[dict[str, Any]],
    mass_budget_kg: float | None = None,
    power_budget_w: float | None = None,
) -> BudgetImpact:
    """Compute running budget totals from current equipment selections.

    Each selection: {category, component, quantity}.
    """
    impact = BudgetImpact()

    for sel in selections:
        comp = sel.get("component", {})
        qty = sel.get("quantity", 1)
        cat = sel.get("category", "")

        mass = (comp.get("mass_kg") or 0) * qty
        power = (comp.get("power_w") or 0) * qty
        cost = (comp.get("cost_keur") or 0) * qty

        # Volume: try dimensions
        dims = comp.get("dimensions_mm")
        vol = 0.0
        if dims and isinstance(dims, dict):
            l = dims.get("length", 0) or dims.get("l", 0)
            w = dims.get("width", 0) or dims.get("w", 0)
            h = dims.get("height", 0) or dims.get("h", 0)
            vol = (l * w * h / 1e6) * qty  # mm³ → litres

        impact.total_mass_kg += mass
        impact.total_power_w += power
        impact.total_cost_keur += cost
        impact.total_volume_litres += vol

        impact.items.append({
            "category": cat,
            "name": comp.get("name", "Unknown"),
            "quantity": qty,
            "mass_kg": round(mass, 3),
            "power_w": round(power, 1),
            "cost_keur": round(cost, 0),
        })

    # Budget warnings
    if mass_budget_kg and impact.total_mass_kg > mass_budget_kg:
        impact.warnings.append(
            f"Mass {impact.total_mass_kg:.1f} kg exceeds budget of {mass_budget_kg:.1f} kg"
        )
    if power_budget_w and impact.total_power_w > power_budget_w:
        impact.warnings.append(
            f"Power {impact.total_power_w:.1f} W exceeds budget of {power_budget_w:.1f} W"
        )

    return impact


# ---------------------------------------------------------------------------
# Optimizer relevance filter
# ---------------------------------------------------------------------------

def filter_relevant_objectives(
    mission_type: str = "earth_observation",
    has_propulsion: bool = False,
    has_link: bool = True,
) -> list[str]:
    """Return only the optimizer objectives that are relevant to this mission."""
    relevant = ["min_mass", "min_dry_mass", "min_cost", "max_mass_margin", "max_power_margin", "max_trl"]

    if has_link:
        relevant.append("max_link_margin")
        relevant.append("min_data_latency")

    if has_propulsion:
        relevant.append("max_debris_compliance")

    relevant.append("max_reliability")
    return relevant


def filter_relevant_variables(
    mission_type: str = "earth_observation",
    has_propulsion: bool = False,
    pointing_accuracy_deg: float = 1.0,
) -> list[str]:
    """Return only the design variables that make sense to optimize."""
    relevant = [
        "orbit.altitude_km",
        "payload.power_w",
        "payload.data_volume_per_day_gb",
        "payload.duty_cycle_percent",
        "power.sa_margin_percent",
        "power.battery_dod_percent",
        "link.downlink_data_rate_mbps",
    ]

    if has_propulsion:
        relevant.append("propulsion.total_dv_ms")

    if pointing_accuracy_deg <= 2.0:
        relevant.append("aocs.pointing_accuracy_deg")

    if mission_type in ("earth_observation", "sar"):
        relevant.append("orbit.inclination_deg")

    # Only include thermal if thermal is active
    relevant.append("thermal.radiator_area_m2")

    return relevant
