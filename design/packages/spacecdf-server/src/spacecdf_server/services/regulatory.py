"""SpaceCDF — Regulatory Paperwork Generator.

Generates deeply auto-populated filing templates for:
  - Canadian RSSSA (Remote Sensing Space Systems Act) licence application
  - ITU API Filing (Appendix 4) — frequency assignment notices
  - COPUOS/UN Registration Convention (Article IV)
  - End-of-life / debris compliance report
  - Export control assessment (ITAR/EAR/CGP classification)

All generators accept design parameters and compute as many fields as
possible, marking each field with ``auto_populated: True/False`` so the
UI can highlight which items still need human review.

References:
  - RSSSA (S.C. 2005, c. 45) and Regulations (SOR-2007-66)
  - ITU Radio Regulations, Appendix 4
  - UN Registration Convention (1975), Article IV
  - IADC Space Debris Mitigation Guidelines (2020 rev.)
  - ECSS-U-AS-10C Rev.2 (debris mitigation)
  - NASA-STD-8719.14 Rev B
  - FCC 47 CFR 25.114 (5-year rule, Sept 2024)
  - ITAR 22 CFR 120-130, USML Category XV
  - EAR 15 CFR 730-774, ECCN 9A515
  - Canadian Controlled Goods List, Item 5504
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

R_EARTH_KM = 6371.0
MU_EARTH_KM3S2 = 3.986004418e5  # km^3/s^2
MU_EARTH_M3S2 = 3.986004418e14  # m^3/s^2
C_LIGHT_MS = 299_792_458.0

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _field(value: Any, auto: bool = True) -> dict[str, Any]:
    """Wrap a value with its auto-populated flag."""
    return {"value": value, "auto_populated": auto}


def _manual(label: str = "[APPLICANT INPUT REQUIRED]") -> dict[str, Any]:
    """Return a placeholder that requires human input."""
    return {"value": label, "auto_populated": False}


def _compute_period_min(altitude_km: float) -> float:
    """Compute Keplerian orbital period in minutes from circular altitude."""
    a_m = (R_EARTH_KM + altitude_km) * 1000.0
    return 2.0 * math.pi * math.sqrt(a_m**3 / MU_EARTH_M3S2) / 60.0


def _compute_gsd_m(
    altitude_km: float,
    focal_length_mm: float | None = None,
    pixel_pitch_um: float | None = None,
    pointing_accuracy_deg: float | None = None,
) -> float | None:
    """Estimate ground sample distance from altitude and optics.

    If optics params are unavailable, use a rough diffraction-limited
    estimate for a 50 mm aperture at 550 nm.
    """
    alt_m = altitude_km * 1000.0
    if focal_length_mm and pixel_pitch_um:
        gsd = alt_m * (pixel_pitch_um * 1e-6) / (focal_length_mm * 1e-3)
        return round(gsd, 2)
    # Fallback: diffraction limit for small-sat optics
    # theta ~ 1.22 * lambda / D  (D=50mm, lambda=550nm)
    theta_rad = 1.22 * 550e-9 / 0.050
    gsd = alt_m * theta_rad
    return round(gsd, 2)


def _estimate_swath_width_km(
    altitude_km: float, fov_deg: float | None = None
) -> float:
    """Estimate swath width from altitude and field of view."""
    fov = fov_deg or 2.5  # typical small-sat imager
    return round(2.0 * altitude_km * math.tan(math.radians(fov / 2.0)), 1)


def _compute_repeat_cycle_days(
    altitude_km: float, inclination_deg: float
) -> float | None:
    """Rough repeat-cycle estimate for near-circular SSO.

    Uses integer-rev resonance: repeat when rev/day divides evenly.
    This is a simplified approximation.
    """
    period_min = _compute_period_min(altitude_km)
    revs_per_day = 1440.0 / period_min
    # For SSO the ground track repeat requires integer revs
    nearest_int = round(revs_per_day)
    if nearest_int == 0:
        return None
    # Approximate repeat cycle
    frac = abs(revs_per_day - nearest_int)
    if frac < 0.001:
        return 1.0
    return round(1.0 / frac, 0)


def _estimate_revisit_days(
    altitude_km: float,
    inclination_deg: float,
    swath_width_km: float | None = None,
) -> float:
    """Rough single-sat revisit time estimate."""
    sw = swath_width_km or _estimate_swath_width_km(altitude_km)
    earth_circumference = 2.0 * math.pi * R_EARTH_KM
    # At equator, ground tracks spaced by ~earth_circ / revs_per_day
    period_min = _compute_period_min(altitude_km)
    revs = 1440.0 / period_min
    track_spacing_km = earth_circumference / revs
    if sw <= 0:
        return 99.0
    return round(track_spacing_km / sw, 1)


def _estimate_orbital_lifetime_years(altitude_km: float) -> float:
    """Simplified orbital lifetime estimate for LEO circular orbits.

    Based on empirical curve for Cd=2.2, A/m ~0.01 m^2/kg CubeSat,
    moderate solar activity.
    """
    if altitude_km <= 250:
        return 0.02  # days
    if altitude_km <= 300:
        return 0.1
    if altitude_km <= 350:
        return 0.5
    if altitude_km <= 400:
        return 1.0
    if altitude_km <= 450:
        return 3.0
    if altitude_km <= 500:
        return 7.0
    if altitude_km <= 550:
        return 15.0
    if altitude_km <= 600:
        return 25.0
    if altitude_km <= 700:
        return 50.0
    if altitude_km <= 800:
        return 100.0
    return 200.0  # essentially permanent without propulsion


# ---------------------------------------------------------------------------
# Emission designator computation  (ITU RR Appendix 1)
# ---------------------------------------------------------------------------

def compute_emission_designator(
    bandwidth_hz: float,
    modulation: str = "QPSK",
    data_rate_bps: float | None = None,
) -> str:
    """Compute ITU-format emission designator string.

    Format:  [bandwidth][modulation_code][signal_type]

    Bandwidth encoding (ITU RR Appendix 1):
      - Value expressed as 4 characters: 3 digits + unit letter
      - H = Hz, K = kHz, M = MHz, G = GHz
      - The unit letter replaces the decimal point.
      Examples: 200 Hz → "200H", 2.5 kHz → "2K50", 200 kHz → "200K",
                1.5 MHz → "1M50", 36 MHz → "36M0"

    Modulation codes (first letter after bandwidth):
      F = frequency modulation, G = phase modulation,
      D = combined AM+FM/PM, W = combined (complex)

    Signal type:  1 = single channel digital, 7 = multiple channel,
                  D = data, E = telephony, W = combo

    Returns e.g. "200KF1D", "1M50G1D", "36M0D7W".
    """
    # --- Encode bandwidth ---
    bw = abs(bandwidth_hz)
    if bw < 1000:
        # Hz range
        val = bw
        if val == int(val):
            bw_str = f"{int(val):d}H"
        else:
            integer = int(val)
            frac = int(round((val - integer) * 10))
            bw_str = f"{integer}H{frac}"
    elif bw < 1_000_000:
        val = bw / 1000.0
        if val == int(val):
            bw_str = f"{int(val):d}K"
        else:
            integer = int(val)
            frac = int(round((val - integer) * 100))
            if frac % 10 == 0:
                bw_str = f"{integer}K{frac // 10}"
            else:
                bw_str = f"{integer}K{frac}"
    elif bw < 1_000_000_000:
        val = bw / 1_000_000.0
        if val == int(val):
            bw_str = f"{int(val):d}M0"
        else:
            integer = int(val)
            frac = int(round((val - integer) * 100))
            if frac % 10 == 0:
                bw_str = f"{integer}M{frac // 10}"
            else:
                bw_str = f"{integer}M{frac}"
    else:
        val = bw / 1_000_000_000.0
        integer = int(val)
        frac = int(round((val - integer) * 100))
        bw_str = f"{integer}G{frac}" if frac else f"{integer}G0"

    # Pad/truncate to 4 chars (ITU format)
    bw_str = bw_str[:4].ljust(4, "0")

    # --- Modulation code ---
    mod_upper = modulation.upper()
    mod_map = {
        "FM": "F",
        "GFSK": "F",
        "FSK": "F",
        "GMSK": "G",
        "BPSK": "G",
        "QPSK": "G",
        "8PSK": "G",
        "OQPSK": "G",
        "PM": "G",
        "AM": "A",
        "OOK": "A",
        "QAM": "D",
        "16QAM": "D",
        "64QAM": "D",
        "OFDM": "W",
        "DSSS": "G",
        "FHSS": "G",
    }
    mod_code = mod_map.get(mod_upper, "G")

    # --- Signal type ---
    # 1 = single channel, 7 = multi-channel
    # D = data, E = telephony, W = combination
    signal_type = "1D"

    return f"{bw_str}{mod_code}{signal_type}"


# ---------------------------------------------------------------------------
# PFD computation
# ---------------------------------------------------------------------------

def compute_pfd_dbw_m2(
    eirp_dbw: float,
    altitude_km: float,
    elevation_deg: float = 5.0,
) -> float:
    """Compute power flux density at Earth's surface (dBW/m^2).

    PFD = EIRP - 10*log10(4*pi*R^2)

    where R is the slant range from satellite to ground point at
    the given elevation angle.

    For elevation_deg = 90, R = altitude.
    For low elevations, R increases due to geometry.
    """
    # Slant range via law of cosines on the Earth-centre triangle
    el_rad = math.radians(elevation_deg)
    r_e = R_EARTH_KM * 1000.0  # metres
    r_sat = (R_EARTH_KM + altitude_km) * 1000.0  # metres from Earth centre

    # Slant range R
    # Using: R = -R_e*sin(el) + sqrt((R_e*sin(el))^2 + r_sat^2 - R_e^2)
    sin_el = math.sin(el_rad)
    R_slant = -r_e * sin_el + math.sqrt(
        (r_e * sin_el) ** 2 + r_sat**2 - r_e**2
    )

    # Spreading loss
    spreading = 10.0 * math.log10(4.0 * math.pi * R_slant**2)

    pfd = eirp_dbw - spreading
    return round(pfd, 2)


# ---------------------------------------------------------------------------
# Priority 1 — RSSSA (Remote Sensing Space Systems Act — Canada)
# ---------------------------------------------------------------------------

def generate_rsssa_template(
    *,
    study_name: str = "",
    operator_name: str = "",
    satellite_description: str = "",
    # Orbit
    orbit_altitude_km: float = 500.0,
    orbit_inclination_deg: float = 97.4,
    orbit_type: str = "",
    orbit_eccentricity: float = 0.0,
    # Imaging / payload
    has_imaging: bool = True,
    gsd_m: float | None = None,
    focal_length_mm: float | None = None,
    pixel_pitch_um: float | None = None,
    pointing_accuracy_deg: float | None = None,
    fov_deg: float | None = None,
    spectral_bands: list[str] | None = None,
    # Spacecraft
    mass_kg: float | None = None,
    dimensions: str = "",
    design_lifetime_years: float = 3.0,
    # Communications
    downlink_freq_mhz: float | None = None,
    downlink_bandwidth_mhz: float | None = None,
    data_rate_mbps: float | None = None,
    encryption_method: str = "",
    # Ground stations
    ground_stations: list[dict[str, Any]] | None = None,
    # Launch
    launch_date: str = "",
    launch_provider: str = "",
    # Design params passthrough — allows bulk auto-populate
    design_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate Canadian RSSSA licence application template.

    Required for any Canadian-operated remote sensing satellite.
    Administered by Global Affairs Canada.
    Auto-populates all computable fields from design parameters.
    """
    dp = design_params or {}

    # --- Resolve parameters from design_params fallback ---
    alt = orbit_altitude_km or dp.get("orbit_altitude_km", 500.0)
    inc = orbit_inclination_deg or dp.get("orbit_inclination_deg", 97.4)
    ecc = orbit_eccentricity or dp.get("orbit_eccentricity", 0.0)
    o_type = orbit_type or dp.get("orbit_type", "")
    if not o_type:
        if 96.0 <= inc <= 99.0:
            o_type = "Sun-Synchronous (SSO)"
        elif inc < 10:
            o_type = "Near-Equatorial"
        elif 80 <= inc <= 100:
            o_type = "Near-Polar"
        else:
            o_type = "Inclined LEO"

    period_min = round(_compute_period_min(alt), 2)
    repeat_cycle = _compute_repeat_cycle_days(alt, inc)

    # GSD
    _gsd = gsd_m
    gsd_auto = False
    if _gsd is None:
        _gsd = _compute_gsd_m(
            alt,
            focal_length_mm=focal_length_mm or dp.get("focal_length_mm"),
            pixel_pitch_um=pixel_pitch_um or dp.get("pixel_pitch_um"),
            pointing_accuracy_deg=pointing_accuracy_deg or dp.get("pointing_accuracy_deg"),
        )
        gsd_auto = True

    swath = _estimate_swath_width_km(alt, fov_deg=fov_deg or dp.get("fov_deg"))
    revisit = _estimate_revisit_days(alt, inc, swath)

    _mass = mass_kg or dp.get("mass_kg") or dp.get("total_mass_kg")
    _dims = dimensions or dp.get("dimensions", "")
    _dl_freq = downlink_freq_mhz or dp.get("downlink_freq_mhz")
    _dl_bw = downlink_bandwidth_mhz or dp.get("downlink_bandwidth_mhz")
    _dl_rate = data_rate_mbps or dp.get("data_rate_mbps")
    _enc = encryption_method or dp.get("encryption_method", "")
    _bands = spectral_bands or dp.get("spectral_bands")
    _gs = ground_stations or dp.get("ground_stations")

    return {
        "document": "RSSSA Operating Licence Application",
        "standard": "Remote Sensing Space Systems Act (S.C. 2005, c. 45)",
        "administering_body": "Global Affairs Canada",
        "contact": "RSSSA-LSTS@international.gc.ca",
        "generated": datetime.now(timezone.utc).isoformat(),
        "applicability": (
            "Required" if has_imaging
            else "Likely not required (no remote sensing payload)"
        ),
        "sections": {
            "applicant_information": {
                "legal_name": _field(operator_name, auto=bool(operator_name)) if operator_name else _manual(),
                "address": _manual(),
                "contact_person": _manual(),
                "canadian_entity": _manual("Yes / No — must be Canadian or operating in Canada"),
                "phone": _manual(),
                "email": _manual(),
            },
            "system_description": {
                "satellite_name": _field(study_name, auto=bool(study_name)),
                "description": _field(
                    satellite_description
                    or f"Remote sensing mission at {alt} km {inc:.1f}° {o_type}",
                    auto=bool(satellite_description),
                ),
                "number_of_satellites": _field(1),
                "design_lifetime_years": _field(design_lifetime_years),
                "launch_date": _field(launch_date, auto=bool(launch_date)) if launch_date else _manual("[TBD — planned launch date]"),
                "launch_provider": _field(launch_provider, auto=bool(launch_provider)) if launch_provider else _manual("[TBD — launch provider]"),
            },
            "orbit": {
                "altitude_km": _field(alt),
                "inclination_deg": _field(inc),
                "orbit_type": _field(o_type),
                "period_min": _field(period_min),
                "eccentricity": _field(ecc),
                "apogee_km": _field(round(alt * (1 + ecc), 1)),
                "perigee_km": _field(round(alt * (1 - ecc), 1)),
                "repeat_cycle_days": _field(repeat_cycle) if repeat_cycle else _manual("[Compute from detailed orbit analysis]"),
            },
            "imaging_capability": {
                "sensor_type": _field("Optical imager") if has_imaging else _field("N/A"),
                "ground_sample_distance_m": _field(_gsd, auto=gsd_auto) if _gsd else _manual(),
                "swath_width_km": _field(swath),
                "spectral_bands": _field(_bands) if _bands else _manual("[List spectral bands: e.g. RGB, NIR, SWIR]"),
                "revisit_time_days": _field(revisit),
                "imaging_modes": _manual("[e.g. pushbroom, staring, video]"),
                "pointing_accuracy_deg": _field(
                    pointing_accuracy_deg or dp.get("pointing_accuracy_deg"),
                    auto=True,
                ) if (pointing_accuracy_deg or dp.get("pointing_accuracy_deg")) else _manual(),
            },
            "spacecraft": {
                "mass_kg": _field(_mass) if _mass else _manual("[Total wet mass in kg]"),
                "dimensions": _field(_dims) if _dims else _manual("[e.g. 10x10x34 cm (3U CubeSat)]"),
                "design_lifetime_years": _field(design_lifetime_years),
            },
            "communications": {
                "downlink_freq_mhz": _field(_dl_freq) if _dl_freq else _manual("[Primary downlink centre frequency MHz]"),
                "downlink_bandwidth_mhz": _field(_dl_bw) if _dl_bw else _manual(),
                "data_rate_mbps": _field(_dl_rate) if _dl_rate else _manual(),
                "encryption_method": _field(_enc) if _enc else _manual("[AES-256 / None / other]"),
            },
            "ground_stations": {
                "stations": _field(_gs) if _gs else _manual(
                    "[List ground stations: {name, location, bands}]"
                ),
            },
            "data_handling": {
                "data_access_control": _manual("[Describe access control measures]"),
                "data_distribution_policy": _manual("[Who receives data and under what terms]"),
                "shutter_control": _manual("[Ability to restrict imaging of specific areas]"),
                "data_retention_policy": _manual("[Data retention period and deletion procedures]"),
            },
            "disposal_plan": {
                "deorbit_method": _manual("[Natural decay / propulsive / drag augmentation]"),
                "post_mission_lifetime_years": _field(
                    round(max(0, _estimate_orbital_lifetime_years(alt) - design_lifetime_years), 1)
                ),
                "passivation_plan": _manual("[Battery discharge, RF shutdown, momentum dump]"),
                "performance_guarantee": _manual("[Financial or technical guarantee for disposal]"),
            },
            "national_security": {
                "assessment": _manual("[How system addresses national security considerations]"),
                "international_obligations": _manual("[Treaty compliance: OST, Registration Convention, etc.]"),
            },
        },
        "notes": [
            "RSSSA licence is SEPARATE from ISED spectrum licence — both are required",
            "Submit application to Global Affairs Canada: RSSSA-LSTS@international.gc.ca",
            "The Minister cannot grant a licence without a satisfactory disposal plan",
            "Processing time: variable, allow 6+ months",
            "Fields marked auto_populated=false require applicant input before filing",
        ],
    }


