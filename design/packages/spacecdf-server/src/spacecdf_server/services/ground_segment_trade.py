"""SpaceCDF — Ground Segment Architecture Trade.

First concrete decision support module. Given data volume, orbit, and
latency requirements, computes ground station network options with
downlink rates, RF subsystem implications, and total ops cost.

This is Decision 0.7 in the lifecycle framework.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroundStationOption:
    """A candidate ground station or network."""
    name: str
    provider: str
    type: str                    # commercial / dsn / estrack / university / satnogs
    latitude_deg: float
    longitude_deg: float
    antenna_diameter_m: float
    bands: list[str]             # S, X, Ka, UHF
    cost_per_pass_eur: float
    cost_per_month_eur: float
    availability: str            # on_demand / reserved / shared


# Pre-populated ground station database
_STATIONS: list[GroundStationOption] = [
    GroundStationOption("KSAT Svalbard (SvalSat)", "KSAT", "commercial", 78.2, 15.4, 13.0, ["S", "X", "Ka"], 150, 8000, "on_demand"),
    GroundStationOption("KSAT Troll", "KSAT", "commercial", -72.0, 2.5, 7.3, ["S", "X"], 150, 6000, "on_demand"),
    GroundStationOption("KSAT Inuvik", "KSAT", "commercial", 68.4, -133.7, 13.0, ["S", "X"], 150, 8000, "on_demand"),
    GroundStationOption("KSAT Puertollano", "KSAT", "commercial", 38.7, -4.1, 13.0, ["S", "X"], 120, 6000, "on_demand"),
    GroundStationOption("Leaf Space Leaf Line", "Leaf Space", "commercial", 45.0, 9.0, 3.7, ["S", "X", "UHF"], 80, 4000, "on_demand"),
    GroundStationOption("AWS Ground Station (Oregon)", "AWS", "commercial", 45.6, -121.2, 5.0, ["S", "X"], 100, 5000, "on_demand"),
    GroundStationOption("AWS Ground Station (Stockholm)", "AWS", "commercial", 59.3, 18.1, 5.0, ["S", "X"], 100, 5000, "on_demand"),
    GroundStationOption("SatNOGS Network (global)", "SatNOGS", "satnogs", 0, 0, 1.5, ["UHF", "S"], 0, 0, "shared"),
    GroundStationOption("ESA ESEC Redu", "ESA", "estrack", 50.0, 5.1, 13.5, ["S", "X"], 0, 15000, "reserved"),
    GroundStationOption("NASA DSN Goldstone", "NASA", "dsn", 35.4, -116.9, 34.0, ["S", "X", "Ka"], 0, 80000, "reserved"),
    GroundStationOption("University GS (typical)", "University", "university", 52.0, 0.0, 3.0, ["UHF", "S"], 0, 500, "shared"),
    GroundStationOption("D-Orbit ION relay", "D-Orbit", "commercial", 0, 0, 0, ["S", "X"], 200, 10000, "on_demand"),
]


@dataclass
class GroundSegmentAlternative:
    """A candidate ground segment architecture."""
    name: str
    description: str
    stations: list[str]           # Station names
    total_contact_min_per_day: float
    achievable_downlink_mbps: float
    data_downlinked_gb_per_day: float
    latency_hours: float
    annual_cost_keur: float
    requires_band: str
    rf_tx_power_w: float
    rf_antenna_gain_dbi: float
    rf_mass_kg: float
    rf_power_w: float
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    meets_data_need: bool = True
    meets_latency_need: bool = True


def compute_ground_segment_trade(
    orbit_altitude_km: float,
    orbit_inclination_deg: float,
    data_volume_gb_per_day: float,
    max_latency_hours: float = 24.0,
    spacecraft_class: str = "nano",
    orbit_type: str = "sso",
) -> dict[str, Any]:
    """Compute ground segment alternatives for a given mission.

    Returns structured trade study with scored alternatives.
    """
    # Estimate passes per station based on orbit and latitude
    is_polar = orbit_inclination_deg > 80

    alternatives: list[GroundSegmentAlternative] = []

    # Compute realistic contact time per station based on orbit geometry.
    # A polar station (78°N) sees every pass of a polar/SSO orbit (~4 passes/day, ~10 min each).
    # For lower-inclination orbits, polar stations see fewer / shorter passes.
    # Mid-latitude stations (~45-60°N) see more passes from mid-inclination orbits.
    def _contact_min(station_lat: float, n_stations: int = 1) -> float:
        """Estimate total contact min/day for n_stations at given latitude."""
        from spacecdf_common.physics.orbit import estimate_contact_time_per_day
        per_station_sec = estimate_contact_time_per_day(
            orbit_altitude_km, station_lat, orbit_inclination_deg,
        )
        # Multiple stations in different longitudes add roughly linearly
        # (diminishing returns if at similar longitudes)
        total_sec = per_station_sec * n_stations * 0.85  # 15% overlap discount
        return max(total_sec / 60, 0.5)  # At least 0.5 min if geometrically possible

    # --- Option 1: Single polar station (CubeSat default) ---
    contact_min_1 = _contact_min(78.0, 1)
    if contact_min_1 >= 1.0:  # Only offer if station actually gets contact
        dl_rate = _required_downlink_rate(data_volume_gb_per_day, contact_min_1 * 60, margin=1.2)
        band, tx_w, gain, mass, power = _rf_sizing(dl_rate, orbit_altitude_km, spacecraft_class)
        annual_cost = 12 * 8000  # KSAT Svalbard
        polar_pros = ["Simple operations", "Proven for CubeSats", "High-latitude = long passes"]
        polar_cons = ["Single point of failure"]
        if not is_polar:
            polar_cons.append(f"Only {contact_min_1:.0f} min/day contact for {orbit_inclination_deg:.0f}° orbit")
        else:
            polar_cons.extend(["Max 4 passes/day", "6-hour typical latency"])
        alternatives.append(GroundSegmentAlternative(
            name="Single polar station (KSAT Svalbard)",
            description="One high-latitude station. Best for SSO/polar orbits; reduced contact for lower inclinations.",
            stations=["KSAT Svalbard (SvalSat)"],
            total_contact_min_per_day=contact_min_1,
            achievable_downlink_mbps=dl_rate / 1e6,
            data_downlinked_gb_per_day=data_volume_gb_per_day,
            latency_hours=6.0 if is_polar else 12.0,
            annual_cost_keur=annual_cost / 1000,
            requires_band=band, rf_tx_power_w=tx_w, rf_antenna_gain_dbi=gain,
            rf_mass_kg=mass, rf_power_w=power,
            pros=polar_pros, cons=polar_cons,
            meets_data_need=True,
            meets_latency_need=(6.0 if is_polar else 12.0) <= max_latency_hours,
        ))

    # --- Option 2: Two-station network ---
    # Svalbard (78°N) + Inuvik (68°N) — both high-latitude
    contact_min_2 = _contact_min(78.0, 1) + _contact_min(68.0, 1)
    # For non-polar orbits, add a mid-latitude station instead of Inuvik
    if not is_polar:
        station_names_2 = ["KSAT Svalbard (SvalSat)", "KSAT Puertollano"]
        contact_min_2 = _contact_min(78.0, 1) + _contact_min(38.7, 1)
        desc_2 = "Polar + mid-latitude stations. Better coverage for non-polar orbits."
        name_2 = "Two-station network (Svalbard + Puertollano)"
    else:
        station_names_2 = ["KSAT Svalbard (SvalSat)", "KSAT Inuvik"]
        desc_2 = "Two polar stations for redundancy and more contact time."
        name_2 = "Two-station network (Svalbard + Inuvik)"
    dl_rate_2 = _required_downlink_rate(data_volume_gb_per_day, contact_min_2 * 60, margin=1.2)
    band_2, tx_w_2, gain_2, mass_2, power_2 = _rf_sizing(dl_rate_2, orbit_altitude_km, spacecraft_class)
    annual_cost_2 = 12 * (8000 + 6000)
    alternatives.append(GroundSegmentAlternative(
        name=name_2,
        description=desc_2,
        stations=station_names_2,
        total_contact_min_per_day=contact_min_2,
        achievable_downlink_mbps=dl_rate_2 / 1e6,
        data_downlinked_gb_per_day=data_volume_gb_per_day,
        latency_hours=4.0 if is_polar else 6.0,
        annual_cost_keur=annual_cost_2 / 1000,
        requires_band=band_2, rf_tx_power_w=tx_w_2, rf_antenna_gain_dbi=gain_2,
        rf_mass_kg=mass_2, rf_power_w=power_2,
        pros=["Redundancy", "More data capacity", f"{contact_min_2:.0f} min/day contact"],
        cons=["Double ground ops cost", "Two station contracts to manage"],
        meets_data_need=True,
        meets_latency_need=(4.0 if is_polar else 6.0) <= max_latency_hours,
    ))

    # --- Option 3: Commercial cloud ground (AWS/Leaf Space) ---
    # AWS stations at mid-latitudes (Oregon 45.6°N, Stockholm 59.3°N)
    contact_min_3 = _contact_min(45.6, 1) + _contact_min(59.3, 1)
    dl_rate_3 = _required_downlink_rate(data_volume_gb_per_day, contact_min_3 * 60, margin=1.3)
    band_3, tx_w_3, gain_3, mass_3, power_3 = _rf_sizing(dl_rate_3, orbit_altitude_km, spacecraft_class)
    annual_cost_3 = 12 * 5000
    alternatives.append(GroundSegmentAlternative(
        name="Cloud ground station (AWS GS / Leaf Space)",
        description="Commercial cloud-based ground stations. Pay-per-pass, global coverage.",
        stations=["AWS Ground Station (Oregon)", "AWS Ground Station (Stockholm)"],
        total_contact_min_per_day=contact_min_3,
        achievable_downlink_mbps=dl_rate_3 / 1e6,
        data_downlinked_gb_per_day=data_volume_gb_per_day,
        latency_hours=5.0,
        annual_cost_keur=annual_cost_3 / 1000,
        requires_band=band_3, rf_tx_power_w=tx_w_3, rf_antenna_gain_dbi=gain_3,
        rf_mass_kg=mass_3, rf_power_w=power_3,
        pros=["No station contract", "Global scalability", "API-driven scheduling",
              f"{contact_min_3:.0f} min/day from mid-latitude stations"],
        cons=["Smaller antennas", "Less established for CubeSats", "Internet latency"],
        meets_data_need=True,
        meets_latency_need=5.0 <= max_latency_hours,
    ))

    # --- Option 4: SatNOGS (free, community) ---
    if spacecraft_class == "nano" and data_volume_gb_per_day < 0.5:
        contact_min_4 = 8 * 5  # Many short passes
        dl_rate_4 = 9600  # UHF 9.6 kbps
        daily_data = dl_rate_4 * contact_min_4 * 60 / 8 / 1e9
        alternatives.append(GroundSegmentAlternative(
            name="SatNOGS community network (free)",
            description="Open-source distributed ground station network. Free but low data rate.",
            stations=["SatNOGS Network (global)"],
            total_contact_min_per_day=contact_min_4,
            achievable_downlink_mbps=dl_rate_4 / 1e6,
            data_downlinked_gb_per_day=daily_data,
            latency_hours=12.0,
            annual_cost_keur=0,
            requires_band="UHF", rf_tx_power_w=1.0, rf_antenna_gain_dbi=2.0,
            rf_mass_kg=0.2, rf_power_w=3.0,
            pros=["Zero cost", "Global coverage", "Community support", "Great for IOD/tech demo"],
            cons=["9.6 kbps only", "No SLA", "Not suitable for high-data missions"],
            meets_data_need=daily_data >= data_volume_gb_per_day,
            meets_latency_need=12.0 <= max_latency_hours,
        ))

    # --- Option 5: University ground station ---
    contact_min_5 = 2 * 8
    dl_rate_5 = _required_downlink_rate(min(data_volume_gb_per_day, 0.5), contact_min_5 * 60, margin=1.5)
    band_5, tx_w_5, gain_5, mass_5, power_5 = _rf_sizing(dl_rate_5, orbit_altitude_km, spacecraft_class)
    daily_data_5 = min(data_volume_gb_per_day, dl_rate_5 * contact_min_5 * 60 / 8 / 1e9)
    alternatives.append(GroundSegmentAlternative(
        name="University ground station (own)",
        description="Single university-owned station. Low cost but limited availability.",
        stations=["University GS (typical)"],
        total_contact_min_per_day=contact_min_5,
        achievable_downlink_mbps=dl_rate_5 / 1e6,
        data_downlinked_gb_per_day=daily_data_5,
        latency_hours=12.0,
        annual_cost_keur=6,
        requires_band=band_5, rf_tx_power_w=tx_w_5, rf_antenna_gain_dbi=gain_5,
        rf_mass_kg=mass_5, rf_power_w=power_5,
        pros=["Very low cost", "Educational value", "Full control"],
        cons=["2 passes/day", "Single point of failure", "Staffing dependent", "Limited data"],
        meets_data_need=daily_data_5 >= data_volume_gb_per_day * 0.8,
        meets_latency_need=12.0 <= max_latency_hours,
    ))

    # Score alternatives
    for alt in alternatives:
        alt_dict = {
            "name": alt.name,
            "description": alt.description,
            "stations": alt.stations,
            "contact_min_per_day": alt.total_contact_min_per_day,
            "downlink_mbps": alt.achievable_downlink_mbps,
            "data_gb_per_day": alt.data_downlinked_gb_per_day,
            "latency_hours": alt.latency_hours,
            "annual_cost_keur": alt.annual_cost_keur,
            "band": alt.requires_band,
            "rf_tx_power_w": alt.rf_tx_power_w,
            "rf_antenna_gain_dbi": alt.rf_antenna_gain_dbi,
            "rf_mass_kg": alt.rf_mass_kg,
            "rf_power_w": alt.rf_power_w,
            "pros": alt.pros,
            "cons": alt.cons,
            "meets_data_need": alt.meets_data_need,
            "meets_latency_need": alt.meets_latency_need,
        }

    return {
        "decision_id": "0.7",
        "question": "What ground segment architecture best serves the mission data needs within cost constraints?",
        "data_volume_gb_per_day": data_volume_gb_per_day,
        "max_latency_hours": max_latency_hours,
        "orbit_altitude_km": orbit_altitude_km,
        "alternatives": [
            {
                "name": a.name, "description": a.description,
                "stations": a.stations,
                "contact_min_per_day": a.total_contact_min_per_day,
                "downlink_mbps": round(a.achievable_downlink_mbps, 1),
                "data_gb_per_day": round(a.data_downlinked_gb_per_day, 2),
                "latency_hours": a.latency_hours,
                "annual_cost_keur": round(a.annual_cost_keur, 0),
                "band": a.requires_band,
                "rf_implications": {
                    "tx_power_w": round(a.rf_tx_power_w, 1),
                    "antenna_gain_dbi": round(a.rf_antenna_gain_dbi, 1),
                    "subsystem_mass_kg": round(a.rf_mass_kg, 2),
                    "subsystem_power_w": round(a.rf_power_w, 1),
                },
                "pros": a.pros, "cons": a.cons,
                "meets_data_need": a.meets_data_need,
                "meets_latency_need": a.meets_latency_need,
            }
            for a in alternatives
        ],
        "recommendation": _recommend(alternatives, data_volume_gb_per_day, max_latency_hours),
    }


def _required_downlink_rate(data_gb: float, contact_seconds: float, margin: float = 1.2) -> float:
    """Required downlink rate in bps to download data_gb in contact_seconds."""
    if contact_seconds <= 0:
        return 1e6
    return (data_gb * 8 * 1e9 * margin) / contact_seconds


def _rf_sizing(required_rate_bps: float, altitude_km: float, sc_class: str) -> tuple[str, float, float, float, float]:
    """Select band and size RF subsystem for the required data rate.
    Returns (band, tx_power_w, antenna_gain_dbi, mass_kg, power_w)."""
    if required_rate_bps < 100e3:
        return "UHF", 1.0, 2.0, 0.2, 3.0
    elif required_rate_bps < 5e6:
        return "S", 2.0, 6.0, 0.5, 11.0
    elif required_rate_bps < 50e6:
        return "X", 2.0 if sc_class == "nano" else 5.0, 8.0 if sc_class == "nano" else 12.0, 1.5, 15.0
    elif required_rate_bps < 200e6:
        return "X", 5.0, 15.0, 2.5, 25.0
    else:
        return "Ka", 10.0, 25.0, 3.5, 40.0


def _recommend(alternatives: list[GroundSegmentAlternative], data_need: float, latency_need: float) -> str:
    """Simple recommendation based on which alternatives meet requirements at lowest cost."""
    viable = [a for a in alternatives if a.meets_data_need and a.meets_latency_need]
    if not viable:
        return "No alternative meets both data volume and latency requirements — consider onboard processing to reduce data volume."
    cheapest = min(viable, key=lambda a: a.annual_cost_keur)
    return f"Recommended: {cheapest.name} — meets requirements at lowest annual cost ({cheapest.annual_cost_keur:.0f} kEUR/year)"
