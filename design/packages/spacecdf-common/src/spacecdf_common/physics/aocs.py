"""SpaceCDF — AOCS (Attitude and Orbit Control System) design equations.

Computes disturbance torques, actuator sizing, sensor selection,
and pointing budget for spacecraft attitude control design.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MU_EARTH = 3.986004418e14  # m^3/s^2
R_EARTH = 6371.0e3         # m
SOLAR_FLUX = 1361.0        # W/m^2
C_LIGHT = 299792458.0      # m/s

# Celestial body parameters for disturbance torque calculations
# (mu [m³/s²], radius [m], dipole_moment [T·m³], has_strong_field)
_BODY_PARAMS: dict[str, dict] = {
    "earth": {"mu": 3.986004418e14, "radius": 6371.0e3, "dipole_T": 3e-5, "has_atmo": True},
    "moon":  {"mu": 4.9048695e12,   "radius": 1737.4e3, "dipole_T": 0.0,  "has_atmo": False},
    "mars":  {"mu": 4.282837e13,    "radius": 3389.5e3, "dipole_T": 0.0,  "has_atmo": True},
}


@dataclass
class AOCSDesignResult:
    """Result of AOCS design analysis."""

    # Disturbance torques (N⋅m)
    gravity_gradient_torque_nm: float = 0.0
    solar_pressure_torque_nm: float = 0.0
    magnetic_torque_nm: float = 0.0
    aerodynamic_torque_nm: float = 0.0
    total_disturbance_torque_nm: float = 0.0

    # Actuator sizing
    reaction_wheel_torque_nm: float = 0.0
    reaction_wheel_momentum_nms: float = 0.0
    num_reaction_wheels: int = 4
    magnetorquer_dipole_am2: float = 0.0

    # Sensor selection
    sensors: list[str] = None

    # Mass/power/cost
    aocs_mass_kg: float = 0.0
    aocs_power_w: float = 0.0
    aocs_cost_keur: float = 0.0

    # Pointing budget
    pointing_accuracy_deg: float = 0.0
    pointing_knowledge_deg: float = 0.0
    pointing_stability_deg_s: float = 0.0

    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.sensors is None:
            self.sensors = []


def compute_disturbance_torques(
    altitude_km: float,
    spacecraft_mass_kg: float,
    spacecraft_area_m2: float = 1.0,
    max_dimension_m: float = 1.0,
    residual_dipole_am2: float = 0.1,
    cg_cp_offset_m: float = 0.01,
    inertia_ratio: float = 0.1,
    body: str = "earth",
) -> dict[str, float]:
    """Compute environmental disturbance torques on the spacecraft.

    Args:
        body: Central body — "earth", "moon", or "mars". Affects gravity
              gradient (mu), magnetic torque (dipole), and aerodynamic drag.

    Returns dict of individual and total torques in N·m.
    """
    bp = _BODY_PARAMS.get(body, _BODY_PARAMS["earth"])
    mu = bp["mu"]
    r_body = bp["radius"]
    b0 = bp["dipole_T"]
    has_atmo = bp["has_atmo"]

    a = r_body + altitude_km * 1e3

    # Gravity gradient torque
    Iz_minus_Iy = spacecraft_mass_kg * max_dimension_m**2 * inertia_ratio / 12
    t_gg = 3 * mu / (2 * a**3) * abs(Iz_minus_Iy)

    # Solar radiation pressure torque (body-independent)
    reflectivity = 0.5
    f_solar = SOLAR_FLUX / C_LIGHT * spacecraft_area_m2 * (1 + reflectivity)
    t_srp = f_solar * cg_cp_offset_m

    # Magnetic torque — Moon and Mars have negligible global dipole fields
    if b0 > 0:
        b_field = b0 * (r_body / a)**3
        t_mag = residual_dipole_am2 * b_field
    else:
        t_mag = 0.0

    # Aerodynamic torque — only for bodies with atmosphere, at low altitude
    t_aero = 0.0
    if has_atmo and body == "earth" and altitude_km < 600:
        h = altitude_km
        if h < 300:
            rho = 2.53e-10 * math.exp(-(h - 200) / 58.5)
        elif h < 500:
            rho = 6.24e-12 * math.exp(-(h - 300) / 53.6)
        else:
            rho = 1.95e-13 * math.exp(-(h - 400) / 53.3)
        v = math.sqrt(mu / a)
        cd = 2.2
        f_aero = 0.5 * rho * v**2 * cd * spacecraft_area_m2
        t_aero = f_aero * cg_cp_offset_m

    return {
        "gravity_gradient": t_gg,
        "solar_pressure": t_srp,
        "magnetic": t_mag,
        "aerodynamic": t_aero,
        "total": t_gg + t_srp + t_mag + t_aero,
    }


def compute_aocs_design(
    altitude_km: float,
    spacecraft_mass_kg: float,
    spacecraft_area_m2: float = 1.0,
    max_dimension_m: float = 1.0,
    required_pointing_deg: float = 0.1,
    required_stability_deg_s: float = 0.01,
    slew_rate_deg_s: float = 1.0,
    max_slew_angle_deg: float = 30.0,
    orbit_period_s: float = 5700.0,
    body: str = "earth",
) -> AOCSDesignResult:
    """Size the AOCS subsystem based on requirements and disturbance environment."""

    result = AOCSDesignResult()

    # Compute disturbances using the correct body's mu and field
    torques = compute_disturbance_torques(
        altitude_km, spacecraft_mass_kg, spacecraft_area_m2, max_dimension_m,
        body=body,
    )
    result.gravity_gradient_torque_nm = torques["gravity_gradient"]
    result.solar_pressure_torque_nm = torques["solar_pressure"]
    result.magnetic_torque_nm = torques["magnetic"]
    result.aerodynamic_torque_nm = torques["aerodynamic"]
    result.total_disturbance_torque_nm = torques["total"]

    # Determine AOCS mode: magnetorquer-only for loose pointing (>2°), else reaction wheels
    magnetorquer_only = required_pointing_deg >= 2.0

    if magnetorquer_only:
        # Magnetorquer-only AOCS — suitable for tech demos, IoT sats, etc.
        result.reaction_wheel_torque_nm = 0.0
        result.reaction_wheel_momentum_nms = 0.0
        result.num_reaction_wheels = 0

        # Magnetorquer dipole sized to overcome disturbances
        b_field = 3e-5 * (R_EARTH / (R_EARTH + altitude_km * 1e3))**3
        result.magnetorquer_dipole_am2 = max(0.2, torques["total"] / max(b_field, 1e-12) * 2.0)

        result.sensors = _select_sensors(required_pointing_deg)
        result.pointing_accuracy_deg = required_pointing_deg
        result.pointing_knowledge_deg = required_pointing_deg * 0.5
        result.pointing_stability_deg_s = required_stability_deg_s

        # Mass: magnetorquers + sensors + electronics
        mtq_mass = result.magnetorquer_dipole_am2 * 0.08  # ~80g per Am²
        sensor_mass = _sensor_mass(result.sensors)
        electronics_mass = 0.3 if spacecraft_mass_kg < 20 else 0.8
        result.aocs_mass_kg = mtq_mass * 3 + sensor_mass + electronics_mass

        # Power: magnetorquers are low-power
        result.aocs_power_w = 2.0 + 1.0  # MTQ + sensors
    else:
        # Reaction wheel AOCS
        # Torque: must exceed disturbance torque by factor 5-10
        control_authority_factor = 10.0
        result.reaction_wheel_torque_nm = torques["total"] * control_authority_factor

        # Slew torque (may dominate)
        inertia = spacecraft_mass_kg * max_dimension_m**2 / 12
        slew_torque = 4 * inertia * (slew_rate_deg_s * math.pi / 180) / max(max_slew_angle_deg, 1.0)
        result.reaction_wheel_torque_nm = max(result.reaction_wheel_torque_nm, slew_torque)

        # Momentum storage: accumulated disturbance over quarter orbit (desaturation twice per orbit)
        result.reaction_wheel_momentum_nms = torques["total"] * orbit_period_s / 4

        result.num_reaction_wheels = 4  # Tetrahedron for redundancy

        # Magnetorquer for desaturation
        b_field = 3e-5 * (R_EARTH / (R_EARTH + altitude_km * 1e3))**3
        if b_field > 0:
            result.magnetorquer_dipole_am2 = result.reaction_wheel_momentum_nms / (b_field * orbit_period_s * 0.1)
        else:
            result.magnetorquer_dipole_am2 = 1.0

        result.sensors = _select_sensors(required_pointing_deg)
        result.pointing_accuracy_deg = required_pointing_deg
        result.pointing_knowledge_deg = required_pointing_deg * 0.3
        result.pointing_stability_deg_s = required_stability_deg_s

        # Mass estimate
        wheel_mass = _wheel_mass(result.reaction_wheel_momentum_nms)
        sensor_mass = _sensor_mass(result.sensors)
        mtq_mass = result.magnetorquer_dipole_am2 * 0.08
        electronics_mass = 0.8 if spacecraft_mass_kg < 50 else 1.5
        result.aocs_mass_kg = (
            wheel_mass * result.num_reaction_wheels
            + sensor_mass
            + mtq_mass * 3
            + electronics_mass
        )

        # Power
        result.aocs_power_w = (
            result.num_reaction_wheels * 2.0
            + 3.0  # Star tracker
            + 1.0  # Magnetorquer (intermittent)
            + 3.0  # AOCS computer
        )

    # Cost
    result.aocs_cost_keur = result.aocs_mass_kg * 100  # ~100 kEUR/kg for AOCS

    # Warnings
    if required_pointing_deg < 0.01:
        result.warnings.append("Sub-0.01 deg pointing requires fine guidance sensor or interferometric techniques")
    if result.reaction_wheel_momentum_nms > 10:
        result.warnings.append(f"Momentum storage {result.reaction_wheel_momentum_nms:.1f} Nms — consider CMGs")

    return result


def _select_sensors(pointing_deg: float) -> list[str]:
    """Select attitude sensors based on pointing requirement."""
    sensors = []
    if pointing_deg < 0.01:
        sensors.extend(["star_tracker_x2", "fine_guidance_sensor", "gyroscope", "sun_sensor"])
    elif pointing_deg < 0.1:
        sensors.extend(["star_tracker_x2", "gyroscope", "sun_sensor"])
    elif pointing_deg < 1.0:
        sensors.extend(["star_tracker", "sun_sensor", "magnetometer"])
    elif pointing_deg < 5.0:
        sensors.extend(["sun_sensor", "magnetometer", "earth_sensor"])
    else:
        sensors.extend(["sun_sensor", "magnetometer"])
    return sensors


def _wheel_mass(momentum_nms: float) -> float:
    """Estimate single reaction wheel mass from momentum capacity."""
    if momentum_nms < 0.1:
        return 0.12  # Micro wheel (CubeSat)
    elif momentum_nms < 1.0:
        return 0.6   # Small wheel
    elif momentum_nms < 5.0:
        return 2.5   # Medium wheel
    elif momentum_nms < 20:
        return 5.0   # Standard wheel
    else:
        return 12.0  # Large wheel


def _sensor_mass(sensors: list[str]) -> float:
    """Estimate total sensor mass."""
    masses = {
        "star_tracker": 0.5,
        "star_tracker_x2": 1.0,
        "fine_guidance_sensor": 2.0,
        "gyroscope": 0.8,
        "sun_sensor": 0.1,
        "magnetometer": 0.1,
        "earth_sensor": 0.5,
    }
    return sum(masses.get(s, 0.3) for s in sensors)
