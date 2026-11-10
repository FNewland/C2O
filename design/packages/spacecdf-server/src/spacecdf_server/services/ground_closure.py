"""Ground segment closure (SCDF-174, design SCDF-170 §2.2).

Closes the *data return* loop for the study: which stations are selected,
how much contact they give the orbit, whether the TT&C link actually closes
at each of them, and whether the data the payload generates per day comes
down.

* stations from ``ctx.ground_stations`` (KB catalogue entries selected as
  ``segment='ground'`` elements with ``kb_component_id``; the element's
  ``performance_json`` may overlay ``lat`` / ``lon`` / ``g_over_t_db_k`` /
  ``min_elevation_deg`` / ``bands`` / ``antenna_m``). No selection → the
  KB stations flagged ``is_default`` / ``default``, else the first two of the
  catalogue, with a warning;
* per-station link margin via ``spacecdf_common.physics.link_budget`` with
  the study's TT&C parameters (``link.*`` flat / last-design values, TT&C /
  antenna element ``performance``, else the link agent's class defaults);
  the station ``g_over_t_db_k`` is honoured by deriving the system noise
  temperature that reproduces it with the station's dish size. A station
  whose margin is negative, or that does not carry the link band, is
  **excluded** (``GS_STATION_EXCLUDED``);
* contacts from ``ground_scheduler.predict_contacts`` (overlapping windows
  serialised — one station at a time), downlinks from ``schedule_downlinks``
  over 48 h with the **second day reported** so the day starts with the
  previous day's tail on board (steady state), with the data generation rate
  (``data.generated_per_day_gb``, else payload data rate x duty) and the
  downlink rate (``link.downlink_rate_bps`` / ``_mbps``, TT&C element, else
  2 Mbps with a warning).

Parameters on the mission root: ``gs_contact_min_per_day``,
``gs_contacts_per_day``, ``gs_data_return_gb_per_day``,
``gs_data_generated_gb_per_day``, ``gs_backlog_end_gb``,
``gs_min_link_margin_db``, ``gs_station_count``.

Conflicts: ``GS_DATA_DEFICIT`` (major — fix: minutes/day, rate, or the
catalogue station that adds the most contact), ``GS_LINK_MARGIN_LOW``
(warning, < 3 dB), ``GS_STATION_EXCLUDED`` (warning), ``GS_NO_STATIONS``
(major).

Public API:
    AnalysisOutput(parameters, conflicts, series, summary, warnings)
    run_ground_segment(ctx) -> AnalysisOutput
    station_to_ground_station(station) -> GroundStation
    OUTPUT_PARAMETERS, CONFLICT_CODES, ANALYSIS
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from spacecdf_common.physics.link_budget import compute_link_budget, frequency_band_name

from .analysis_context import AnalysisContext
from .analysis_results import ANALYSIS_INPUT_KEYS, Conflict, ParamWrite
from .ground_scheduler import ContactWindow, GroundStation, OrbitParams, ScheduleResult, predict_contacts, schedule_downlinks

logger = logging.getLogger(__name__)

ANALYSIS = "ground_segment"
ANALYSIS_INPUT_KEYS.setdefault(ANALYSIS, ANALYSIS_INPUT_KEYS.get("ground", ("elements", "params", "orbit", "stations")))

OUTPUT_PARAMETERS: tuple[str, ...] = (
    "gs_contact_min_per_day", "gs_contacts_per_day", "gs_data_return_gb_per_day",
    "gs_data_generated_gb_per_day", "gs_backlog_end_gb", "gs_min_link_margin_db", "gs_station_count",
)
CONFLICT_CODES: tuple[str, ...] = ("GS_DATA_DEFICIT", "GS_LINK_MARGIN_LOW", "GS_STATION_EXCLUDED", "GS_NO_STATIONS")

MARGIN_WARN_DB = 3.0                 # ECSS-E-ST-50C typical minimum
DAY_S = 86400.0
FALLBACK_DOWNLINK_BPS = 2e6          # same as mission_simulation
DEFAULT_FALLBACK_STATIONS = 2
BUFFER_TRACE_STEP_S = 60.0
DEFICIT_TOL_GB = 0.01
DEFICIT_TOL_FRAC = 0.05             # greedy scheduler + contact placement jitter between days

#: Link agent class defaults: (frequency_ghz, tx_power_w, gs_diameter_m, tx_gain_dbi).
CLASS_LINK_DEFAULTS: dict[str, tuple[float, float, float, float]] = {
    "nano": (8.2, 2.0, 13.0, 6.0),
    "micro": (8.2, 8.0, 13.0, 10.0),
    "small": (8.2, 5.0, 13.0, 10.0),
    "medium": (8.2, 10.0, 13.0, 15.0),
    "large": (26.0, 15.0, 13.0, 20.0),
    "flagship": (26.0, 15.0, 13.0, 20.0),
}
BAND_CENTRE_GHZ: dict[str, float] = {
    "VHF": 0.145, "UHF": 0.437, "L": 1.6, "S": 2.2, "C": 4.0, "X": 8.2, "KU": 12.0, "K": 20.0, "KA": 26.0,
}
GS_ANTENNA_EFFICIENCY = 0.55
GS_DEFAULT_NOISE_K = 200.0


@dataclass
class AnalysisOutput:
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    series: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class _LinkInputs:
    frequency_ghz: float
    tx_power_w: float
    tx_gain_dbi: float
    tx_line_loss_db: float
    downlink_bps: float
    band: str
    source: dict[str, str] = field(default_factory=dict)


# ── helpers ─────────────────────────────────────────────────────────────

def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _pick(ctx: AnalysisContext, *paths: str) -> float | None:
    """First numeric value among ``paths`` in ``flat`` then ``latest_design``."""
    for p in paths:
        v = _num(ctx.flat.get(p))
        if v is not None:
            return v
    for p in paths:
        entry = ctx.latest_design.get(p)
        v = _num(entry.get("value") if isinstance(entry, dict) else entry)
        if v is not None:
            return v
    return None


def _perf(e: dict | None) -> dict:
    if not e:
        return {}
    perf = e.get("performance_json") or e.get("performance") or {}
    return perf if isinstance(perf, dict) else {}


def _perf_num(ctx: AnalysisContext, domain: str, *keys: str) -> float | None:
    for e in ctx.elements:
        if e.get("subsystem_domain") != domain or (e.get("segment") or "space") != "space":
            continue
        p = _perf(e)
        for k in keys:
            v = _num(p.get(k))
            if v is not None:
                return v
    return None


def _perf_str(ctx: AnalysisContext, domain: str, *keys: str) -> str | None:
    for e in ctx.elements:
        if e.get("subsystem_domain") != domain:
            continue
        p = _perf(e)
        for k in keys:
            v = p.get(k) or e.get(k)
            if isinstance(v, str) and v:
                return v
    return None


def _band_to_ghz(band: str | None) -> float | None:
    if not band:
        return None
    key = band.upper().replace("-BAND", "").replace("BAND", "").strip().split("/")[0].strip()
    return BAND_CENTRE_GHZ.get(key)


def _band_key(band: str) -> str:
    return band.upper().replace("-BAND", "").replace("BAND", "").strip()


def _link_band(freq_ghz: float) -> str:
    """Band letter used in the KB station ``bands`` lists."""
    if 0.3 <= freq_ghz < 1.0:
        return "UHF"    # Nov 2026: 400-450 MHz CubeSat links (frequency_band_name calls them S)
    if 1.0 <= freq_ghz < 2.0:
        return "L"
    name = frequency_band_name(freq_ghz)
    return _band_key(name.split()[0]) if name else "X"


def _link_inputs(ctx: AnalysisContext, warnings: list[str]) -> _LinkInputs:
    sc_class = str(getattr(getattr(ctx.study, "requirements", None), "spacecraft_class", "small") or "small").lower()
    d_freq, d_pow, _d_diam, d_gain = CLASS_LINK_DEFAULTS.get(sc_class, CLASS_LINK_DEFAULTS["small"])
    src: dict[str, str] = {}

    freq = _pick(ctx, "link.frequency_ghz", "link.downlink_frequency_ghz")
    if freq is not None:
        src["frequency"] = "link.frequency_ghz"
    if freq is None:
        freq = _perf_num(ctx, "ttc", "frequency_ghz", "downlink_frequency_ghz")
        if freq is not None:
            src["frequency"] = "ttc element"
    if freq is None:
        freq = _band_to_ghz(_perf_str(ctx, "ttc", "frequency_band", "band"))
        if freq is not None:
            src["frequency"] = "ttc element band"
    if freq is None:
        freq, src["frequency"] = d_freq, f"class default ({sc_class})"

    eirp = _pick(ctx, "link.eirp_dbw", "link.downlink_eirp_dbw")
    if eirp is None:
        eirp = _perf_num(ctx, "ttc", "eirp_dbw")
    if eirp is not None:
        tx_power, gain, line = 10 ** (eirp / 10.0), 0.0, 0.0
        src["eirp"] = "link.eirp_dbw" if "link.eirp_dbw" in ctx.flat or "link.eirp_dbw" in ctx.latest_design else "ttc element"
    else:
        tx_power = _pick(ctx, "link.tx_power_w")
        src["tx_power"] = "link.tx_power_w"
        if tx_power is None:
            tx_power = _perf_num(ctx, "ttc", "tx_power_w", "power_tx_w", "rf_power_w")
            src["tx_power"] = "ttc element"
        if tx_power is None:
            tx_power, src["tx_power"] = d_pow, f"class default ({sc_class})"
        gain = _pick(ctx, "link.tx_antenna_gain_dbi", "link.antenna_gain_dbi")
        src["tx_gain"] = "link.tx_antenna_gain_dbi"
        if gain is None:
            gain = _perf_num(ctx, "ttc", "gain_dbi", "antenna_gain_dbi", "tx_antenna_gain_dbi")
            src["tx_gain"] = "ttc element"
        if gain is None:
            gain, src["tx_gain"] = d_gain, f"class default ({sc_class})"
        line = 1.0

    rate = _pick(ctx, "link.downlink_rate_bps")
    src["downlink_rate"] = "link.downlink_rate_bps"
    if rate is None:
        mbps = _pick(ctx, "link.downlink_rate_mbps", "link.data_rate_mbps")
        rate = mbps * 1e6 if mbps is not None else None
        src["downlink_rate"] = "link.downlink_rate_mbps"
    if rate is None:
        rate = _perf_num(ctx, "ttc", "downlink_rate_bps", "data_rate_bps")
        if rate is None:
            mbps = _perf_num(ctx, "ttc", "downlink_rate_mbps", "data_rate_mbps")
            rate = mbps * 1e6 if mbps is not None else None
        src["downlink_rate"] = "ttc element"
    if rate is None or rate <= 0:
        rate, src["downlink_rate"] = FALLBACK_DOWNLINK_BPS, "fallback"
        warnings.append(f"no downlink rate in the model (link.downlink_rate_bps); assumed {FALLBACK_DOWNLINK_BPS/1e6:.0f} Mbps")

    return _LinkInputs(frequency_ghz=float(freq), tx_power_w=float(tx_power), tx_gain_dbi=float(gain),
                       tx_line_loss_db=line, downlink_bps=float(rate), band=_link_band(float(freq)), source=src)


def _data_generated_gb_per_day(ctx: AnalysisContext, warnings: list[str]) -> tuple[float, str]:
    gb = _pick(ctx, "data.generated_per_day_gb")
    if gb is not None:
        return gb, "data.generated_per_day_gb"
    bps = _pick(ctx, "payload.data_rate_bps")
    if bps is None:
        mbps = _pick(ctx, "payload.data_rate_mbps", "payload.0.data_rate_mbps")
        bps = mbps * 1e6 if mbps is not None else None
    duty = None
    if bps is None:
        for e in ctx.elements:
            if e.get("subsystem_domain") != "payload":
                continue
            p = _perf(e)
            bps = _num(p.get("data_rate_bps")) or ((_num(p.get("data_rate_mbps")) or 0.0) * 1e6 or None)
            if bps is not None:
                duty = _num(p.get("duty_cycle_percent")) or ((_num(p.get("duty_cycle")) or 0.0) * 100 or None)
                break
    if bps is None:
        payloads = getattr(getattr(ctx.study, "requirements", None), "payloads", None) or []
        for pl in payloads:
            mbps = _num(getattr(pl, "data_rate_mbps", None))
            if mbps:
                bps = mbps * 1e6
                duty = _num(getattr(pl, "duty_cycle_percent", None))
                break
    if bps is None:
        warnings.append("no payload data rate in the model (data.generated_per_day_gb / payload data_rate_bps); assumed 0 GB/day")
        return 0.0, "none"
    if duty is None:
        pay_modes = [m for m in ctx.modes if m.payload_active and m.source != "default"]
        duty = min((m.duty_cycle_percent for m in pay_modes), default=100.0)
    duty = max(0.0, min(100.0, duty))
    return bps * DAY_S * duty / 100.0 / 8e9, f"payload data rate x {duty:.0f} % duty"


def _storage_gb(ctx: AnalysisContext) -> float | None:
    v = _pick(ctx, "data.storage_gb", "obc.storage_gb")
    if v is None:
        v = _perf_num(ctx, "obc", "storage_gb", "memory_gb") or _perf_num(ctx, "payload", "storage_gb")
    return v


def _station_overlay(ctx: AnalysisContext, station: dict) -> dict:
    """KB station dict with the selecting element's ``performance`` overlaid."""
    el = ctx.elements_by_id.get(station.get("element_id") or "")
    p = _perf(el)
    out = dict(station)
    for k in ("lat", "lon", "alt_m", "bands", "antenna_m", "min_elevation_deg", "g_over_t_db_k", "eirp_dbw", "name"):
        if p.get(k) is not None:
            out[k] = p[k]
    if isinstance(out.get("band"), str) and not out.get("bands"):
        out["bands"] = [out["band"]]
    return out


