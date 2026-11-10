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
from .ground_scheduler import (ContactWindow, GroundStation, OrbitParams, ScheduleResult, contact_statistics, parse_epoch,
                               parse_ltan_h, predict_contacts_j2, schedule_downlinks, sso_inclination_deg)

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
STATS_DAYS = 30.0                   # contact statistics: J2 propagation over 30 days ...
STATS_STEP_S = 10.0                 # ... at a 10 s step (W4.05 contact table: 5 s)

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


def _path_source(ctx: AnalysisContext, path: str) -> str:
    """Provenance label of a flat ``link.*`` path: the path itself when the model states it, or
    where ``analysis_context._derive_link`` took it from (the TT&C element or a link case)."""
    link = getattr(ctx, "link", None) or {}
    if path in (link.get("derived_paths") or ()):
        src = str(link.get("source") or "")
        return "ttc element" if src.startswith("ttc element") else (src or path)
    return path


def _link_inputs(ctx: AnalysisContext, warnings: list[str]) -> _LinkInputs:
    sc_class = str(getattr(getattr(ctx.study, "requirements", None), "spacecraft_class", "small") or "small").lower()
    d_freq, d_pow, _d_diam, d_gain = CLASS_LINK_DEFAULTS.get(sc_class, CLASS_LINK_DEFAULTS["small"])
    src: dict[str, str] = {}

    freq = _pick(ctx, "link.frequency_ghz", "link.downlink_frequency_ghz")
    if freq is not None:
        src["frequency"] = _path_source(ctx, "link.frequency_ghz")
    if freq is None:
        freq = _perf_num(ctx, "ttc", "frequency_ghz", "downlink_frequency_ghz")
        if freq is not None:
            src["frequency"] = "ttc element"
    if freq is None:
        freq = _band_to_ghz(_perf_str(ctx, "ttc", "frequency_band", "band", "rf_band"))
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
        src["tx_power"] = _path_source(ctx, "link.tx_power_w")
        if tx_power is None:
            tx_power = _perf_num(ctx, "ttc", "tx_power_w", "power_tx_w", "rf_power_w")
            src["tx_power"] = "ttc element"
        if tx_power is None:
            tx_power, src["tx_power"] = d_pow, f"class default ({sc_class})"
        gain = _pick(ctx, "link.tx_antenna_gain_dbi", "link.antenna_gain_dbi")
        src["tx_gain"] = _path_source(ctx, "link.tx_antenna_gain_dbi")
        if gain is None:
            gain = _perf_num(ctx, "ttc", "gain_dbi", "antenna_gain_dbi", "tx_antenna_gain_dbi")
            src["tx_gain"] = "ttc element"
        if gain is None:
            gain, src["tx_gain"] = d_gain, f"class default ({sc_class})"
        line = 1.0

    rate = _pick(ctx, "link.downlink_rate_bps")
    src["downlink_rate"] = _path_source(ctx, "link.downlink_rate_bps")
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


def _case_margin(c: dict) -> float | None:
    m = _num(c.get("margin_db"))
    return m if m is not None else _num((c.get("results") or {}).get("margin_db"))


def station_link_case(ctx: AnalysisContext, link: _LinkInputs, station_name: str) -> dict | None:
    """The stored downlink case that states this station's margin (integration, wave 2): a case
    in the link's band naming the station (else one for all sites), preferring the one at the
    operational transmit power and rate, then the design case's coding, then the design case,
    then display order. ``None`` when the study has no such case (the model margin is used)."""
    from ..routers.link_budgets import _station_matches
    cases = [c for c in (getattr(ctx, "link_cases", None) or [])
             if c.get("direction") == "downlink" and _case_margin(c) is not None
             and _num(c.get("frequency_mhz")) and _link_band(float(c["frequency_mhz"]) / 1000.0) == link.band
             and _station_matches(c.get("station") or "", station_name)]
    if not cases:
        return None
    design = next((c for c in (getattr(ctx, "link_cases", None) or [])
                   if c.get("direction") == "downlink" and c.get("is_design_case")), {})

    def close(a: Any, b: float) -> bool:
        a = _num(a)
        return a is not None and abs(a - b) <= 1e-6 * max(1.0, abs(b))

    def rank(c: dict) -> tuple:
        cs = (c.get("station") or "").strip().lower()
        return (0 if cs and not cs.startswith("all") else 1,
                0 if close(c.get("tx_power_w"), link.tx_power_w) else 1,
                0 if close(c.get("data_rate_bps"), link.downlink_bps) else 1,
                0 if (c.get("coding") or "") == (design.get("coding") or "") else 1,
                0 if c.get("is_design_case") else 1, c.get("order") or 0)
    return sorted(cases, key=rank)[0]


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


