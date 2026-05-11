"""SpaceCDF — Space debris mitigation and orbital lifetime model.

Implements orbital lifetime prediction, deorbit compliance assessment,
passivation planning, and casualty risk estimation.

References:
  - ESA Space Debris Mitigation Compliance Verification Guidelines (ESSB-HB-U-002)
  - ISO 24113:2023 — Space systems — Space debris mitigation requirements
  - ECSS-U-AS-10C Rev.2 — Space sustainability — Space debris mitigation
  - NASA-STD-8719.14 Rev B — Process for Limiting Orbital Debris
  - NASA DAS 3.2 — Debris Assessment Software methodology
  - King-Hele (1987) — Satellite Orbits in an Atmosphere (lifetime model)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


# Solar cycle parameters (simplified F10.7 model)
# Mean F10.7 over a solar cycle: ~120 sfu
# Solar max: ~200 sfu, solar min: ~70 sfu
_F107_MEAN = 120.0
_F107_MAX = 200.0
_F107_MIN = 70.0

# Earth parameters
_R_EARTH_KM = 6371.0
_MU_EARTH = 3.986004418e14  # m³/s²


@dataclass
class OrbitalLifetimeResult:
    """Result of orbital lifetime and debris compliance analysis."""

    # Lifetime prediction
    lifetime_years: float = 0.0
    lifetime_years_solar_max: float = 0.0
    lifetime_years_solar_min: float = 0.0

    # Compliance
    compliant_25yr: bool = False     # Pre-2024 rule (IADC, ESA)
    compliant_5yr: bool = False      # FCC 2024+ rule / ESA Zero Debris target
    deorbit_delta_v_ms: float = 0.0  # ΔV needed to achieve 25-year compliance
    deorbit_method: str = ""         # "natural", "propulsive", "drag_augmentation"

    # Casualty risk (uncontrolled re-entry)
    casualty_risk: float = 0.0       # Probability (NASA limit: 1:10000)
    casualty_compliant: bool = False  # < 1:10000
    surviving_mass_kg: float = 0.0   # Mass surviving re-entry
    demise_altitude_km: float = 78.0 # Typical breakup altitude

    # Passivation assessment
    passivation_items: list[str] = field(default_factory=list)
    passivation_score: float = 0.0   # 0-1 (1 = fully passivatable)

    # Collision environment
    debris_density_objects_per_km3: float = 0.0
    collision_avoidance_dv_per_year_ms: float = 0.0

    # Composite
    debris_compliance_score: float = 0.0  # 0-100

    warnings: list[str] = field(default_factory=list)


# CubeSat form-factor cross-sections (m²) — average tumbling area
CUBESAT_CROSS_SECTIONS: dict[str, float] = {
    "1U": 0.01, "1.5U": 0.015, "2U": 0.02, "3U": 0.035,
    "6U": 0.06, "6U_deployed": 0.15, "12U": 0.12, "12U_deployed": 0.30,
    "16U": 0.16, "27U": 0.27,
}

# Atmospheric model: altitude bands with reference density, scale height, solar exponent
# (h_ref_km, rho_ref_kg_m3, H_km, solar_exponent)
# Reference densities from NRLMSISE-00 at F10.7=120 (mean solar activity)
_ATMO_BANDS: list[tuple[float, float, float, float]] = [
    (180, 3.50e-10, 37.0, 0.5),
    (200, 2.50e-10, 40.0, 0.8),
    (300, 2.00e-11, 50.0, 1.2),
    (400, 3.00e-12, 55.0, 1.5),
    (500, 5.00e-13, 60.0, 1.8),
    (600, 1.00e-13, 65.0, 2.0),
    (700, 2.50e-14, 72.0, 2.2),
    (800, 7.00e-15, 80.0, 2.5),
    (900, 2.00e-15, 88.0, 2.5),
]


def _atmospheric_density(altitude_km: float, f107: float = _F107_MEAN) -> tuple[float, float]:
    """Return (density_kg_m3, scale_height_km) at given altitude and solar flux."""
    solar_factor = f107 / 120.0
    h = altitude_km

    # Find the band
    for i in range(len(_ATMO_BANDS) - 1, -1, -1):
        h_ref, rho_ref, H, exp = _ATMO_BANDS[i]
        if h >= h_ref or i == 0:
            rho = rho_ref * (solar_factor ** exp) * math.exp(-(h - h_ref) / H)
            return max(rho, 1e-25), H

    return 1e-25, 90.0


def estimate_orbital_lifetime(
    altitude_km: float,
    area_to_mass_ratio_m2_kg: float = 0.01,
    cd: float = 2.2,
    f107: float = _F107_MEAN,
    eccentricity: float = 0.0,
    solar_cycle_phase_years: float = 5.5,
) -> float:
    """Estimate orbital lifetime using numerical altitude-stepping integration.

    Integrates the drag decay equation step-by-step through the atmosphere
    rather than using a single-point approximation, giving much better
    accuracy (typically within 30% for circular LEO).

    Args:
        altitude_km: Initial orbit altitude (circular, or mean for eccentric).
        area_to_mass_ratio_m2_kg: Ballistic coefficient A/m (m²/kg).
        cd: Drag coefficient (typically 2.0-2.5).
        f107: Solar F10.7 flux (sfu). Higher = more drag.
        eccentricity: Orbital eccentricity (0 = circular). For eccentric
            orbits, drag is concentrated at perigee — lifetime is shorter
            than circular at the same mean altitude.
        solar_cycle_phase_years: Years from solar minimum (0=min, 5.5=max,
            11=next min). If provided, f107 is modulated sinusoidally.

    Returns:
        Estimated lifetime in years.
    """
    if altitude_km > 1000:
        return float("inf")
    if altitude_km < 150:
        return 0.0

    # For eccentric orbits, perigee altitude determines drag
    # Perigee altitude ≈ mean_alt × (1 - e) approximately
    if eccentricity > 0.001:
        # Semi-major axis from mean altitude
        a_m = (_R_EARTH_KM + altitude_km) * 1000
        perigee_km = (a_m * (1 - eccentricity)) / 1000 - _R_EARTH_KM
        # Eccentric orbit lifetime ≈ circular lifetime at perigee × correction
        # King-Hele correction factor for eccentricity
        if perigee_km < 150:
            return 0.0
        ecc_factor = max(0.1, 1.0 + 2.5 * eccentricity)  # Eccentric orbits live longer at same perigee
        base_lifetime = _integrate_lifetime(perigee_km, area_to_mass_ratio_m2_kg, cd, f107, solar_cycle_phase_years)
        return base_lifetime * ecc_factor

    return _integrate_lifetime(altitude_km, area_to_mass_ratio_m2_kg, cd, f107, solar_cycle_phase_years)


def _integrate_lifetime(
    altitude_km: float,
    a_over_m: float,
    cd: float,
    f107: float,
    solar_cycle_phase_years: float,
) -> float:
    """Numerically integrate lifetime by stepping through altitude bands.

    Steps in 10 km decrements from initial altitude to 150 km, computing
    the time to decay through each band using local density and scale height.
    """
    h = altitude_km
    total_seconds = 0.0
    step_km = 10.0  # 10 km steps
    elapsed_years = 0.0

    while h > 150:
        # Modulate F10.7 with solar cycle if time evolves
        current_f107 = f107
        if solar_cycle_phase_years > 0:
            # Sinusoidal solar cycle centred on the given f107
            phase = solar_cycle_phase_years + elapsed_years
            amplitude = min(80, f107 * 0.5)  # ±50% of mean
            current_f107 = f107 + amplitude * math.cos(2 * math.pi * phase / 11.0)
            current_f107 = max(70, min(250, current_f107))

        rho, H = _atmospheric_density(h, current_f107)

        # Orbital velocity at this altitude
        a_m = (_R_EARTH_KM + h) * 1000
        v = math.sqrt(_MU_EARTH / a_m)

        # Decay rate: da/dt = -ρ × v × Cd × (A/m) × a (Vallado 2013, eq. 8-41)
        # No π factor — reference densities are already orbit-averaged values
        dh_dt = rho * v * cd * a_over_m * a_m  # m/s of altitude decay

        if dh_dt <= 1e-15:
            # Negligible drag — would take >1e6 years
            return total_seconds / (365.25 * 86400) + 1e6

        # Time to decay through this step
        actual_step = min(step_km, h - 150)
        dt = (actual_step * 1000) / dh_dt  # seconds

        total_seconds += dt
        elapsed_years = total_seconds / (365.25 * 86400)
        h -= actual_step

        # Safety limit
        if elapsed_years > 1e5:
            return elapsed_years

    return max(total_seconds / (365.25 * 86400), 0.001)


def estimate_cubesat_cross_section(form_factor: str, deployed_panels: bool = False) -> float:
    """Return average tumbling cross-section for a CubeSat form factor.

    Uses measured/estimated values for standard CubeSat sizes.
    If deployed solar panels, uses larger cross-section.
    """
    key = f"{form_factor}_deployed" if deployed_panels else form_factor
    if key in CUBESAT_CROSS_SECTIONS:
        return CUBESAT_CROSS_SECTIONS[key]
    if form_factor in CUBESAT_CROSS_SECTIONS:
        return CUBESAT_CROSS_SECTIONS[form_factor]
    # Estimate from mass: fallback
    return 0.01


def compute_debris_compliance(
    altitude_km: float,
    inclination_deg: float,
    dry_mass_kg: float,
    cross_section_m2: float | None = None,
    has_propulsion: bool = False,
    propulsion_type: str = "none",
    available_delta_v_ms: float = 0.0,
    has_battery: bool = True,
    has_pressurised_tanks: bool = False,
    mission_duration_years: float = 3.0,
) -> OrbitalLifetimeResult:
    """Compute full debris compliance assessment.

    Implements checks per ECSS-U-AS-10C Rev.2 and NASA-STD-8719.14.
    """
    result = OrbitalLifetimeResult()

    # Estimate cross-section from mass if not provided
    if cross_section_m2 is None:
        # Use CubeSat form factor tables where possible
        if dry_mass_kg <= 2:
            cross_section_m2 = CUBESAT_CROSS_SECTIONS["1U"]
        elif dry_mass_kg <= 4:
            cross_section_m2 = CUBESAT_CROSS_SECTIONS["2U"]
        elif dry_mass_kg <= 6:
            cross_section_m2 = CUBESAT_CROSS_SECTIONS["3U"]
        elif dry_mass_kg <= 12:
            cross_section_m2 = CUBESAT_CROSS_SECTIONS["6U"]
        elif dry_mass_kg <= 24:
            cross_section_m2 = CUBESAT_CROSS_SECTIONS["12U"]
        else:
            # Larger spacecraft: empirical A ≈ 0.01 × m^(2/3)
            cross_section_m2 = 0.01 * dry_mass_kg ** (2.0 / 3.0)

    a_over_m = cross_section_m2 / max(dry_mass_kg, 0.1)

    # --- Orbital lifetime prediction ---
    result.lifetime_years = estimate_orbital_lifetime(altitude_km, a_over_m, f107=_F107_MEAN)
    result.lifetime_years_solar_max = estimate_orbital_lifetime(altitude_km, a_over_m, f107=_F107_MAX)
    result.lifetime_years_solar_min = estimate_orbital_lifetime(altitude_km, a_over_m, f107=_F107_MIN)

    # --- Compliance assessment ---
    # Post-mission lifetime = orbital lifetime - mission duration
    post_mission_lifetime = max(result.lifetime_years - mission_duration_years, result.lifetime_years * 0.8)
    result.compliant_25yr = post_mission_lifetime <= 25.0
    result.compliant_5yr = post_mission_lifetime <= 5.0

    # Deorbit method and ΔV
    if result.compliant_5yr:
        result.deorbit_method = "natural"
        result.deorbit_delta_v_ms = 0.0
    elif has_propulsion and available_delta_v_ms > 0:
        result.deorbit_method = "propulsive"
        # Estimate ΔV to lower perigee to ~200 km for 25-year decay
        # Simplified: ΔV ≈ 0.5 × (v_circ - v_circ_at_target_perigee)
        target_alt = _find_compliant_altitude(dry_mass_kg, a_over_m, 25.0, mission_duration_years)
        if target_alt < altitude_km:
            a1 = (_R_EARTH_KM + altitude_km) * 1000
            a2 = (_R_EARTH_KM + target_alt) * 1000
            v1 = math.sqrt(_MU_EARTH / a1)
            v_transfer = math.sqrt(_MU_EARTH * (2 / a1 - 2 / (a1 + a2)))
            result.deorbit_delta_v_ms = abs(v1 - v_transfer)
    else:
        result.deorbit_method = "drag_augmentation"
        result.deorbit_delta_v_ms = 0.0
        if not result.compliant_25yr:
            result.warnings.append(
                f"Post-mission lifetime {post_mission_lifetime:.0f} yr exceeds 25-year limit; "
                f"no propulsion for deorbit — consider drag augmentation device"
            )

    # --- Casualty risk (uncontrolled re-entry) ---
    # NASA DAS simplified: surviving mass fraction depends on materials
    # Aluminium: ~10-40% survives; titanium/steel: 60-80%
    surviving_fraction = 0.2 if dry_mass_kg < 100 else 0.3
    result.surviving_mass_kg = dry_mass_kg * surviving_fraction
    result.demise_altitude_km = 78.0  # Typical breakup at ~78 km

    # Casualty expectation = surviving_area × human_density
    # NASA limit: Ec < 1:10000 = 0.0001
    surviving_area = result.surviving_mass_kg * 0.01  # ~0.01 m²/kg for debris
    casualty_area = surviving_area + 0.36  # Human cross-section 0.36 m²
    world_pop_density = 15.0  # people per km² (land average)
    result.casualty_risk = casualty_area * world_pop_density / 5.1e8  # Earth surface 5.1e8 km²
    result.casualty_compliant = result.casualty_risk < 0.0001

    # --- Passivation assessment ---
    passivation = []
    score = 0.0
    total_items = 0

    if has_battery:
        passivation.append("Battery discharge to safe level (< 50% SoC)")
        total_items += 1
        score += 1.0  # Achievable by command

    if has_pressurised_tanks:
        passivation.append("Propellant tank venting / depletion burn")
        total_items += 1
        if has_propulsion:
            score += 1.0
        else:
            score += 0.5
            result.warnings.append("Pressurised tanks but no venting capability")

    passivation.append("RF transmitter shutdown")
    total_items += 1
    score += 1.0

    passivation.append("Momentum wheel spin-down")
    total_items += 1
    score += 1.0

    result.passivation_items = passivation
    result.passivation_score = score / max(total_items, 1)

    # --- Collision environment ---
    # Simplified debris density model from ESA MASTER-8 (objects > 1 cm)
    if altitude_km < 400:
        result.debris_density_objects_per_km3 = 1e-8
    elif altitude_km < 600:
        result.debris_density_objects_per_km3 = 5e-8
    elif altitude_km < 900:
        result.debris_density_objects_per_km3 = 2e-7  # Peak debris zone
    elif altitude_km < 1100:
        result.debris_density_objects_per_km3 = 1e-7
    else:
        result.debris_density_objects_per_km3 = 3e-8

    # Collision avoidance ΔV budget: ~5-15 m/s per year for LEO
    if altitude_km < 1000:
        result.collision_avoidance_dv_per_year_ms = (
            5.0 * result.debris_density_objects_per_km3 / 1e-7
        )
    else:
        result.collision_avoidance_dv_per_year_ms = 0.0

    # --- Composite debris compliance score (0-100) ---
    lifetime_score = 30 * (1.0 if result.compliant_25yr else max(0, 1 - post_mission_lifetime / 100))
    five_yr_bonus = 20 if result.compliant_5yr else 0
    casualty_score = 20 if result.casualty_compliant else 0
    passivation_component = 15 * result.passivation_score
    deorbit_capability = 15 if (has_propulsion and available_delta_v_ms > result.deorbit_delta_v_ms) else (
        7 if result.deorbit_method == "natural" else 0
    )

    result.debris_compliance_score = min(100, (
        lifetime_score + five_yr_bonus + casualty_score +
        passivation_component + deorbit_capability
    ))

    return result


def _find_compliant_altitude(
    dry_mass_kg: float,
    a_over_m: float,
    target_lifetime_years: float,
    mission_duration_years: float,
) -> float:
    """Find the altitude that gives target post-mission lifetime.

    Binary search for the altitude where remaining lifetime = target.
    """
    lo, hi = 150.0, 800.0
    for _ in range(30):
        mid = (lo + hi) / 2
        lt = estimate_orbital_lifetime(mid, a_over_m)
        post_mission = max(lt - mission_duration_years, lt * 0.8)
        if post_mission < target_lifetime_years:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