def station_to_ground_station(s: dict, link_band: str | None = None) -> GroundStation:
    bands = s.get("bands") or ([s["band"]] if s.get("band") else ["X"])
    band = link_band if link_band and link_band in [_band_key(str(b)) for b in bands] else str(bands[0])
    return GroundStation(
        id=str(s.get("id") or s.get("name")), name=str(s.get("name") or s.get("id")),
        latitude_deg=float(s.get("lat") or s.get("latitude_deg") or 0.0),
        longitude_deg=float(s.get("lon") or s.get("longitude_deg") or 0.0),
        elevation_m=float(s.get("alt_m") or s.get("elevation_m") or 0.0),
        antenna_diameter_m=float(s.get("antenna_m") or s.get("antenna_diameter_m") or 13.0),
        min_elevation_deg=float(s.get("min_elevation_deg") or 5.0), band=band,
    )


def _station_margin_db(link: _LinkInputs, gs: GroundStation, g_t_db_k: float | None, altitude_km: float,
                       contact_s: float) -> tuple[float, float]:
    """``(margin_db, G/T used)`` at the operational downlink rate, min elevation."""
    wavelength = 299792458.0 / (link.frequency_ghz * 1e9)
    gain_dbi = 10 * math.log10(GS_ANTENNA_EFFICIENCY * (math.pi * gs.antenna_diameter_m / wavelength) ** 2)
    if g_t_db_k is not None:
        noise_k = max(1.0, min(1e6, 10 ** ((gain_dbi - g_t_db_k) / 10.0)))
    else:
        noise_k = GS_DEFAULT_NOISE_K
        g_t_db_k = gain_dbi - 10 * math.log10(noise_k)
    lb = compute_link_budget(
        altitude_km=altitude_km, min_elevation_deg=gs.min_elevation_deg,
        tx_power_w=link.tx_power_w, tx_antenna_gain_dbi=link.tx_gain_dbi, tx_line_loss_db=link.tx_line_loss_db,
        frequency_ghz=link.frequency_ghz, gs_antenna_diameter_m=gs.antenna_diameter_m,
        gs_antenna_efficiency=GS_ANTENNA_EFFICIENCY, gs_system_noise_temp_k=noise_k,
        required_data_rate_bps=link.downlink_bps, contact_time_per_day_s=max(contact_s, 1.0), rain_rate_mm_hr=0.0,
    )
    return lb.downlink_margin_db, g_t_db_k


