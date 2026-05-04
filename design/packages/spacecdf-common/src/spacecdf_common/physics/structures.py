"""SpaceCDF — Structural design equations.

Parametric mass estimation for spacecraft structures, launch load analysis,
and structural sizing. Uses heritage-data correlations.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class StructureDesignResult:
    """Result of structural design analysis."""

    structure_mass_kg: float = 0.0
    structure_fraction: float = 0.0
    primary_structure_mass_kg: float = 0.0
    secondary_structure_mass_kg: float = 0.0
    mechanisms_mass_kg: float = 0.0
    first_natural_freq_hz: float = 0.0
    axial_load_g: float = 0.0
    lateral_load_g: float = 0.0
    structure_cost_keur: float = 0.0
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def estimate_structure_mass(
    spacecraft_dry_mass_kg: float,
    spacecraft_class: str = "small",
    has_deployables: bool = True,
    has_propulsion: bool = False,
    num_deployable_panels: int = 2,
) -> StructureDesignResult:
    """Estimate structural mass using parametric heritage correlations.

    Structure fraction varies by spacecraft class:
    - CubeSat: 20-30% (standardised structure dominates)
    - Small (50-500kg): 15-25%
    - Medium (500-2000kg): 12-20%
    - Large (2000kg+): 10-18%
    """
    result = StructureDesignResult()

    # For CubeSats: use COTS frame mass lookup (not parametric fraction)
    # Real CubeSat frames: ISIS 3U = 0.35 kg, Pumpkin 6U = 0.9 kg
    CUBESAT_FRAME_MASS = {
        "1U": 0.20, "2U": 0.28, "3U": 0.35, "6U": 0.70,
        "12U": 1.20, "16U": 1.60, "27U": 2.50,
    }

    if spacecraft_class in ("nano", "micro") and spacecraft_dry_mass_kg < 30:
        # CubeSat: use COTS frame + fasteners + brackets
        if spacecraft_dry_mass_kg <= 2:
            form = "1U"
        elif spacecraft_dry_mass_kg <= 4:
            form = "2U"
        elif spacecraft_dry_mass_kg <= 6:
            form = "3U"
        elif spacecraft_dry_mass_kg <= 14:
            form = "6U"
        elif spacecraft_dry_mass_kg <= 24:
            form = "12U"
        else:
            form = "16U"

        frame_mass = CUBESAT_FRAME_MASS.get(form, 0.35)
        fasteners_mass = 0.03 * spacecraft_dry_mass_kg  # ~3% for fasteners, standoffs
        mechanisms_mass = num_deployable_panels * 0.03 + (0.02 if has_deployables else 0)
        total_structure = frame_mass + fasteners_mass + mechanisms_mass

        result.structure_fraction = total_structure / max(spacecraft_dry_mass_kg, 0.1)
        result.primary_structure_mass_kg = frame_mass
        result.secondary_structure_mass_kg = fasteners_mass
        result.mechanisms_mass_kg = mechanisms_mass
    else:
        # Larger spacecraft: use parametric fraction
        fractions = {
            "small": (0.14, 0.18),    # 100-500 kg
            "medium": (0.12, 0.16),   # 500-2000 kg
            "large": (0.10, 0.14),    # 2000-5000 kg
            "flagship": (0.08, 0.12), # 5000+ kg
        }

        low, high = fractions.get(spacecraft_class, (0.14, 0.18))
        base_fraction = (low + high) / 2
        if has_deployables:
            base_fraction += 0.02
        if has_propulsion:
            base_fraction += 0.03

        result.structure_fraction = base_fraction
        capped_fraction = min(base_fraction, 0.25)
        total_structure = spacecraft_dry_mass_kg * capped_fraction / (1.0 + capped_fraction)

        result.primary_structure_mass_kg = total_structure * 0.60
        result.secondary_structure_mass_kg = total_structure * 0.25
        result.mechanisms_mass_kg = total_structure * 0.15 + num_deployable_panels * 0.3

    result.structure_mass_kg = (
        result.primary_structure_mass_kg
        + result.secondary_structure_mass_kg
        + result.mechanisms_mass_kg
    )

    # Natural frequency estimation (empirical)
    # First lateral mode typically 15-45 Hz depending on mass and size
    if spacecraft_dry_mass_kg < 20:
        result.first_natural_freq_hz = 90.0  # CubeSat
    elif spacecraft_dry_mass_kg < 200:
        result.first_natural_freq_hz = 45.0
    elif spacecraft_dry_mass_kg < 1000:
        result.first_natural_freq_hz = 25.0
    else:
        result.first_natural_freq_hz = 15.0

    # Cost (structure is relatively cheap per kg)
    result.structure_cost_keur = result.structure_mass_kg * 8  # ~8 kEUR/kg

    return result


def launch_loads(
    launch_vehicle: str = "falcon_9",
) -> tuple[float, float]:
    """Return (axial_g, lateral_g) quasi-static launch loads.

    These are envelope values including safety factor.
    """
    loads = {
        "falcon_9": (6.0, 2.0),
        "falcon_heavy": (6.0, 2.0),
        "vega_c": (6.5, 1.5),
        "ariane_6": (5.5, 2.0),
        "soyuz": (4.5, 1.5),
        "electron": (7.5, 2.0),
        "pslv": (6.5, 2.0),
        "h3": (5.0, 2.0),
        "sls": (4.0, 2.0),
        "starship": (4.0, 1.5),
        "new_glenn": (5.5, 2.0),
        "long_march_5": (5.5, 2.5),
    }
    return loads.get(launch_vehicle, (6.0, 2.0))
