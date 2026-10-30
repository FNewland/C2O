"""SpaceCDF — Multi-mission payload sizing.

Sizes payloads from mission requirements. Supports:
  - Optical imager: GSD → aperture → mass → power
  - RF communications relay: data rate → antenna gain → mass → power
  - SAR: resolution → antenna area → mass → power
  - AIS/IoT receiver: coverage → antenna → mass → power
  - GNSS-R: reflection → mass → power
  - Radiometer: resolution → antenna → mass → power

References:
  - SMAD4 §9.3 — Payload sizing
  - Wertz, Space Mission Engineering §9.4 — Optical payload design
  - Ball Aerospace heritage data for EO instruments
  - ITU Radio Regulations for RF payloads
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


# ---------------------------------------------------------------------------
# RF Communications Relay payload
# ---------------------------------------------------------------------------

@dataclass
class RfPayloadSizing:
    """Result of RF communications relay payload sizing."""
    data_rate_mbps: float = 0.0
    frequency_ghz: float = 0.0
    antenna_diameter_m: float = 0.0
    antenna_gain_dbi: float = 0.0
    tx_power_w: float = 0.0
    mass_kg: float = 0.0
    power_w: float = 0.0
    eirp_dbw: float = 0.0
    volume_litres: float = 0.0
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def size_rf_relay(
    data_rate_mbps: float = 10.0,
    frequency_ghz: float = 8.0,
    altitude_km: float = 500.0,
    link_margin_db: float = 3.0,
    ground_antenna_m: float = 3.0,
    ground_gt_dbk: float = 20.0,
) -> RfPayloadSizing:
    """Size an RF communications relay payload from data rate and frequency.

    Uses link budget to determine required EIRP, then sizes antenna and
    transmitter from heritage parametric models.
    """
    result = RfPayloadSizing()
    result.data_rate_mbps = data_rate_mbps
    result.frequency_ghz = frequency_ghz

    c = 3e8  # speed of light
    wavelength = c / (frequency_ghz * 1e9)

    # Free-space path loss
    slant_range = altitude_km * 1000 * 1.1  # 10% margin for off-nadir
    fspl_db = 20 * math.log10(4 * math.pi * slant_range / wavelength)

    # Required C/N0 for target data rate (QPSK + FEC assumed)
    eb_n0_db = 4.0  # Typical for LDPC-coded QPSK
    required_cn0 = 10 * math.log10(data_rate_mbps * 1e6) + eb_n0_db

    # Required EIRP = C/N0 + FSPL - G/T(ground) + k(Boltzmann) + margin
    k_dbw = -228.6  # Boltzmann constant in dBW/K/Hz
    required_eirp_dbw = required_cn0 + fspl_db - ground_gt_dbk - k_dbw + link_margin_db

    result.eirp_dbw = required_eirp_dbw

    # Size antenna: start with 0.1m minimum for CubeSat
    # Gain = eta * (pi*D/lambda)^2, eta=0.55
    eta = 0.55
    # Try to minimise antenna size, maximise TX power (within reason)
    # Typical TX power range: 1-30W for CubeSat
    tx_power_w = min(max(data_rate_mbps * 0.5, 2.0), 30.0)
    tx_power_dbw = 10 * math.log10(tx_power_w)
    required_gain_dbi = required_eirp_dbw - tx_power_dbw

    antenna_diameter = wavelength * math.sqrt(10**(required_gain_dbi / 10) / (eta * math.pi**2))
    antenna_diameter = max(antenna_diameter, 0.05)  # 5cm minimum

    result.antenna_diameter_m = antenna_diameter
    result.antenna_gain_dbi = 10 * math.log10(eta * (math.pi * antenna_diameter / wavelength)**2)
    result.tx_power_w = tx_power_w

    # Mass: antenna + transponder + amplifier
    antenna_mass = 0.5 * antenna_diameter**2 + 0.1  # Parabolic or phased array
    transponder_mass = 0.3 + 0.01 * data_rate_mbps  # Scales with data handling
    amplifier_mass = 0.05 * tx_power_w + 0.2  # SSPA scaling
    result.mass_kg = antenna_mass + transponder_mass + amplifier_mass

    # Power: TX + processing
    result.power_w = tx_power_w / 0.3 + 5 + data_rate_mbps * 0.1  # 30% PA efficiency + baseband

    # Volume
    result.volume_litres = math.pi * (antenna_diameter / 2)**2 * 0.1 * 1000  # Flat antenna

    if antenna_diameter > 0.5:
        result.warnings.append(f"Antenna {antenna_diameter*100:.0f} cm — may need deployable")
    if tx_power_w > 20:
        result.warnings.append(f"TX power {tx_power_w:.0f} W — thermal management critical")

    return result


# ---------------------------------------------------------------------------
# SAR (Synthetic Aperture Radar) payload
# ---------------------------------------------------------------------------

@dataclass
class SarPayloadSizing:
    """Result of SAR payload sizing."""
    resolution_m: float = 0.0
    frequency_ghz: float = 0.0
    antenna_length_m: float = 0.0
    antenna_width_m: float = 0.0
    peak_power_w: float = 0.0
    avg_power_w: float = 0.0
    mass_kg: float = 0.0
    power_w: float = 0.0
    data_rate_mbps: float = 0.0
    swath_km: float = 0.0
    volume_litres: float = 0.0
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def size_sar(
    resolution_m: float = 5.0,
    altitude_km: float = 500.0,
    frequency_ghz: float = 9.65,
    incidence_deg: float = 30.0,
    swath_km: float = 20.0,
    duty_cycle: float = 0.15,
) -> SarPayloadSizing:
    """Size a SAR payload from resolution and altitude.

    Uses fundamental SAR sizing equations (antenna length from azimuth
    resolution, minimum antenna area constraint).
    """
    result = SarPayloadSizing()
    result.resolution_m = resolution_m
    result.frequency_ghz = frequency_ghz

    c = 3e8
    wavelength = c / (frequency_ghz * 1e9)
    h = altitude_km * 1000

    # Minimum antenna length for azimuth resolution: L >= 2 * resolution
    antenna_length = max(2 * resolution_m, 1.0)

    # Antenna width from minimum area constraint and swath
    # Minimum area: A_min = 4 * lambda * R * v / c (for range ambiguity)
    v_orbit = math.sqrt(3.986e14 / (6371e3 + h))  # orbital velocity
    slant_range = h / math.cos(math.radians(incidence_deg))
    a_min = 4 * wavelength * slant_range * v_orbit / c
    antenna_width = max(a_min / antenna_length, 0.3)

    result.antenna_length_m = antenna_length
    result.antenna_width_m = antenna_width
    result.swath_km = swath_km

    # Peak power from radar equation (simplified)
    # P_avg = (4*pi)^3 * R^4 * k*T*B*SNR / (G^2 * lambda^2 * sigma)
    # For CubeSat SAR: typically 50-500W peak, 5-50W average
    peak_power = max(50, min(500, 10 * slant_range / 1e6))
    result.peak_power_w = peak_power
    result.avg_power_w = peak_power * duty_cycle

    # Data rate: swath_width * velocity / resolution^2 * bits
    ground_velocity = v_orbit * 6371e3 / (6371e3 + h)
    pixels_per_second = swath_km * 1000 / resolution_m * ground_velocity / resolution_m
    result.data_rate_mbps = pixels_per_second * 16 / 1e6  # 16-bit complex

    # Mass: antenna + electronics + power supply
    antenna_mass = 2.0 * antenna_length * antenna_width + 1.0  # Deployable antenna
    electronics_mass = 3.0 + 0.02 * peak_power  # Digital backend + waveform gen
    result.mass_kg = antenna_mass + electronics_mass

    # Power: average TX + processing
    result.power_w = result.avg_power_w / 0.25 + 10 + result.data_rate_mbps * 0.2

    # Volume
    result.volume_litres = antenna_length * antenna_width * 0.05 * 1000  # Stowed

    if antenna_length > 3:
        result.warnings.append(f"Antenna {antenna_length:.1f}m — requires deployable structure")
    if peak_power > 200:
        result.warnings.append(f"Peak power {peak_power:.0f}W — needs dedicated power bus")

    return result


# ---------------------------------------------------------------------------
# AIS / IoT Receiver payload
# ---------------------------------------------------------------------------

@dataclass
class AisPayloadSizing:
    """Result of AIS/IoT receiver payload sizing."""
    frequency_mhz: float = 0.0
    sensitivity_dbm: float = 0.0
    antenna_length_m: float = 0.0
    mass_kg: float = 0.0
    power_w: float = 0.0
    data_rate_kbps: float = 0.0
    coverage_radius_km: float = 0.0
    volume_litres: float = 0.0
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def size_ais_receiver(
    altitude_km: float = 600.0,
    frequency_mhz: float = 162.0,
    target_detection_rate: float = 0.9,
) -> AisPayloadSizing:
    """Size an AIS/IoT receiver payload.

    AIS operates at 161.975/162.025 MHz. For CubeSat AIS, the main challenge
    is collision rate in high-traffic areas, addressed by antenna gain.
    """
    result = AisPayloadSizing()
    result.frequency_mhz = frequency_mhz

    wavelength = 3e8 / (frequency_mhz * 1e6)

    # VHF antenna for AIS: typically dipole or crossed-dipole
    result.antenna_length_m = wavelength / 2  # Half-wave dipole

    # Coverage radius (horizon-limited)
    h = altitude_km * 1000
    result.coverage_radius_km = math.sqrt(2 * 6371e3 * h + h**2) / 1000

    # Sensitivity
    result.sensitivity_dbm = -120  # Typical AIS receiver

    # Mass: receiver + antenna + processor
    result.mass_kg = 0.5  # Typical CubeSat AIS payload (e.g. exactEarth, Spire)
    result.power_w = 5.0  # Low-power receiver
    result.data_rate_kbps = 10  # AIS message rate
    result.volume_litres = 0.5  # 0.5U

    if altitude_km > 800:
        result.warnings.append("High altitude reduces AIS detection rate due to larger footprint collisions")

    return result


# ---------------------------------------------------------------------------
# Generic payload sizing dispatcher
# ---------------------------------------------------------------------------

def size_payload(
    payload_type: str,
    altitude_km: float = 500.0,
    **kwargs,
) -> dict:
    """Dispatch to the appropriate payload sizer based on type.

    Returns a dict with mass_kg, power_w, data_rate_mbps, and type-specific fields.
    """
    if payload_type in ("optical_imager", "earth_observation"):
        r = size_optical_imager(
            gsd_m=kwargs.get("gsd_m", 10),
            altitude_km=altitude_km,
            wavelength_um=kwargs.get("wavelength_um", 0.55),
            num_bands=kwargs.get("num_bands", 4),
        )
        return {"type": "optical", "mass_kg": r.mass_kg, "power_w": r.power_w,
                "data_rate_mbps": r.data_rate_mbps, "gsd_m": r.gsd_m,
                "aperture_m": r.aperture_m, "swath_km": r.swath_km, "warnings": r.warnings}

    elif payload_type in ("communications", "rf_relay"):
        r = size_rf_relay(
            data_rate_mbps=kwargs.get("data_rate_mbps", 10),
            frequency_ghz=kwargs.get("frequency_ghz", 8.0),
            altitude_km=altitude_km,
        )
        return {"type": "rf_relay", "mass_kg": r.mass_kg, "power_w": r.power_w,
                "data_rate_mbps": r.data_rate_mbps, "antenna_diameter_m": r.antenna_diameter_m,
                "eirp_dbw": r.eirp_dbw, "warnings": r.warnings}

    elif payload_type == "sar":
        r = size_sar(
            resolution_m=kwargs.get("resolution_m", 5),
            altitude_km=altitude_km,
            frequency_ghz=kwargs.get("frequency_ghz", 9.65),
        )
        return {"type": "sar", "mass_kg": r.mass_kg, "power_w": r.power_w,
                "data_rate_mbps": r.data_rate_mbps, "resolution_m": r.resolution_m,
                "antenna_length_m": r.antenna_length_m, "swath_km": r.swath_km, "warnings": r.warnings}

    elif payload_type in ("ais", "iot", "m2m"):
        r = size_ais_receiver(altitude_km=altitude_km)
        return {"type": "ais", "mass_kg": r.mass_kg, "power_w": r.power_w,
                "data_rate_mbps": r.data_rate_kbps / 1000, "coverage_radius_km": r.coverage_radius_km,
                "warnings": r.warnings}

    elif payload_type == "technology_demo":
        # Generic low-resource payload
        mass = kwargs.get("mass_kg", 2.0)
        power = kwargs.get("power_w", 10.0)
        return {"type": "tech_demo", "mass_kg": mass, "power_w": power,
                "data_rate_mbps": 1.0, "warnings": []}

    else:
        # Default: user-specified mass/power
        mass = kwargs.get("mass_kg", 5.0)
        power = kwargs.get("power_w", 20.0)
        return {"type": "generic", "mass_kg": mass, "power_w": power,
                "data_rate_mbps": kwargs.get("data_rate_mbps", 1.0), "warnings": []}
