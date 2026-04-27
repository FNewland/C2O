"""SpaceCDF — Payload-driven optical sizing.

Sizes optical imager payloads from GSD requirements: GSD → aperture → mass → power.
Uses diffraction-limited optics and heritage mass/power CERs.

References:
  - SMAD4 §9.3 — Payload sizing
  - Wertz, Space Mission Engineering §9.4 — Optical payload design
  - Ball Aerospace heritage data for EO instruments
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class OpticalPayloadSizing:
    """Result of optical payload sizing from GSD requirements."""
    gsd_m: float = 0.0
    aperture_m: float = 0.0
    focal_length_m: float = 0.0
    detector_size_mm: float = 0.0
    mass_kg: float = 0.0
    power_w: float = 0.0
    data_rate_mbps: float = 0.0
    volume_litres: float = 0.0
    swath_km: float = 0.0
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def size_optical_imager(
    gsd_m: float,
    altitude_km: float,
    wavelength_um: float = 0.55,
    pixel_size_um: float = 6.5,
    num_bands: int = 4,
    swath_pixels: int = 5000,
    f_number: float = 8.0,
    detector_read_rate_mhz: float = 40.0,
    bits_per_pixel: int = 12,
) -> OpticalPayloadSizing:
    """Size an optical imager from GSD and altitude.

    Computes aperture diameter from diffraction limit and GSD, then
    estimates mass, power, and data rate from heritage parametric models.
    """
    result = OpticalPayloadSizing()
    result.gsd_m = gsd_m

    h = altitude_km * 1000  # metres
    wl = wavelength_um * 1e-6  # metres
    px = pixel_size_um * 1e-6  # metres

    # Aperture from GSD: GSD = pixel_size × altitude / focal_length
    # Focal length = f_number × aperture
    # Also: diffraction limit GSD_diff = 1.22 × λ × altitude / aperture
    # Use the more demanding of the two
    focal_length = px * h / gsd_m
    aperture_from_fl = focal_length / f_number
    aperture_from_diff = 1.22 * wl * h / gsd_m
    aperture = max(aperture_from_fl, aperture_from_diff)

    result.aperture_m = aperture
    result.focal_length_m = focal_length

    # Swath
    swath_angle = swath_pixels * px / focal_length  # radians
    result.swath_km = 2 * h * math.tan(swath_angle / 2) / 1000

    # Detector
    result.detector_size_mm = swath_pixels * pixel_size_um / 1000

    # Data rate
    lines_per_second = detector_read_rate_mhz * 1e6 / swath_pixels
    result.data_rate_mbps = swath_pixels * lines_per_second * bits_per_pixel * num_bands / 1e6

    # Mass from aperture: heritage CER
    # Ball Aerospace fit: mass ≈ 20 × D^1.5 + 2 (kg), for D in metres
    # Includes optics, structure, detector, electronics, baffles
    result.mass_kg = 20 * aperture**1.5 + 2.0
    if num_bands > 4:
        result.mass_kg *= 1.0 + 0.05 * (num_bands - 4)  # Multi-band overhead

    # Power from mass: heritage fit ~3 W/kg for optical instruments
    result.power_w = result.mass_kg * 3.0

    # Volume: cylinder D × 2D (typical telescope package)
    result.volume_litres = math.pi * (aperture / 2)**2 * (aperture * 2) * 1000

    # Warnings
    if aperture > 0.5:
        result.warnings.append(f"Aperture {aperture*100:.0f} cm — requires deployable or off-axis design")
    if gsd_m < 0.5:
        result.warnings.append(f"Sub-metre GSD ({gsd_m}m) — challenging for small satellites")

    return result