def _contact_minutes(orbit: OrbitParams, gs: GroundStation, rate_mbps: float, ltan_h: float | None = None,
                     epoch: tuple[int, int, int] | None = None) -> tuple[float, int]:
    """(minutes per day, passes per day rounded) of one station: J2 propagation over 30 days."""
    st = contact_statistics(orbit, [gs], days=STATS_DAYS, step_s=STATS_STEP_S, ltan_h=ltan_h, epoch=epoch)
    row = st.stations.get(gs.id) or {}
    return float(row.get("min_per_day") or 0.0), int(round(float(row.get("passes_per_day") or 0.0)))


def orbit_inputs(ctx: AnalysisContext) -> tuple[OrbitParams, float | None, tuple[int, int, int]]:
    """Orbit of the contact prediction, the LTAN (h) and the epoch (the launch date target)."""
    altitude = float(ctx.orbit.get("altitude_km") or 500.0)
    inc = _num(ctx.orbit.get("inclination_deg"))
    if inc is None:
        inc = sso_inclination_deg(altitude) if str(ctx.orbit.get("orbit_type") or "").lower() == "sso" else 97.4
    orbit = OrbitParams(altitude_km=altitude, inclination_deg=float(inc), period_s=float(ctx.orbit.get("period_s") or 0.0))
    req = getattr(ctx.study, "requirements", None)
    return orbit, parse_ltan_h(ctx.orbit.get("ltan")), parse_epoch(getattr(req, "launch_date_target", None))


def _is_control(s: dict) -> bool:
    role = str(s.get("role") or s.get("description") or "").lower()
    return bool(s.get("control") or s.get("mission_control")) or "mission control" in role or "control centre" in role


def _rate_from_transmitter(ctx: AnalysisContext, link: _LinkInputs, warnings: list[str]) -> None:
    """No link rate in the parameters: use the selected transmitter's rate (KB part / element)."""
    from . import mode_model as mm
    from .rule_inputs import kb_component, perf
    best = None
    for e in mm.proposal_units(ctx.elements):
        if mm.unit_class(e) != "transmitter":
            continue
        r = perf(e).get("data_rate_bps") or ((kb_component(e) or {}).get("performance") or {}).get("data_rate_bps")
        if isinstance(r, (int, float)) and r > 0 and (best is None or r > best[0]):
            best = (float(r), e.get("name"))
    if best:
        link.downlink_bps = best[0]
        link.source["downlink_rate"] = f"transmitter part ({best[1]})"
        warnings[:] = [w for w in warnings if "no downlink rate" not in w]


