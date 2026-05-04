"""SpaceCDF — RF Spectrum & Licensing Module.

Manages frequency allocation knowledge, licensing constraints,
and ITU filing support for CubeSat missions.

References:
  - ITU Radio Regulations (RR), Articles 4.4, 9, 11
  - ITU RR Appendix 4 (data requirements for satellite filings)
  - IARU Satellite Frequency Coordination
  - FCC 47 CFR Part 5 (experimental), Part 25 (commercial), Part 97 (amateur)
  - ISED CPC-2-6-01 (developmental), CPC-2-6-02 (space station)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Frequency band database
# ---------------------------------------------------------------------------

@dataclass
class FrequencyBand:
    """A frequency band allocation for satellite use."""
    name: str
    band_label: str  # UHF, VHF, S, X, Ka, L
    freq_min_mhz: float
    freq_max_mhz: float
    direction: str  # "uplink", "downlink", "both"
    service: str  # ITU service designation
    license_types: list[str]  # ["amateur", "experimental", "commercial"]
    typical_data_rate: str  # Human-readable
    notes: str = ""
    requires_itu_filing: bool = False
    requires_national_license: bool = True


# Comprehensive CubeSat-relevant frequency allocations
FREQUENCY_BANDS: list[FrequencyBand] = [
    # --- Amateur ---
    FrequencyBand("VHF Amateur", "VHF", 145.8, 146.0, "downlink", "Amateur-Satellite (EA)",
                  ["amateur"], "1.2-9.6 kbps",
                  "IARU coordination required. No encryption except TC. No commercial use. Open data.",
                  requires_itu_filing=False),
    FrequencyBand("UHF Amateur", "UHF", 435.0, 438.0, "both", "Amateur-Satellite (EA)",
                  ["amateur"], "1.2-19.2 kbps",
                  "Most popular CubeSat band. IARU coordination required. No commercial use.",
                  requires_itu_filing=False),
    FrequencyBand("S-band Amateur", "S", 2400.0, 2450.0, "both", "Amateur-Satellite (EA)",
                  ["amateur"], "up to 256 kbps",
                  "Shared with ISM band. IARU coordination. Less commonly used.",
                  requires_itu_filing=False),

    # --- MetAids / Earth Exploration ---
    FrequencyBand("UHF MetAids DL", "UHF", 400.0, 402.0, "downlink", "MetAids/MetSat/EESS",
                  ["experimental", "commercial"], "1.2-9.6 kbps",
                  "Used by some science CubeSats. National administration filing required.",
                  requires_itu_filing=True),

    # --- S-band (most common commercial CubeSat) ---
    FrequencyBand("S-band Uplink", "S", 2025.0, 2110.0, "uplink", "Space Operation / EESS",
                  ["experimental", "commercial"], "4-256 kbps",
                  "Common CubeSat TT&C uplink. Requires ITU API + national license.",
                  requires_itu_filing=True),
    FrequencyBand("S-band Downlink", "S", 2200.0, 2290.0, "downlink", "Space Operation / EESS",
                  ["experimental", "commercial"], "256 kbps - 10 Mbps",
                  "Common CubeSat TT&C + moderate data downlink. Not allocated for non-Federal US use.",
                  requires_itu_filing=True),

    # --- X-band (high data rate) ---
    FrequencyBand("X-band Downlink", "X", 8025.0, 8400.0, "downlink", "EESS (space-to-Earth)",
                  ["commercial"], "12.5-400 Mbps",
                  "Primary choice for high-data-rate EO/SAR payloads. Requires precise pointing.",
                  requires_itu_filing=True),

    # --- Ka-band (very high data rate, emerging) ---
    FrequencyBand("Ka-band Downlink", "Ka", 25500.0, 27000.0, "downlink", "EESS / FSS",
                  ["commercial"], "100 Mbps - 1+ Gbps",
                  "Emerging for CubeSats. Very high data rates but significant rain attenuation.",
                  requires_itu_filing=True),

    # --- L-band (IoT/M2M) ---
    FrequencyBand("L-band Downlink", "L", 1525.0, 1559.0, "downlink", "Mobile-Satellite (MSS)",
                  ["commercial"], "1-50 kbps",
                  "Dominated by Inmarsat/Iridium. Difficult for independent CubeSats.",
                  requires_itu_filing=True),
    FrequencyBand("L-band Uplink", "L", 1626.5, 1660.5, "uplink", "Mobile-Satellite (MSS)",
                  ["commercial"], "1-50 kbps",
                  "User terminal uplink for MSS. Heavy coordination required.",
                  requires_itu_filing=True),

    # --- AIS (receive only) ---
    FrequencyBand("AIS Maritime", "VHF", 156.0, 163.0, "receive", "Maritime Mobile",
                  ["amateur", "experimental", "commercial"], "9.6 kbps",
                  "Passive receive only — no TX licensing needed. AIS channels at 161.975/162.025 MHz.",
                  requires_itu_filing=False, requires_national_license=False),
]


def get_bands_for_mission(
    mission_type: str = "earth_observation",
    license_type: str = "commercial",
    data_rate_mbps: float = 10.0,
) -> list[dict[str, Any]]:
    """Return frequency bands suitable for a given mission and license type.

    Filters by license compatibility and data rate requirements.
    """
    results = []
    for band in FREQUENCY_BANDS:
        if license_type not in band.license_types:
            continue

        # Check data rate compatibility (rough)
        suitable = True
        if data_rate_mbps > 10 and band.band_label in ("VHF", "UHF"):
            suitable = False  # Too slow for high data rate
        if data_rate_mbps > 100 and band.band_label == "S":
            suitable = False

        results.append({
            "name": band.name,
            "band": band.band_label,
            "freq_min_mhz": band.freq_min_mhz,
            "freq_max_mhz": band.freq_max_mhz,
            "direction": band.direction,
            "service": band.service,
            "typical_data_rate": band.typical_data_rate,
            "notes": band.notes,
            "requires_itu_filing": band.requires_itu_filing,
            "suitable_for_data_rate": suitable,
            "license_types": band.license_types,
        })

    # Sort: suitable first, then by frequency
    results.sort(key=lambda r: (not r["suitable_for_data_rate"], r["freq_min_mhz"]))
    return results


# ---------------------------------------------------------------------------
# ITU filing template
# ---------------------------------------------------------------------------

def generate_itu_api_template(
    *,
    network_name: str = "",
    administration: str = "CAN",
    orbit_altitude_km: float = 500,
    orbit_inclination_deg: float = 97.4,
    orbit_eccentricity: float = 0.0,
    num_satellites: int = 1,
    frequency_bands: list[dict] | None = None,
    operator_name: str = "",
    contact_email: str = "",
) -> dict[str, Any]:
    """Generate ITU Advance Publication Information (API) template.

    Per ITU RR Appendix 4, Section I.
    """
    import math

    a_m = (6371 + orbit_altitude_km) * 1000
    period_min = 2 * math.pi * math.sqrt(a_m**3 / 3.986004418e14) / 60

    bands = frequency_bands or []

    return {
        "document": "ITU Advance Publication Information (API)",
        "standard": "ITU RR Appendix 4, Section I",
        "generated": "auto",
        "sections": {
            "administration": {
                "notifying_administration": administration,
                "operator_name": operator_name,
                "contact": contact_email,
            },
            "satellite_network": {
                "network_name": network_name or f"{operator_name}-SAT-1",
                "service_type": "Earth Exploration-Satellite Service (EESS)" if any(b.get("band") in ("S", "X") for b in bands) else "Amateur-Satellite Service",
                "number_of_satellites": num_satellites,
            },
            "orbital_characteristics": {
                "orbit_type": "non-geostationary" if orbit_inclination_deg < 90 else "sun-synchronous",
                "apogee_km": orbit_altitude_km * (1 + orbit_eccentricity),
                "perigee_km": orbit_altitude_km * (1 - orbit_eccentricity),
                "inclination_deg": orbit_inclination_deg,
                "nodal_period_min": round(period_min, 2),
                "number_of_orbital_planes": 1,
                "satellites_per_plane": num_satellites,
            },
            "frequency_assignments": [
                {
                    "beam_id": f"BEAM-{i+1}",
                    "centre_frequency_mhz": (b["freq_min_mhz"] + b["freq_max_mhz"]) / 2,
                    "assigned_bandwidth_mhz": b["freq_max_mhz"] - b["freq_min_mhz"],
                    "direction": b["direction"],
                    "emission_designator": "TBD",  # e.g. "200KG1D"
                    "polarization": "RHCP",
                    "eirp_dbw": "TBD",
                    "service": b.get("service", "EESS"),
                }
                for i, b in enumerate(bands)
            ],
        },
        "notes": [
            "All fields marked TBD must be completed before filing",
            "Emission designator format: [bandwidth][modulation][signal_type]",
            "EIRP values must be computed from link budget analysis",
            "Filing must be submitted through national administration to ITU BR",
        ],
    }


# ---------------------------------------------------------------------------
# IARU coordination form template
# ---------------------------------------------------------------------------

def generate_iaru_coordination_template(
    *,
    mission_name: str = "",
    institution: str = "",
    country: str = "",
    callsign: str = "",
    orbit_altitude_km: float = 500,
    orbit_inclination_deg: float = 97.4,
    proposed_uplink_mhz: float = 145.9,
    proposed_downlink_mhz: float = 435.0,
    modulation: str = "GMSK",
    data_rate_bps: int = 9600,
    tx_power_w: float = 1.0,
    launch_date: str = "TBD",
    mission_lifetime_years: float = 2.0,
) -> dict[str, Any]:
    """Generate IARU Amateur Satellite Coordination Request template.

    Per IARU Coordination Request Form Version 40.
    """
    return {
        "document": "IARU Amateur Satellite Coordination Request",
        "standard": "IARU Form Version 40",
        "generated": "auto",
        "sections": {
            "contact_information": {
                "institution": institution,
                "country": country,
                "amateur_callsign": callsign,
                "iaru_member_society": f"National society of {country}",
            },
            "mission_description": {
                "satellite_name": mission_name,
                "mission_objectives": "TBD — describe educational/scientific objectives",
                "satellite_dimensions": "TBD — e.g. 10×10×34 cm (3U CubeSat)",
                "satellite_mass_kg": "TBD",
            },
            "orbital_parameters": {
                "altitude_km": orbit_altitude_km,
                "inclination_deg": orbit_inclination_deg,
                "expected_launch_date": launch_date,
                "mission_lifetime_years": mission_lifetime_years,
            },
            "frequency_plan": {
                "uplink_frequency_mhz": proposed_uplink_mhz,
                "uplink_bandwidth_khz": 25,
                "downlink_frequency_mhz": proposed_downlink_mhz,
                "downlink_bandwidth_khz": 25,
                "modulation": modulation,
                "data_rate_bps": data_rate_bps,
                "protocol": "AX.25" if data_rate_bps <= 9600 else "CSP",
            },
            "transmitter": {
                "tx_power_w": tx_power_w,
                "eirp_w": tx_power_w * 1.5,  # Approximate with monopole
                "antenna_type": "Monopole / Dipole",
                "antenna_gain_dbi": 2.0,
            },
            "ground_control": {
                "telecommand_shutoff": "YES — ground-based transmitter shutoff capability included",
                "ground_station_location": "TBD",
                "ground_station_callsign": callsign,
            },
        },
        "notes": [
            "Submit through your national IARU Member Society",
            "All amateur transmissions must be unencrypted (except telecommand)",
            "No commercial use permitted under amateur-satellite service",
            "Submit at least 6 months before planned launch",
        ],
    }
