"""SpaceCDF — Ground Segment Scheduler (SCDF-221/222/223).

Predicts satellite-to-ground contact windows for LEO missions and
schedules downlink passes using a greedy buffer-fill strategy.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

R_EARTH_KM = 6371.0
DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi
SECONDS_PER_DAY = 86400.0


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class GroundStation:
    """Ground station definition."""
    id: str
    name: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float
    antenna_diameter_m: float
    min_elevation_deg: float = 5.0
    band: str = "X"


@dataclass
class ContactWindow:
    """A single predicted contact window."""
    station_id: str
    start_s: float
    end_s: float
    max_elevation_deg: float
    data_volume_mbit: float = 0.0

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass
class ScheduleResult:
    """Summary of a downlink schedule over 24 hours."""
    contacts: list[ContactWindow]
    total_contact_min_per_day: float
    total_data_volume_mbit: float
    max_gap_hours: float
    coverage_pct: float


# ---------------------------------------------------------------------------
# Default Station Catalogue
# ---------------------------------------------------------------------------

DEFAULT_STATIONS: list[GroundStation] = [
    GroundStation(
        id="svalbard",
        name="KSAT Svalbard (SvalSat)",
        latitude_deg=78.2,
        longitude_deg=15.4,
        elevation_m=450.0,
        antenna_diameter_m=13.0,
        min_elevation_deg=5.0,
        band="X",
    ),
    GroundStation(
        id="kiruna",
        name="ESA Kiruna",
        latitude_deg=67.9,
        longitude_deg=20.2,
        elevation_m=390.0,
        antenna_diameter_m=15.0,
        min_elevation_deg=5.0,
        band="S",
    ),
    GroundStation(
        id="weilheim",
        name="DLR Weilheim",
        latitude_deg=47.9,
        longitude_deg=11.1,
        elevation_m=560.0,
        antenna_diameter_m=15.0,
        min_elevation_deg=5.0,
        band="S",
    ),
    GroundStation(
        id="kourou",
        name="ESA Kourou",
        latitude_deg=5.2,
        longitude_deg=-52.8,
        elevation_m=10.0,
        antenna_diameter_m=15.0,
        min_elevation_deg=5.0,
        band="S",
    ),
    GroundStation(
        id="canberra",
        name="DSN Canberra",
        latitude_deg=-35.4,
        longitude_deg=149.0,
        elevation_m=680.0,
        antenna_diameter_m=34.0,
        min_elevation_deg=5.0,
        band="X",
    ),
]


# ---------------------------------------------------------------------------
# Orbit Parameters
# ---------------------------------------------------------------------------

@dataclass
class OrbitParams:
    """Simplified orbit parameters for contact prediction."""
    altitude_km: float = 600.0
    inclination_deg: float = 97.8
    period_s: float = 0.0  # auto-computed if 0

    def __post_init__(self) -> None:
        if self.period_s <= 0:
            # Kepler: T = 2pi * sqrt(a^3 / mu)
            mu = 398600.4418  # km^3/s^2
            a = R_EARTH_KM + self.altitude_km
            self.period_s = 2 * math.pi * math.sqrt(a**3 / mu)


# ---------------------------------------------------------------------------
# Contact Prediction
# ---------------------------------------------------------------------------

def _max_earth_central_angle(altitude_km: float, min_elevation_deg: float) -> float:
    """Maximum Earth central angle (rad) for visibility above min elevation."""
    # gamma_max = arccos(R_e * cos(el) / (R_e + h)) - el
    r = R_EARTH_KM
    h = altitude_km
    el_rad = min_elevation_deg * DEG2RAD
    cos_gamma = math.cos(el_rad) * r / (r + h)
    gamma = math.acos(min(1.0, cos_gamma)) - el_rad
    return gamma


def _station_latitude_overlap(
    station_lat_deg: float, inclination_deg: float, gamma_deg: float
) -> bool:
    """Check if a station can ever see a satellite with given inclination."""
    # Satellite ground track spans +/- inclination in latitude
    max_sat_lat = inclination_deg
    min_sat_lat = -inclination_deg
    # Station must be within gamma_deg of some ground track point
    effective_lat = abs(station_lat_deg)
    return effective_lat <= (max_sat_lat + gamma_deg)


def _contacts_per_day_estimate(
    station: GroundStation,
    orbit: OrbitParams,
    gamma_deg: float,
) -> float:
    """Estimate number of contacts per day for a station.

    Uses simplified geometric model: the fraction of orbits whose ascending
    node places the ground track within the station footprint.
    """
    # Number of orbits per day
    orbits_per_day = SECONDS_PER_DAY / orbit.period_s

    # Fraction of longitude range covered by station visibility cone
    # At station latitude, the longitude span visible is:
    cos_lat = math.cos(station.latitude_deg * DEG2RAD)
    if cos_lat < 0.01:
        cos_lat = 0.01
    lon_span_deg = 2 * gamma_deg / cos_lat  # effective longitude window

    # Probability of a given orbit passing through station cone
    # (ascending + descending nodes give two chances per orbit)
    p_pass = min(1.0, lon_span_deg / 360.0) * 2

    # For polar orbits at high-latitude stations, add bonus from pole convergence
    if abs(station.latitude_deg) > 60 and orbit.inclination_deg > 80:
        p_pass = min(1.0, p_pass * 1.8)

    return orbits_per_day * p_pass


def _contact_duration_s(
    orbit: OrbitParams, gamma_deg: float, max_elevation_deg: float
) -> float:
    """Approximate contact duration from visible arc fraction."""
    # Visible arc ≈ 2 * gamma / 360 * period (simplified)
    arc_fraction = (2 * gamma_deg) / 360.0
    duration = arc_fraction * orbit.period_s
    # Clamp to reasonable range (30s to period/4)
    return max(30.0, min(duration, orbit.period_s / 4.0))


def _estimate_max_elevation(gamma_deg: float, altitude_km: float) -> float:
    """Rough max elevation for a pass (average geometry)."""
    # Average pass peaks at roughly half the max possible elevation
    # Max elevation occurs when ground track passes directly overhead
    # Use 60% of (90 - half_gamma) as typical peak
    half_gamma = gamma_deg / 2.0
    return min(89.0, max(10.0, (90.0 - half_gamma) * 0.6))


def predict_contacts(
    orbit: OrbitParams,
    stations: list[GroundStation] | None = None,
    duration_hours: float = 24.0,
    downlink_rate_mbps: float = 100.0,
) -> list[ContactWindow]:
    """Predict contact windows over a time period.

    Parameters
    ----------
    orbit : OrbitParams
        Orbital parameters.
    stations : list[GroundStation] or None
        Ground stations to consider (defaults to DEFAULT_STATIONS).
    duration_hours : float
        Simulation duration in hours (default 24).
    downlink_rate_mbps : float
        Data rate during contact in Mbps.

    Returns
    -------
    list[ContactWindow]
        Predicted contact windows sorted by start time.
    """
    if stations is None:
        stations = DEFAULT_STATIONS

    gamma_rad = _max_earth_central_angle(orbit.altitude_km, 5.0)
    gamma_deg = gamma_rad * RAD2DEG

    total_seconds = duration_hours * 3600.0
    contacts: list[ContactWindow] = []

    for station in stations:
        # Check if station can ever see this orbit
        sta_gamma_rad = _max_earth_central_angle(
            orbit.altitude_km, station.min_elevation_deg
        )
        sta_gamma_deg = sta_gamma_rad * RAD2DEG

        if not _station_latitude_overlap(
            station.latitude_deg, orbit.inclination_deg, sta_gamma_deg
        ):
            continue

        # Estimate contacts per day
        cpd = _contacts_per_day_estimate(station, orbit, sta_gamma_deg)
        n_contacts = int(round(cpd * (duration_hours / 24.0)))

        if n_contacts <= 0:
            continue

        # Distribute contacts roughly evenly over the time window
        contact_dur = _contact_duration_s(orbit, sta_gamma_deg, 45.0)
        spacing = total_seconds / max(n_contacts, 1)

        # Offset based on station longitude to spread contacts
        offset = (station.longitude_deg % 360) / 360.0 * spacing * 0.5

        for i in range(n_contacts):
            start = offset + i * spacing
            if start + contact_dur > total_seconds:
                break
            max_el = _estimate_max_elevation(sta_gamma_deg, orbit.altitude_km)
            data_vol = (contact_dur * downlink_rate_mbps)  # Mbit

            contacts.append(ContactWindow(
                station_id=station.id,
                start_s=round(start, 1),
                end_s=round(start + contact_dur, 1),
                max_elevation_deg=round(max_el, 1),
                data_volume_mbit=round(data_vol, 1),
            ))

    # Sort by start time
    contacts.sort(key=lambda c: c.start_s)
    return contacts


# ---------------------------------------------------------------------------
# Multi-pass Scheduling
# ---------------------------------------------------------------------------

def schedule_downlinks(
    contacts: list[ContactWindow],
    data_rate_mbps: float = 100.0,
    buffer_size_mbit: float = 64000.0,
    fill_rate_mbps: float = 10.0,
    duration_hours: float = 24.0,
) -> ScheduleResult:
    """Greedy downlink scheduler.

    Fills the onboard data buffer at *fill_rate_mbps* (imaging/science)
    and empties it during scheduled contacts at *data_rate_mbps*.

    Parameters
    ----------
    contacts : list[ContactWindow]
        Available contact windows (from predict_contacts).
    data_rate_mbps : float
        Downlink data rate during contacts.
    buffer_size_mbit : float
        Onboard storage capacity in Mbit.
    fill_rate_mbps : float
        Rate at which data is generated onboard.
    duration_hours : float
        Total scheduling horizon in hours.

    Returns
    -------
    ScheduleResult
    """
    total_seconds = duration_hours * 3600.0

    # Sort contacts by start time
    sorted_contacts = sorted(contacts, key=lambda c: c.start_s)

    scheduled: list[ContactWindow] = []
    buffer_level = 0.0  # current buffer fill in Mbit
    last_contact_end = 0.0

    for contact in sorted_contacts:
        # Fill buffer from last event to start of this contact
        gap = contact.start_s - last_contact_end
        buffer_level = min(buffer_size_mbit, buffer_level + gap * fill_rate_mbps)

        if buffer_level > 0:
            # Schedule this contact — dump as much as possible
            duration = contact.duration_s
            max_dump = duration * data_rate_mbps
            actual_dump = min(buffer_level, max_dump)
            buffer_level -= actual_dump

            scheduled.append(ContactWindow(
                station_id=contact.station_id,
                start_s=contact.start_s,
                end_s=contact.end_s,
                max_elevation_deg=contact.max_elevation_deg,
                data_volume_mbit=round(actual_dump, 1),
            ))

        last_contact_end = contact.end_s

    # Compute metrics
    total_contact_s = sum(c.duration_s for c in scheduled)
    total_data = sum(c.data_volume_mbit for c in scheduled)

    # Max gap
    max_gap_s = 0.0
    prev_end = 0.0
    for c in scheduled:
        gap = c.start_s - prev_end
        max_gap_s = max(max_gap_s, gap)
        prev_end = c.end_s
    # Also check gap from last contact to end of day
    if scheduled:
        max_gap_s = max(max_gap_s, total_seconds - scheduled[-1].end_s)
    else:
        max_gap_s = total_seconds

    coverage_pct = (total_contact_s / total_seconds) * 100.0

    return ScheduleResult(
        contacts=scheduled,
        total_contact_min_per_day=round(total_contact_s / 60.0, 2),
        total_data_volume_mbit=round(total_data, 1),
        max_gap_hours=round(max_gap_s / 3600.0, 2),
        coverage_pct=round(coverage_pct, 3),
    )