def network(ctx: AnalysisContext, warnings: list[str]) -> dict[str, Any]:
    """The ground network the downlink uses: link inputs, orbit, per-station rows (contact
    statistics and link margin) and the stations included (band carried, margin ≥ 0 dB)."""
    link = _link_inputs(ctx, warnings)
    if link.source.get("downlink_rate") == "fallback":
        _rate_from_transmitter(ctx, link, warnings)
    orbit, ltan_h, epoch = orbit_inputs(ctx)
    rows: list[dict] = []
    included: list[GroundStation] = []
    control: set[str] = set()
    picked = _pick_stations(ctx, warnings)
    gss = [station_to_ground_station(s, link.band) for s in picked]
    stats = contact_statistics(orbit, gss, days=STATS_DAYS, step_s=STATS_STEP_S, ltan_h=ltan_h, epoch=epoch) if gss else None
    for s, gs in zip(picked, gss):
        bands = [_band_key(str(b)) for b in (s.get("bands") or [gs.band])]
        st = (stats.stations.get(gs.id) if stats else None) or {}
        row = {"station_id": gs.id, "name": gs.name, "element_id": s.get("element_id"), "lat": gs.latitude_deg,
               "lon": gs.longitude_deg, "bands": bands, "antenna_m": gs.antenna_diameter_m,
               "min_elevation_deg": gs.min_elevation_deg, "contact_min_per_day": round(float(st.get("min_per_day") or 0.0), 2),
               "contacts_per_day": int(round(float(st.get("passes_per_day") or 0.0))),
               "passes_per_day": st.get("passes_per_day"), "mean_pass_min": st.get("mean_pass_min"),
               "max_pass_min": st.get("max_pass_min"), "passes_above_30deg_per_day": st.get("passes_above_30deg_per_day"),
               "margin_db": None, "g_t_db_k": _num(s.get("g_over_t_db_k")), "status": "ok", "reason": None,
               "control": _is_control(s)}
        if link.band not in bands:
            row["status"], row["reason"] = "excluded", f"no {link.band}-band ({'/'.join(bands)})"
        else:
            margin, g_t = _station_margin_db(link, gs, _num(s.get("g_over_t_db_k")), orbit.altitude_km,
                                             row["contact_min_per_day"] * 60.0)
            row["margin_db"], row["g_t_db_k"] = round(margin, 2), round(g_t, 2)
            row["margin_source"] = "station G/T model"
            case = station_link_case(ctx, link, gs.name)
            if case is not None:
                # the stored link case of this site (its noise temperature, losses and coding) is
                # the margin of record; the generic G/T model figure is kept beside it
                row["model_margin_db"] = row["margin_db"]
                margin = float(_case_margin(case))
                row["margin_db"] = round(margin, 2)
                row["margin_source"] = f"link_case:{case.get('name') or case.get('id')}"
            if margin < 0:
                row["status"], row["reason"] = "excluded", f"link margin {margin:.1f} dB < 0 dB at {link.downlink_bps / 1e6:.2f} Mbps"
            elif margin < MARGIN_WARN_DB:
                row["status"] = "low_margin"
            elif not row["contacts_per_day"] and not row["contact_min_per_day"]:
                row["status"], row["reason"] = "no_contact", "orbit never visible"
        if row["status"] != "excluded":
            included.append(gs)
            if row["control"]:
                control.add(gs.id)
        rows.append(row)
    if included and not control:
        control.add(included[0].id)          # the first station hosts mission control unless one says so
        for r in rows:
            r["control"] = r["station_id"] == included[0].id
    return {"link": link, "orbit": orbit, "ltan_h": ltan_h, "epoch": epoch, "rows": rows, "included": included,
            "control": control, "stats": stats}


