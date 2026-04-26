"""SpaceCDF — TLE Generator for SMO orbit.yaml export.

Converts Keplerian orbital elements to Two-Line Element (TLE) format
for the SMO simulator's SGP4 propagator.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone


def compute_tle_checksum(line: str) -> int:
    """Compute TLE line checksum (modulo 10 sum of digits, '-' counts as 1)."""
    s = 0
    for ch in line[:68]:
        if ch.isdigit():
            s += int(ch)
        elif ch == '-':
            s += 1
    return s % 10


def keplerian_to_tle(
    altitude_km: float,
    inclination_deg: float,
    eccentricity: float = 0.0,
    raan_deg: float = 0.0,
    arg_perigee_deg: float = 0.0,
    mean_anomaly_deg: float = 0.0,
    epoch: datetime | None = None,
    norad_id: int = 99001,
    intl_designator: str = "26001A  ",
) -> tuple[str, str]:
    """Convert Keplerian elements to TLE lines.

    Args:
        altitude_km: Orbital altitude (assuming circular orbit, this is both a and p)
        inclination_deg: Orbital inclination
        eccentricity: Orbital eccentricity (0 for circular)
        raan_deg: Right Ascension of Ascending Node
        arg_perigee_deg: Argument of Perigee
        mean_anomaly_deg: Mean Anomaly at epoch
        epoch: TLE epoch (defaults to now)
        norad_id: NORAD catalog number
        intl_designator: International designator (8 chars)

    Returns:
        (tle_line1, tle_line2) as formatted strings
    """
    if epoch is None:
        epoch = datetime.now(timezone.utc)

    # Semi-major axis and mean motion
    R_EARTH = 6371.0  # km
    MU = 398600.4418  # km^3/s^2
    a_km = R_EARTH + altitude_km
    n_rad_s = math.sqrt(MU / a_km**3)
    n_rev_day = n_rad_s * 86400.0 / (2.0 * math.pi)

    # Epoch in TLE format: YYddd.dddddddd
    year_2digit = epoch.year % 100
    day_of_year = (epoch - datetime(epoch.year, 1, 1, tzinfo=timezone.utc)).total_seconds() / 86400.0 + 1.0
    epoch_str = f"{year_2digit:02d}{day_of_year:012.8f}"

    # --- Line 1 ---
    # Format: 1 NNNNNC NNNNNAAA NNNNN.NNNNNNNN +.NNNNNNNN +NNNNN-N +NNNNN-N N NNNNN
    line1_raw = (
        f"1 {norad_id:05d}U {intl_designator:8s} {epoch_str} "
        f" .00000100  00000-0  10000-4 0  999"
    )
    # Pad to 68 chars
    line1_raw = line1_raw.ljust(68)[:68]
    checksum1 = compute_tle_checksum(line1_raw)
    line1 = line1_raw + str(checksum1)

    # --- Line 2 ---
    # Format: 2 NNNNN NNN.NNNN NNN.NNNN NNNNNNN NNN.NNNN NNN.NNNN NN.NNNNNNNNNNNNNN
    ecc_str = f"{eccentricity:.7f}"[2:]  # Remove "0." prefix → 7 digits

    line2_raw = (
        f"2 {norad_id:05d} "
        f"{inclination_deg:8.4f} "
        f"{raan_deg:8.4f} "
        f"{ecc_str} "
        f"{arg_perigee_deg:8.4f} "
        f"{mean_anomaly_deg:8.4f} "
        f"{n_rev_day:11.8f}"
        f"    1"
    )
    line2_raw = line2_raw.ljust(68)[:68]
    checksum2 = compute_tle_checksum(line2_raw)
    line2 = line2_raw + str(checksum2)

    return line1, line2


def generate_orbit_yaml(
    altitude_km: float,
    inclination_deg: float,
    eccentricity: float = 0.0,
    raan_deg: float = 0.0,
    ground_stations: list[dict] | None = None,
    epoch: datetime | None = None,
) -> dict:
    """Generate complete orbit.yaml content for SMO."""
    if epoch is None:
        epoch = datetime.now(timezone.utc)

    line1, line2 = keplerian_to_tle(
        altitude_km=altitude_km,
        inclination_deg=inclination_deg,
        eccentricity=eccentricity,
        raan_deg=raan_deg,
        epoch=epoch,
    )

    gs_configs = []
    if ground_stations:
        for gs in ground_stations:
            gs_configs.append({
                "name": gs.get("name", "Station"),
                "lat_deg": gs.get("lat_deg", 78.23),
                "lon_deg": gs.get("lon_deg", 15.41),
                "alt_km": gs.get("alt_km", 0.0),
                "min_elevation_deg": gs.get("min_elevation_deg", 5.0),
            })
    else:
        # Default: Svalbard
        gs_configs.append({
            "name": "Svalbard",
            "lat_deg": 78.229,
            "lon_deg": 15.407,
            "alt_km": 0.458,
            "min_elevation_deg": 5.0,
        })

    return {
        "tle_line1": line1,
        "tle_line2": line2,
        "t0_epoch": epoch.isoformat(),
        "altitude_km": altitude_km,
        "inclination_deg": inclination_deg,
        "earth_radius_km": 6371.0,
        "ground_stations": gs_configs,
    }
