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

    # Structure fraction by class
    fractions = {
        "nano": (0.25, 0.30),     # CubeSat/nanosat
        "micro": (0.20, 0.28),    # 10-100 kg
        "small": (0.18, 0.25),    # 100-500 kg
        "medium": (0.14, 0.20),   # 500-2000 kg
        "large": (0.12, 0.18),    # 2000-5000 kg
        "flagship": (0.10, 0.15), # 5000+ kg
    }

    low, high = fractions.get(spacecraft_class, (0.18, 0.25))
    base_fraction = (low + high) / 2

    # Adjust for deployables
    if has_deployables:
        base_fraction += 0.02

    # Adjust for propulsion (tank support structure)
    if has_propulsion:
        base_fraction += 0.03

    result.structure_fraction = base_fraction
    total_structure = spacecraft_dry_mass_kg * base_fraction

    # Breakdown
    result.primary_structure_mass_kg = total_structure * 0.60  # Bus, panels
    result.secondary_structure_mass_kg = total_structure * 0.25  # Brackets, inserts
    result.mechanisms_mass_kg = total_structure * 0.15 + num_deployable_panels * 0.3  # HRMs, hinges

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
