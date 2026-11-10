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
        # Fill buffer from last event to start of this contact, plus what is
        # generated during the contact itself (data is conserved: nothing is
        # lost when a window is skipped or overlaps the previous one).
        gap = max(0.0, contact.start_s - last_contact_end)
        duration = max(0.0, contact.end_s - max(contact.start_s, last_contact_end))
        buffer_level = min(buffer_size_mbit, buffer_level + (gap + duration) * fill_rate_mbps)

        if buffer_level > 0 and duration > 0:
            # Schedule this contact — dump as much as possible
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

        last_contact_end = max(last_contact_end, contact.end_s)

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


# ---------------------------------------------------------------------------
# J2 secular contact prediction (W3.01 / W4.05, Nov 2026)
# ---------------------------------------------------------------------------
# The geometric estimate above spreads an estimated number of passes evenly over the day. It is
# kept for the quick ground tools. Contact time, the union of overlapping passes and the per-pass
# downlink allocation use the propagation below: circular orbit, J2 secular rates (node, argument
# of latitude), Earth rotation from GMST, WGS-84 station positions, elevation mask per station.
# Same method as the teaching baseline's contact statistics (5 s step, 30 days).

J2_MU = 398600.4418          # km^3/s^2
J2_RE = 6378.137             # km (WGS-84 equatorial radius)
J2 = 1.08262668e-3
WGS84_F = 1 / 298.257223563
DAYS_PER_YEAR = 365.2421897
DEFAULT_EPOCH = (2030, 6, 1)  # contact statistics hardly depend on the epoch; a fixed default keeps them reproducible
DEFAULT_LTAN_H = 22.5


@dataclass
class UnionWindow:
    """One contact window of the network: the union of the overlapping station passes."""
    start_s: float
    end_s: float
    max_elevation_deg: float
    stations: list[str] = field(default_factory=list)       # station ids seeing the spacecraft in the window
    best_station: str = ""                                  # highest-elevation station (the one that uplinks)
    min_above_30deg: float = 0.0

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass
class ContactStatistics:
    days: float
    step_s: float
    stations: dict[str, dict]                # id -> {name, min_per_day, passes_per_day, mean_pass_min, max_pass_min, passes_above_30deg_per_day}
    union: dict                              # min_per_day, windows_per_day, mean/median/max window, longest_gap_h, ...
    windows: list[UnionWindow]
    station_windows: dict[str, list[ContactWindow]]


def sso_inclination_deg(altitude_km: float) -> float:
    a = J2_RE + altitude_km
    n = math.sqrt(J2_MU / a ** 3)
    req = 2 * math.pi / (DAYS_PER_YEAR * 86400)
    cosi = -req / (1.5 * n * J2 * (J2_RE / a) ** 2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosi))))


def _jd(y: int, mo: int, d: int, hr: float = 0.0) -> float:
    if mo <= 2:
        y -= 1
        mo += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (mo + 1)) + d + b - 1524.5 + hr / 24


