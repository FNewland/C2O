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
    orbit_type: str  # sso, polar, equatorial, iss, meo

    # Computed properties
    period_min: float = 0.0
    velocity_ms: float = 0.0
    eclipse_fraction: float = 0.0
    orbits_per_day: float = 0.0

    # Coverage
    swath_km: float = 0.0
    revisit_days: float = 0.0
    latitude_coverage: str = ""

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
        name="ISS orbit (420 km, 51.6°)",
        altitude_km=420, inclination_deg=51.6, orbit_type="iss",
    ))

    # Equatorial LEO (if target is equatorial)
    if target_latitude_band[0] >= -15 and target_latitude_band[1] <= 15:
        candidates.append(OrbitCandidate(
            name="Equatorial LEO 550 km",
            altitude_km=550, inclination_deg=0, orbit_type="equatorial",
        ))

    # Compute properties for each
    for c in candidates:
        _compute_orbit_properties(c, aperture_m, wavelength_um,
                                  target_latitude_band, downlink_rate_mbps)

    # Score candidates
    criteria_weights = {
        "gsd": 0.25,         # How close to target GSD
        "revisit": 0.20,     # How close to target revisit
        "lifetime": 0.15,    # Meets lifetime need
        "debris": 0.15,      # Debris compliance
        "cost": 0.15,        # Launch cost
        "data": 0.10,        # Daily data downlink capacity
    }

    for c in candidates:
        # GSD score: 1.0 if meets target, degrades linearly
        if c.achievable_gsd_m <= target_gsd_m:
            c.scores["gsd"] = 1.0
        else:
            c.scores["gsd"] = max(0, 1.0 - (c.achievable_gsd_m - target_gsd_m) / target_gsd_m)

        # Revisit score
        if c.revisit_days <= target_revisit_days:
            c.scores["revisit"] = 1.0
        else:
            c.scores["revisit"] = max(0, 1.0 - (c.revisit_days - target_revisit_days) / (target_revisit_days * 3))

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
                "period_min": round(c.period_min, 1),
                "achievable_gsd_m": round(c.achievable_gsd_m, 1),
                "meets_gsd": c.achievable_gsd_m <= target_gsd_m,
                "revisit_days": round(c.revisit_days, 1),
                "meets_revisit": c.revisit_days <= target_revisit_days,
                "eclipse_fraction": round(c.eclipse_fraction, 2),
                "natural_lifetime_years": round(c.natural_lifetime_years, 1),
                "compliant_25yr": c.compliant_25yr,
                "compliant_5yr": c.compliant_5yr,
                "needs_deorbit_propulsion": c.needs_propulsion_for_deorbit,
                "contact_min_per_day": round(c.contact_min_per_day, 0),
                "max_data_gb_per_day": round(c.max_data_gb_per_day, 1),
                "launch_cost_keur": round(c.launch_cost_keur, 0),
                "rideshare_available": c.rideshare_available,
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
    a = (R_EARTH_KM + c.altitude_km) * 1000  # metres
    c.velocity_ms = math.sqrt(MU_EARTH / a)
    c.period_min = 2 * math.pi * math.sqrt(a**3 / MU_EARTH) / 60
    c.orbits_per_day = 1440 / c.period_min

    # Eclipse fraction (cylindrical shadow, beta=0 worst case)
    rho = math.asin(R_EARTH_KM * 1000 / a)
    c.eclipse_fraction = rho / math.pi
    c.eclipse_fraction = min(c.eclipse_fraction, 0.40)

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

    # Revisit time (for a single satellite in polar/SSO orbit)
    # Each orbit, the ground track shifts west by (360° / orbits_per_day) × cos(inclination).
    # At the equator, the inter-orbit spacing is Earth_circumference / orbits_per_day.
    # Revisit = inter_orbit_spacing / swath_width (number of days to fill the gap).
    # At higher latitudes, tracks converge so revisit improves.
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

    # Check if target latitude band is covered
    max_lat = c.inclination_deg
    if lat_band[0] < -max_lat or lat_band[1] > max_lat:
        c.revisit_days = 999  # Can't reach target latitude

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

    if best.revisit_days <= revisit:
        parts.append(f"Revisit: {best.revisit_days:.1f} days (target: {revisit} days)")
    else:
        parts.append(f"Revisit: {best.revisit_days:.1f} days — exceeds {revisit}-day target. Consider constellation or wider swath.")

    if best.needs_propulsion_for_deorbit:
        parts.append(f"Orbit lifetime {best.natural_lifetime_years:.0f} years — needs propulsion for deorbit.")
    elif best.compliant_5yr:
        parts.append(f"Naturally compliant with 5-year deorbit rule ({best.natural_lifetime_years:.1f} years).")
    else:
        parts.append(f"Compliant with 25-year rule ({best.natural_lifetime_years:.1f} years) but not 5-year rule.")

    if len(top3) > 1:
        parts.append(f"Alternative: {top3[1].name} (score {top3[1].total_score:.2f})")

    return " ".join(parts)
