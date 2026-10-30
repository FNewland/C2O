"""SpaceCDF — Constellation Design & Coverage Analysis.

Supports Walker delta/star constellations, coverage computation,
and constellation-level budgets (total mass, cost, launch planning).

References:
  - Walker, J.G. (1984) "Satellite Constellations"
  - Wertz, Space Mission Engineering Ch. 7 — Coverage
  - SMAD4 §7.6 — Constellation Design
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

MU_EARTH = 3.986004418e14
R_EARTH_KM = 6371.0


@dataclass
class ConstellationDesign:
    """A Walker delta constellation configuration."""
    total_satellites: int  # T
    num_planes: int  # P
    phasing_parameter: int  # F (0 to P-1)
    altitude_km: float
    inclination_deg: float
    sats_per_plane: int = 0  # T/P

    def __post_init__(self):
        self.sats_per_plane = self.total_satellites // max(self.num_planes, 1)


@dataclass
class CoverageResult:
    """Coverage analysis result for a constellation."""
    design: ConstellationDesign
    coverage_percent: float = 0.0  # Global surface covered
    max_revisit_hours: float = 0.0  # Worst-case gap
    mean_revisit_hours: float = 0.0
    min_elevation_deg: float = 10.0
    ground_track_repeat_days: float = 0.0
    coverage_latitude_band: tuple[float, float] = (-90.0, 90.0)


@dataclass
class ConstellationBudget:
    """Constellation-level budget roll-up."""
    num_satellites: int
    per_satellite_mass_kg: float
    per_satellite_cost_meur: float
    total_mass_kg: float = 0.0
    total_cost_meur: float = 0.0
    launch_cost_meur: float = 0.0
    spare_satellites: int = 0
    learning_curve_factor: float = 0.95  # 95% for <5 units
    operations_cost_meur_per_year: float = 0.0


def design_walker_constellation(
    coverage_target_percent: float = 95.0,
    max_revisit_hours: float = 6.0,
    altitude_km: float = 500.0,
    inclination_deg: float = 97.4,
    min_elevation_deg: float = 10.0,
    latitude_band: tuple[float, float] = (-60.0, 60.0),
) -> list[ConstellationDesign]:
    """Generate candidate Walker delta constellations for given coverage targets.

    Returns multiple options ranked by satellite count (fewer is better).
    """
    candidates: list[ConstellationDesign] = []

    # Compute single-satellite ground swath
    a_m = (R_EARTH_KM + altitude_km) * 1000
    orbital_period_s = 2 * math.pi * math.sqrt(a_m**3 / MU_EARTH)
    orbital_period_h = orbital_period_s / 3600

    # Earth angular radius as seen from satellite
    rho = math.asin(R_EARTH_KM / (R_EARTH_KM + altitude_km))
    # Half-angle of coverage cone at min elevation
    eta = math.asin(math.cos(math.radians(min_elevation_deg)) * math.sin(rho))
    lambda_0 = math.pi / 2 - math.radians(min_elevation_deg) - eta  # Half-angle Earth-centric
    swath_radius_km = R_EARTH_KM * lambda_0

    # Estimate number of satellites needed
    # Simplified: coverage = N × swath_area / total_area_in_band
    lat_lo, lat_hi = latitude_band
    band_area_km2 = 2 * math.pi * R_EARTH_KM**2 * abs(
        math.sin(math.radians(lat_hi)) - math.sin(math.radians(lat_lo))
    )
    single_swath_area = math.pi * swath_radius_km**2

    # Try various configurations
    for num_planes in [2, 3, 4, 6, 8, 12]:
        for sats_per_plane in range(2, 20):
            total = num_planes * sats_per_plane
            if total > 100:
                continue

            # Approximate overlap factor (Walker delta provides good uniformity)
            overlap_factor = 0.6 + 0.1 * (num_planes / total)  # Less overlap with more planes
            effective_coverage = min(100, (total * single_swath_area * overlap_factor / band_area_km2) * 100)

            # Revisit estimate: orbital period / (sats in adjacent planes visible)
            revisit = orbital_period_h / max(sats_per_plane * min(num_planes, 3) * 0.3, 1)

            if effective_coverage >= coverage_target_percent and revisit <= max_revisit_hours:
                candidates.append(ConstellationDesign(
                    total_satellites=total,
                    num_planes=num_planes,
                    phasing_parameter=1,  # F=1 is typical for Walker delta
                    altitude_km=altitude_km,
                    inclination_deg=inclination_deg,
                ))

    # Sort by total satellite count (fewer is more cost-effective)
    candidates.sort(key=lambda c: c.total_satellites)

    # Return top 5 options
    return candidates[:5]


def compute_coverage(design: ConstellationDesign, min_elevation_deg: float = 10.0) -> CoverageResult:
    """Compute coverage metrics for a constellation design."""
    a_m = (R_EARTH_KM + design.altitude_km) * 1000
    orbital_period_s = 2 * math.pi * math.sqrt(a_m**3 / MU_EARTH)
    orbital_period_h = orbital_period_s / 3600

    rho = math.asin(R_EARTH_KM / (R_EARTH_KM + design.altitude_km))
    eta = math.asin(math.cos(math.radians(min_elevation_deg)) * math.sin(rho))
    lambda_0 = math.pi / 2 - math.radians(min_elevation_deg) - eta
    swath_radius_km = R_EARTH_KM * lambda_0

    # Coverage estimate
    total_area = 4 * math.pi * R_EARTH_KM**2
    single_swath = math.pi * swath_radius_km**2
    overlap = 0.6 + 0.1 * (design.num_planes / max(design.total_satellites, 1))
    coverage_pct = min(100, (design.total_satellites * single_swath * overlap / total_area) * 100)

    # Revisit
    mean_revisit = orbital_period_h / max(design.sats_per_plane * 0.5, 1)
    max_revisit = mean_revisit * 2.5  # Worst case ~2.5× mean for Walker delta

    # Ground track repeat (approximate for SSO)
    earth_rotation_deg_per_orbit = 360 * orbital_period_s / 86400
    node_spacing_deg = 360 / max(design.num_planes, 1)
    repeat_orbits = round(node_spacing_deg / earth_rotation_deg_per_orbit) if earth_rotation_deg_per_orbit > 0 else 1
    repeat_days = repeat_orbits * orbital_period_h / 24

    return CoverageResult(
        design=design,
        coverage_percent=round(coverage_pct, 1),
        max_revisit_hours=round(max_revisit, 1),
        mean_revisit_hours=round(mean_revisit, 1),
        min_elevation_deg=min_elevation_deg,
        ground_track_repeat_days=round(repeat_days, 1),
        coverage_latitude_band=(-design.inclination_deg, design.inclination_deg),
    )


def compute_constellation_budget(
    num_satellites: int,
    per_satellite_mass_kg: float,
    per_satellite_cost_meur: float,
    spare_fraction: float = 0.15,
    launch_cost_per_kg_usd: float = 7000,
    ops_cost_meur_per_year: float = 0.5,
) -> ConstellationBudget:
    """Compute constellation-level budgets including spares and learning curve."""
    spares = max(1, round(num_satellites * spare_fraction))
    total_sats = num_satellites + spares

    # Learning curve: unit cost decreases with quantity
    # T1 × N^(ln(learning_rate)/ln(2))
    if total_sats <= 5:
        learning = 0.95
    elif total_sats <= 50:
        learning = 0.90
    else:
        learning = 0.85

    b = math.log(learning) / math.log(2)
    # Average unit cost = T1 × N^b (cumulative average)
    avg_cost = per_satellite_cost_meur * (total_sats ** b)
    total_hw_cost = avg_cost * total_sats

    # Launch cost
    total_mass = total_sats * per_satellite_mass_kg
    launch_cost = total_mass * launch_cost_per_kg_usd / 1e6  # MEUR

    return ConstellationBudget(
        num_satellites=num_satellites,
        per_satellite_mass_kg=per_satellite_mass_kg,
        per_satellite_cost_meur=per_satellite_cost_meur,
        total_mass_kg=total_mass,
        total_cost_meur=round(total_hw_cost + launch_cost + ops_cost_meur_per_year * 3, 2),
        launch_cost_meur=round(launch_cost, 2),
        spare_satellites=spares,
        learning_curve_factor=learning,
        operations_cost_meur_per_year=ops_cost_meur_per_year,
    )