def contact_table(ctx: AnalysisContext, warnings: list[str] | None = None, *, days: float = 30.0,
                  step_s: float = 5.0) -> dict[str, Any]:
    """W4.05: per station and union — minutes/day, passes/day, mean and maximum pass, longest
    gap, data per day at the information rate; plus the leave-one-out unions."""
    W = warnings if warnings is not None else []
    net = network(ctx, W)
    from .data_budget import framing as _framing
    info = net["link"].downlink_bps
    inc = net["included"]
    stats = contact_statistics(net["orbit"], inc, days=days, step_s=step_s, ltan_h=net["ltan_h"], epoch=net["epoch"]) if inc else None
    fr = _framing([], info)
    acq, avail, eff = fr["acquisition_s"], fr["availability"], fr["frame_efficiency"]

    def mb(min_day: float, windows_day: float) -> float:
        return max(0.0, (min_day - windows_day * acq / 60.0) * avail) * 60 * info * eff / 8e6

    stations = []
    for r in net["rows"]:
        st = (stats.stations.get(r["station_id"]) if stats else None) or {}
        stations.append({"id": r["station_id"], "name": r["name"], "lat": r["lat"], "lon": r["lon"], "status": r["status"],
                         "reason": r["reason"], "control": r["control"], "margin_db": r["margin_db"],
                         "min_per_day": st.get("min_per_day", 0.0), "passes_per_day": st.get("passes_per_day", 0.0),
                         "mean_pass_min": st.get("mean_pass_min", 0.0), "max_pass_min": st.get("max_pass_min", 0.0),
                         "passes_above_30deg_per_day": st.get("passes_above_30deg_per_day", 0.0),
                         "data_mb_per_day_alone": round(mb(st.get("min_per_day", 0.0), st.get("passes_per_day", 0.0)), 2)})
    union = dict(stats.union) if stats else {}
    if stats:
        union["data_mb_per_day"] = round(mb(union["min_per_day"], union["windows_per_day"]), 2)
    loo = []
    if stats and len(inc) > 1:
        for gs in inc:
            s2 = contact_statistics(net["orbit"], [g for g in inc if g.id != gs.id], days=days, step_s=step_s,
                                    ltan_h=net["ltan_h"], epoch=net["epoch"])
            loo.append({"without": gs.name, "union_min_per_day": s2.union["min_per_day"],
                        "windows_per_day": s2.union["windows_per_day"], "longest_gap_h": s2.union["longest_gap_h"],
                        "data_mb_per_day": round(mb(s2.union["min_per_day"], s2.union["windows_per_day"]), 2)})
    return {"stations": stations, "union": union, "leave_one_out": loo, "days": days, "step_s": step_s,
            "method": {"propagator": "J2 secular, circular", "ltan_h": net["ltan_h"] if net["ltan_h"] is not None else 22.5,
                       "epoch": list(net["epoch"]), "altitude_km": net["orbit"].altitude_km,
                       "inclination_deg": round(net["orbit"].inclination_deg, 3),
                       "information_rate_bps": round(info * eff, 1), "frame_efficiency": eff,
                       "acquisition_s": acq, "availability": avail},
            "link": {"band": net["link"].band, "rate_bps": info}, "warnings": W}


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


async def _hk_terms(ctx: AnalysisContext, net: dict) -> dict | None:
    """Stored HK (MB/day), acquisition per window and the share of the channel left for stored
    data, from the data budget — None when the study has no housekeeping SIDs."""
    try:
        from ..db import cdr_repo
        from . import data_budget as db_
        rows = await cdr_repo.list_rows(ctx.study_id)
        if not any(r.get("kind") == "hk" and not r.get("deleted_at") and r.get("status") != "rejected" for r in rows):
            return None
        modes = [db_._mode_dict(m) for m in db_.study_modes(ctx.elements)]
        res = db_.compute(rows, modes, contacts=net["stats"] if net["included"] else None, link_rate_bps=net["link"].downlink_bps,
                          period_s=ctx.orbit.get("period_s") or 5700.0,
                          stations=[{"id": g.id, "name": g.name, "lon": g.longitude_deg, "control": g.id in net["control"]}
                                    for g in net["included"]])
    except Exception:  # noqa: BLE001 — the analysis still runs on the payload alone
        logger.debug("data budget unavailable for %s", ctx.study_id, exc_info=True)
        return None
    fr = res["framing"]
    cap = res["capacity"]["capacity_mb_per_day"]
    rt = next((c["rt_hk_mb"] for c in res["cases"] if c["id"] == "C1"), 0.0)
    factor = fr["frame_efficiency"] * fr["availability"] * (max(0.0, cap - rt) / cap if cap else 1.0)
    return {"stored_mb_per_day": res["stored"]["mb_per_day"], "acquisition_s": fr["acquisition_s"],
            "payload_rate_factor": factor, "rt_hk_mb_per_day": rt, "capacity_mb_per_day": cap,
            "frame_efficiency": fr["frame_efficiency"], "availability": fr["availability"]}


# ── public entry ────────────────────────────────────────────────────────