def parse_ltan_h(v: Any) -> float | None:
    """LTAN as hours: 22.5, "22:30", "22h30" → 22.5; None when unknown."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v) % 24
    if isinstance(v, str):
        s = v.strip().lower().replace("h", ":")
        try:
            if ":" in s:
                hh, mm = s.split(":", 1)
                return (int(hh) + int((mm or "0")[:2]) / 60) % 24
            return float(s) % 24
        except ValueError:
            return None
    return None


def parse_epoch(v: Any) -> tuple[int, int, int]:
    """(y, m, d) from "2030-06", "2030-06-15", a date, else the default epoch."""
    try:
        if hasattr(v, "year"):
            return int(v.year), int(getattr(v, "month", 6)), int(getattr(v, "day", 1))
        if isinstance(v, str) and v[:4].isdigit():
            parts = [int(p) for p in v[:10].split("-") if p.isdigit()]
            return parts[0], (parts[1] if len(parts) > 1 else 6), (parts[2] if len(parts) > 2 else 1)
    except (ValueError, TypeError):
        pass
    return DEFAULT_EPOCH


def _elevations(altitude_km: float, inclination_deg: float, ltan_h: float, epoch: tuple[int, int, int],
                stations: list[GroundStation], days: float, step_s: float):
    import numpy as np
    jd0 = _jd(*epoch)
    t = np.arange(0.0, days * 86400.0, step_s)
    a = J2_RE + altitude_km
    n = math.sqrt(J2_MU / a ** 3)
    inc = math.radians(inclination_deg)
    k = 1.5 * J2 * (J2_RE / a) ** 2
    raan_dot = -k * n * math.cos(inc)
    u_dot = n * (1 + 0.5 * k * (3 * math.cos(inc) ** 2 - 1)) + 0.5 * k * n * (5 * math.cos(inc) ** 2 - 1)
    # node from the local time of the ascending node and the sun's right ascension at the epoch
    dn = jd0 - 2451545.0
    L = math.radians((280.460 + 0.9856474 * dn) % 360)
    g = math.radians((357.528 + 0.9856003 * dn) % 360)
    lam = L + math.radians(1.915) * math.sin(g) + math.radians(0.020) * math.sin(2 * g)
    eps = math.radians(23.439 - 4e-7 * dn)
    sun_ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    O = sun_ra + math.radians((ltan_h - 12) * 15) + raan_dot * t
    u = u_dot * t
    cO, sO, cu, su = np.cos(O), np.sin(O), np.cos(u), np.sin(u)
    ci, si = math.cos(inc), math.sin(inc)
    rx = a * (cO * cu - sO * su * ci)
    ry = a * (sO * cu + cO * su * ci)
    rz = a * (su * si)
    jd = jd0 + t / 86400.0
    th = np.radians((280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360)
    c, s = np.cos(th), np.sin(th)
    ex, ey = c * rx + s * ry, -s * rx + c * ry
    e2 = WGS84_F * (2 - WGS84_F)
    out = {}
    for st in stations:
        la, lo = math.radians(st.latitude_deg), math.radians(st.longitude_deg)
        N = J2_RE / math.sqrt(1 - e2 * math.sin(la) ** 2)
        h = st.elevation_m / 1000.0
        sx = (N + h) * math.cos(la) * math.cos(lo)
        sy = (N + h) * math.cos(la) * math.sin(lo)
        sz = (N * (1 - e2) + h) * math.sin(la)
        up = (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))
        dx, dy, dz = ex - sx, ey - sy, rz - sz
        rng = np.sqrt(dx * dx + dy * dy + dz * dz)
        out[st.id] = np.degrees(np.arcsin((dx * up[0] + dy * up[1] + dz * up[2]) / rng))
    return t, out


def _runs(mask) -> list[tuple[int, int]]:
    import numpy as np
    d = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    return list(zip(np.flatnonzero(d == 1).tolist(), np.flatnonzero(d == -1).tolist()))


_STATS_CACHE: dict[tuple, ContactStatistics] = {}


def contact_statistics(orbit: OrbitParams, stations: list[GroundStation], *, days: float = 30.0, step_s: float = 5.0,
                       ltan_h: float | None = None, epoch: tuple[int, int, int] | None = None,
                       downlink_rate_mbps: float = 0.0) -> ContactStatistics:
    """Per-station and union contact statistics over ``days`` (J2 secular circular propagation).

    The union is what one transmitter can use: overlapping passes of several stations count once.
    Results are cached by their inputs (the propagation of 30 days at 5 s takes about 0.3 s)."""
    import numpy as np
    ltan = DEFAULT_LTAN_H if ltan_h is None else float(ltan_h)
    ep = epoch or DEFAULT_EPOCH
    key = (round(orbit.altitude_km, 3), round(orbit.inclination_deg, 4), round(ltan, 4), ep, days, step_s,
           tuple((s.id, s.name, round(s.latitude_deg, 4), round(s.longitude_deg, 4), round(s.min_elevation_deg, 2),
                  round(s.elevation_m, 1)) for s in stations), round(downlink_rate_mbps, 6))
    hit = _STATS_CACHE.get(key)
    if hit is not None:
        return hit
    t, el = _elevations(orbit.altitude_km, orbit.inclination_deg, ltan, ep, stations, days, step_s)
    vis = {s.id: el[s.id] >= s.min_elevation_deg for s in stations}
    st_stats: dict[str, dict] = {}
    st_windows: dict[str, list[ContactWindow]] = {}
    for s in stations:
        runs = _runs(vis[s.id])
        durs = [(b - a) * step_s / 60.0 for a, b in runs]
        mx = [float(el[s.id][a:b].max()) for a, b in runs]
        st_windows[s.id] = [ContactWindow(station_id=s.id, start_s=float(t[a]), end_s=float(t[a]) + (b - a) * step_s,
                                          max_elevation_deg=round(m, 1),
                                          data_volume_mbit=round((b - a) * step_s * downlink_rate_mbps, 1))
                            for (a, b), m in zip(runs, mx)]
        st_stats[s.id] = {"name": s.name, "min_per_day": round(sum(durs) / days, 2),
                          "passes_per_day": round(len(runs) / days, 2),
                          "mean_pass_min": round(float(np.mean(durs)), 2) if durs else 0.0,
                          "max_pass_min": round(max(durs), 2) if durs else 0.0,
                          "passes_above_30deg_per_day": round(sum(1 for m in mx if m >= 30) / days, 2)}
    windows: list[UnionWindow] = []
    if stations:
        stack = np.stack([np.where(vis[s.id], el[s.id], -90.0) for s in stations])
        best = stack.max(axis=0)
        uni = best > -90.0
        for a, b in _runs(uni):
            seg = stack[:, a:b]
            seen = [s.id for i, s in enumerate(stations) if (seg[i] > -90.0).any()]
            bi = int(np.unravel_index(int(seg.argmax()), seg.shape)[0])
            windows.append(UnionWindow(start_s=float(t[a]), end_s=float(t[a]) + (b - a) * step_s,
                                       max_elevation_deg=round(float(best[a:b].max()), 1), stations=seen,
                                       best_station=stations[bi].id,
                                       min_above_30deg=round(float((best[a:b] >= 30).sum()) * step_s / 60.0, 2)))
    durs = [w.duration_s / 60.0 for w in windows]
    gaps = [(windows[i + 1].start_s - windows[i].end_s) / 3600.0 for i in range(len(windows) - 1)]
    daily = [sum(w.duration_s for w in windows if d * 86400 <= w.start_s < (d + 1) * 86400) / 60.0
             for d in range(int(days))]
    union = {
        "min_per_day": round(sum(durs) / days, 2),
        "sum_of_stations_min_per_day": round(sum(v["min_per_day"] for v in st_stats.values()), 2),
        "windows_per_day": round(len(windows) / days, 2),
        "mean_window_min": round(float(np.mean(durs)), 2) if durs else 0.0,
        "median_window_min": round(float(np.median(durs)), 2) if durs else 0.0,
        "min_window_min": round(min(durs), 2) if durs else 0.0,
        "max_window_min": round(max(durs), 2) if durs else 0.0,
        "windows_lt3min_per_day": round(sum(1 for x in durs if x < 3) / days, 2),
        "longest_gap_h": round(max(gaps), 2) if gaps else (days * 24.0 if not windows else 0.0),
        "daily_min_range": [round(min(daily), 1), round(max(daily), 1)] if daily else [0.0, 0.0],
        "min_above_30deg_per_day": round(sum(w.min_above_30deg for w in windows) / days, 2),
    }
    res = ContactStatistics(days=days, step_s=step_s, stations=st_stats, union=union, windows=windows,
                            station_windows=st_windows)
    if len(_STATS_CACHE) > 64:
        _STATS_CACHE.clear()
    _STATS_CACHE[key] = res
    return res


def predict_contacts_j2(orbit: OrbitParams, stations: list[GroundStation], duration_hours: float = 24.0,
                        downlink_rate_mbps: float = 0.0, *, ltan_h: float | None = None,
                        epoch: tuple[int, int, int] | None = None, step_s: float = 10.0) -> list[ContactWindow]:
    """Station passes over ``duration_hours`` (J2 propagation), sorted by start (same shape as
    ``predict_contacts``; passes of different stations may overlap)."""
    st = contact_statistics(orbit, stations, days=duration_hours / 24.0, step_s=step_s, ltan_h=ltan_h, epoch=epoch,
                            downlink_rate_mbps=downlink_rate_mbps)
    out = [c for ws in st.station_windows.values() for c in ws]
    out.sort(key=lambda c: (c.start_s, c.station_id))
    return out


# ---------------------------------------------------------------------------
# Multi-queue per-pass allocation (W3.03, Nov 2026)
# ---------------------------------------------------------------------------
# One transmitter, virtual channels served in strict priority per pass: VC0 (real-time HK and
# service reports, at the pass's real-time profile rate) first, then the virtual channel the
# operators selected for the pass (VC1 delayed HK and events, or VC2 payload files), then the
# other. Queues fill continuously at their generation rates and empty in passes.

@dataclass
class PassSlot:
    """A pass to serve: its usable information time, VC0 rate and the VC order after VC0."""
    start_s: float
    usable_s: float                  # after acquisition and availability
    rt_bps: float                    # VC0 load during the pass
    order: tuple[str, ...] = ("VC1", "VC2")
    label: str = ""


def allocate_passes(slots: list[PassSlot], info_rate_bps: float, gen_bps: dict[str, float],
                    initial_bits: dict[str, float] | None = None, horizon_s: float | None = None,
                    efficiency: dict[str, float] | None = None, t0_s: float = 0.0) -> dict[str, Any]:
    """Serve the queues pass by pass. ``gen_bps``: generation rate of each queue (VC1, VC2, …).
    ``efficiency``: per-queue extra efficiency on the channel (e.g. CFDP 0.96 for VC2: one bit
    of file data costs 1/0.96 channel bits). ``t0_s``: when the queues start filling from
    ``initial_bits`` (the slots of a day-in-the-life window do not start at 0). Returns per-slot
    allocations (bits) and the queue level at the end of every slot and at ``horizon_s``."""
    eff = efficiency or {}
    level = {q: float((initial_bits or {}).get(q, 0.0)) for q in gen_bps}
    last = float(t0_s)
    rows = []
    for s in sorted(slots, key=lambda x: x.start_s):
        dt = max(0.0, s.start_s - last)
        for q, r in gen_bps.items():
            level[q] += r * dt
        last = max(last, s.start_s)
        cap = info_rate_bps * s.usable_s
        rt = min(cap, s.rt_bps * s.usable_s)
        free = cap - rt
        sent: dict[str, float] = {"VC0": rt}
        for q in s.order:
            if q not in level:
                continue
            e = float(eff.get(q, 1.0)) or 1.0
            can = free * e
            take = min(level[q], can)
            level[q] -= take
            free -= take / e
            sent[q] = take
        rows.append({"start_s": s.start_s, "label": s.label, "usable_s": s.usable_s, "capacity_bits": cap,
                     "sent_bits": sent, "idle_bits": max(0.0, free), "levels_bits": dict(level)})
    if horizon_s is not None and horizon_s > last:
        for q, r in gen_bps.items():
            level[q] += r * (horizon_s - last)
    return {"slots": rows, "levels_bits": level}
