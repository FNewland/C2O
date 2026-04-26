"""SpaceCDF — Orbital mechanics for mission design.

Provides design-point orbital calculations: period, eclipse fraction,
ground station contact statistics, delta-V budgets, and coverage analysis.

Adapted from SMO's orbit propagator for steady-state design parameters
rather than time-stepping simulation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# Constants
MU_EARTH = 3.986004418e14  # m^3/s^2
R_EARTH = 6371.0e3  # m
J2 = 1.08263e-3
AU_KM = 1.495978707e8
SOLAR_FLUX = 1361.0  # W/m^2 at 1 AU
DEG = math.pi / 180.0
C_LIGHT = 299792458.0  # m/s


@dataclass
class OrbitDesignParams:
    """Design-point orbital parameters for a circular orbit."""

    altitude_km: float
    inclination_deg: float
    eccentricity: float = 0.0
    raan_deg: float = 0.0
    period_s: float = 0.0
    period_min: float = 0.0
    velocity_ms: float = 0.0
    eclipse_fraction: float = 0.0
    sunlight_fraction: float = 0.0
    eclipse_duration_min: float = 0.0
    sunlight_duration_min: float = 0.0
    orbits_per_day: float = 0.0
    ground_track_repeat_km: float = 0.0
    raan_drift_deg_day: float = 0.0
    arg_perigee_drift_deg_day: float = 0.0
    max_earth_angle_deg: float = 0.0
    footprint_radius_km: float = 0.0
    ground_speed_km_s: float = 0.0


def compute_orbit_params(
    altitude_km: float,
    inclination_deg: float,
    eccentricity: float = 0.0,
    beta_angle_deg: float = 0.0,
) -> OrbitDesignParams:
    """Compute design-point orbital parameters for a (near-)circular orbit.

    Args:
        altitude_km: Orbital altitude above Earth surface.
        inclination_deg: Orbital inclination in degrees.
        eccentricity: Orbital eccentricity (0 for circular).
        beta_angle_deg: Sun beta angle in degrees (affects eclipse fraction).
    """
    a = (R_EARTH + altitude_km * 1e3)  # semi-major axis in metres
    n = math.sqrt(MU_EARTH / a**3)  # mean motion (rad/s)
    period_s = 2 * math.pi / n
    velocity = math.sqrt(MU_EARTH / a)

    # Eclipse fraction for circular orbit
    beta_rad = beta_angle_deg * DEG
    rho = math.asin(R_EARTH / a)  # Earth angular radius from orbit
    cos_beta = math.cos(beta_rad)

    if abs(beta_angle_deg) >= (90 - math.degrees(rho)):
        eclipse_fraction = 0.0  # No eclipse (polar summer / high beta)
    else:
        # Cylindrical shadow approximation
        eclipse_half_angle = math.acos(math.sqrt(
            max(0, a**2 * cos_beta**2 - R_EARTH**2)
        ) / (a * abs(cos_beta) + 1e-9))
        eclipse_fraction = eclipse_half_angle / math.pi
        eclipse_fraction = min(eclipse_fraction, 0.5)  # Can't be in eclipse more than half

    # J2 perturbation rates
    inc_rad = inclination_deg * DEG
    p = a * (1 - eccentricity**2)
    raan_drift = -1.5 * n * J2 * (R_EARTH / p)**2 * math.cos(inc_rad)
    arg_p_drift = 0.75 * n * J2 * (R_EARTH / p)**2 * (5 * math.cos(inc_rad)**2 - 1)

    # Footprint / coverage
    earth_angle = math.acos(R_EARTH / a)
    footprint_radius = R_EARTH * earth_angle / 1e3  # km

    # Ground speed (for SSO-like orbits)
    ground_speed = velocity * R_EARTH / a / 1e3  # km/s

    return OrbitDesignParams(
        altitude_km=altitude_km,
        inclination_deg=inclination_deg,
        eccentricity=eccentricity,
        period_s=period_s,
        period_min=period_s / 60.0,
        velocity_ms=velocity,
        eclipse_fraction=eclipse_fraction,
        sunlight_fraction=1.0 - eclipse_fraction,
        eclipse_duration_min=(eclipse_fraction * period_s) / 60.0,
        sunlight_duration_min=((1.0 - eclipse_fraction) * period_s) / 60.0,
        orbits_per_day=86400.0 / period_s,
        raan_drift_deg_day=math.degrees(raan_drift) * 86400.0,
        arg_perigee_drift_deg_day=math.degrees(arg_p_drift) * 86400.0,
        max_earth_angle_deg=math.degrees(earth_angle),
        footprint_radius_km=footprint_radius,
        ground_speed_km_s=ground_speed,
    )


def sso_inclination(altitude_km: float) -> float:
    """Compute inclination for a Sun-Synchronous Orbit at given altitude.

    Returns inclination in degrees that gives RAAN drift = 0.9856 deg/day.
    """
    a = R_EARTH + altitude_km * 1e3
    n = math.sqrt(MU_EARTH / a**3)
    target_raan_rate = 0.9856 * DEG / 86400.0  # rad/s
    cos_i = -target_raan_rate / (1.5 * n * J2 * (R_EARTH / a)**2)
    cos_i = max(-1.0, min(1.0, cos_i))
    return math.degrees(math.acos(cos_i))


def delta_v_hohmann(r1_km: float, r2_km: float) -> tuple[float, float]:
    """Hohmann transfer delta-V between two circular orbits.

    Returns (dv1, dv2) in m/s.
    """
    r1 = (R_EARTH + r1_km * 1e3)
    r2 = (R_EARTH + r2_km * 1e3)
    a_t = (r1 + r2) / 2
    v1_circ = math.sqrt(MU_EARTH / r1)
    v2_circ = math.sqrt(MU_EARTH / r2)
    v1_trans = math.sqrt(MU_EARTH * (2 / r1 - 1 / a_t))
    v2_trans = math.sqrt(MU_EARTH * (2 / r2 - 1 / a_t))
    return abs(v1_trans - v1_circ), abs(v2_circ - v2_trans)


def delta_v_plane_change(velocity_ms: float, angle_deg: float) -> float:
    """Delta-V for a simple plane change manoeuvre."""
    return 2 * velocity_ms * math.sin(angle_deg * DEG / 2)


def delta_v_deorbit(altitude_km: float, target_perigee_km: float = 200.0) -> float:
    """Delta-V to lower perigee for deorbit (circular to elliptical)."""
    dv1, _ = delta_v_hohmann(altitude_km, target_perigee_km)
    return dv1


def delta_v_station_keeping(
    altitude_km: float,
    years: float,
    drag_coefficient: float = 2.2,
    area_to_mass_ratio: float = 0.01,
) -> float:
    """Estimated annual delta-V for drag makeup in LEO.

    Simple atmospheric density model + drag equation.
    """
    if altitude_km > 800:
        return 0.0  # Negligible drag above 800 km

    # Simplified exponential atmosphere
    h = altitude_km
    if h < 200:
        rho = 2.53e-10
    elif h < 300:
        rho = 2.53e-10 * math.exp(-(h - 200) / 58.5)
    elif h < 400:
        rho = 6.24e-12 * math.exp(-(h - 300) / 53.6)
    elif h < 500:
        rho = 1.95e-13 * math.exp(-(h - 400) / 53.3)
    elif h < 600:
        rho = 6.57e-15 * math.exp(-(h - 500) / 54.0)
    else:
        rho = 2.39e-16 * math.exp(-(h - 600) / 56.0)

    v = math.sqrt(MU_EARTH / (R_EARTH + h * 1e3))
    a_drag = 0.5 * rho * v**2 * drag_coefficient * area_to_mass_ratio
    dv_per_year = a_drag * 365.25 * 86400
    return dv_per_year * years


def estimate_contact_time_per_day(
    altitude_km: float,
    gs_latitude_deg: float,
    inclination_deg: float,
    min_elevation_deg: float = 5.0,
) -> float:
    """Estimate total ground station contact time per day (seconds).

    Geometric approximation, not SGP4. Good for design-point sizing.
    """
    a = R_EARTH + altitude_km * 1e3
    el_rad = min_elevation_deg * DEG
    # Max slant range at min elevation
    cos_gamma = R_EARTH * math.cos(el_rad) / a
    if cos_gamma >= 1:
        return 0.0
    gamma = math.acos(cos_gamma)
    half_swath_deg = math.degrees(gamma - el_rad)

    # Number of passes visible depends on latitude vs inclination
    lat_diff = abs(gs_latitude_deg) - abs(inclination_deg)
    if lat_diff > half_swath_deg:
        return 0.0  # GS never sees the orbit
    if lat_diff < -half_swath_deg:
        passes_per_day = 4.0  # Typical for polar/SSO over high-lat station
    else:
        passes_per_day = 2.0  # Fewer passes for lower latitude stations

    # Average pass duration
    period_s = 2 * math.pi * math.sqrt(a**3 / MU_EARTH)
    avg_pass_fraction = half_swath_deg / 180.0
    avg_pass_s = period_s * avg_pass_fraction
    return passes_per_day * avg_pass_s