async def run_ground_segment(ctx: AnalysisContext) -> AnalysisOutput:
    """Contacts, per-station link margins, downlink schedule and data closure
    over 24 h. Pure with respect to the model — the router publishes."""
    out = AnalysisOutput()
    W = out.warnings
    root = ctx.mission_root
    root_id = root["id"] if root else None

    net = network(ctx, W)
    link = net["link"]
    gen_gb, gen_src = _data_generated_gb_per_day(ctx, W)
    storage_gb = _storage_gb(ctx)
    rate_mbps = link.downlink_bps / 1e6
    orbit, ltan_h, epoch = net["orbit"], net["ltan_h"], net["epoch"]
    altitude = orbit.altitude_km
    rows = net["rows"]
    stations = rows
    included = net["included"]

    # Housekeeping and framing from the data budget when the study designs its TM (W3.03): stored HK
    # is generated data too; passes lose the acquisition time and the availability; the channel
    # carries frame data at the frame efficiency, minus the real-time HK of each pass.
    hk = await _hk_terms(ctx, net)
    acq_s = 0.0
    if hk:
        gen_gb += hk["stored_mb_per_day"] / 1000.0
        gen_src += f" + stored HK {hk['stored_mb_per_day']:.2f} MB/day (TM/TC SIDs)"
        rate_mbps = rate_mbps * hk["payload_rate_factor"]
        acq_s = hk["acquisition_s"]
    fill_mbps = gen_gb * 8000.0 / DAY_S
    buffer_mbit = storage_gb * 8000.0 if storage_gb else 1e12

    # Two days are scheduled and the *second* is reported, so the day starts
    # with the previous day's tail on board (steady state, not a cold start).
    all_contacts = _deconflict(predict_contacts_j2(orbit, included, 48.0, rate_mbps, ltan_h=ltan_h, epoch=epoch)) if included else []
    if acq_s:
        all_contacts = [ContactWindow(station_id=c.station_id, start_s=round(c.start_s + acq_s, 1), end_s=c.end_s,
                                      max_elevation_deg=c.max_elevation_deg, data_volume_mbit=c.data_volume_mbit)
                        for c in all_contacts if c.end_s - c.start_s > acq_s + 1.0]
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
    # Two different per-station volumes (integration, wave 2): what the greedy schedule of the
    # reported day actually routed through the station (shared with the other stations, overlaps
    # given to one) and what the station could return on its own (the W4.05 contact table's
    # "alone" figure: mean minutes x availability less acquisition, at the information rate).
    from .data_budget import framing as _framing
    fr = _framing([], link.downlink_bps)
    for r in rows:
        r["data_gb_per_day"] = round(per_station_data.get(r["station_id"], 0.0), 3)
        r["data_mb_per_day_scheduled"] = round(per_station_data.get(r["station_id"], 0.0) * 1000.0, 2)
        alone = 0.0
        if r["status"] != "excluded":
            alone = max(0.0, (float(r.get("contact_min_per_day") or 0.0) - float(r.get("passes_per_day") or 0.0)
                              * fr["acquisition_s"] / 60.0) * fr["availability"]) * 60 * link.downlink_bps \
                * fr["frame_efficiency"] / 8e6
        r["data_mb_per_day_alone"] = round(alone, 2)

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
            m, _n = _contact_minutes(orbit, station_to_ground_station(s, link.band), rate_mbps, ltan_h, epoch)
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
        "stations": rows, "union": dict(net["stats"].union) if net["stats"] else {},
        "housekeeping": hk, "backlog_growth_gb_per_day": round(growth, 4), "max_gap_hours": sched.max_gap_hours, "coverage_pct": sched.coverage_pct,
        "downlink_rate_mbps": round(rate_mbps, 4), "band": link.band, "frequency_ghz": link.frequency_ghz,
        "data_source": gen_src, "closure_pct": round(100.0 * returned_gb / gen_gb, 1) if gen_gb > 0 else 100.0,
        "conflict_codes": [c.code for c in C], "warnings": W,
    }
    return out
