"""SpaceCDF — Power subsystem design equations.

Computes solar array sizing, battery sizing, and power budgets for
design-point analysis. Adapted from SMO's EPS model and budget tracker.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


# Solar constants
SOLAR_FLUX_W_M2 = 1361.0  # Solar constant at 1 AU
BOL_DEGRADATION = 0.98     # Beginning-of-life efficiency factor
CELL_PACKING = 0.90        # Cell packing factor on panel


@dataclass
class PowerBudgetResult:
    """Result of power budget analysis."""

    # Solar array
    sa_area_m2: float = 0.0
    sa_power_bol_w: float = 0.0
    sa_power_eol_w: float = 0.0
    sa_mass_kg: float = 0.0

    # Battery
    battery_capacity_wh: float = 0.0
    battery_mass_kg: float = 0.0
    battery_dod_percent: float = 0.0
    num_eclipse_cycles: float = 0.0

    # Power budget
    total_power_sunlight_w: float = 0.0
    total_power_eclipse_w: float = 0.0
    power_margin_w: float = 0.0
    power_margin_percent: float = 0.0

    # Subsystem totals
    eps_mass_kg: float = 0.0
    eps_cost_keur: float = 0.0

    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def compute_power_budget(
    # Orbit parameters
    eclipse_fraction: float,
    sunlight_fraction: float,
    orbit_period_s: float,
    mission_duration_years: float = 3.0,
    # Power consumers
    platform_power_w: float = 50.0,
    payload_power_w: float = 30.0,
    payload_duty_cycle: float = 0.25,
    heater_power_eclipse_w: float = 10.0,
    # Solar array parameters
    cell_efficiency: float = 0.30,
    sa_degradation_per_year: float = 0.025,
    sa_specific_power_w_kg: float = 100.0,
    sa_cost_keur_per_m2: float = 50.0,
    # Battery parameters
    battery_specific_energy_wh_kg: float = 150.0,
    battery_max_dod: float = 0.30,
    battery_cost_keur_per_kwh: float = 10.0,
    # Distance from sun (for non-Earth missions)
    solar_distance_au: float = 1.0,
) -> PowerBudgetResult:
    """Compute power budget, solar array and battery sizing.

    Follows the standard approach:
    1. Compute average power demand in sunlight and eclipse
    2. Size solar arrays to provide enough power in sunlight + charge battery
    3. Size battery for eclipse duration at max DOD
    """
    result = PowerBudgetResult()

    # --- Multi-mode power analysis ---
    # Mode 1: Nominal sunlight (platform + payload at duty cycle)
    avg_payload_power = payload_power_w * payload_duty_cycle
    p_sunlight = platform_power_w + avg_payload_power

    # Mode 2: Eclipse (platform + heaters, no payload)
    p_eclipse = platform_power_w + heater_power_eclipse_w

    # Mode 3: Safe mode (essential bus only — AOCS in coarse mode, no payload,
    # heaters at full). Typically 50-70% of nominal bus power + full heaters.
    p_safe_mode = platform_power_w * 0.6 + heater_power_eclipse_w * 1.5

    # Mode 4: Peak (simultaneous imaging + downlink + slew — short duration)
    p_peak = platform_power_w + payload_power_w  # Full payload, no duty cycle discount

    result.total_power_eclipse_w = p_eclipse
    result.total_power_sunlight_w = p_sunlight

    # Energy needed per orbit
    eclipse_time_s = eclipse_fraction * orbit_period_s
    sunlight_time_s = sunlight_fraction * orbit_period_s
    e_eclipse_wh = p_eclipse * (eclipse_time_s / 3600.0)

    # Battery sizing: worst case of (eclipse energy) and (safe mode through full eclipse)
    e_safe_eclipse_wh = p_safe_mode * (eclipse_time_s / 3600.0)
    e_battery_design_wh = max(e_eclipse_wh, e_safe_eclipse_wh)

    result.battery_dod_percent = battery_max_dod * 100
    result.battery_capacity_wh = e_battery_design_wh / battery_max_dod if battery_max_dod > 0 else e_battery_design_wh
    result.battery_mass_kg = result.battery_capacity_wh / battery_specific_energy_wh_kg
    result.num_eclipse_cycles = mission_duration_years * 365.25 * 86400 / orbit_period_s

    # Solar array sizing: must cover PEAK demand + battery recharge simultaneously
    # SA must be large enough for the worst-case instantaneous power draw
    charge_efficiency = 0.90  # Battery charge/discharge round-trip
    recharge_power = (e_eclipse_wh / max(sunlight_time_s / 3600.0, 0.01)) / charge_efficiency
    sa_power_required = max(
        p_peak + recharge_power,             # Peak payload active + recharge
        p_sunlight + recharge_power * 1.2,   # Average with 20% margin on recharge
    )

    # End-of-life degradation
    eol_factor = (1 - sa_degradation_per_year) ** mission_duration_years
    solar_flux_at_distance = SOLAR_FLUX_W_M2 / (solar_distance_au ** 2)

    # Area calculation
    power_per_m2_eol = (
        solar_flux_at_distance * cell_efficiency * BOL_DEGRADATION * CELL_PACKING * eol_factor
    )
    if power_per_m2_eol > 0:
        result.sa_area_m2 = sa_power_required / power_per_m2_eol
    else:
        result.sa_area_m2 = 0.0
        result.warnings.append("Solar array sizing failed — zero power per m2")

    result.sa_power_bol_w = result.sa_area_m2 * solar_flux_at_distance * cell_efficiency * BOL_DEGRADATION * CELL_PACKING
    result.sa_power_eol_w = result.sa_power_bol_w * eol_factor
    result.sa_mass_kg = result.sa_power_eol_w / sa_specific_power_w_kg if sa_specific_power_w_kg > 0 else 0

    # Power margin
    result.power_margin_w = result.sa_power_eol_w - sa_power_required
    result.power_margin_percent = (result.power_margin_w / sa_power_required * 100) if sa_power_required > 0 else 0

    # Solar array cost
    result.eps_cost_keur = result.sa_area_m2 * sa_cost_keur_per_m2 + result.battery_capacity_wh / 1000 * battery_cost_keur_per_kwh

    # Total EPS mass (SA + battery + PCDU + harness)
    # The PCDU/harness overhead scales with spacecraft complexity, not just
    # SA+battery mass. For CubeSats it's ~15% (integrated EPS boards). For
    # larger spacecraft with dedicated PCDUs, harness, and regulation it's
    # a significant fixed mass + ~30-50% of generation mass.
    # Reference: SMAD4 §11.6 — EPS mass typically 8-12% of S/C dry mass.
    sa_batt_mass = result.sa_mass_kg + result.battery_mass_kg
    if sa_batt_mass < 2.0:
        # CubeSat/nanosat: integrated EPS boards
        harness_overhead_kg = sa_batt_mass * 0.15
    elif sa_batt_mass < 10.0:
        # Microsat: small PCDU + harness
        harness_overhead_kg = 1.5 + sa_batt_mass * 0.25
    else:
        # Small+: dedicated PCDU, battery management, harness, solar array drive
        harness_overhead_kg = 3.0 + sa_batt_mass * 0.40
    result.eps_mass_kg = sa_batt_mass + harness_overhead_kg

    # Warnings
    if result.battery_dod_percent > 40:
        result.warnings.append(f"Battery DOD {result.battery_dod_percent:.0f}% exceeds 40% — reduce eclipse power or increase capacity")
    if result.num_eclipse_cycles > 30000:
        result.warnings.append(f"Eclipse cycles ({result.num_eclipse_cycles:.0f}) exceeds 30k — verify battery cycle life")

    return result


def rtg_power(
    isotope: str = "Pu-238",
    initial_power_w: float = 300.0,
    elapsed_years: float = 0.0,
) -> float:
    """Compute RTG/RHU power output accounting for radioactive decay.

    For deep-space missions beyond ~3 AU where solar power is impractical.
    """
    half_life_years = {"Pu-238": 87.7, "Am-241": 432.0, "Sr-90": 28.8}
    hl = half_life_years.get(isotope, 87.7)
    return initial_power_w * (0.5 ** (elapsed_years / hl))
