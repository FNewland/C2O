"""SpaceCDF — Propulsion design equations.

Computes propellant mass, thruster selection, and propulsion system sizing
using the Tsiolkovsky rocket equation and parametric models.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

G0 = 9.80665  # m/s^2


@dataclass
class PropulsionDesignResult:
    """Result of propulsion design analysis."""

    propellant_mass_kg: float = 0.0
    tank_mass_kg: float = 0.0
    thruster_mass_kg: float = 0.0
    feed_system_mass_kg: float = 0.0
    total_propulsion_mass_kg: float = 0.0
    wet_mass_kg: float = 0.0
    isp_s: float = 0.0
    thrust_n: float = 0.0
    propulsion_type: str = ""
    total_delta_v_ms: float = 0.0
    burn_time_s: float = 0.0
    propulsion_cost_keur: float = 0.0
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# Common propulsion system ISP and thrust ranges
PROPULSION_TYPES = {
    "cold_gas": {"isp_s": 65, "thrust_range_n": (0.001, 1.0), "tank_fraction": 0.10, "cost_factor": 0.5},
    "monoprop_hydrazine": {"isp_s": 220, "thrust_range_n": (0.5, 22.0), "tank_fraction": 0.12, "cost_factor": 1.0},
    "monoprop_green": {"isp_s": 240, "thrust_range_n": (0.1, 22.0), "tank_fraction": 0.12, "cost_factor": 1.2},
    "biprop": {"isp_s": 310, "thrust_range_n": (10.0, 22000.0), "tank_fraction": 0.15, "cost_factor": 2.0},
    "electric_hall": {"isp_s": 1500, "thrust_range_n": (0.01, 0.5), "tank_fraction": 0.05, "cost_factor": 3.0},
    "electric_ion": {"isp_s": 3000, "thrust_range_n": (0.001, 0.1), "tank_fraction": 0.05, "cost_factor": 4.0},
    "electric_ppt": {"isp_s": 1000, "thrust_range_n": (0.0001, 0.01), "tank_fraction": 0.03, "cost_factor": 2.5},
    "electric_resistojet": {"isp_s": 300, "thrust_range_n": (0.01, 0.5), "tank_fraction": 0.08, "cost_factor": 1.5},
}


def tsiolkovsky(delta_v_ms: float, isp_s: float, dry_mass_kg: float) -> float:
    """Compute propellant mass using Tsiolkovsky rocket equation.

    m_prop = m_dry * (exp(dv / (Isp * g0)) - 1)
    """
    if delta_v_ms <= 0 or isp_s <= 0:
        return 0.0
    mass_ratio = math.exp(delta_v_ms / (isp_s * G0))
    return dry_mass_kg * (mass_ratio - 1)


def select_propulsion_type(
    delta_v_ms: float,
    spacecraft_mass_kg: float,
    available_power_w: float = 100.0,
    preference: str = "auto",
) -> str:
    """Select appropriate propulsion type based on delta-V and spacecraft size.

    Rules of thumb:
    - dV < 10 m/s: cold gas
    - dV < 100 m/s, small sat: monoprop (green preferred for innovation)
    - dV < 500 m/s: monoprop or electric (if time allows)
    - dV < 2000 m/s: biprop or electric
    - dV > 2000 m/s: biprop (or electric for very patient missions)
    """
    if preference != "auto":
        return preference

    if delta_v_ms <= 0:
        return "none"
    elif delta_v_ms < 10:
        return "cold_gas"
    elif delta_v_ms < 100:
        if available_power_w > 200 and spacecraft_mass_kg < 200:
            return "electric_hall"
        return "monoprop_green"
    elif delta_v_ms < 500:
        if available_power_w > 200:
            return "electric_hall"
        return "monoprop_hydrazine"
    elif delta_v_ms < 2000:
        if available_power_w > 500:
            return "electric_hall"
        return "biprop"
    else:
        return "biprop"


def compute_propulsion_budget(
    delta_v_ms: float,
    dry_mass_kg: float,
    propulsion_type: str = "auto",
    available_power_w: float = 100.0,
) -> PropulsionDesignResult:
    """Size the propulsion system for the given delta-V budget.

    Computes propellant mass, tank mass, and total propulsion system mass.
    """
    result = PropulsionDesignResult()
    result.total_delta_v_ms = delta_v_ms

    if delta_v_ms <= 0:
        result.propulsion_type = "none"
        return result

    # Select propulsion type
    if propulsion_type == "auto":
        propulsion_type = select_propulsion_type(delta_v_ms, dry_mass_kg, available_power_w)

    result.propulsion_type = propulsion_type
    props = PROPULSION_TYPES.get(propulsion_type)

    if props is None:
        result.warnings.append(f"Unknown propulsion type: {propulsion_type}")
        return result

    result.isp_s = props["isp_s"]
    result.thrust_n = (props["thrust_range_n"][0] + props["thrust_range_n"][1]) / 2

    # Propellant mass (iterative because prop system adds to dry mass)
    prop_mass = tsiolkovsky(delta_v_ms, result.isp_s, dry_mass_kg)
    tank_mass = prop_mass * props["tank_fraction"]
    # Iterate once with tank mass included
    prop_mass = tsiolkovsky(delta_v_ms, result.isp_s, dry_mass_kg + tank_mass)
    tank_mass = prop_mass * props["tank_fraction"]

    result.propellant_mass_kg = prop_mass
    result.tank_mass_kg = tank_mass
    result.thruster_mass_kg = 0.5 + result.thrust_n * 0.01  # Empirical
    result.feed_system_mass_kg = 0.3 + prop_mass * 0.02  # Valves, piping

    result.total_propulsion_mass_kg = (
        result.propellant_mass_kg
        + result.tank_mass_kg
        + result.thruster_mass_kg
        + result.feed_system_mass_kg
    )
    result.wet_mass_kg = dry_mass_kg + result.total_propulsion_mass_kg

    # Burn time
    if result.thrust_n > 0:
        result.burn_time_s = (prop_mass * result.isp_s * G0) / result.thrust_n

    # Cost
    result.propulsion_cost_keur = result.total_propulsion_mass_kg * 50 * props["cost_factor"]

    # Warnings for electric propulsion
    if propulsion_type.startswith("electric"):
        power_needed = result.thrust_n * result.isp_s * G0 / (2 * 0.6)  # ~60% efficiency
        if power_needed > available_power_w:
            result.warnings.append(
                f"Electric propulsion needs {power_needed:.0f}W but only {available_power_w:.0f}W available"
            )
        if result.burn_time_s > 365 * 86400:
            result.warnings.append(
                f"Total burn time {result.burn_time_s / 86400:.0f} days exceeds 1 year"
            )

    return result