def _pick_stations(ctx: AnalysisContext, warnings: list[str]) -> list[dict]:
    if ctx.ground_stations:
        return [_station_overlay(ctx, s) for s in ctx.ground_stations]
    defaults = [s for s in ctx.all_kb_stations if s.get("is_default") or s.get("default")]
    if not defaults:
        defaults = list(ctx.all_kb_stations[:DEFAULT_FALLBACK_STATIONS])
    if defaults:
        warnings.append("no ground station selected for the study; using catalogue defaults: "
                        + ", ".join(str(s.get("name") or s.get("id")) for s in defaults))
    return [dict(s) for s in defaults]


def _contact_minutes(orbit: OrbitParams, gs: GroundStation, rate_mbps: float) -> tuple[float, int]:
    cs = predict_contacts(orbit, [gs], 24.0, rate_mbps)
    return sum(c.duration_s for c in cs) / 60.0, len(cs)


def _buffer_trace(contacts: list[ContactWindow], fill_mbps: float, buffer_mbit: float, rate_mbps: float,
                  horizon_s: float = DAY_S) -> tuple[list[float], list[float], float]:
    """Buffer level (GB) over ``horizon_s`` sampled every ``BUFFER_TRACE_STEP_S``,
    replaying ``schedule_downlinks``' greedy logic; returns ``(t_s, gb, end_gb)``."""
    t_s: list[float] = []
    gb: list[float] = []
    level = 0.0
    scheduled = sorted(contacts, key=lambda c: c.start_s)
    idx = 0
    t = 0.0
    while t <= horizon_s + 1e-6:
        in_contact = None
        while idx < len(scheduled) and scheduled[idx].end_s <= t:
            idx += 1
        for c in scheduled[idx:]:
            if c.start_s <= t < c.end_s:
                in_contact = c
                break
            if c.start_s > t:
                break
        level = min(buffer_mbit, level + fill_mbps * BUFFER_TRACE_STEP_S)
        if in_contact is not None:
            level = max(0.0, level - rate_mbps * BUFFER_TRACE_STEP_S)
        t_s.append(t)
        gb.append(round(level / 8000.0, 5))
        t += BUFFER_TRACE_STEP_S
    return t_s, gb, gb[-1] if gb else 0.0


