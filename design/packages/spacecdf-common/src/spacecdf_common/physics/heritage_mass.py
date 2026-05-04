"""SpaceCDF — CubeSat-calibrated parametric models.

Subsystem mass fractions, cost fractions, and power duty cycles derived
from real published CubeSat mission data.

ALL PARAMETRIC DATA IS EXPOSED via get_all_parametric_data() so the user
can view and override any value in the UI.

Sources:
  - SMAD4 Table 10-8: Spacecraft subsystem mass fractions
  - Planet SuperDove, Spire LEMUR-2, OPS-SAT, GOMX-3/4 published data
  - SwissCube (1U), Delfi-C3 (3U), PicSat (3U), INSPIRE (3U) from eoPortal
  - ASTERIA (6U), MarCO (6U) from NASA/JPL
  - GomSpace, ISIS, NanoAvionics, Endurosat vendor datasheets
  - Bouwmeester & Guo (2010) nanosatellite survey
  - Aerospace Corporation SSCM (Small Spacecraft Cost Model)
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Mass fractions: typical % of dry mass per subsystem, by spacecraft class
# These are TYPICAL values, not minimums — used as starting estimates
# when no specific component selection has been made.
# ---------------------------------------------------------------------------

MASS_FRACTIONS: dict[str, dict[str, float]] = {
    "structure": {
        "nano":  0.09,   # 3U: 350g / 4000g = 8.8%
        "micro": 0.13,   # 6U: 600-900g / 8000g = 10%; 12U: ~12%
        "small": 0.14,
        "medium": 0.12,
        "large": 0.10,
    },
    "eps": {
        # EPS = solar panels + battery + EPS board
        "nano":  0.19,   # 3U: ~750g / 4000g = 18.8%
        "micro": 0.17,   # 6U: ~1200g / 8000g = 15%
        "small": 0.10,
        "medium": 0.08,
        "large": 0.07,
    },
    "aocs": {
        # Active 3-axis: RW + magnetorquers + star tracker + sun sensors
        "nano":  0.14,   # 3U: ~550g / 4000g = 13.8% (with reaction wheels)
        "micro": 0.10,   # 6U: ~800g / 8000g = 10%
        "small": 0.06,
        "medium": 0.04,
        "large": 0.03,
    },
    "aocs_coarse": {
        # Coarse pointing only: magnetorquers + sun sensors (no RW, no ST)
        "nano":  0.03,   # 3U: ~100g / 4000g = 2.5%
        "micro": 0.03,
        "small": 0.02,
        "medium": 0.02,
        "large": 0.01,
    },
    "ttc": {
        # TTC = transponder + antennas
        "nano":  0.06,   # 3U: ~250g / 4000g = 6.3%
        "micro": 0.06,
        "small": 0.04,
        "medium": 0.03,
        "large": 0.02,
    },
    "obdh": {
        "nano":  0.02,   # 3U: ~80g / 4000g = 2%
        "micro": 0.02,
        "small": 0.015,
        "medium": 0.01,
        "large": 0.008,
    },
    "tcs": {
        "nano":  0.01,   # 3U: ~50g / 4000g = 1.3% (passive thermal)
        "micro": 0.03,
        "small": 0.04,
        "medium": 0.04,
        "large": 0.05,
    },
    "harness": {
        "nano":  0.04,   # 3U: ~150g / 4000g = 3.8%
        "micro": 0.05,
        "small": 0.06,
        "medium": 0.06,
        "large": 0.07,
    },
}

# Default payload mass fraction (rest of the budget after bus)
PAYLOAD_FRACTION: dict[str, float] = {
    "nano":  0.30,   # 3U: ~1200g / 4000g = 30%
    "micro": 0.35,
    "small": 0.40,
    "medium": 0.45,
    "large": 0.45,
}

# Design margin by phase
MASS_MARGIN: dict[str, float] = {
    "nano":  0.15,   # 15% margin for CubeSat
    "micro": 0.15,
    "small": 0.20,
    "medium": 0.20,
    "large": 0.20,
}


# ---------------------------------------------------------------------------
# Cost fractions: typical % of total mission cost, by spacecraft class
# ---------------------------------------------------------------------------

COST_FRACTIONS: dict[str, dict[str, float]] = {
    "bus_hardware": {
        "nano":  0.30,   # 3U: ~30% bus HW ($50-150k of $500k)
        "micro": 0.28,
        "small": 0.25,
    },
    "payload": {
        "nano":  0.20,   # Variable: 15-35%
        "micro": 0.25,
        "small": 0.30,
    },
    "integration_test": {
        "nano":  0.12,   # I&T: 10-15%
        "micro": 0.12,
        "small": 0.10,
    },
    "software": {
        "nano":  0.08,   # FSW + GSW
        "micro": 0.08,
        "small": 0.07,
    },
    "launch": {
        "nano":  0.15,   # $50-100k per U
        "micro": 0.12,
        "small": 0.10,
    },
    "ground_segment": {
        "nano":  0.05,
        "micro": 0.05,
        "small": 0.05,
    },
    "operations_1yr": {
        "nano":  0.05,
        "micro": 0.05,
        "small": 0.05,
    },
    "program_management": {
        "nano":  0.05,
        "micro": 0.05,
        "small": 0.08,
    },
}


# ---------------------------------------------------------------------------
# Power duty cycles: typical % of orbit time per mode
# ---------------------------------------------------------------------------

POWER_DUTY_CYCLES: dict[str, dict[str, Any]] = {
    "idle": {
        "power_w": {"nano": 2.0, "micro": 5.0, "small": 15.0},
        "duty_pct": 55,  # % of orbit
        "description": "OBC, ADCS standby, beacon, health monitoring",
    },
    "imaging": {
        "power_w": {"nano": 6.0, "micro": 15.0, "small": 40.0},
        "duty_pct": 10,
        "description": "Camera/sensor active, fine pointing, data recording",
    },
    "downlink_uhf": {
        "power_w": {"nano": 4.0, "micro": 6.0, "small": 10.0},
        "duty_pct": 8,
        "description": "UHF transmitter active, ~2W RF, ~10 kbps",
    },
    "downlink_sband": {
        "power_w": {"nano": 8.0, "micro": 12.0, "small": 20.0},
        "duty_pct": 5,
        "description": "S-band transmitter, ~2W RF, ~1 Mbps",
    },
    "downlink_xband": {
        "power_w": {"nano": 12.0, "micro": 18.0, "small": 25.0},
        "duty_pct": 3,
        "description": "X-band transmitter, ~2-4W RF, ~50-200 Mbps",
    },
    "eclipse": {
        "power_w": {"nano": 3.0, "micro": 8.0, "small": 20.0},
        "duty_pct": 35,  # Eclipse fraction ~35% for SSO 500km
        "description": "Battery-powered: OBC, ADCS, heaters",
    },
    "safe": {
        "power_w": {"nano": 1.0, "micro": 3.0, "small": 10.0},
        "duty_pct": 100,  # Continuous when in safe mode
        "description": "Minimum survival: beacon, coarse ADCS, heaters",
    },
}

# Typical SA power generation by form factor (body-mounted vs deployable)
SA_POWER_GENERATION: dict[str, dict[str, float]] = {
    "body_mounted": {
        "1U": 2.0, "2U": 3.5, "3U": 7.0,
        "6U": 12.0, "12U": 20.0,
    },
    "single_deployable": {
        "1U": 4.0, "2U": 7.0, "3U": 15.0,
        "6U": 30.0, "12U": 50.0,
    },
    "dual_deployable": {
        "3U": 25.0, "6U": 48.0, "12U": 80.0,
    },
}


# ---------------------------------------------------------------------------
# API: calibrate_mass (backward-compatible)
# ---------------------------------------------------------------------------

def calibrate_mass(
    subsystem: str,
    parametric_mass_kg: float,
    dry_mass_estimate_kg: float,
    spacecraft_class: str,
) -> float:
    """Return the greater of parametric mass and heritage fraction floor.

    Uses the CubeSat-calibrated mass fractions from real mission data.
    """
    fractions = MASS_FRACTIONS.get(subsystem, {})
    typical_fraction = fractions.get(spacecraft_class, 0.0)
    heritage_floor = typical_fraction * dry_mass_estimate_kg
    return max(parametric_mass_kg, heritage_floor)


def get_heritage_fractions(spacecraft_class: str) -> dict[str, float]:
    """Return all subsystem mass fractions for a spacecraft class."""
    return {
        subsystem: fracs.get(spacecraft_class, 0.0)
        for subsystem, fracs in MASS_FRACTIONS.items()
    }


# ---------------------------------------------------------------------------
# Duty cycle estimator
# ---------------------------------------------------------------------------

def estimate_duty_cycles(
    spacecraft_class: str = "nano",
    mission_type: str = "earth_observation",
    comms_band: str = "S",
    eclipse_fraction: float = 0.35,
) -> list[dict[str, Any]]:
    """Estimate power duty cycles for a given mission configuration.

    Returns a list of modes with power draw, duty cycle %, and orbit-average power.
    """
    modes = []

    # Always have idle
    idle = POWER_DUTY_CYCLES["idle"]
    idle_power = idle["power_w"].get(spacecraft_class, 2.0)

    # Eclipse
    eclipse = POWER_DUTY_CYCLES["eclipse"]
    eclipse_power = eclipse["power_w"].get(spacecraft_class, 3.0)
    eclipse_pct = eclipse_fraction * 100

    sunlight_pct = 100 - eclipse_pct

    # Science/payload mode
    if mission_type in ("earth_observation", "sar"):
        sci = POWER_DUTY_CYCLES["imaging"]
        sci_pct = sci["duty_pct"]
        sci_power = sci["power_w"].get(spacecraft_class, 6.0)
        modes.append({"mode": "Imaging", "power_w": sci_power, "duty_pct": sci_pct,
                       "orbit_avg_w": sci_power * sci_pct / 100, "description": sci["description"]})
    elif mission_type in ("communications", "ais", "iot"):
        sci_pct = 50  # Continuous receive for comms/AIS
        sci_power = idle_power + 1  # Receiver adds ~1W
        modes.append({"mode": "Receive", "power_w": sci_power, "duty_pct": sci_pct,
                       "orbit_avg_w": sci_power * sci_pct / 100, "description": "Payload receiver active"})

    # Downlink
    dl_key = f"downlink_{comms_band.lower()}band"
    dl = POWER_DUTY_CYCLES.get(dl_key, POWER_DUTY_CYCLES.get("downlink_sband"))
    if dl:
        dl_power = dl["power_w"].get(spacecraft_class, 8.0)
        dl_pct = dl["duty_pct"]
        modes.append({"mode": f"Downlink ({comms_band}-band)", "power_w": dl_power, "duty_pct": dl_pct,
                       "orbit_avg_w": dl_power * dl_pct / 100, "description": dl["description"]})

    # Idle fills the rest of sunlight
    used_sunlight = sum(m["duty_pct"] for m in modes)
    idle_pct = max(0, sunlight_pct - used_sunlight)
    modes.insert(0, {"mode": "Idle", "power_w": idle_power, "duty_pct": idle_pct,
                      "orbit_avg_w": idle_power * idle_pct / 100, "description": idle["description"]})

    # Eclipse
    modes.append({"mode": "Eclipse", "power_w": eclipse_power, "duty_pct": eclipse_pct,
                   "orbit_avg_w": eclipse_power * eclipse_pct / 100, "description": eclipse["description"]})

    # Orbit-average total
    total_avg = sum(m["orbit_avg_w"] for m in modes)
    for m in modes:
        m["orbit_avg_w"] = round(m["orbit_avg_w"], 2)

    return modes


def estimate_sa_power_needed(
    spacecraft_class: str = "nano",
    mission_type: str = "earth_observation",
    comms_band: str = "S",
    eclipse_fraction: float = 0.35,
    battery_charge_efficiency: float = 0.9,
    orbit_period_s: float = 5700.0,
) -> float:
    """Estimate SA power needed from duty cycle analysis.

    The SA must provide enough power during sunlight to:
    1. Run the highest-demand sunlight mode (not orbit average)
    2. Recharge the battery for eclipse loads

    This is more accurate than summing all subsystem peaks because not
    all modes run simultaneously, but it's higher than orbit-average
    because the SA must handle peak sunlight demand + recharge.
    """
    modes = estimate_duty_cycles(spacecraft_class, mission_type, comms_band, eclipse_fraction)

    sunlight_frac = 1.0 - eclipse_fraction
    sunlight_time_s = sunlight_frac * orbit_period_s
    eclipse_time_s = eclipse_fraction * orbit_period_s

    # Find highest sunlight mode power (SA must handle this during that mode)
    max_sunlight_power = 0
    eclipse_energy_wh = 0

    for m in modes:
        if "eclipse" in m["mode"].lower():
            eclipse_energy_wh = m["power_w"] * (eclipse_time_s / 3600)
        else:
            max_sunlight_power = max(max_sunlight_power, m["power_w"])

    # Battery recharge: eclipse energy / sunlight time / charge efficiency
    if sunlight_time_s > 0:
        recharge_power = eclipse_energy_wh / (sunlight_time_s / 3600) / battery_charge_efficiency
    else:
        recharge_power = 0

    # SA power = max sunlight demand + recharge
    sa_power_needed = max_sunlight_power + recharge_power
    return round(sa_power_needed, 1)


# ---------------------------------------------------------------------------
# Get all parametric data for UI display/editing
# ---------------------------------------------------------------------------

def get_all_parametric_data() -> dict[str, Any]:
    """Return ALL parametric model data for UI display and editing.

    The user should be able to view and override any value in these tables.
    """
    return {
        "mass_fractions": MASS_FRACTIONS,
        "payload_fraction": PAYLOAD_FRACTION,
        "mass_margin": MASS_MARGIN,
        "cost_fractions": COST_FRACTIONS,
        "power_duty_cycles": POWER_DUTY_CYCLES,
        "sa_power_generation": SA_POWER_GENERATION,
        "sources": [
            "SMAD4 Table 10-8",
            "Planet SuperDove, Spire LEMUR-2, OPS-SAT, GOMX-3/4",
            "SwissCube, Delfi-C3, PicSat, INSPIRE, ASTERIA, MarCO",
            "GomSpace, ISIS, NanoAvionics vendor datasheets",
            "Bouwmeester & Guo (2010) nanosatellite survey",
            "Aerospace Corporation SSCM",
        ],
    }
