"""SpaceCDF — Lumped-parameter CubeSat thermal transient solver (SCDF-214).

Single-node ODE model driven by orbital heating (solar, albedo, Earth IR)
and spacecraft radiation.  Uses scipy.integrate.solve_ivp.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

# ── Physical constants ──────────────────────────────────────────────────
STEFAN_BOLTZMANN = 5.670374419e-8  # W m⁻² K⁻⁴
SOLAR_FLUX = 1361.0               # W m⁻² (at 1 AU)
EARTH_RADIUS_KM = 6371.0
EARTH_IR_TEMP_K = 255.0           # Effective Earth IR temperature
ALBEDO_COEFF = 0.30               # Average Earth albedo
MU_EARTH = 3.986004418e14         # m³ s⁻² (standard gravitational parameter)
CP_ALUMINIUM = 900.0              # J kg⁻¹ K⁻¹


def _orbit_period_s(altitude_km: float) -> float:
    """Keplerian orbit period from altitude."""
    a = (EARTH_RADIUS_KM + altitude_km) * 1e3  # semi-major axis in m
    return 2.0 * math.pi * math.sqrt(a ** 3 / MU_EARTH)


def _eclipse_fraction(altitude_km: float, inclination_deg: float) -> float:
    """Approximate eclipse fraction for a circular orbit.

    Uses geometric shadow cylinder model.  For high-inclination SSO the
    eclipse fraction is fairly constant; for low inclination it depends
    on beta angle, which we approximate here.
    """
    r_orbit = EARTH_RADIUS_KM + altitude_km
    # Half-angle subtended by Earth shadow cone
    rho = math.asin(EARTH_RADIUS_KM / r_orbit)
    # Fraction of orbit in shadow (cylindrical approximation)
    frac = rho / math.pi
    # Beta-angle modulation (simple model — worst-case zero beta)
    beta_deg = abs(90.0 - inclination_deg) if inclination_deg <= 90 else abs(inclination_deg - 90.0)
    if beta_deg > math.degrees(rho):
        # Full sun — no eclipse (e.g. dawn-dusk SSO)
        return 0.0
    return float(frac)


def _earth_view_factor(altitude_km: float) -> float:
    """View factor from spacecraft to Earth (sphere to point approximation)."""
    r_orbit = EARTH_RADIUS_KM + altitude_km
    sin_rho = EARTH_RADIUS_KM / r_orbit
    return sin_rho ** 2


def compute_thermal_transient(
    orbit_altitude_km: float = 500,
    orbit_inclination_deg: float = 97.4,
    mass_kg: float = 4.0,
    surface_area_m2: float = 0.06,
    alpha_s: float = 0.3,
    epsilon_ir: float = 0.8,
    internal_power_w: float = 5.0,
    num_orbits: int = 3,
) -> dict[str, Any]:
    """Run lumped-parameter thermal transient and return results.

    Returns
    -------
    dict with keys:
        times_s          – list of time values [s]
        temperatures_k   – list of temperature values [K]
        hot_case_k       – maximum temperature over the simulation
        cold_case_k      – minimum temperature over the simulation
        eclipse_fraction – fraction of orbit in eclipse
        orbit_period_s   – orbital period [s]
    """
    period_s = _orbit_period_s(orbit_altitude_km)
    ecl_frac = _eclipse_fraction(orbit_altitude_km, orbit_inclination_deg)
    f_earth = _earth_view_factor(orbit_altitude_km)

    # Projected area for solar flux (assume 1/6 of total surface faces sun)
    a_sun = surface_area_m2 / 6.0

    # Eclipse timing within one orbit
    ecl_start = period_s * (1.0 - ecl_frac)  # sunlit first, then eclipse

    def in_sunlight(t: float) -> bool:
        """True if spacecraft is in sunlight at time *t*."""
        phase = t % period_s
        return phase < ecl_start

    def _rhs(_t: float, state: np.ndarray) -> np.ndarray:
        T = state[0]

        # Solar heating (zero during eclipse)
        if in_sunlight(_t):
            # Simple cos(theta) = 1 model (sun-pointing face)
            q_sun = alpha_s * SOLAR_FLUX * a_sun
            q_albedo = alpha_s * SOLAR_FLUX * ALBEDO_COEFF * f_earth * a_sun
        else:
            q_sun = 0.0
            q_albedo = 0.0

        # Earth IR (always present)
        q_earth = epsilon_ir * STEFAN_BOLTZMANN * EARTH_IR_TEMP_K ** 4 * f_earth * surface_area_m2

        # Internal dissipation
        q_internal = internal_power_w

        # Radiative loss
        q_rad = epsilon_ir * STEFAN_BOLTZMANN * T ** 4 * surface_area_m2

        dTdt = (q_sun + q_earth + q_albedo + q_internal - q_rad) / (mass_kg * CP_ALUMINIUM)
        return np.array([dTdt])

    # Initial temperature — rough equilibrium estimate
    q_avg_in = (
        alpha_s * SOLAR_FLUX * a_sun * (1.0 - ecl_frac)
        + alpha_s * SOLAR_FLUX * ALBEDO_COEFF * f_earth * a_sun * (1.0 - ecl_frac)
        + epsilon_ir * STEFAN_BOLTZMANN * EARTH_IR_TEMP_K ** 4 * f_earth * surface_area_m2
        + internal_power_w
    )
    T0 = (q_avg_in / (epsilon_ir * STEFAN_BOLTZMANN * surface_area_m2)) ** 0.25

    t_end = period_s * num_orbits
    n_points = max(500, int(num_orbits * 200))
    t_eval = np.linspace(0, t_end, n_points)

    sol = solve_ivp(
        _rhs,
        [0, t_end],
        [T0],
        t_eval=t_eval,
        method="RK45",
        rtol=1e-8,
        atol=1e-8,
    )

    temps = sol.y[0]
    times = sol.t

    # Use last orbit for hot/cold case (quasi-steady state)
    last_orbit_mask = times >= (t_end - period_s)
    last_temps = temps[last_orbit_mask]

    hot_case_k = float(np.max(last_temps))
    cold_case_k = float(np.min(last_temps))

    return {
        "times_s": [float(x) for x in times],
        "temperatures_k": [float(x) for x in temps],
        "hot_case_k": hot_case_k,
        "cold_case_k": cold_case_k,
        "eclipse_fraction": ecl_frac,
        "orbit_period_s": period_s,
    }
