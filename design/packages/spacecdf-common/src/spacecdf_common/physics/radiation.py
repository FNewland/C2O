"""SpaceCDF — Radiation environment and shielding model.

Simplified trapped particle dose and GCR/SPE estimates for mission planning.
Not a replacement for SPENVIS/OMERE — provides design-point TID estimates
for electronics selection and shielding mass budgeting.

References:
  - AP-8/AE-8 trapped particle models (simplified fits)
  - ECSS-E-ST-10-04C Rev.1 — Space environment
  - ECSS-E-ST-10-12C — Methods for the calculation of radiation received
  - Wertz, SMAD4 §8.1 — Space radiation environment
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class RadiationResult:
    """Radiation environment assessment."""
    tid_krad_per_year: float = 0.0      # Total ionising dose behind shielding
    tid_mission_krad: float = 0.0       # Total mission dose
    shielding_mm_al: float = 0.0        # Required Al equivalent shielding
    shielding_mass_kg: float = 0.0      # Shielding mass estimate
    see_rate_per_day: float = 0.0       # Single-event effect rate (relative)
    environment: str = ""               # "LEO_low" / "LEO_high" / "MEO" / "lunar" / etc.
    electronics_class: str = ""         # "commercial" / "rad_tolerant" / "rad_hard"
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def estimate_radiation(
    altitude_km: float,
    inclination_deg: float,
    mission_duration_years: float = 3.0,
    shielding_mm_al: float = 1.0,
    body: str = "earth",
    dry_mass_kg: float = 100.0,
) -> RadiationResult:
    """Estimate radiation environment and shielding requirements.

    Args:
        altitude_km: Orbital altitude.
        inclination_deg: Orbital inclination.
        mission_duration_years: Mission duration.
        shielding_mm_al: Existing aluminium shielding thickness (mm).
        body: Central body ("earth", "moon", "mars").
        dry_mass_kg: Spacecraft dry mass (for shielding mass estimate).
    """
    result = RadiationResult()
    result.shielding_mm_al = shielding_mm_al

    if body in ("moon", "mars"):
        # Deep-space: dominated by GCR and SPE
        # GCR: ~10-20 krad/yr behind 1mm Al (solar min), ~5-10 (solar max)
        # SPE: stochastic, ~10-50 krad per major event
        gcr_dose = 15.0 / max(shielding_mm_al, 0.5)  # krad/yr, drops with shielding
        spe_dose = 20.0 / max(shielding_mm_al, 0.5)   # krad per major event, ~1/yr avg
        result.tid_krad_per_year = gcr_dose + spe_dose
        result.environment = "deep_space"
        result.see_rate_per_day = 0.5  # Higher SEE rate outside magnetosphere
    else:
        # Earth orbit: trapped protons + electrons + GCR
        # Simplified dose model from AP-8/AE-8 fits
        h = altitude_km

        # South Atlantic Anomaly dominates for LEO
        if h < 600:
            # Low LEO: moderate trapped protons
            base_dose = 0.5 + 0.005 * h  # krad/yr behind 1mm Al
            result.environment = "LEO_low"
        elif h < 1000:
            # High LEO: increasing trapped particles
            base_dose = 3.0 + 0.02 * (h - 600)
            result.environment = "LEO_high"
        elif h < 2000:
            # Inner proton belt edge
            base_dose = 20.0 + 0.1 * (h - 1000)
            result.environment = "proton_belt"
        elif h < 15000:
            # Heart of proton belt (MEO)
            base_dose = 100.0
            result.environment = "MEO_proton_belt"
        elif h < 25000:
            # Electron belt
            base_dose = 50.0
            result.environment = "electron_belt"
        else:
            # Above belts (GEO region)
            base_dose = 10.0
            result.environment = "GEO"

        # Inclination effect: higher inclination → more SAA exposure (for LEO)
        if h < 1000 and inclination_deg > 50:
            inclination_factor = 1.0 + 0.5 * (inclination_deg - 50) / 50
        else:
            inclination_factor = 1.0

        # Shielding attenuation: dose drops roughly as 1/thickness for protons
        shielding_factor = 1.0 / max(shielding_mm_al, 0.5)

        result.tid_krad_per_year = base_dose * inclination_factor * shielding_factor
        result.see_rate_per_day = 0.1 * inclination_factor  # Relative rate

    result.tid_mission_krad = result.tid_krad_per_year * mission_duration_years

    # Electronics class recommendation
    if result.tid_mission_krad < 5:
        result.electronics_class = "commercial"
    elif result.tid_mission_krad < 30:
        result.electronics_class = "rad_tolerant"
    elif result.tid_mission_krad < 100:
        result.electronics_class = "rad_hard"
    else:
        result.electronics_class = "rad_hard_plus"
        result.warnings.append(f"TID {result.tid_mission_krad:.0f} krad — requires rad-hard electronics and/or additional shielding")

    # Shielding mass estimate: if current dose exceeds 20 krad, add shielding
    if result.tid_mission_krad > 20:
        # Target: bring dose below 20 krad
        required_thickness = shielding_mm_al * (result.tid_mission_krad / 20.0)
        additional_mm = max(0, required_thickness - shielding_mm_al)
        # Al shielding mass: density 2700 kg/m³, applied as spot shielding
        # on ~10% of surface area (electronics boxes)
        surface_area_m2 = 0.01 * dry_mass_kg ** (2.0 / 3.0)
        shielded_area = surface_area_m2 * 0.10  # 10% of surface
        result.shielding_mass_kg = shielded_area * (additional_mm / 1000) * 2700
    else:
        result.shielding_mass_kg = 0.0

    return result
