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


def estimate_orbital_lifetime(
    altitude_km: float,
    area_to_mass_ratio_m2_kg: float = 0.01,
    cd: float = 2.2,
    f107: float = _F107_MEAN,
) -> float:
    """Estimate orbital lifetime in years using simplified King-Hele model.

    Uses exponential atmosphere with scale heights fitted to NRLMSISE-00
    for solar mean conditions. Accurate to ~factor 2 for 200-1000 km.

    Args:
        altitude_km: Initial circular orbit altitude.
        area_to_mass_ratio_m2_kg: Ballistic coefficient A/m (m²/kg).
        cd: Drag coefficient (typically 2.0-2.5).
        f107: Solar F10.7 flux (sfu). Higher = more drag = shorter lifetime.

    Returns:
        Estimated lifetime in years.
    """
    if altitude_km > 1000:
        return float("inf")  # Effectively permanent above 1000 km
    if altitude_km < 150:
        return 0.0  # Immediate re-entry

    # Atmospheric density model (exponential, fitted to NRLMSISE-00 mean)
    # Scale heights vary with altitude and solar activity
    h = altitude_km
    solar_factor = f107 / 120.0  # Normalise to mean

    # Density at altitude (kg/m³) — piecewise exponential fit
    if h < 200:
        rho_base, H = 2.53e-10, 37.0
        rho = rho_base * math.exp(-(h - 180) / H)
    elif h < 300:
        rho_base, H = 2.53e-10 * solar_factor, 45.0
        rho = rho_base * math.exp(-(h - 200) / H)
    elif h < 400:
        rho_base, H = 6.24e-12 * solar_factor**1.5, 53.6
        rho = rho_base * math.exp(-(h - 300) / H)
    elif h < 500:
        rho_base, H = 1.95e-13 * solar_factor**2, 58.0
        rho = rho_base * math.exp(-(h - 400) / H)
    elif h < 600:
        rho_base, H = 6.57e-15 * solar_factor**2.5, 62.0
        rho = rho_base * math.exp(-(h - 500) / H)
    elif h < 700:
        rho_base, H = 2.39e-16 * solar_factor**3, 68.0
        rho = rho_base * math.exp(-(h - 600) / H)
    elif h < 800:
        rho_base, H = 1.17e-17 * solar_factor**3, 75.0
        rho = rho_base * math.exp(-(h - 700) / H)
    elif h < 900:
        rho_base, H = 7.0e-19 * solar_factor**3, 82.0
        rho = rho_base * math.exp(-(h - 800) / H)
    else:
        rho_base, H = 5.0e-20 * solar_factor**3, 90.0
        rho = rho_base * math.exp(-(h - 900) / H)

    if rho <= 0:
        return float("inf")

    # Simplified King-Hele lifetime estimate
    # T ≈ -H / (ρ × v × Cd × A/m) where v is orbital velocity
    a = (_R_EARTH_KM + h) * 1000  # metres
    v = math.sqrt(_MU_EARTH / a)
    decay_rate = rho * v * cd * area_to_mass_ratio_m2_kg  # m/s per s of altitude loss
    if decay_rate <= 0:
        return float("inf")

    # Time to decay from h to 150 km (re-entry)
    # Integrate the decay: dt = dh / (ρ(h) × v × Cd × A/m × H)
    # Simplified: use mean conditions over the altitude range
    effective_h = max(h - 150, 1)
    lifetime_s = (effective_h * 1000) / (decay_rate * 0.5 * H * 1000)
    lifetime_years = lifetime_s / (365.25 * 86400)

    return max(lifetime_years, 0.001)


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
        # Empirical: A ≈ 0.01 × m^(2/3) for compact spacecraft
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