# ---------------------------------------------------------------------------
# Priority 2 — ITU API Filing (Appendix 4)
# ---------------------------------------------------------------------------

def generate_itu_api_filing(
    *,
    network_name: str = "",
    administration: str = "Canada — ISED",
    operator_name: str = "",
    contact_email: str = "",
    # Orbit
    orbit_altitude_km: float = 500.0,
    orbit_inclination_deg: float = 97.4,
    orbit_eccentricity: float = 0.0,
    ascending_node_deg: float | None = None,
    num_satellites: int = 1,
    # Frequency assignments — list of dicts
    frequency_assignments: list[dict[str, Any]] | None = None,
    # Antenna
    antenna_gain_dbi: float | None = None,
    antenna_beamwidth_deg: float | None = None,
    antenna_type: str = "",
    # Transmitter
    tx_power_w: float | None = None,
    modulation: str = "QPSK",
    data_rate_bps: float | None = None,
    polarisation: str = "RHCP",
    # Design params passthrough
    design_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate ITU Advance Publication Information (API) filing template.

    Per ITU RR Appendix 4.  Auto-computes emission designators, EIRP,
    and PFD from design parameters.
    """
    dp = design_params or {}

    alt = orbit_altitude_km or dp.get("orbit_altitude_km", 500.0)
    inc = orbit_inclination_deg or dp.get("orbit_inclination_deg", 97.4)
    ecc = orbit_eccentricity or dp.get("orbit_eccentricity", 0.0)
    period_min = round(_compute_period_min(alt), 2)
    apogee = round(alt * (1 + ecc), 2)
    perigee = round(alt * (1 - ecc), 2)
    asc_node = ascending_node_deg if ascending_node_deg is not None else dp.get("ascending_node_deg")

    _tx_power = tx_power_w or dp.get("tx_power_w")
    _gain = antenna_gain_dbi or dp.get("antenna_gain_dbi")
    _beamwidth = antenna_beamwidth_deg or dp.get("antenna_beamwidth_deg")
    _ant_type = antenna_type or dp.get("antenna_type", "")
    _mod = modulation or dp.get("modulation", "QPSK")
    _dr = data_rate_bps or dp.get("data_rate_bps")
    _pol = polarisation or dp.get("polarisation", "RHCP")

    # Compute EIRP if possible
    eirp_dbw: float | None = None
    if _tx_power and _gain:
        eirp_dbw = round(10.0 * math.log10(_tx_power) + _gain, 2)

    # Build frequency assignment entries
    raw_assignments = frequency_assignments or dp.get("frequency_assignments", [])
    computed_assignments = []
    for i, fa in enumerate(raw_assignments):
        centre_mhz = fa.get("centre_freq_mhz") or fa.get("center_freq_mhz")
        bw_khz = fa.get("bandwidth_khz")
        bw_hz = (bw_khz * 1000.0) if bw_khz else fa.get("bandwidth_hz")
        direction = fa.get("direction", "downlink")

        # Emission designator
        emiss = None
        if bw_hz:
            emiss = compute_emission_designator(
                bandwidth_hz=bw_hz,
                modulation=fa.get("modulation", _mod),
                data_rate_bps=fa.get("data_rate_bps", _dr),
            )

        # Per-assignment EIRP (use assignment-level or system-level)
        fa_eirp = fa.get("eirp_dbw")
        if fa_eirp is None and eirp_dbw is not None:
            fa_eirp = eirp_dbw

        # PFD
        fa_pfd = None
        if fa_eirp is not None:
            fa_pfd = compute_pfd_dbw_m2(fa_eirp, alt, elevation_deg=5.0)

        entry: dict[str, Any] = {
            "beam_id": _field(fa.get("beam_id", f"BEAM-{i+1}")),
            "centre_freq_mhz": _field(centre_mhz) if centre_mhz else _manual("[Centre frequency MHz]"),
            "bandwidth_khz": _field(bw_khz) if bw_khz else _manual("[Assigned bandwidth kHz]"),
            "direction": _field(direction),
            "emission_designator": _field(emiss) if emiss else _manual("[e.g. 200KG1D]"),
            "eirp_dbw": _field(fa_eirp) if fa_eirp is not None else _manual("[Compute from Tx power + antenna gain]"),
            "polarisation": _field(fa.get("polarisation", _pol)),
            "service": _field(fa.get("service", "EESS")),
            "pfd_dbw_m2_at_5deg": _field(fa_pfd) if fa_pfd is not None else _manual("[Auto-computed from EIRP + altitude]"),
        }
        computed_assignments.append(entry)

    # If no assignments provided, add a placeholder
    if not computed_assignments:
        computed_assignments.append({
            "beam_id": _manual("[BEAM-1]"),
            "centre_freq_mhz": _manual(),
            "bandwidth_khz": _manual(),
            "direction": _manual("[uplink / downlink]"),
            "emission_designator": _manual(),
            "eirp_dbw": _manual(),
            "polarisation": _manual(),
            "service": _manual("[EESS / FSS / AMS / other]"),
            "pfd_dbw_m2_at_5deg": _manual(),
        })

    return {
        "document": "ITU Advance Publication Information (API) — Appendix 4",
        "standard": "ITU Radio Regulations, Appendix 4",
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": {
            "administration": {
                "notifying_administration": _field(administration),
                "operator_name": _field(operator_name) if operator_name else _manual(),
                "contact_email": _field(contact_email) if contact_email else _manual(),
                "correspondence_language": _field("English"),
            },
            "satellite_network": {
                "network_name": _field(network_name or f"{operator_name or 'MISSION'}-SAT-1"),
                "service_type": _field("Earth Exploration-Satellite Service (EESS)"),
                "number_of_satellites": _field(num_satellites),
            },
            "orbital_elements": {
                "orbit_type": _field(
                    "sun-synchronous" if 96 <= inc <= 99 else "non-geostationary"
                ),
                "apogee_km": _field(apogee),
                "perigee_km": _field(perigee),
                "inclination_deg": _field(inc),
                "period_min": _field(period_min),
                "eccentricity": _field(ecc),
                "ascending_node_deg": _field(asc_node) if asc_node is not None else _manual("[RAAN in degrees]"),
                "number_of_orbital_planes": _field(1),
                "satellites_per_plane": _field(num_satellites),
            },
            "antenna": {
                "gain_dbi": _field(_gain) if _gain else _manual("[Antenna gain dBi]"),
                "beamwidth_deg": _field(_beamwidth) if _beamwidth else _manual("[3 dB beamwidth degrees]"),
                "type": _field(_ant_type) if _ant_type else _manual("[e.g. patch, helix, horn, parabolic]"),
            },
            "frequency_assignments": computed_assignments,
            "pfd_reference": {
                "computation_method": _field("PFD = EIRP - 10*log10(4*pi*R^2), R = slant range at elevation angle"),
                "reference_elevation_deg": _field(5.0),
                "eirp_dbw": _field(eirp_dbw) if eirp_dbw is not None else _manual(),
                "pfd_dbw_m2": _field(
                    compute_pfd_dbw_m2(eirp_dbw, alt, 5.0)
                ) if eirp_dbw is not None else _manual(),
            },
        },
        "notes": [
            "Filing must be submitted through national administration (ISED for Canada) to ITU BR",
            "API must be submitted at least 2 years before planned operation date",
            "Emission designator format: [bandwidth][modulation][signal_type] per ITU RR Appendix 1",
            "PFD limits per ITU RR Article 21, Table 21-4 must not be exceeded",
            "Fields marked auto_populated=false require operator input",
        ],
    }


# ---------------------------------------------------------------------------
# Priority 3 — COPUOS Registration Convention (Article IV)
# ---------------------------------------------------------------------------

# Map mission_type strings to UN general function descriptions
_MISSION_TYPE_TO_UN_FUNCTION: dict[str, str] = {
    "earth_observation": "Earth observation — remote sensing of land, ocean, and atmosphere",
    "eo": "Earth observation — remote sensing of land, ocean, and atmosphere",
    "remote_sensing": "Earth observation — remote sensing of land, ocean, and atmosphere",
    "communications": "Telecommunications — provision of communication services",
    "comms": "Telecommunications — provision of communication services",
    "navigation": "Navigation — positioning, navigation, and timing services",
    "gnss": "Navigation — positioning, navigation, and timing services",
    "science": "Scientific research — space science and exploration",
    "astronomy": "Scientific research — space astronomy and astrophysics",
    "weather": "Meteorological observation — weather monitoring and forecasting",
    "meteorology": "Meteorological observation — weather monitoring and forecasting",
    "technology": "Technology demonstration — in-orbit validation of new technologies",
    "tech_demo": "Technology demonstration — in-orbit validation of new technologies",
    "education": "Educational — university-built satellite for STEM education and training",
    "cubesat": "Technology demonstration / educational — small satellite mission",
    "surveillance": "Earth observation — surveillance and situational awareness",
    "sar": "Earth observation — synthetic aperture radar imaging",
    "sigint": "Signal intelligence and spectrum monitoring",
    "relay": "Data relay — inter-satellite communication relay services",
    "debris": "Space environment — debris monitoring or active debris removal",
    "ispection": "In-orbit servicing — proximity operations and inspection",
}


def generate_copuos_registration(
    *,
    study_name: str = "",
    mission_id: str = "",
    mission_type: str = "",
    launching_state: str = "Canada",
    launch_date: str = "",
    launch_site: str = "",
    launch_provider: str = "",
    # Orbit
    orbit_altitude_km: float = 500.0,
    orbit_inclination_deg: float = 97.4,
    orbit_eccentricity: float = 0.0,
    # Spacecraft
    mass_kg: float | None = None,
    design_lifetime_years: float | None = None,
    general_function: str = "",
    # Design params passthrough
    design_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate UN Registration Convention Article IV filing template.

    Auto-fills all 5 mandatory data items from design parameters.
    """
    dp = design_params or {}

    alt = orbit_altitude_km or dp.get("orbit_altitude_km", 500.0)
    inc = orbit_inclination_deg or dp.get("orbit_inclination_deg", 97.4)
    ecc = orbit_eccentricity or dp.get("orbit_eccentricity", 0.0)
    period_min = round(_compute_period_min(alt), 2)
    apogee = round(alt * (1 + ecc), 1)
    perigee = round(alt * (1 - ecc), 1)

    _mission_id = mission_id or dp.get("mission_id", "")
    _mission_type = mission_type or dp.get("mission_type", "")
    _launch_date = launch_date or dp.get("launch_date", "")
    _launch_site = launch_site or dp.get("launch_site", "")
    _launch_provider = launch_provider or dp.get("launch_provider", "")
    _mass = mass_kg or dp.get("mass_kg") or dp.get("total_mass_kg")
    _lifetime = design_lifetime_years or dp.get("design_lifetime_years")

    # Resolve general function
    func_desc = general_function
    if not func_desc:
        func_desc = _MISSION_TYPE_TO_UN_FUNCTION.get(
            _mission_type.lower().replace(" ", "_").replace("-", "_"),
            "",
        )

    # Build designator
    designator = _mission_id or study_name or "[DESIGNATOR TBD]"

    return {
        "document": "UN Space Object Registration (Registration Convention Article IV)",
        "standard": "Convention on Registration of Objects Launched into Outer Space (1975)",
        "generated": datetime.now(timezone.utc).isoformat(),
        "filing_to": "UN Secretary-General, via national registrar (Canada: Global Affairs Canada)",
        "article_iv_data_items": {
            "item_a_launching_state": {
                "description": "Name of launching State or States",
                "value": _field(launching_state),
                "co_launching_states": _manual("[List any co-launching states]"),
            },
            "item_b_designator": {
                "description": "Appropriate designator of the space object or its registration number",
                "value": _field(designator, auto=bool(_mission_id or study_name)),
                "cospar_id": _manual("[Assigned post-launch, e.g. 2026-001A]"),
            },
            "item_c_launch": {
                "description": "Date and territory or location of launch",
                "launch_date_utc": _field(_launch_date) if _launch_date else _manual("[Launch date UTC]"),
                "launch_territory": _field(_launch_site) if _launch_site else _manual("[Launch site / territory]"),
                "launch_provider": _field(_launch_provider) if _launch_provider else _manual("[Launch provider]"),
            },
            "item_d_orbital_parameters": {
                "description": "Basic orbital parameters",
                "nodal_period_min": _field(period_min),
                "inclination_deg": _field(inc),
                "apogee_km": _field(apogee),
                "perigee_km": _field(perigee),
            },
            "item_e_general_function": {
                "description": "General function of the space object",
                "value": _field(func_desc) if func_desc else _manual("[Describe general function of spacecraft]"),
            },
        },
        "additional_recommended_info": {
            "web_link": _manual("[URL with additional mission information]"),
            "operator": _field(study_name) if study_name else _manual(),
            "mass_kg": _field(_mass) if _mass else _manual("[Spacecraft mass kg]"),
            "expected_lifetime_years": _field(_lifetime) if _lifetime else _manual(),
            "status": _field("Pre-launch"),
        },
        "notes": [
            "Filing through national registrar (Canada: Global Affairs Canada)",
            "File 'as soon as practicable' after launch (GA Res 62/101)",
            "Update registration if orbital parameters change significantly",
            "Canada maintains the Registry of Space Objects (RSO) per the Canadian Space Agency",
            "Fields marked auto_populated=false require applicant input",
        ],
    }


# ---------------------------------------------------------------------------
# Priority 4 — End-of-Life / Debris Compliance Report
# ---------------------------------------------------------------------------

def generate_eol_report(
    *,
    study_name: str = "",
    # Orbit
    orbit_altitude_km: float = 500.0,
    orbit_inclination_deg: float = 97.4,
    # Spacecraft
    dry_mass_kg: float = 5.0,
    wet_mass_kg: float | None = None,
    cross_section_m2: float | None = None,
    # Propulsion
    has_propulsion: bool = False,
    delta_v_available_ms: float | None = None,
    isp_s: float | None = None,
    # Power
    battery_capacity_wh: float | None = None,
    # Mission
    mission_duration_years: float = 3.0,
    # Design params passthrough
    design_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate end-of-life / debris compliance analysis report.

    Auto-computes orbital lifetime, 25-year compliance, deorbit delta-V,
    casualty risk, and passivation checklist from design parameters.
    """
    dp = design_params or {}

    alt = orbit_altitude_km or dp.get("orbit_altitude_km", 500.0)
    inc = orbit_inclination_deg or dp.get("orbit_inclination_deg", 97.4)
    _dry = dry_mass_kg or dp.get("dry_mass_kg", 5.0)
    _wet = wet_mass_kg or dp.get("wet_mass_kg") or _dry
    _cs = cross_section_m2 or dp.get("cross_section_m2")
    _has_prop = has_propulsion or dp.get("has_propulsion", False)
    _dv = delta_v_available_ms or dp.get("delta_v_available_ms")
    _isp = isp_s or dp.get("isp_s")
    _batt = battery_capacity_wh or dp.get("battery_capacity_wh")

    # --- Orbital lifetime ---
    lifetime_years = _estimate_orbital_lifetime_years(alt)
    post_mission_years = max(0.0, lifetime_years - mission_duration_years)

    # --- 25-year and 5-year compliance ---
    compliant_25yr = post_mission_years <= 25.0
    compliant_5yr = post_mission_years <= 5.0

    # --- Deorbit delta-V estimate ---
    # To deorbit from circular alt to ~200 km perigee (natural decay within weeks)
    deorbit_dv: float | None = None
    if alt > 200:
        r1 = R_EARTH_KM + alt  # initial circular
        r2_peri = R_EARTH_KM + 200.0  # target perigee
        a_transfer = (r1 + r2_peri) / 2.0
        v_circ = math.sqrt(MU_EARTH_KM3S2 / r1)  # km/s
        v_transfer = math.sqrt(MU_EARTH_KM3S2 * (2.0 / r1 - 1.0 / a_transfer))
        deorbit_dv = round(abs(v_circ - v_transfer) * 1000.0, 1)  # m/s

    # --- Casualty risk estimate ---
    surviving_mass_kg = _dry * 0.2  # ~20% typically survives reentry
    if _dry > 100:
        casualty_assessment = "Detailed casualty risk analysis required (mass > 100 kg)"
        casualty_risk_level = "MEDIUM-HIGH"
        casualty_expectation = None  # needs detailed analysis
    elif _dry > 50:
        casualty_assessment = "Moderate surviving debris expected — analysis recommended"
        casualty_risk_level = "MEDIUM"
        # Rough estimate: Ac = 0.6 * (M_survive)^0.5 m^2, Ec = Ac * pop_density
        debris_area_m2 = 0.6 * math.sqrt(surviving_mass_kg)
        human_casualty_area = debris_area_m2 + 0.4 * 0.4 * math.pi  # human cross-section ~0.5m^2
        # World average pop density ~15 ppl/km^2, but ground track weighted ~5
        casualty_expectation = round(human_casualty_area * 1e-6 * 5.0, 6)
    elif _dry > 10:
        casualty_assessment = "Low-moderate risk — simplified analysis may suffice"
        casualty_risk_level = "LOW-MEDIUM"
        surviving_mass_kg = _dry * 0.15
        debris_area_m2 = 0.6 * math.sqrt(surviving_mass_kg)
        human_casualty_area = debris_area_m2 + 0.5
        casualty_expectation = round(human_casualty_area * 1e-6 * 5.0, 6)
    else:
        casualty_assessment = "Low risk — small object expected to fully demise on reentry"
        casualty_risk_level = "LOW"
        casualty_expectation = 0.0

    nasa_compliant = (casualty_expectation is not None and casualty_expectation < 0.0001)

    # --- Area-to-mass ratio ---
    area_to_mass: float | None = None
    if _cs and _dry:
        area_to_mass = round(_cs / _dry, 4)

    # --- Passivation checklist ---
    passivation_items = []
    passivation_items.append({
        "item": "Battery discharge to safe level",
        "detail": f"Discharge to <50% SoC ({_batt} Wh capacity)" if _batt else "Discharge to <50% SoC",
        "stored_energy_wh": _field(_batt) if _batt else _manual("[Battery capacity Wh]"),
        "applicable": _field(True),
    })
    passivation_items.append({
        "item": "Pressurant venting",
        "detail": "Vent all pressurised systems to vacuum" if _has_prop else "No pressurised systems",
        "applicable": _field(_has_prop),
    })
    passivation_items.append({
        "item": "Momentum wheel / reaction wheel spin-down",
        "detail": "Command all wheels to zero speed",
        "applicable": _field(True),
    })
    passivation_items.append({
        "item": "Solar array short-circuit",
        "detail": "Short SA strings to prevent charging after passivation",
        "applicable": _field(True),
    })
    passivation_items.append({
        "item": "RF transmitter shutdown",
        "detail": "Disable all transmitters to free spectrum",
        "applicable": _field(True),
    })

    # --- Determine deorbit method ---
    if _has_prop and _dv and deorbit_dv and _dv >= deorbit_dv:
        deorbit_method = "Propulsive deorbit (sufficient delta-V available)"
    elif _has_prop:
        deorbit_method = "Propulsive deorbit (verify delta-V budget)"
    elif compliant_25yr:
        deorbit_method = "Natural orbital decay (compliant with 25-year guideline)"
    else:
        deorbit_method = "Drag augmentation device required — natural decay exceeds 25 years"

    return {
        "document": "End-of-Life / Debris Compliance Analysis Report",
        "standard": "IADC Guidelines (2020) / NASA-STD-8719.14 Rev B / ECSS-U-AS-10C / FCC 47 CFR 25.114",
        "study_name": study_name,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": {
            "orbital_lifetime": {
                "initial_altitude_km": _field(alt),
                "inclination_deg": _field(inc),
                "estimated_orbital_lifetime_years": _field(lifetime_years),
                "mission_duration_years": _field(mission_duration_years),
                "post_mission_lifetime_years": _field(round(post_mission_years, 1)),
                "area_to_mass_ratio_m2_kg": _field(area_to_mass) if area_to_mass else _manual("[Cross-section / mass]"),
                "model_used": _field("Simplified empirical (moderate solar activity, Cd=2.2)"),
                "note": _field("For regulatory filing, use DAS/DRAMA/STK for high-fidelity lifetime prediction"),
            },
            "compliance_25yr": {
                "compliant": _field(compliant_25yr),
                "post_mission_years": _field(round(post_mission_years, 1)),
                "limit_years": _field(25),
                "standard": _field("IADC / ECSS-U-AS-10C / UN COPUOS Guidelines"),
            },
            "compliance_5yr_fcc": {
                "compliant": _field(compliant_5yr),
                "post_mission_years": _field(round(post_mission_years, 1)),
                "limit_years": _field(5),
                "standard": _field("FCC 47 CFR 25.114 (effective September 2024)"),
                "note": _field("Applies to any satellite filing with FCC, including non-US operators on US launches"),
            },
            "deorbit_plan": {
                "method": _field(deorbit_method),
                "propulsion_available": _field(_has_prop),
                "delta_v_required_ms": _field(deorbit_dv) if deorbit_dv else _field("N/A (already compliant)"),
                "delta_v_available_ms": _field(_dv) if _dv else _manual("[From propulsion budget]"),
                "isp_s": _field(_isp) if _isp else _manual("[Specific impulse if applicable]"),
                "deorbit_sufficient": _field(
                    _dv >= deorbit_dv if (_dv and deorbit_dv) else None
                ),
                "backup_plan": _field(
                    "Drag augmentation device"
                    if (not compliant_25yr and not _has_prop)
                    else "N/A"
                ),
            },
            "stored_energy": {
                "battery_capacity_wh": _field(_batt) if _batt else _manual("[Total battery capacity Wh]"),
                "pressurised_systems": _field(_has_prop),
                "note": _field("All stored energy must be depleted at end of mission per IADC 5.3.2"),
            },
            "passivation_checklist": passivation_items,
            "casualty_risk": {
                "dry_mass_kg": _field(_dry),
                "estimated_surviving_mass_kg": _field(round(surviving_mass_kg, 2)),
                "assessment": _field(casualty_assessment),
                "risk_level": _field(casualty_risk_level),
                "casualty_expectation": _field(casualty_expectation) if casualty_expectation is not None else _manual("[Detailed analysis required]"),
                "compliant_nasa_1e4": _field(nasa_compliant),
                "nasa_limit": _field("1:10,000 (Ec < 0.0001)"),
            },
            "collision_avoidance": {
                "capability": _manual("[GPS-based OD + conjunction screening service]"),
                "screening_provider": _manual("[18 SDS / LeoLabs / other]"),
                "delta_v_budget_per_year_ms": _manual("[Annual collision avoidance budget]"),
            },
        },
        "regulatory_compliance_summary": {
            "IADC_25yr_guideline": _field(compliant_25yr),
            "FCC_5yr_rule": _field(compliant_5yr),
            "ECSS_U_AS_10C": _field(compliant_25yr),
            "NASA_STD_8719_14": _field(nasa_compliant),
            "passivation_plan": _field(True),
        },
        "notes": [
            "This is a preliminary assessment — use high-fidelity tools (DAS, DRAMA, STK) for formal filing",
            "Solar activity assumptions significantly affect lifetime at 400-600 km",
            "FCC 5-year rule is mandatory for US-launched or US-licensed satellites (Sept 2024)",
            "Fields marked auto_populated=false require operator input",
        ],
    }


# ---------------------------------------------------------------------------
# Priority 5 — Export Control Assessment
# ---------------------------------------------------------------------------

def generate_export_assessment(
    *,
    study_name: str = "",
    country_of_origin: str = "Canada",
    launch_country: str = "USA",
    # Components — list of {name, origin, manufacturer, type, ...}
    components_origin: list[dict[str, str]] | None = None,
    # Auto-flag triggers
    has_encryption: bool = False,
    encryption_bits: int | None = None,
    gsd_m: float | None = None,
    has_propulsion: bool = False,
    isp_s: float | None = None,
    # KB components for US-origin flagging
    kb_components: list[dict[str, Any]] | None = None,
    # Design params passthrough
    design_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate export control classification assessment.

    Automatically flags potential controlled technologies based on
    design parameters and component origins.
    """
    dp = design_params or {}
    comps = components_origin or dp.get("components_origin", [])
    _gsd = gsd_m or dp.get("gsd_m")
    _enc = has_encryption or dp.get("has_encryption", False)
    _enc_bits = encryption_bits or dp.get("encryption_bits")
    _has_prop = has_propulsion or dp.get("has_propulsion", False)
    _isp = isp_s or dp.get("isp_s")
    _kb = kb_components or dp.get("kb_components", [])

    # --- Automatic flags ---
    flags: list[dict[str, Any]] = []

    # GSD < 2m → potential controlled technology
    if _gsd is not None and _gsd < 2.0:
        severity = "HIGH" if _gsd < 0.5 else "MEDIUM"
        flags.append({
            "flag": "HIGH_RESOLUTION_IMAGING",
            "severity": severity,
            "parameter": f"GSD = {_gsd} m",
            "detail": (
                f"Ground sample distance < 2 m ({_gsd} m) may constitute controlled "
                f"remote sensing technology"
            ),
            "us_regime": (
                "USML Category XV (ITAR)" if _gsd < 0.5
                else "EAR ECCN 9A515 / 6A002"
            ),
            "canadian_regime": "Canadian Controlled Goods List, Group 6",
            "action": (
                "Obtain DDTC classification determination"
                if _gsd < 0.5
                else "Request BIS commodity classification"
            ),
            "auto_populated": True,
        })

    # Encryption > 56-bit → EAR Category 5
    if _enc and _enc_bits and _enc_bits > 56:
        flags.append({
            "flag": "ENCRYPTION_CONTROLLED",
            "severity": "MEDIUM",
            "parameter": f"Encryption = {_enc_bits}-bit",
            "detail": (
                f"Encryption exceeding 56-bit key length ({_enc_bits}-bit) is "
                f"controlled under Wassenaar Arrangement Category 5 Part 2"
            ),
            "us_regime": "EAR ECCN 5A002 / 5D002",
            "canadian_regime": "ECL Group 5, Category 5-A.2",
            "action": "File ENC classification request with BIS; License Exception ENC may apply",
            "auto_populated": True,
        })
    elif _enc:
        flags.append({
            "flag": "ENCRYPTION_PRESENT",
            "severity": "LOW",
            "parameter": "Encryption present (key length unknown)",
            "detail": "Encryption capability detected — determine key length for classification",
            "action": "Determine encryption key length and algorithm for proper classification",
            "auto_populated": True,
        })

    # Propulsion Isp > 250s → potential controlled
    if _has_prop and _isp and _isp > 250:
        flags.append({
            "flag": "HIGH_ISP_PROPULSION",
            "severity": "MEDIUM",
            "parameter": f"Isp = {_isp} s",
            "detail": (
                f"Propulsion system with Isp > 250 s ({_isp} s) may be "
                f"controlled under missile technology export controls"
            ),
            "us_regime": "EAR ECCN 9A515 / USML Category IV (if ITAR)",
            "canadian_regime": "ECL Group 9 / MTCR Annex",
            "action": "Verify propulsion system classification with vendor",
            "auto_populated": True,
        })

    # US-origin components from KB → flag for EAR review
    us_components: list[dict[str, Any]] = []
    for comp in _kb:
        origin = (comp.get("country_of_origin", "") or comp.get("origin", "")).upper()
        manufacturer = comp.get("manufacturer", "")
        if origin in ("US", "USA", "UNITED STATES") or _is_likely_us_manufacturer(manufacturer):
            us_components.append({
                "component": comp.get("name", comp.get("component_id", "unknown")),
                "manufacturer": manufacturer,
                "type": comp.get("type", "unknown"),
                "auto_populated": True,
            })

    if us_components:
        flags.append({
            "flag": "US_ORIGIN_COMPONENTS",
            "severity": "HIGH",
            "parameter": f"{len(us_components)} US-origin component(s) detected",
            "detail": (
                "US-origin components subject to EAR re-export controls. "
                "Satellite containing US parts requires BIS licence for launch "
                "from non-Wassenaar countries."
            ),
            "us_regime": "EAR 15 CFR 734.3 — de minimis / direct product rules",
            "components": us_components,
            "action": "Request ECCN classification from each US vendor; assess de minimis percentage",
            "auto_populated": True,
        })

    for comp in comps:
        origin = (comp.get("origin", "")).upper()
        if origin in ("US", "USA", "UNITED STATES"):
            # Check if already covered by KB
            if not any(
                uc["component"] == comp.get("name", comp.get("component", ""))
                for uc in us_components
            ):
                us_components.append({
                    "component": comp.get("name", comp.get("component", "unknown")),
                    "manufacturer": comp.get("manufacturer", "unknown"),
                    "type": comp.get("type", ""),
                    "auto_populated": True,
                })

    # --- Build classifications ---
    classifications: list[dict[str, Any]] = []

    if any(f["flag"] == "US_ORIGIN_COMPONENTS" for f in flags) or any(
        c.get("origin", "").upper() in ("US", "USA", "UNITED STATES") for c in comps
    ):
        if _gsd is not None and _gsd < 0.5:
            classifications.append({
                "regime": "ITAR",
                "category": "USML Category XV",
                "reason": f"Sub-metre GSD ({_gsd} m) with US-origin components — likely ITAR-controlled",
                "action": "Consult DDTC for classification. State Department licence required.",
                "auto_populated": True,
            })
        else:
            classifications.append({
                "regime": "EAR",
                "eccn": "9A515.x",
                "reason": "Spacecraft with US-origin components",
                "action": "BIS classification request recommended. License Exception STA/CSA may apply for Wassenaar countries.",
                "auto_populated": True,
            })

    if country_of_origin == "Canada":
        classifications.append({
            "regime": "Canadian CGP",
            "category": "Item 5504",
            "reason": "Satellite systems are controlled goods under Canadian regulations",
            "action": "Register with Controlled Goods Directorate (CGD) if handling US-origin controlled components.",
            "auto_populated": True,
        })

    if launch_country == "USA":
        classifications.append({
            "regime": "EAR (launch services)",
            "reason": "Any satellite launching from US soil must comply with EAR regardless of nationality",
            "action": "Ensure all satellite components classified before integration at US launch site.",
            "auto_populated": True,
        })

    return {
        "document": "Export Control Classification Assessment",
        "study_name": study_name,
        "generated": datetime.now(timezone.utc).isoformat(),
        "country_of_origin": _field(country_of_origin),
        "launch_country": _field(launch_country),
        "sections": {
            "automated_flags": {
                "total_flags": _field(len(flags)),
                "high_severity": _field(sum(1 for f in flags if f.get("severity") == "HIGH")),
                "medium_severity": _field(sum(1 for f in flags if f.get("severity") == "MEDIUM")),
                "flags": flags,
            },
            "classifications": classifications,
            "us_origin_components": {
                "count": _field(len(us_components)),
                "components": us_components,
                "de_minimis_note": _field(
                    "If US-origin content < 25% by value, de minimis exception MAY apply "
                    "(but NOT for ITAR items, and NOT for certain EAR items to embargoed destinations)"
                ),
            },
            "encryption_assessment": {
                "has_encryption": _field(_enc),
                "key_length_bits": _field(_enc_bits) if _enc_bits else _manual("[Specify key length]") if _enc else _field("N/A"),
                "algorithm": _manual("[e.g. AES-256, RSA-2048]") if _enc else _field("N/A"),
                "wassenaar_cat5": _field(
                    _enc and (_enc_bits is not None and _enc_bits > 56)
                ),
            },
            "propulsion_assessment": {
                "has_propulsion": _field(_has_prop),
                "isp_s": _field(_isp) if _isp else _field("N/A"),
                "mtcr_concern": _field(
                    _has_prop and _isp is not None and _isp > 250
                ),
            },
            "imaging_assessment": {
                "gsd_m": _field(_gsd) if _gsd else _manual("[GSD not available]"),
                "controlled": _field(_gsd is not None and _gsd < 2.0),
                "itar_threshold": _field("< 0.5 m (USML Cat XV)"),
                "ear_threshold": _field("< 2.0 m (ECCN 6A002 / 9A515)"),
            },
        },
        "recommendations": [
            "Classify all components BEFORE procurement (request vendor ECCN/USML classification)",
            "Apply for necessary export licences at least 6 months before hardware delivery",
            "Maintain records of all component classifications for audit purposes",
            "Consult with export control counsel if any component origin is uncertain",
            "For Canadian entities: register with Controlled Goods Directorate if handling ITAR items",
            "Review Wassenaar Arrangement dual-use list for all subsystem technologies",
        ],
        "notes": [
            "This assessment is auto-generated and does NOT constitute legal advice",
            "All flagged items require review by a qualified export control professional",
            "Fields marked auto_populated=false require operator input",
        ],
    }


def _is_likely_us_manufacturer(name: str) -> bool:
    """Heuristic check for known US space component manufacturers."""
    us_names = {
        "aerojet", "ball aerospace", "bae", "blue canyon", "clyde space",
        "endurosat", "gomspace", "honeywell", "l3harris", "lockheed",
        "northrop", "raytheon", "rocket lab", "spacex", "tyvak",
        "virgin orbit", "general dynamics", "boeing", "maxar",
        "collins aerospace", "moog", "pumpkin", "innovative solutions",
        "isi", "cubesat pro", "nanoavionics",
    }
    lower = name.lower()
    return any(n in lower for n in us_names)
