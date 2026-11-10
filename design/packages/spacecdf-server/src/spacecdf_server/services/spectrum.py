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

import re
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


LICENSE_TYPES = ("amateur", "experimental", "commercial", "academic")

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

    # --- UHF / VHF space operation (TT&C of small EO satellites outside the amateur service) ---
    # Canadian Table of Frequency Allocations (2018 ed.; re-check against the 2026 edition) and ITU RR.
    FrequencyBand("UHF space operation downlink", "UHF", 401.0, 402.0, "downlink",
                  "Space Operation (space-to-Earth)",
                  ["experimental", "commercial", "academic"], "1.2-38.4 kbps",
                  "Primary SPACE OPERATION (space-to-Earth) allocation, shared with METEOROLOGICAL AIDS "
                  "(radiosondes) and EESS/MetSat (Earth-to-space) data-collection uplinks: avoid 401.4-401.7 MHz "
                  "(NGSO DCS, ITU-R SA.2045). Not a meteorological-aids or amateur assignment.",
                  requires_itu_filing=True),
    FrequencyBand("UHF space operation uplink (RR 5.286)", "UHF", 449.75, 450.25, "uplink",
                  "Space Operation (Earth-to-space)",
                  ["experimental", "commercial", "academic"], "1.2-9.6 kbps",
                  "RR 5.286: 449.75-450.25 MHz may be used for the space operation and space research services "
                  "(Earth-to-space), subject to agreement obtained under RR No. 9.21. Radiolocation-primary below "
                  "450 MHz; land mobile 450-470 MHz (Canadian footnote C23).",
                  requires_itu_filing=True),
    FrequencyBand("VHF space operation uplink (fallback)", "VHF", 148.0, 149.9, "uplink",
                  "Space Operation (Earth-to-space)",
                  ["experimental", "commercial", "academic"], "1.2-9.6 kbps",
                  "Space operation (Earth-to-space) under RR 5.218, subject to agreement under RR No. 9.21; "
                  "individual transmissions within +/- 25 kHz. Shared with the mobile-satellite service "
                  "(Earth-to-space). Footnote wording to be confirmed against the RR in force.",
                  requires_itu_filing=True),

    # --- S-band (most common commercial CubeSat) ---
    FrequencyBand("S-band Uplink", "S", 2025.0, 2110.0, "uplink", "Space Operation / EESS",
                  ["experimental", "commercial", "academic"], "4-256 kbps",
                  "Common CubeSat TT&C uplink. Requires ITU API + national license.",
                  requires_itu_filing=True),
    FrequencyBand("S-band Downlink", "S", 2200.0, 2290.0, "downlink", "Space Operation / EESS",
                  ["experimental", "commercial", "academic"], "256 kbps - 10 Mbps",
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
    if license_type not in LICENSE_TYPES:
        raise ValueError(f"license_type must be one of {', '.join(LICENSE_TYPES)}")
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
            "coordination": coordination_for(band),
        })

    # Sort: suitable first, then by frequency
    results.sort(key=lambda r: (not r["suitable_for_data_rate"], r["freq_min_mhz"]))
    return results



def band_by_name(name: str) -> FrequencyBand | None:
    return next((b for b in FREQUENCY_BANDS if b.name == name), None)


def coordination_for(band: FrequencyBand) -> str:
    n = band.notes
    if "9.21" in n:
        return "agreement under RR No. 9.21"
    if band.service.startswith("Amateur"):
        return "IARU coordination"
    return "advance publication (RR No. 9.1) and notification" if band.requires_itu_filing else "none"


def service_for(freq_mhz: float, direction: str = "") -> dict[str, Any]:
    """ITU service, allocation and footnotes for a centre frequency (EG D9: derived from the band,
    never "amateur" or "meteorological aids" for the space-operation bands).

    ``direction`` is "space-to-Earth" or "Earth-to-space"; a band whose direction disagrees is
    skipped when another band covers the frequency."""
    want = "downlink" if direction.lower().startswith("space") else ("uplink" if direction else "")
    cands = [b for b in FREQUENCY_BANDS if b.freq_min_mhz <= freq_mhz <= b.freq_max_mhz]
    if want:
        cands = sorted(cands, key=lambda b: (b.direction not in (want, "both"), b.service.startswith("Amateur")))
    else:
        cands = sorted(cands, key=lambda b: b.service.startswith("Amateur"))
    if not cands:
        return {"service": "Not in the SpaceCDF catalogue: check the Table of Frequency Allocations",
                "allocation": "", "footnotes": [], "coordination": "to be determined", "band": None}
    b = cands[0]
    fn = re.findall(r"RR (5\.\d+[A-Z]?)", b.name + " " + b.notes)
    fn += [f"C{x}" for x in re.findall(r"footnote C(\d+)", b.notes)]
    return {"service": b.service, "allocation": f"{b.freq_min_mhz:g}-{b.freq_max_mhz:g} MHz",
            "footnotes": sorted(set(fn)), "coordination": coordination_for(b), "band": b.name}


def _validate_band(b: Any, i: int) -> dict:
    if not isinstance(b, dict):
        raise ValueError(f"frequency_bands[{i}] must be an object")
    try:
        lo, hi = float(b["freq_min_mhz"]), float(b["freq_max_mhz"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"frequency_bands[{i}] needs numeric freq_min_mhz and freq_max_mhz") from None
    if not (0 < lo < hi):
        raise ValueError(f"frequency_bands[{i}]: freq_min_mhz must be positive and below freq_max_mhz")
    if b.get("direction") not in (None, "uplink", "downlink", "both", "receive"):
        raise ValueError(f"frequency_bands[{i}].direction must be uplink, downlink, both or receive")
    return {**b, "freq_min_mhz": lo, "freq_max_mhz": hi}

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

    bands = [_validate_band(b, i) for i, b in enumerate(frequency_bands or [])]

    def _svc(b: dict) -> dict:
        centre = (b["freq_min_mhz"] + b["freq_max_mhz"]) / 2
        d = "space-to-Earth" if b.get("direction") == "downlink" else ("Earth-to-space" if b.get("direction") == "uplink" else "")
        return service_for(centre, d)

    services = sorted({_svc(b)["service"] for b in bands})

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
                "service_type": "; ".join(services) if services else "to be determined from the frequency assignments",
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
                    "service": _svc(b)["service"],
                    "footnotes": _svc(b)["footnotes"],
                    "coordination": _svc(b)["coordination"],
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
