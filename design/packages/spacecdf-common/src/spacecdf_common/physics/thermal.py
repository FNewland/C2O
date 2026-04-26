"""SpaceCDF — Thermal design equations.

Computes radiator sizing, heater power, and thermal balance for
spacecraft design. Adapted from SMO's TCS thermal zone model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Constants
STEFAN_BOLTZMANN = 5.670374419e-8  # W/m^2/K^4
SOLAR_FLUX = 1361.0  # W/m^2 at 1 AU
EARTH_IR_FLUX = 237.0  # W/m^2 (average Earth infrared)
EARTH_ALBEDO = 0.30


@dataclass
class ThermalDesignResult:
    """Result of thermal design analysis."""

    # Hot case
    hot_case_temp_c: float = 0.0
    hot_case_heater_w: float = 0.0

    # Cold case
    cold_case_temp_c: float = 0.0
    cold_case_heater_w: float = 0.0

    # Radiator
    radiator_area_m2: float = 0.0
    radiator_mass_kg: float = 0.0

    # MLI
    mli_area_m2: float = 0.0
    mli_mass_kg: float = 0.0

    # Totals
    tcs_mass_kg: float = 0.0
    tcs_heater_power_w: float = 0.0
    tcs_cost_keur: float = 0.0

    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def compute_thermal_balance(
    # Internal heat
    internal_power_w: float = 50.0,
    # Spacecraft geometry
    spacecraft_area_m2: float = 1.0,
    radiator_emissivity: float = 0.85,
    radiator_absorptivity: float = 0.15,
    mli_effective_emissivity: float = 0.01,
    # Environment
    solar_flux_w_m2: float = SOLAR_FLUX,
    earth_ir_flux_w_m2: float = EARTH_IR_FLUX,
    earth_albedo: float = EARTH_ALBEDO,
    view_factor_earth: float = 0.3,
    view_factor_sun: float = 0.25,
    eclipse_fraction: float = 0.35,
    # Temperature limits
    t_min_c: float = -20.0,
    t_max_c: float = 50.0,
    # Design parameters
    radiator_specific_mass_kg_m2: float = 3.0,
    mli_specific_mass_kg_m2: float = 0.5,
    heater_margin_factor: float = 1.5,
) -> ThermalDesignResult:
    """Compute thermal balance and size radiators/heaters.

    Uses steady-state energy balance:
        Q_internal + Q_solar + Q_albedo + Q_earth_IR = Q_radiated + Q_heater

    Two cases computed:
    - Hot case (sunlight, max power): size radiator to keep below T_max
    - Cold case (eclipse, min power): size heater to keep above T_min
    """
    result = ThermalDesignResult()

    # External heat inputs
    q_solar = solar_flux_w_m2 * radiator_absorptivity * view_factor_sun * spacecraft_area_m2
    q_albedo = solar_flux_w_m2 * earth_albedo * radiator_absorptivity * view_factor_earth * spacecraft_area_m2
    q_earth_ir = earth_ir_flux_w_m2 * radiator_emissivity * view_factor_earth * spacecraft_area_m2

    # --- HOT CASE (sunlight, max internal power) ---
    t_max_k = t_max_c + 273.15
    q_total_hot = internal_power_w + q_solar + q_albedo + q_earth_ir

    # Radiator area needed to reject q_total_hot at T_max
    q_rad_per_m2 = radiator_emissivity * STEFAN_BOLTZMANN * t_max_k**4
    if q_rad_per_m2 > 0:
        result.radiator_area_m2 = q_total_hot / q_rad_per_m2
    else:
        result.radiator_area_m2 = 0.0
        result.warnings.append("Radiator sizing failed — zero radiation capability")

    result.hot_case_temp_c = t_max_c
    result.hot_case_heater_w = 0.0

    # --- COLD CASE (eclipse, min internal power) ---
    min_internal_power = internal_power_w * 0.3  # Approximate standby power
    q_total_cold = min_internal_power + q_earth_ir  # No solar/albedo in eclipse
    t_min_k = t_min_c + 273.15

    # Heat radiated at T_min with sized radiator
    q_radiated_cold = result.radiator_area_m2 * radiator_emissivity * STEFAN_BOLTZMANN * t_min_k**4

    # Heater power needed to maintain T_min
    heater_deficit = q_radiated_cold - q_total_cold
    result.cold_case_heater_w = max(0, heater_deficit) * heater_margin_factor
    result.cold_case_temp_c = t_min_c

    # --- Mass and cost ---
    result.radiator_mass_kg = result.radiator_area_m2 * radiator_specific_mass_kg_m2
    result.mli_area_m2 = spacecraft_area_m2 - result.radiator_area_m2
    result.mli_mass_kg = max(0, result.mli_area_m2) * mli_specific_mass_kg_m2
    result.tcs_heater_power_w = result.cold_case_heater_w
    result.tcs_mass_kg = result.radiator_mass_kg + result.mli_mass_kg + 0.5  # +0.5 kg for heaters/thermistors
    result.tcs_cost_keur = result.tcs_mass_kg * 15  # ~15 kEUR/kg for thermal hardware

    # Warnings
    if result.cold_case_heater_w > 20:
        result.warnings.append(f"Eclipse heater power {result.cold_case_heater_w:.1f}W is high — consider larger MLI blankets")
    if result.radiator_area_m2 > spacecraft_area_m2 * 0.5:
        result.warnings.append(f"Radiator area {result.radiator_area_m2:.2f}m² exceeds 50% of S/C area — consider active cooling")

    return result


def spacecraft_surface_area(mass_kg: float, form_factor: str = "box") -> float:
    """Estimate total spacecraft surface area from mass.

    Empirical relationships for different form factors.
    """
    if form_factor == "cubesat":
        # 1U = 0.1m x 0.1m x 0.1m = 0.06 m^2
        # Roughly 1U per 1.33 kg
        units = max(1, mass_kg / 1.33)
        side = 0.1  # m
        if units <= 3:
            return 2 * (side * side + side * units * side + units * side * side)
        elif units <= 6:
            return 2 * (2 * side * side + 2 * side * 3 * side + 3 * side * side)
        else:
            return 2 * (2 * side * side + 2 * side * (units / 2) * side + (units / 2) * side * side)
    elif form_factor == "box":
        # Empirical: surface area ~ 6 * (mass/density)^(2/3)
        # Typical satellite density ~150 kg/m^3
        volume = mass_kg / 150.0
        side = volume ** (1 / 3)
        return 6 * side * side
    elif form_factor == "cylinder":
        volume = mass_kg / 150.0
        radius = (volume / (2 * math.pi)) ** (1 / 3)
        height = 2 * radius
        return 2 * math.pi * radius * (radius + height)
    return 1.0  # fallback
