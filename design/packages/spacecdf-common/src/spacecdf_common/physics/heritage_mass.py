"""SpaceCDF — Heritage mass calibration factors.

Per-subsystem minimum mass fractions derived from published mission data.
These ensure that parametric sizing never produces subsystem masses below
what real spacecraft of that class actually achieve.

Sources:
  - SMAD4 Table 10-8: Spacecraft subsystem mass fractions
  - ESA CDF heritage database (PROBA, Sentinel, Herschel)
  - SSTL platform data (DMC, NovaSAR, TechDemoSat)
  - Planet, Spire, GomSpace CubeSat mass budgets

Usage:
    from spacecdf_common.physics.heritage_mass import calibrate_mass
    calibrated = calibrate_mass("eps", parametric_mass, dry_mass_estimate, "micro")
"""
from __future__ import annotations


# Per-subsystem minimum mass as fraction of dry mass, by spacecraft class.
# Format: {subsystem: {class: fraction}}
# If parametric model computes less than fraction × dry_mass, use the floor.
#
# Fractions represent the MINIMUM plausible mass for a real spacecraft.
# They account for harness, connectors, brackets, thermal interface, and
# integration overhead that parametric models systematically miss.

_MIN_MASS_FRACTIONS: dict[str, dict[str, float]] = {
    "eps": {
        # EPS = SA + battery + PCDU + harness + regulation
        "nano":     0.10,   # CubeSat: NanoPower board + battery + SA cells
        "micro":    0.10,   # PROBA-V: ~12 kg / 138 kg = 8.7%; add margin
        "small":    0.08,   # Sentinel: ~8-10% of dry mass
        "medium":   0.07,
        "large":    0.06,
        "flagship": 0.05,
    },
    "ttc": {
        # TTC = transponder + PA + antenna + diplexer + harness
        "nano":     0.03,   # GomSpace NanoCom: ~0.3 kg / 7 kg = 4%
        "micro":    0.03,   # PROBA-V: ~4 kg / 138 kg = 2.9%
        "small":    0.025,
        "medium":   0.02,
        "large":    0.015,
        "flagship": 0.01,
    },
    "aocs": {
        # AOCS = sensors + actuators + electronics + brackets
        "nano":     0.04,   # Magnetorquers/RWs + magnetometer
        "micro":    0.04,   # PROBA-V: ~6 kg / 138 kg = 4.3%
        "small":    0.035,
        "medium":   0.03,
        "large":    0.025,
        "flagship": 0.02,
    },
    "tcs": {
        # TCS = MLI + radiators + heaters + thermistors + heat pipes
        "nano":     0.02,   # CubeSat: mostly passive
        "micro":    0.03,   # PROBA-V: ~4 kg / 138 kg = 2.9%
        "small":    0.03,
        "medium":   0.04,
        "large":    0.04,
        "flagship": 0.05,
    },
    "structure": {
        # Structure = primary + secondary + mechanisms + adapters
        "nano":     0.15,   # CubeSat frame ~15-20%
        "micro":    0.16,   # PROBA-V: ~22 kg / 138 kg = 15.9%
        "small":    0.14,   # ~14-18% for small class
        "medium":   0.12,
        "large":    0.10,
        "flagship": 0.08,
    },
    "obdh": {
        # OBDH = OBC + mass memory + data bus + harness
        "nano":     0.02,
        "micro":    0.02,
        "small":    0.015,
        "medium":   0.01,
        "large":    0.008,
        "flagship": 0.006,
    },
}


def calibrate_mass(
    subsystem: str,
    parametric_mass_kg: float,
    dry_mass_estimate_kg: float,
    spacecraft_class: str,
) -> float:
    """Return the greater of parametric mass and heritage minimum.

    Args:
        subsystem: One of "eps", "ttc", "aocs", "tcs", "structure", "obdh".
        parametric_mass_kg: Mass computed by the subsystem's parametric model.
        dry_mass_estimate_kg: Current estimate of total spacecraft dry mass.
        spacecraft_class: "nano", "micro", "small", "medium", "large", "flagship".

    Returns:
        Calibrated mass (always >= parametric mass, always >= heritage floor).
    """
    fractions = _MIN_MASS_FRACTIONS.get(subsystem, {})
    min_fraction = fractions.get(spacecraft_class, 0.0)
    heritage_floor = min_fraction * dry_mass_estimate_kg
    return max(parametric_mass_kg, heritage_floor)


def get_heritage_fractions(spacecraft_class: str) -> dict[str, float]:
    """Return all subsystem minimum fractions for a spacecraft class."""
    return {
        subsystem: fracs.get(spacecraft_class, 0.0)
        for subsystem, fracs in _MIN_MASS_FRACTIONS.items()
    }
