"""SpaceCDF — Beyond-LEO Orbit Support.

Provides orbit mechanics, power scaling, and link budgets for
MEO, GEO, HEO, lunar, and interplanetary missions.

References:
  - Wertz, Space Mission Engineering Ch. 5 — Orbit Design
  - Bate, Mueller, White — Fundamentals of Astrodynamics
  - NASA DSN Telecommunications Link Design Handbook (810-005)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# Constants
MU_EARTH = 3.986004418e14  # m³/s²
MU_MOON = 4.9048695e12
MU_SUN = 1.32712440018e20
R_EARTH_KM = 6371.0
R_MOON_KM = 1737.4
AU_KM = 149597870.7
SOLAR_FLUX_1AU = 1361.0  # W/m²


@dataclass
class BeyondLeoOrbit:
    """Orbital parameters for beyond-LEO missions."""
    name: str
    orbit_type: str  # "meo", "geo", "heo", "lunar", "interplanetary"
    altitude_km: float  # For circular; apogee for HEO
    perigee_km: float = 0  # For HEO
    inclination_deg: float = 0
    period_hours: float = 0
    # Environment
    radiation_dose_krad_per_year: float = 0
    eclipse_fraction: float = 0
    solar_flux_w_m2: float = SOLAR_FLUX_1AU
    # Communications
    max_range_km: float = 0
    free_space_loss_db: float = 0  # at 8 GHz


@dataclass
class TransferOrbit:
    """Transfer orbit parameters."""
    name: str
    delta_v_ms: float
    transfer_time_days: float
    type: str  # "hohmann", "bi-elliptic", "low_energy", "direct"


# Pre-computed orbit catalogue
BEYOND_LEO_ORBITS: list[BeyondLeoOrbit] = [
    # MEO
    BeyondLeoOrbit("MEO 2000 km", "meo", 2000, 2000, 55, 2.1,
                   radiation_dose_krad_per_year=50, eclipse_fraction=0.3,
                   max_range_km=4500, free_space_loss_db=178),
    BeyondLeoOrbit("GPS orbit (20200 km)", "meo", 20200, 20200, 55, 12.0,
                   radiation_dose_krad_per_year=100, eclipse_fraction=0.01,
                   max_range_km=26000, free_space_loss_db=195),
    # GEO
    BeyondLeoOrbit("GEO (35786 km)", "geo", 35786, 35786, 0, 24.0,
                   radiation_dose_krad_per_year=20, eclipse_fraction=0.01,
                   max_range_km=42000, free_space_loss_db=200),
    # HEO
    BeyondLeoOrbit("Molniya (500×39800 km)", "heo", 39800, 500, 63.4, 12.0,
                   radiation_dose_krad_per_year=80, eclipse_fraction=0.05,
                   max_range_km=46000, free_space_loss_db=201),
    BeyondLeoOrbit("Tundra (500×35786 km)", "heo", 35786, 500, 63.4, 24.0,
                   radiation_dose_krad_per_year=60, eclipse_fraction=0.03,
                   max_range_km=42000, free_space_loss_db=200),
    # Lunar
    BeyondLeoOrbit("Low Lunar Orbit (100 km)", "lunar", 100, 100, 90, 2.0,
                   radiation_dose_krad_per_year=15, eclipse_fraction=0.35,
                   solar_flux_w_m2=SOLAR_FLUX_1AU,
                   max_range_km=400000, free_space_loss_db=220),
    BeyondLeoOrbit("NRHO (Near-Rectilinear Halo)", "lunar", 70000, 1500, 0, 168,
                   radiation_dose_krad_per_year=20, eclipse_fraction=0.05,
                   solar_flux_w_m2=SOLAR_FLUX_1AU,
                   max_range_km=450000, free_space_loss_db=221),
    # Interplanetary
    BeyondLeoOrbit("Mars transfer (1.5 AU)", "interplanetary", 0, 0, 0, 0,
                   radiation_dose_krad_per_year=30, eclipse_fraction=0.0,
                   solar_flux_w_m2=SOLAR_FLUX_1AU / 2.25,  # 1/1.5²
                   max_range_km=400e6, free_space_loss_db=280),
]


def compute_transfer_delta_v(
    from_orbit_km: float,
    to_orbit: BeyondLeoOrbit,
) -> TransferOrbit:
    """Compute delta-V for transfer from LEO to target orbit."""
    r1 = (R_EARTH_KM + from_orbit_km) * 1000
    v_circ = math.sqrt(MU_EARTH / r1)

    if to_orbit.orbit_type == "meo":
        r2 = (R_EARTH_KM + to_orbit.altitude_km) * 1000
        # Hohmann transfer
        v_transfer_1 = math.sqrt(MU_EARTH * (2/r1 - 2/(r1 + r2)))
        v_transfer_2 = math.sqrt(MU_EARTH * (2/r2 - 2/(r1 + r2)))
        v_circ_2 = math.sqrt(MU_EARTH / r2)
        dv = abs(v_transfer_1 - v_circ) + abs(v_circ_2 - v_transfer_2)
        transfer_time = math.pi * math.sqrt((r1 + r2)**3 / (8 * MU_EARTH)) / 86400
        return TransferOrbit("Hohmann to MEO", round(dv, 1), round(transfer_time, 2), "hohmann")

    elif to_orbit.orbit_type == "geo":
        r2 = (R_EARTH_KM + 35786) * 1000
        v_transfer_1 = math.sqrt(MU_EARTH * (2/r1 - 2/(r1 + r2)))
        v_transfer_2 = math.sqrt(MU_EARTH * (2/r2 - 2/(r1 + r2)))
        v_circ_2 = math.sqrt(MU_EARTH / r2)
        dv = abs(v_transfer_1 - v_circ) + abs(v_circ_2 - v_transfer_2)
        transfer_time = math.pi * math.sqrt((r1 + r2)**3 / (8 * MU_EARTH)) / 86400
        return TransferOrbit("Hohmann to GEO", round(dv, 1), round(transfer_time, 2), "hohmann")

    elif to_orbit.orbit_type == "heo":
        r_apo = (R_EARTH_KM + to_orbit.altitude_km) * 1000
        v_transfer = math.sqrt(MU_EARTH * (2/r1 - 2/(r1 + r_apo)))
        dv = abs(v_transfer - v_circ)
        transfer_time = math.pi * math.sqrt((r1 + r_apo)**3 / (8 * MU_EARTH)) / 86400
        return TransferOrbit("Direct to HEO", round(dv, 1), round(transfer_time, 2), "direct")

    elif to_orbit.orbit_type == "lunar":
        # TLI from LEO: ~3100 m/s + LOI: ~800 m/s
        dv_tli = 3100
        dv_loi = 800
        if "NRHO" in to_orbit.name:
            dv_loi = 450  # Lower insertion for NRHO
        return TransferOrbit("TLI + LOI", dv_tli + dv_loi, 4.5, "direct")

    elif to_orbit.orbit_type == "interplanetary":
        # Earth escape + TMI: ~3600 m/s for Mars
        return TransferOrbit("Earth escape + TMI", 3600, 180, "hohmann")

    return TransferOrbit("Unknown", 0, 0, "unknown")


def compute_power_at_distance(
    solar_panel_power_1au_w: float,
    distance_au: float = 1.0,
) -> float:
    """Compute solar panel power at a given distance from the Sun.

    Power scales as 1/r² from solar flux.
    """
    if distance_au <= 0:
        return 0
    return solar_panel_power_1au_w / (distance_au ** 2)


def compute_dsn_link_budget(
    frequency_ghz: float = 8.4,
    tx_power_w: float = 4.0,
    tx_antenna_gain_dbi: float = 29.0,
    range_km: float = 400000,
    ground_antenna_m: float = 34.0,
    ground_system_temp_k: float = 25.0,
    data_rate_bps: float = 8000,
) -> dict[str, float]:
    """Compute deep-space link budget for DSN communication.

    Default values based on MarCO X-band parameters.
    """
    c = 3e8
    wavelength = c / (frequency_ghz * 1e9)

    # EIRP
    eirp_dbw = 10 * math.log10(tx_power_w) + tx_antenna_gain_dbi

    # Free space path loss
    fspl = 20 * math.log10(4 * math.pi * range_km * 1000 / wavelength)

    # Ground antenna gain
    eta = 0.55
    gr_gain = 10 * math.log10(eta * (math.pi * ground_antenna_m / wavelength)**2)

    # G/T
    gt = gr_gain - 10 * math.log10(ground_system_temp_k)

    # Required Eb/N0 (LDPC coded BPSK)
    eb_n0_required = 2.0  # dB

    # Received C/N0
    k_dbw = -228.6  # Boltzmann
    cn0 = eirp_dbw - fspl + gt - k_dbw

    # Available Eb/N0
    eb_n0_available = cn0 - 10 * math.log10(data_rate_bps)

    margin = eb_n0_available - eb_n0_required

    return {
        "eirp_dbw": round(eirp_dbw, 1),
        "fspl_db": round(fspl, 1),
        "ground_gain_dbi": round(gr_gain, 1),
        "gt_dbk": round(gt, 1),
        "cn0_dbhz": round(cn0, 1),
        "eb_n0_available_db": round(eb_n0_available, 1),
        "eb_n0_required_db": eb_n0_required,
        "margin_db": round(margin, 1),
        "link_closes": margin >= 0,
    }