def _deconflict(contacts: list[ContactWindow]) -> list[ContactWindow]:
    """Serialise overlapping windows (one TT&C chain: a single station at a
    time) — the later window starts when the earlier one ends; windows that
    vanish are dropped. ``schedule_downlinks`` needs non-overlapping input."""
    out: list[ContactWindow] = []
    end = -1.0
    for c in sorted(contacts, key=lambda c: (c.start_s, c.end_s)):
        start = max(c.start_s, end)
        if c.end_s - start < 30.0:
            continue
        out.append(ContactWindow(station_id=c.station_id, start_s=round(start, 1), end_s=c.end_s,
                                 max_elevation_deg=c.max_elevation_deg, data_volume_mbit=c.data_volume_mbit))
        end = c.end_s
    return out


def _shift(c: ContactWindow, by_s: float = DAY_S) -> ContactWindow:
    return ContactWindow(station_id=c.station_id, start_s=round(c.start_s - by_s, 1), end_s=round(c.end_s - by_s, 1),
                         max_elevation_deg=c.max_elevation_deg, data_volume_mbit=c.data_volume_mbit)


# ── public entry ────────────────────────────────────────────────────────

async def run_ground_segment(ctx: AnalysisContext) -> AnalysisOutput:
    """Contacts, per-station link margins, downlink schedule and data closure
    over 24 h. Pure with respect to the model — the router publishes."""
    out = AnalysisOutput()
    W = out.warnings
    root = ctx.mission_root
    root_id = root["id"] if root else None

    link = _link_inputs(ctx, W)
    gen_gb, gen_src = _data_generated_gb_per_day(ctx, W)
    storage_gb = _storage_gb(ctx)
    rate_mbps = link.downlink_bps / 1e6
    fill_mbps = gen_gb * 8000.0 / DAY_S
    buffer_mbit = storage_gb * 8000.0 if storage_gb else 1e12
    altitude = float(ctx.orbit.get("altitude_km") or 500.0)
    orbit = OrbitParams(altitude_km=altitude, inclination_deg=float(ctx.orbit.get("inclination_deg") or 97.4),
                        period_s=float(ctx.orbit.get("period_s") or 0.0))

    stations = _pick_stations(ctx, W)
    rows: list[dict] = []
    included: list[GroundStation] = []
    for s in stations:
        gs = station_to_ground_station(s, link.band)
        minutes, n = _contact_minutes(orbit, gs, rate_mbps)
        bands = [_band_key(str(b)) for b in (s.get("bands") or [gs.band])]
        row = {
            "station_id": gs.id, "name": gs.name, "element_id": s.get("element_id"), "lat": gs.latitude_deg,
            "lon": gs.longitude_deg, "bands": bands, "antenna_m": gs.antenna_diameter_m,
            "min_elevation_deg": gs.min_elevation_deg, "contacts_per_day": n, "contact_min_per_day": round(minutes, 2),
            "margin_db": None, "g_t_db_k": _num(s.get("g_over_t_db_k")), "status": "ok", "reason": None,
        }
        if link.band not in bands:
            row["status"], row["reason"] = "excluded", f"no {link.band}-band ({'/'.join(bands)})"
        else:
            margin, g_t = _station_margin_db(link, gs, _num(s.get("g_over_t_db_k")), altitude, minutes * 60.0)
            row["margin_db"], row["g_t_db_k"] = round(margin, 2), round(g_t, 2)
            if margin < 0:
                row["status"], row["reason"] = "excluded", f"link margin {margin:.1f} dB < 0 dB at {rate_mbps:.2f} Mbps"
            elif margin < MARGIN_WARN_DB:
                row["status"] = "low_margin"
            elif n == 0:
                row["status"], row["reason"] = "no_contact", "orbit never visible"
        if row["status"] != "excluded":
            included.append(gs)
        rows.append(row)

    # Two days are scheduled and the *second* is reported, so the day starts
    # with the previous day's tail on board (steady state, not a cold start).
    all_contacts = _deconflict(predict_contacts(orbit, included, 48.0, rate_mbps)) if included else []
    sched48 = schedule_downlinks(all_contacts, rate_mbps, buffer_mbit, fill_mbps, 48.0)
    t48, gb48, backlog_end = _buffer_trace(sched48.contacts, fill_mbps, buffer_mbit, rate_mbps, 2 * DAY_S)
    contacts = [_shift(c) for c in all_contacts if c.start_s >= DAY_S]
    sched_day = [_shift(c) for c in sched48.contacts if c.start_s >= DAY_S]
    total_min = sum(c.duration_s for c in contacts) / 60.0
    t_s = [round(t - DAY_S, 1) for t in t48 if t >= DAY_S]
    buf_gb = gb48[len(gb48) - len(t_s):]
    backlog_start = buf_gb[0] if buf_gb else 0.0
    returned_gb = sum(c.data_volume_mbit for c in sched_day) / 8000.0
    sched = ScheduleResult(contacts=sched_day, total_contact_min_per_day=round(sum(c.duration_s for c in sched_day) / 60.0, 2),
                           total_data_volume_mbit=round(returned_gb * 8000.0, 1),
                           max_gap_hours=sched48.max_gap_hours, coverage_pct=round(100.0 * total_min * 60.0 / DAY_S, 3))
    margins = [r["margin_db"] for r in rows if r["status"] != "excluded" and r["margin_db"] is not None]
    min_margin = min(margins) if margins else None
    by_id = {r["station_id"]: r for r in rows}
    per_station_data: dict[str, float] = {}
    for c in sched.contacts:
        per_station_data[c.station_id] = per_station_data.get(c.station_id, 0.0) + c.data_volume_mbit / 8000.0
    for r in rows:
        r["data_gb_per_day"] = round(per_station_data.get(r["station_id"], 0.0), 3)

    # ── parameters
    P = out.parameters
    P.append(ParamWrite("gs_contact_min_per_day", round(total_min, 2), unit="min", description="Available contact minutes per day over the included stations"))
    P.append(ParamWrite("gs_contacts_per_day", float(len(contacts)), unit="", description="Predicted contact windows per day"))
    P.append(ParamWrite("gs_data_return_gb_per_day", round(returned_gb, 4), unit="GB", description="Data downlinked per day (greedy schedule)"))
    P.append(ParamWrite("gs_data_generated_gb_per_day", round(gen_gb, 4), unit="GB", description=f"Data generated per day ({gen_src})"))
    P.append(ParamWrite("gs_backlog_end_gb", round(backlog_end, 4), unit="GB", description="On-board data left after 24 h"))
    P.append(ParamWrite("gs_min_link_margin_db", round(min_margin, 2) if min_margin is not None else -99.0, unit="dB", description="Lowest downlink margin over the included stations"))
    P.append(ParamWrite("gs_station_count", float(len(included)), unit="", description="Stations included in the schedule"))

    # ── conflicts
    C = out.conflicts
    if not stations:
        C.append(Conflict("major", "GS_NO_STATIONS", "No ground station",
                          "The study has no ground station and the catalogue is empty; no data can be returned.",
                          element_ids=[root_id] if root_id else [],
                          suggested_fix="Add a ground station to the study (POST /studies/{id}/ground-stations)."))
    elif not included:
        C.append(Conflict("major", "GS_NO_STATIONS", "No usable ground station",
                          "Every selected station is excluded: " + "; ".join(f"{r['name']}: {r['reason']}" for r in rows if r["reason"]),
                          element_ids=[r["element_id"] for r in rows if r["element_id"]] or ([root_id] if root_id else []),
                          suggested_fix=f"Select a station with {link.band}-band and adequate G/T, or raise EIRP / lower the downlink rate."))
    for r in rows:
        if r["status"] == "excluded":
            C.append(Conflict("warning", "GS_STATION_EXCLUDED", f"{r['name']} excluded", r["reason"] or "",
                              element_ids=[r["element_id"]] if r["element_id"] else [],
                              suggested_fix=f"Remove {r['name']} or change the link ({link.band}-band, {rate_mbps:.2f} Mbps, {link.tx_power_w:.1f} W) so it closes."))
    low = [r for r in rows if r["status"] == "low_margin"]
    if low:
        C.append(Conflict("warning", "GS_LINK_MARGIN_LOW", f"Link margin below {MARGIN_WARN_DB:.0f} dB",
                          ", ".join(f"{r['name']} {r['margin_db']:.1f} dB" for r in low),
                          element_ids=[r["element_id"] for r in low if r["element_id"]],
                          suggested_fix="Raise transmit power / antenna gain, lower the downlink rate, or pick a station with higher G/T."))
    deficit = gen_gb - returned_gb
    growth = backlog_end - backlog_start
    if included and gen_gb > 0 and (deficit > max(DEFICIT_TOL_GB, DEFICIT_TOL_FRAC * gen_gb) or growth > max(DEFICIT_TOL_GB, DEFICIT_TOL_FRAC * gen_gb)):
        fixes = []
        need_min = deficit * 8000.0 / (rate_mbps * 60.0) if rate_mbps > 0 else float("inf")
        fixes.append(f"add {need_min:.0f} min/day of contact")
        if total_min > 0:
            fixes.append(f"or raise the downlink rate to {gen_gb * 8000.0 / (total_min * 60.0) * 1.1:.2f} Mbps")
        selected_ids = {r["station_id"] for r in rows}
        best: tuple[float, str] | None = None
        for s in ctx.all_kb_stations:
            if s.get("id") in selected_ids:
                continue
            bands = [_band_key(str(b)) for b in (s.get("bands") or [])]
            if bands and link.band not in bands:
                continue
            m, _n = _contact_minutes(orbit, station_to_ground_station(s, link.band), rate_mbps)
            if best is None or m > best[0]:
                best = (m, str(s.get("name") or s.get("id")))
        if best and best[0] > 0:
            fixes.append(f"or add {best[1]} from the catalogue (+{best[0]:.0f} min/day)")
        C.append(Conflict("major", "GS_DATA_DEFICIT", "Data return below generation",
                          f"{returned_gb:.2f} GB/day returned against {gen_gb:.2f} GB/day generated "
                          f"({total_min:.0f} min/day of contact at {rate_mbps:.2f} Mbps); backlog grows by {growth:.2f} GB/day "
                          f"({backlog_end:.2f} GB on board at the end of the day).",
                          element_ids=[root_id] if root_id else [],
                          suggested_fix="; ".join(fixes)))

    # ── series / summary
    out.series = {
        "analysis": ANALYSIS, "duration_s": DAY_S,
        "contacts": [{"station_id": c.station_id, "station": by_id.get(c.station_id, {}).get("name", c.station_id),
                      "start_s": c.start_s, "end_s": c.end_s, "max_elevation_deg": c.max_elevation_deg,
                      "data_gb": round(next((s.data_volume_mbit for s in sched.contacts
                                             if s.station_id == c.station_id and s.start_s == c.start_s), 0.0) / 8000.0, 4)}
                     for c in contacts],
        "buffer": {"t_s": t_s, "gb": buf_gb},
        "stations": rows,
        "inputs": {
            "frequency_ghz": link.frequency_ghz, "band": link.band, "tx_power_w": round(link.tx_power_w, 3),
            "tx_gain_dbi": link.tx_gain_dbi, "downlink_rate_mbps": round(rate_mbps, 4),
            "data_generated_gb_per_day": round(gen_gb, 4), "data_source": gen_src, "storage_gb": storage_gb,
            "altitude_km": altitude, "inclination_deg": orbit.inclination_deg, "period_s": round(orbit.period_s, 1),
            "sources": link.source,
        },
    }
    out.summary = {
        **{p.name: p.value for p in P},
        "stations": rows, "backlog_growth_gb_per_day": round(growth, 4), "max_gap_hours": sched.max_gap_hours, "coverage_pct": sched.coverage_pct,
        "downlink_rate_mbps": round(rate_mbps, 4), "band": link.band, "frequency_ghz": link.frequency_ghz,
        "data_source": gen_src, "closure_pct": round(100.0 * returned_gb / gen_gb, 1) if gen_gb > 0 else 100.0,
        "conflict_codes": [c.code for c in C], "warnings": W,
    }
    return out
