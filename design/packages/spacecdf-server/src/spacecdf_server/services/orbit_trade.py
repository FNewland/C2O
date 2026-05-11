"""SpaceCDF — Orbit Trade Calculator.

Given mission objectives (coverage, revisit, GSD, lifetime, cost constraints),
computes and compares candidate orbits. This is DECISION 0.6 — the single
most impactful early decision in mission design.

For each candidate orbit, computes:
  - Ground coverage and revisit time for target latitude band
  - Achievable GSD from a given aperture budget
  - Orbital lifetime and debris compliance (25-year / 5-year rules)
  - Eclipse fraction and thermal/power implications
  - Launch vehicle access and cost delta
  - Contact time with standard ground stations

Returns a scored multi-criteria trade matrix.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# Constants
MU_EARTH = 3.986004418e14
R_EARTH_KM = 6371.0
SOLAR_FLUX_W_M2 = 1361.0
C_LIGHT = 299792458.0


@dataclass
class OrbitCandidate:
    """A candidate orbit with computed properties."""
    name: str
    altitude_km: float
    inclination_deg: float
    orbit_type: str  # sso, polar, equatorial, iss, meo, molniya, tundra, gto, lunar
    eccentricity: float = 0.0

    # Computed properties
    period_min: float = 0.0
    velocity_ms: float = 0.0
    eclipse_fraction: float = 0.0
    orbits_per_day: float = 0.0

    # Coverage
    swath_km: float = 0.0
    revisit_days: float = 0.0
    practical_revisit_days: float = 0.0
    latitude_coverage: str = ""
    coverage_description: str = ""

    # Resolution
    achievable_gsd_m: float = 0.0
    diffraction_limited_gsd_m: float = 0.0

    # Lifetime / debris
    natural_lifetime_years: float = 0.0
    compliant_25yr: bool = True
    compliant_5yr: bool = False
    needs_propulsion_for_deorbit: bool = False

    # Contact / ground
    contact_min_per_day: float = 0.0
    max_data_gb_per_day: float = 0.0

    # Cost / access
    rideshare_available: bool = True
    launch_cost_keur: float = 0.0
    orbit_access_notes: str = ""

    # Scoring
    scores: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    rank: int = 0


def compute_orbit_trade(
    target_gsd_m: float = 10.0,
    target_revisit_days: float = 3.0,
    target_latitude_band: tuple[float, float] = (-30.0, 30.0),
    aperture_m: float = 0.15,
    max_mass_kg: float = 12.0,
    max_cost_meur: float = 10.0,
    min_lifetime_years: float = 2.0,
    downlink_rate_mbps: float = 50.0,
    wavelength_um: float = 0.55,
    mission_type: str = "earth_observation",
) -> dict[str, Any]:
    """Compute orbit trade study from mission objectives.

    Returns scored candidates with full rationale for each.
    """
    # Generate candidate orbits
    candidates: list[OrbitCandidate] = []

    # SSO at various altitudes
    for alt in [350, 400, 450, 500, 550, 600, 700, 800]:
        inc = _sso_inclination(alt)
        candidates.append(OrbitCandidate(
            name=f"SSO {alt} km",
            altitude_km=alt, inclination_deg=inc, orbit_type="sso",
        ))

    # ISS orbit
    candidates.append(OrbitCandidate(
        name="ISS orbit (410 km, 51.6°)",
        altitude_km=410, inclination_deg=51.6, orbit_type="iss",
    ))

    # Equatorial LEO
    candidates.append(OrbitCandidate(
        name="Equatorial LEO (500 km, 0°)",
        altitude_km=500, inclination_deg=0, orbit_type="equatorial",
    ))

    # Polar non-SSO
    candidates.append(OrbitCandidate(
        name="Polar non-SSO (500 km, 90°)",
        altitude_km=500, inclination_deg=90, orbit_type="polar",
    ))

    # Mid-inclination (constellation coverage)
    candidates.append(OrbitCandidate(
        name="Mid-inclination (550 km, 53°)",
        altitude_km=550, inclination_deg=53, orbit_type="mid_inc",
        orbit_access_notes="Good for constellation coverage (Starlink-like inclination)",
    ))

    # --- Non-LEO / HEO candidates (conditionally added) ---
    add_heo = max_cost_meur > 5 or target_revisit_days < 0.1
    add_lunar = mission_type == "lunar"

    if add_heo or target_revisit_days < 0.1:
        candidates.append(OrbitCandidate(
            name="Molniya (39 000 km apogee, 63.4°)",
            altitude_km=39000, inclination_deg=63.4, orbit_type="molniya",
            eccentricity=0.74,
            orbit_access_notes="Highly elliptical — dedicated launch (Soyuz/Proton heritage). "
                               "Two-satellite constellation gives continuous high-latitude coverage.",
            coverage_description="8 h dwell over 50–90°N per orbit",
        ))
        candidates.append(OrbitCandidate(
            name="Tundra (42 164 km, 63.4°)",
            altitude_km=42164, inclination_deg=63.4, orbit_type="tundra",
            eccentricity=0.26,
            orbit_access_notes="Semi-synchronous HEO — dedicated launch required. "
                               "Single satellite covers northern hemisphere 12 h/day.",
            coverage_description="12 h continuous dwell over northern hemisphere per orbit",
        ))

    if add_heo:
        candidates.append(OrbitCandidate(
            name="GTO (35 786 km apogee, 28.5°)",
            altitude_km=35786, inclination_deg=28.5, orbit_type="gto",
            eccentricity=0.73,
            orbit_access_notes="Geostationary Transfer Orbit — rideshare as secondary payload "
                               "on GTO launches (Falcon 9, Ariane 6). Not a final orbit.",
            coverage_description="Transit orbit; ~2 h near apogee per 10.5 h period",
        ))

    if add_lunar:
        candidates.append(OrbitCandidate(
            name="Lunar transfer (~384 400 km)",
            altitude_km=384400, inclination_deg=28.5, orbit_type="lunar",
            eccentricity=0.97,
            orbit_access_notes="Trans-lunar injection — dedicated launch or Artemis rideshare. "
                               "Requires deep-space navigation and comms.",
            coverage_description="Ballistic transfer; 4–5 day transit to lunar orbit",
        ))

    # Compute properties for each
    for c in candidates:
        _compute_orbit_properties(c, aperture_m, wavelength_um,
                                  target_latitude_band, downlink_rate_mbps)

    # Score candidates — weights depend on mission type
    is_optical = mission_type in ("earth_observation", "optical_imager", "science_planetary")
    is_comms = mission_type in ("communications", "rf_relay", "iot")
    is_sar = mission_type == "sar"

    if is_comms:
        criteria_weights = {
            "coverage": 0.25,    # Ground coverage / contact time
            "latency": 0.20,     # End-to-end latency
            "lifetime": 0.15,
            "debris": 0.15,
            "cost": 0.15,
            "data": 0.10,
        }
    elif is_sar:
        criteria_weights = {
            "revisit": 0.25,
            "coverage": 0.20,
            "lifetime": 0.15,
            "debris": 0.15,
            "cost": 0.15,
            "data": 0.10,
        }
    else:
        criteria_weights = {
            "gsd": 0.25,
            "revisit": 0.20,
            "lifetime": 0.15,
            "debris": 0.15,
            "cost": 0.15,
            "data": 0.10,
        }

    heo_types = {"molniya", "tundra", "gto", "lunar"}

    for c in candidates:
        is_heo_candidate = c.orbit_type in heo_types

        # GSD score (optical missions only)
        if is_optical:
            if is_heo_candidate:
                c.scores["gsd"] = 0.0  # HEO cannot do Earth imaging
            elif c.achievable_gsd_m <= target_gsd_m:
                c.scores["gsd"] = 1.0
            else:
                c.scores["gsd"] = max(0, 1.0 - (c.achievable_gsd_m - target_gsd_m) / target_gsd_m)

        # Coverage / contact score (comms missions)
        if is_comms:
            c.scores["coverage"] = min(1.0, c.contact_min_per_day / 60)  # 60 min/day = perfect
            # Latency: lower altitude = lower latency
            latency_ms = c.altitude_km * 1000 / C_LIGHT * 2 * 1000  # Round-trip
            c.scores["latency"] = max(0, 1.0 - latency_ms / 20)  # 20ms = worst acceptable

        # Coverage for SAR
        if is_sar:
            c.scores["coverage"] = min(1.0, c.contact_min_per_day / 30)

        # Revisit score (use practical revisit with off-nadir pointing)
        if c.practical_revisit_days <= target_revisit_days:
            c.scores["revisit"] = 1.0
        else:
            c.scores["revisit"] = max(0, 1.0 - (c.practical_revisit_days - target_revisit_days) / (target_revisit_days * 3))

        # Lifetime score
        if c.natural_lifetime_years >= min_lifetime_years:
            c.scores["lifetime"] = 1.0
        elif c.needs_propulsion_for_deorbit:
            c.scores["lifetime"] = 0.7  # Achievable but needs propulsion
        else:
            c.scores["lifetime"] = max(0, c.natural_lifetime_years / min_lifetime_years)

        # Debris compliance score
        c.scores["debris"] = 1.0 if c.compliant_5yr else (0.7 if c.compliant_25yr else 0.2)

        # Cost score (normalised against max_cost)
        if c.launch_cost_keur <= max_cost_meur * 1000 * 0.15:  # Launch < 15% of total budget
            c.scores["cost"] = 1.0
        else:
            c.scores["cost"] = max(0, 1.0 - (c.launch_cost_keur - max_cost_meur * 150) / (max_cost_meur * 500))

        # Data throughput score
        if c.max_data_gb_per_day >= 1.0:
            c.scores["data"] = min(1.0, c.max_data_gb_per_day / 5.0)
        else:
            c.scores["data"] = c.max_data_gb_per_day

        # Weighted total
        c.total_score = sum(c.scores.get(k, 0) * w for k, w in criteria_weights.items())

    # Rank
    candidates.sort(key=lambda c: c.total_score, reverse=True)
    for i, c in enumerate(candidates):
        c.rank = i + 1

    # Build rationale for top 3
    top3 = candidates[:3]
    recommendation = _build_recommendation(top3, target_gsd_m, target_revisit_days, min_lifetime_years)

    return {
        "question": "Which orbit best serves the mission objectives?",
        "inputs": {
            "target_gsd_m": target_gsd_m,
            "target_revisit_days": target_revisit_days,
            "target_latitude_band": target_latitude_band,
            "aperture_m": aperture_m,
            "min_lifetime_years": min_lifetime_years,
            "max_cost_meur": max_cost_meur,
        },
        "criteria_weights": criteria_weights,
        "candidates": [
            {
                "rank": c.rank,
                "name": c.name,
                "altitude_km": c.altitude_km,
                "inclination_deg": round(c.inclination_deg, 1),
                "orbit_type": c.orbit_type,
                "eccentricity": c.eccentricity,
                "period_min": round(c.period_min, 1),
                "achievable_gsd_m": round(c.achievable_gsd_m, 1),
                "meets_gsd": c.achievable_gsd_m <= target_gsd_m and c.achievable_gsd_m > 0,
                "revisit_days": round(c.revisit_days, 1),
                "practical_revisit_days": round(c.practical_revisit_days, 1),
                "meets_revisit": c.practical_revisit_days <= target_revisit_days,
                "eclipse_fraction": round(c.eclipse_fraction, 2),
                "natural_lifetime_years": round(c.natural_lifetime_years, 1),
                "compliant_25yr": c.compliant_25yr,
                "compliant_5yr": c.compliant_5yr,
                "needs_deorbit_propulsion": c.needs_propulsion_for_deorbit,
                "contact_min_per_day": round(c.contact_min_per_day, 0),
                "max_data_gb_per_day": round(c.max_data_gb_per_day, 1),
                "launch_cost_keur": round(c.launch_cost_keur, 0),
                "rideshare_available": c.rideshare_available,
                "coverage_description": c.coverage_description,
                "scores": {k: round(v, 2) for k, v in c.scores.items()},
                "total_score": round(c.total_score, 3),
            }
            for c in candidates
        ],
        "recommendation": recommendation,
    }


def _compute_orbit_properties(
    c: OrbitCandidate,
    aperture_m: float,
    wavelength_um: float,
    lat_band: tuple[float, float],
    downlink_mbps: float,
) -> None:
    """Compute all derived properties for an orbit candidate."""
    HEO_TYPES = {"molniya", "tundra", "gto", "lunar"}
    is_heo = c.orbit_type in HEO_TYPES

    a = (R_EARTH_KM + c.altitude_km) * 1000  # metres
    c.velocity_ms = math.sqrt(MU_EARTH / a)
    c.period_min = 2 * math.pi * math.sqrt(a**3 / MU_EARTH) / 60
    c.orbits_per_day = 1440 / c.period_min

    # --- HEO / non-LEO orbits: override with known values ---
    if c.orbit_type == "molniya":
        c.period_min = 720.0          # 12 h
        c.orbits_per_day = 2.0
    elif c.orbit_type == "tundra":
        c.period_min = 1436.0         # ~24 h
        c.orbits_per_day = 1.0
    elif c.orbit_type == "gto":
        c.period_min = 630.0
        c.orbits_per_day = 1440 / 630
    elif c.orbit_type == "lunar":
        c.period_min = 655 * 60       # 27.3 days in minutes
        c.orbits_per_day = 1440 / c.period_min

    # Eclipse fraction (cylindrical shadow, beta=0 worst case)
    if is_heo:
        # HEO spends most time near apogee far from Earth shadow
        c.eclipse_fraction = 0.05 if c.orbit_type != "lunar" else 0.0
    else:
        rho = math.asin(R_EARTH_KM * 1000 / a)
        c.eclipse_fraction = rho / math.pi
        c.eclipse_fraction = min(c.eclipse_fraction, 0.40)

    if is_heo:
        # GSD / imaging not applicable for HEO comms/science orbits
        c.achievable_gsd_m = 0.0
        c.diffraction_limited_gsd_m = 0.0
        c.swath_km = 0.0
        c.revisit_days = 0.0
        c.practical_revisit_days = 0.0

        # Latitude coverage descriptions
        if c.orbit_type in ("molniya", "tundra"):
            c.latitude_coverage = "High-latitude (50–90°N dwell)"
        elif c.orbit_type == "gto":
            c.latitude_coverage = f"±{c.inclination_deg:.0f}° (transit orbit)"
        elif c.orbit_type == "lunar":
            c.latitude_coverage = "Cislunar"

        # Skip debris compliance for HEO — not meaningful
        c.natural_lifetime_years = 999
        c.compliant_25yr = True
        c.compliant_5yr = False
        c.needs_propulsion_for_deorbit = False

        # Contact time — HEO has long visibility from high-latitude stations
        if c.orbit_type == "molniya":
            c.contact_min_per_day = 480   # ~8 h/day visible from Arctic
        elif c.orbit_type == "tundra":
            c.contact_min_per_day = 720   # ~12 h/day
        elif c.orbit_type == "gto":
            c.contact_min_per_day = 120   # Apogee visibility windows
        elif c.orbit_type == "lunar":
            c.contact_min_per_day = 480   # DSN-like tracking

        c.max_data_gb_per_day = downlink_mbps * c.contact_min_per_day * 60 / 8 / 1000

        # Launch cost for HEO orbits
        if c.orbit_type == "molniya":
            c.launch_cost_keur = 5000
            c.rideshare_available = False
        elif c.orbit_type == "tundra":
            c.launch_cost_keur = 6000
            c.rideshare_available = False
        elif c.orbit_type == "gto":
            c.launch_cost_keur = 1500
            c.rideshare_available = True  # GTO rideshare is common
        elif c.orbit_type == "lunar":
            c.launch_cost_keur = 15000
            c.rideshare_available = False

        return  # Done — skip LEO-specific computations below

    # --- LEO-specific computations ---

    # GSD from aperture and altitude
    wl = wavelength_um * 1e-6
    h = c.altitude_km * 1000
    # Diffraction limit
    c.diffraction_limited_gsd_m = 1.22 * wl * h / aperture_m
    # Pixel-limited (assuming 6.5 um pixel, f/8)
    focal_length = aperture_m * 8  # f/8
    pixel_gsd = 6.5e-6 * h / focal_length
    c.achievable_gsd_m = max(c.diffraction_limited_gsd_m, pixel_gsd)

    # Swath width (assuming 5000 pixel detector)
    c.swath_km = 5000 * c.achievable_gsd_m / 1000

    # Revisit time — repeat ground track period (for reference)
    target_lat = (lat_band[0] + lat_band[1]) / 2
    lat_circumference_km = 2 * math.pi * R_EARTH_KM * math.cos(math.radians(target_lat))
    inter_orbit_km = lat_circumference_km / max(c.orbits_per_day, 1)

    if c.swath_km > 0 and inter_orbit_km > 0:
        c.revisit_days = max(1.0, inter_orbit_km / c.swath_km)
    else:
        c.revisit_days = 999

    # Latitude coverage
    if c.inclination_deg >= 80:
        c.latitude_coverage = "Global (±90°)"
    elif c.inclination_deg >= 50:
        c.latitude_coverage = f"±{c.inclination_deg:.0f}°"
    else:
        c.latitude_coverage = f"±{c.inclination_deg:.0f}° (equatorial band only)"

    # Practical revisit — swath-based calculation for single satellite
    # strips_per_day = orbits_per_day * swath_km / circumference_at_latitude
    # practical_revisit = 1 / strips_per_day
    equator_circumference_km = 2 * math.pi * R_EARTH_KM
    if c.swath_km > 0:
        strips_per_day = c.orbits_per_day * c.swath_km / equator_circumference_km
        if strips_per_day > 0:
            c.practical_revisit_days = max(1.0, 1.0 / strips_per_day)
        else:
            c.practical_revisit_days = 999
    else:
        c.practical_revisit_days = 999

    # Check if target latitude band is covered
    max_lat = c.inclination_deg
    if lat_band[0] < -max_lat or lat_band[1] > max_lat:
        c.revisit_days = 999  # Can't reach target latitude
        c.practical_revisit_days = 999

    # Orbital lifetime (simplified exponential atmosphere)
    from spacecdf_common.physics.debris import estimate_orbital_lifetime
    c.natural_lifetime_years = estimate_orbital_lifetime(c.altitude_km, area_to_mass_ratio_m2_kg=0.01)
    c.compliant_25yr = c.natural_lifetime_years <= 25
    c.compliant_5yr = c.natural_lifetime_years <= 5
    c.needs_propulsion_for_deorbit = not c.compliant_25yr

    # Contact time (Svalbard-like polar station)
    from spacecdf_common.physics.orbit import estimate_contact_time_per_day
    c.contact_min_per_day = estimate_contact_time_per_day(c.altitude_km, 78.0, c.inclination_deg) / 60

    # Data throughput
    c.max_data_gb_per_day = downlink_mbps * c.contact_min_per_day * 60 / 8 / 1000

    # Launch cost (rideshare estimate)
    if c.orbit_type == "iss":
        c.launch_cost_keur = 80
        c.rideshare_available = True
        c.orbit_access_notes = "ISS deployment via NanoRacks. Fixed orbit. Rapid decay (~1 year)."
    elif c.orbit_type == "sso" and 400 <= c.altitude_km <= 600:
        c.launch_cost_keur = 200
        c.rideshare_available = True
        c.orbit_access_notes = "Standard SSO rideshare (SpaceX Transporter, Vega-C SSMS)"
    elif c.orbit_type == "sso" and c.altitude_km > 600:
        c.launch_cost_keur = 300
        c.rideshare_available = True
        c.orbit_access_notes = "Higher SSO rideshare — less frequent, may need dedicated small launcher"
    elif c.orbit_type == "equatorial":
        c.launch_cost_keur = 500
        c.rideshare_available = False
        c.orbit_access_notes = "Equatorial orbit — limited rideshare, may need dedicated launcher from Kourou"
    elif c.orbit_type == "polar":
        c.launch_cost_keur = 220
        c.rideshare_available = True
        c.orbit_access_notes = "Polar non-SSO — similar access to SSO, slightly cheaper. No fixed LTAN."
    elif c.orbit_type == "mid_inc":
        c.launch_cost_keur = 180
        c.rideshare_available = True
        c.orbit_access_notes = "Mid-inclination — SpaceX Transporter or Falcon 9 rideshare. Good constellation orbit."
    else:
        c.launch_cost_keur = 250
        c.rideshare_available = True


def _sso_inclination(altitude_km: float) -> float:
    """Compute SSO inclination from altitude."""
    a = (R_EARTH_KM + altitude_km) * 1000
    n = math.sqrt(MU_EARTH / a**3)
    J2 = 1.08263e-3
    R = R_EARTH_KM * 1000
    target_rate = 0.9856 * math.pi / 180 / 86400
    cos_i = -target_rate / (1.5 * n * J2 * (R / a)**2)
    cos_i = max(-1.0, min(1.0, cos_i))
    return math.degrees(math.acos(cos_i))


def _build_recommendation(top3: list[OrbitCandidate], gsd: float, revisit: float, lifetime: float) -> str:
    """Build a plain-language recommendation from the top candidates."""
    if not top3:
        return "No viable orbit found for the given constraints."

    best = top3[0]
    parts = [f"Recommended: {best.name} (score {best.total_score:.2f}/1.00)"]

    if best.achievable_gsd_m <= gsd:
        parts.append(f"Achieves {best.achievable_gsd_m:.1f}m GSD (target: {gsd}m)")
    else:
        parts.append(f"GSD: {best.achievable_gsd_m:.1f}m — does NOT meet {gsd}m target. Consider larger aperture or lower orbit.")

    if best.practical_revisit_days <= revisit:
        parts.append(f"Practical revisit (±30° off-nadir): {best.practical_revisit_days:.1f} days (target: {revisit} days)")
    else:
        parts.append(f"Practical revisit: {best.practical_revisit_days:.1f} days — exceeds {revisit}-day target. Consider constellation or wider swath.")

    if best.needs_propulsion_for_deorbit:
        parts.append(f"Orbit lifetime {best.natural_lifetime_years:.0f} years — needs propulsion for deorbit.")
    elif best.compliant_5yr:
        parts.append(f"Naturally compliant with 5-year deorbit rule ({best.natural_lifetime_years:.1f} years).")
    else:
        parts.append(f"Compliant with 25-year rule ({best.natural_lifetime_years:.1f} years) but not 5-year rule.")

    if len(top3) > 1:
        parts.append(f"Alternative: {top3[1].name} (score {top3[1].total_score:.2f})")

    return " ".join(parts)
