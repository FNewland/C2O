"""SpaceCDF physics engines for subsystem design calculations."""

from .orbit import compute_orbit_params, sso_inclination, delta_v_hohmann, delta_v_deorbit, delta_v_station_keeping, estimate_contact_time_per_day
from .power import compute_power_budget, rtg_power
from .thermal import compute_thermal_balance, spacecraft_surface_area
from .link_budget import compute_link_budget
from .structures import estimate_structure_mass, launch_loads
from .propulsion import compute_propulsion_budget, tsiolkovsky, select_propulsion_type
from .aocs import compute_aocs_design, compute_disturbance_torques

__all__ = [
    "compute_orbit_params", "sso_inclination", "delta_v_hohmann",
    "delta_v_deorbit", "delta_v_station_keeping", "estimate_contact_time_per_day",
    "compute_power_budget", "rtg_power",
    "compute_thermal_balance", "spacecraft_surface_area",
    "compute_link_budget",
    "estimate_structure_mass", "launch_loads",
    "compute_propulsion_budget", "tsiolkovsky", "select_propulsion_type",
    "compute_aocs_design", "compute_disturbance_torques",
]
