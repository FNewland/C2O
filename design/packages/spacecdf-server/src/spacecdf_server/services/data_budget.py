"""SpaceCDF — the data budget: the single source of the housekeeping and downlink numbers (W3, Nov 2026).

Housekeeping is modelled as PUS-C ST[03] structures (SIDs, CDR rows of kind ``hk``):

* each SID has a real-time collection interval per mode (``rt_period_by_mode``) and, when it is
  stored, a stored copy (``store_sid``) with its own interval per mode (``store_period_by_mode``)
  routed by ST[15] into a packet store (``store_id``); ``null`` = disabled in that mode;
* ``enabled: {realtime, stored}`` replaces ``enabled_at_boot`` (kept as the alias of realtime);
* ``diagnostic: true`` SIDs (e.g. the ADCS diagnostic SID) are left out of the routine budget and
  billed only when a campaign enables them; ``beacon: true`` is the bootloader lifeline;
* the packet size is the parameter list (``params`` inline with ``bits``, or ``parameter_ids``)
  plus the packet overhead of the database settings (23 B for full PUS-C).

The budget then takes the modes and their operational mix, the union of the ground contacts
(``ground_scheduler.contact_statistics``: overlapping passes count once — one transmitter), the
link framing (RS coding, transfer frame and SDLS overheads, acquisition per window, availability),
the service reports, the real-time profiles and the pass classes, and gives:

* real-time HK per mode and per profile (FULL / LEAN / BEACON) with the tier fit;
* stored HK per mode and per day over the mix; store fill and days held;
* the per-pass allocation (VC0 real-time → the VC the operators selected → the other), the day in
  the life and the 7-day backlog of the HK and payload stores;
* the daily closure: capacity against real-time HK + stored HK + science on the channel (science
  delivered after compression ÷ CFDP efficiency) + other, in named cases (C0 FULL on every pass,
  C1 per-pass profiles = the baseline, diagnostics campaign, commissioning day, a station out,
  the fallback rate, the product set uncompressed).

``compute(rows, modes, contacts, ...)`` is pure; ``for_study(study_id, scenario)`` loads the
study. The Modes data chain, the ground-segment analysis, the TM/TC checks, the Data budget page
and the export collector all read it, so they quote one set of numbers. When a study has no
``hk`` rows the budget falls back to ``mode_rules.yaml data.housekeeping_bps`` and says so
(``status: not_designed``).

MB = 10^6 bytes throughout.
"""
from __future__ import annotations

import math
import re
from typing import Any

from . import cdr_model as cm

DAY_S = 86400.0
MB = 8e6                      # bits per MB


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _slug(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


def defaults() -> dict[str, Any]:
    return cm.cfg()["data_budget"]


# ───────────────────────────────────────────────────────────── packets

def packet_overhead_bytes(settings: dict | None, c: dict | None = None) -> int:
    """Bytes per HK packet besides the parameters: the settings' value, else the layout
    (with or without message counter and destination id, CUC size, SID size, CRC)."""
    c = c or cm.cfg()
    st = settings or {}
    v = _num(st.get("packet_overhead_bytes"))
    if v is not None:
        return int(v)
    lay = dict(c["downlink_budget"].get("packet_layout") or {})
    for k in ("msg_counter", "destination_id", "time_bytes", "sid_bytes", "crc_bytes"):
        if _num(st.get(k)) is not None:
            lay[k] = st[k]
    if st.get("has_msg_counter") is False:
        lay["msg_counter"] = 0
    if st.get("has_destination_id") is False:
        lay["destination_id"] = 0
    if lay:
        return int(sum(int(_num(x) or 0) for x in lay.values()))
    return int(c["downlink_budget"]["packet_overhead_bytes"])


def overhead_breakdown(settings: dict | None, c: dict | None = None) -> dict[str, int]:
    c = c or cm.cfg()
    lay = dict(c["downlink_budget"].get("packet_layout") or {})
    for k in list(lay):
        if _num((settings or {}).get(k)) is not None:
            lay[k] = int((settings or {})[k])
    return {k: int(_num(v) or 0) for k, v in lay.items()}


def _body_bytes(h: dict, params_by_id: dict[Any, dict], c: dict) -> tuple[int, int]:
    """(body bytes, number of parameters) of a SID."""
    inline = h.get("params") or h.get("parameters")
    if isinstance(inline, list) and inline and isinstance(inline[0], dict):
        bits = 0
        for p in inline:
            b = _num(p.get("bits"))
            if b is None:
                b = 8 * float(c["types"]["bytes"].get(_type_name(p.get("type")), 2))
            bits += b
        return int(math.ceil(bits / 8.0)), len(inline)
    sizes = c["types"]["bytes"]
    ids = h.get("parameter_ids") or []
    body = 0
    for pid in ids:
        p = params_by_id.get(pid) or {}
        b = _num(p.get("bits"))
        body += int(math.ceil(b / 8.0)) if b is not None else int(sizes.get(p.get("type") or "uint16", 2))
    if not ids and _num(h.get("body_bytes")) is not None:
        return int(h["body_bytes"]), int(_num(h.get("n_parameters")) or 0)
    return body, len(ids)


def _type_name(t: Any) -> str:
    t = str(t or "uint16").lower()
    return {"u8": "uint8", "i8": "int8", "u16": "uint16", "i16": "int16", "u32": "uint32", "i32": "int32",
            "f32": "float32", "f64": "float64"}.get(t, t)


def enabled_of(h: dict) -> dict[str, bool]:
    en = h.get("enabled")
    if isinstance(en, dict):
        rt = en.get("realtime")
        st = en.get("stored")
    else:
        rt = st = None
    if rt is None:
        rt = bool(h.get("enabled_at_boot", True)) if "enabled_at_boot" in h else True
    if st is None:
        st = h.get("store_sid") is not None
    return {"realtime": bool(rt), "stored": bool(st)}


def mode_keys(m: dict) -> list[str]:
    """Keys a per-mode interval map may use for a mode: id, template key, kind, name slug."""
    out = [str(m.get("id") or "")]
    for k in (m.get("template_key"), m.get("key"), m.get("kind"), _slug(m.get("name"))):
        if k and str(k) not in out:
            out.append(str(k))
    return [k for k in out if k]


_MISSING = object()


def period_in(table: Any, m: dict, fallback: Any = _MISSING) -> float | None:
    """Interval (s) of a SID in mode ``m`` from a per-mode map; None = disabled. When the map
    says nothing about the mode, ``fallback`` (None when not given)."""
    if isinstance(table, dict):
        for k in mode_keys(m):
            if k in table:
                v = _num(table[k])
                return v if v and v > 0 else None
    if fallback is _MISSING:
        return None
    v = _num(fallback)
    return v if v and v > 0 else None


def sid_table(rows: list[dict], c: dict | None = None) -> tuple[list[dict], int]:
    """The SIDs of the study with their packet size and flags; ``(sids, overhead bytes)``."""
    c = c or cm.cfg()
    settings = cm.singleton(rows, "settings")
    ovh = packet_overhead_bytes(settings, c)
    params = {p.get("param_id"): p for p in cm.live_data(rows, "parameters")}
    out = []
    for h in cm.live_data(rows, "hk"):
        body, n = _body_bytes(h, params, c)
        explicit = _num(h.get("packet_bytes")) if not (h.get("params") or h.get("parameter_ids")) else None
        size = int(explicit) if explicit else ovh + body
        out.append({
            "row_id": h.get("_id"), "sid": h.get("sid"), "store_sid": h.get("store_sid"), "name": h.get("name"),
            "subsystem": h.get("subsystem"), "apid": h.get("apid"), "bytes": size, "body_bytes": body, "n_parameters": n,
            "diagnostic": bool(h.get("diagnostic")), "beacon": bool(h.get("beacon")), "enabled": enabled_of(h),
            "period_s": _num(h.get("period_s")), "rt_period_by_mode": h.get("rt_period_by_mode"),
            "store_period_by_mode": h.get("store_period_by_mode"), "store_id": h.get("store_id"),
            "auto_disable_s": _num(h.get("auto_disable_s")), "obcp": h.get("obcp"),
            "designed": isinstance(h.get("rt_period_by_mode"), dict) or h.get("store_sid") is not None,
        })
    out.sort(key=lambda s: (s["sid"] if isinstance(s["sid"], int) else 9999))
    return out, ovh


def rt_period(s: dict, m: dict) -> float | None:
    if isinstance(s.get("rt_period_by_mode"), dict):
        return period_in(s["rt_period_by_mode"], m, s.get("period_s") if not s["designed"] else None)
    return s.get("period_s") if (s.get("period_s") or 0) > 0 else None


def store_period(s: dict, m: dict) -> float | None:
    if s.get("store_sid") is None and not isinstance(s.get("store_period_by_mode"), dict):
        return None
    return period_in(s.get("store_period_by_mode"), m)


def _bps(size: int, period: float | None) -> float:
    return size * 8.0 / period if period else 0.0


# ───────────────────────────────────────────────────────────── modes and mix

MIX_KINDS = ("nominal", "imaging", "downlink")


def in_operational_mix(m: dict) -> bool:
    """Nominal, imaging and downlink modes, plus custom modes of the nominal phase that take a
    share of an orbit (0 < share < 1), e.g. an exploratory night acquisition mode."""
    f = _num(m.get("orbit_fraction")) or 0.0
    kind = m.get("kind") or "custom"
    if kind in MIX_KINDS:
        return f > 0
    return kind == "custom" and (m.get("phase") or "nominal") == "nominal" and 0 < f < 1


def operational_mix(modes: list[dict]) -> list[tuple[dict, float]]:
    mix = [(m, float(_num(m.get("orbit_fraction")) or 0.0)) for m in modes if in_operational_mix(m)]
    tot = sum(f for _, f in mix)
    return [(m, f / tot) for m, f in mix] if tot > 0 else []


def _contact_mode(modes: list[dict]) -> dict | None:
    return next((m for m in modes if m.get("kind") == "downlink"), None) or \
        next((m for m in modes if m.get("kind") == "nominal"), None) or (modes[0] if modes else None)


# ───────────────────────────────────────────────────────────── services, profiles, framing

def services(rows: list[dict], c: dict | None = None) -> dict[str, Any]:
    c = c or cm.cfg()
    d = cm.singleton(rows, "service_allowances") or defaults()["service_allowances"]
    s1, s5 = d.get("S1_verification") or {}, d.get("S5_events") or {}
    s9, s15 = d.get("S9_time_report") or {}, d.get("S15_store_status") or {}
    s1_ops = _num(s1.get("rt_bps_ops_pass")) or 0.0
    ratio = (_num(s1.get("tcs_per_dump_pass")) or 0.0) / (_num(s1.get("tcs_per_ops_pass")) or 1.0)
    s5_rt = _num(s5.get("rt_bps_typical"))
    if s5_rt is None:
        s5_rt = (_num(s5.get("packet_bytes")) or 0) * 8 * (_num(s5.get("rt_rate_per_s")) or 0)
    s5_burst = (_num(s5.get("packet_bytes")) or 0) * 8 * (_num(s5.get("burst_rate_per_s")) or 0)
    s9_rt = _num(s9.get("rt_bps"))
    if s9_rt is None:
        s9_rt = (_num(s9.get("packet_bytes")) or 0) * 8 / (_num(s9.get("interval_s")) or 1e9)
    s15_rt = _num(s15.get("rt_bps")) or 0.0
    ev_mb = _num(s5.get("stored_mb_per_day"))
    if ev_mb is None:
        ev_mb = (_num(s5.get("packet_bytes")) or 0) * (_num(s5.get("stored_per_day")) or 0) / 1e6
    return {"s1_ops_bps": s1_ops, "s1_dump_bps": s1_ops * ratio, "s5_bps": s5_rt, "s5_burst_bps": s5_burst,
            "s9_bps": s9_rt, "s15_bps": s15_rt, "events_mb_per_day": ev_mb,
            "ops_total_bps": s1_ops + s5_rt + s9_rt + s15_rt,
            "dump_total_bps": s1_ops * ratio + s5_rt + s9_rt + s15_rt, "source": d}


def framing(rows: list[dict], link_rate_bps: float, c: dict | None = None) -> dict[str, Any]:
    """Frame efficiency and information rate from the link framing row (or the defaults)."""
    row = cm.singleton(rows, "link_framing")
    f = {**defaults()["link_framing"], **{k: v for k, v in row.items() if not str(k).startswith("_")}}
    n, k_, il = _num(f.get("rs_n")) or 0, _num(f.get("rs_k")) or 0, _num(f.get("rs_interleave")) or 1
    frame = _num(f.get("frame_bytes")) or (k_ * il if k_ else 0)
    channel = (n * il if n else frame) + (_num(f.get("asm_bytes")) or 0)
    over = sum(_num(f.get(x)) or 0 for x in ("tf_header_bytes", "sdls_header_bytes", "sdls_mac_bytes", "ocf_bytes", "fecf_bytes"))
    data_field = max(0.0, frame - over)
    eff = data_field / channel if channel else float(cm.cfg()["downlink_budget"]["frame_efficiency"])
    return {"frame_bytes": frame, "channel_bytes_per_frame": channel, "data_field_bytes": data_field,
            "frame_efficiency": round(eff, 4), "raw_rate_bps": link_rate_bps, "information_rate_bps": round(link_rate_bps * eff, 1),
            "acquisition_s": _num(f.get("acquisition_s")) or 0.0, "availability": _num(f.get("availability")) or 1.0,
            "designed": bool(row), "inputs": {k: f.get(k) for k in ("rs_n", "rs_k", "rs_interleave", "asm_bytes", "tf_header_bytes",
                                                                    "sdls_header_bytes", "sdls_mac_bytes", "ocf_bytes", "fecf_bytes")}}


def _profile_rows(rows: list[dict]) -> list[dict]:
    got = cm.live_data(rows, "rt_profiles")
    return got or [dict(p) for p in defaults()["rt_profiles"]]


def profile_bps(p: dict, sids: list[dict], mode: dict | None, svc: dict) -> dict[str, float]:
    """Designed bit rate of a real-time profile in the contact mode (periodic SIDs + reports)."""
    routine = [s for s in sids if not s["diagnostic"] and not s["beacon"] and s["enabled"]["realtime"]]
    if p.get("beacon_only"):
        sids_bps = sum(_bps(s["bytes"], rt_period(s, mode) or s.get("period_s")) for s in sids if s["beacon"])
        return {"sids_bps": sids_bps, "services_bps": 0.0, "designed_bps": sids_bps}
    iv = p.get("intervals_s")
    if isinstance(iv, dict) and iv:
        tot = 0.0
        for s in routine:
            per = _num(iv.get(str(s["sid"]), iv.get(s["sid"]) if isinstance(s["sid"], int) else None))
            tot += _bps(s["bytes"], per)
        svc_bps = svc["dump_total_bps"]
    elif p.get("mode_intervals", True) and not p.get("interval_factor"):
        tot = sum(_bps(s["bytes"], rt_period(s, mode)) for s in routine) if mode else 0.0
        svc_bps = svc["ops_total_bps"]
    else:
        keep = set(p.get("keep_subsystems") or [])
        fac = _num(p.get("interval_factor")) or 1.0
        tot = 0.0
        for s in routine:
            if keep and s.get("subsystem") not in keep:
                continue
            per = rt_period(s, mode) if mode else s.get("period_s")
            tot += _bps(s["bytes"], per * fac if per else None)
        svc_bps = svc["dump_total_bps"]
    return {"sids_bps": tot, "services_bps": svc_bps, "designed_bps": tot + svc_bps}


# ───────────────────────────────────────────────────────────── contacts and passes

def _local_h(t_s: float, lon_deg: float) -> float:
    return ((t_s / 3600.0) + lon_deg / 15.0) % 24.0


def classify_windows(windows: list, days: float, classes: list[dict], control: set[str],
                     control_lon: float, overrides: dict | None = None) -> list[str]:
    """Pass class of every union window: OPS = per day and per local-time cluster, the
    highest-elevation window seen by a control station; SHORT < max_minutes; DUMP otherwise.
    ``overrides``: {window index: class name}."""
    by = {c.get("name"): c for c in classes}
    ops = by.get("OPS") or {}
    short = by.get("SHORT") or {}
    short_max = _num((short.get("rule") or {}).get("max_minutes")) or 3.0
    rule = ops.get("rule") or {}
    clusters = rule.get("clusters_local_h") or [[0, 24]]
    per = int(_num(rule.get("per_cluster")) or 1)
    out = ["SHORT" if w.duration_s / 60.0 < short_max else "DUMP" for w in windows]
    if ops:
        for d in range(int(math.ceil(days))):
            for lo, hi in clusters:
                cands = []
                for i, w in enumerate(windows):
                    if not (d * DAY_S <= w.start_s < (d + 1) * DAY_S):
                        continue
                    if control and not (set(w.stations) & control):
                        continue
                    h = _local_h(w.start_s, control_lon)
                    inside = lo <= h < hi if lo < hi else (h >= lo or h < hi)
                    if inside:
                        cands.append((w.max_elevation_deg, w.duration_s, i))
                for _el, _d, i in sorted(cands, reverse=True)[:per]:
                    out[i] = "OPS"
    for k, v in (overrides or {}).items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            continue
        if 0 <= i < len(out) and v in by:
            out[i] = v
    return out


# ───────────────────────────────────────────────────────────── science

def science(rows: list[dict], scenario: dict | None = None) -> dict[str, Any]:
    d = {**defaults()["payload_products"], **{k: v for k, v in cm.singleton(rows, "payload_products").items()
                                               if not str(k).startswith("_")}}
    sc = scenario or {}
    cr = _num(sc.get("compression_ratio")) or _num(d.get("compression_ratio")) or 1.0
    cfdp = _num(d.get("cfdp_efficiency")) or 1.0
    products = [p for p in d.get("products") or [] if isinstance(p, dict)]
    raw = sum((_num(p.get("mb_raw")) or 0) * (_num(p.get("per_day")) or 0) for p in products)
    target = _num(sc.get("science_mb_per_day")) if sc.get("science_mb_per_day") is not None else _num(d.get("science_mb_per_day"))
    basis = sc.get("basis") or ("target" if target is not None else "products")
    delivered = (target if basis == "target" and target is not None else raw / cr)
    needed = (raw / target) if (target and raw) else None
    return {"target_mb_per_day": target, "compression_ratio": cr, "cfdp_efficiency": cfdp, "basis": basis,
            "products": [{"name": p.get("name"), "mb_raw": _num(p.get("mb_raw")), "per_day": _num(p.get("per_day")),
                          "mb_per_day_raw": round((_num(p.get("mb_raw")) or 0) * (_num(p.get("per_day")) or 0), 3),
                          "priority": p.get("priority")} for p in products],
            "raw_mb_per_day": round(raw, 3), "after_compression_mb_per_day": round(raw / cr, 3) if raw else 0.0,
            "delivered_mb_per_day": round(delivered or 0.0, 3), "on_channel_mb_per_day": round((delivered or 0.0) / cfdp, 3),
            "compression_needed": round(needed, 3) if needed else None,
            "compression_ok": (cr + 1e-9 >= needed) if needed else None}


# ───────────────────────────────────────────────────────────── the budget

def compute(rows: list[dict], modes: list[dict], *, contacts=None, link_rate_bps: float, period_s: float,
            stations: list[dict] | None = None, tiers: list[dict] | None = None, scenario: dict | None = None,
            degraded: list[dict] | None = None, gate: str | None = None, fallback_hk_bps: float = 2000.0,
            utc_offset_h: float | None = None) -> dict[str, Any]:
    """The whole data budget (see the module docstring). ``contacts``: a
    ``ground_scheduler.ContactStatistics`` of the stations used (None = no contact plan);
    ``stations``: ``[{id, name, lon, control}]``; ``degraded``: ``[{station, union_min_per_day,
    windows_per_day}]`` leave-one-out unions; ``tiers``: rate tiers ``[{name, bps}]``."""
    c = cm.cfg()
    sc = dict(scenario or {})
    warnings: list[str] = []
    T = float(period_s or 5700.0)
    sids, ovh = sid_table(rows, c)
    designed = any(s["designed"] for s in sids)
    svc = services(rows, c)
    fr = framing(rows, float(sc.get("link_rate_bps") or link_rate_bps or 0.0), c)
    info = fr["information_rate_bps"]
    routine = [s for s in sids if not s["diagnostic"] and not s["beacon"]]
    diag = [s for s in sids if s["diagnostic"]]
    beacons = [s for s in sids if s["beacon"]]

    # ── per SID and per mode
    sid_rows = []
    for s in sids:
        rt_by = {m["id"]: rt_period(s, m) for m in modes}
        st_by = {m["id"]: store_period(s, m) for m in modes}
        sid_rows.append({**{k: v for k, v in s.items() if k not in ("rt_period_by_mode", "store_period_by_mode")},
                         "rt_period_by_mode": s.get("rt_period_by_mode"), "store_period_by_mode": s.get("store_period_by_mode"),
                         "rt_interval_by_mode": rt_by, "store_interval_by_mode": st_by,
                         "rt_bps_by_mode": {k: round(_bps(s["bytes"], v), 1) for k, v in rt_by.items()},
                         "store_bps_by_mode": {k: round(_bps(s["bytes"], v), 2) for k, v in st_by.items()}})
    mode_rows = []
    for m in modes:
        rt = sum(_bps(s["bytes"], rt_period(s, m)) for s in routine if s["enabled"]["realtime"])
        rt_b = sum(_bps(s["bytes"], rt_period(s, m)) for s in beacons if s["enabled"]["realtime"])
        rt_d = sum(_bps(s["bytes"], rt_period(s, m)) for s in diag)
        stv = sum(_bps(s["bytes"], store_period(s, m)) for s in routine if s["enabled"]["stored"])
        st_d = sum(_bps(s["bytes"], store_period(s, m)) for s in diag)
        if not sids:
            stv = fallback_hk_bps
        mode_rows.append({"id": m["id"], "name": m.get("name"), "kind": m.get("kind"), "orbit_fraction": m.get("orbit_fraction"),
                          "in_mix": in_operational_mix(m), "rt_bps": round(rt, 1), "rt_beacon_bps": round(rt_b, 1),
                          "rt_diag_bps": round(rt_d, 1), "store_bps": round(stv, 2), "store_diag_bps": round(st_d, 2),
                          "store_mb_per_day": round(stv * DAY_S / MB, 3)})
    by_mode = {r["id"]: r for r in mode_rows}
    mix = operational_mix(modes)
    if mix:
        store_mix_bps = sum(by_mode[m["id"]]["store_bps"] * f for m, f in mix)
    else:
        store_mix_bps = max((r["store_bps"] for r in mode_rows), default=(fallback_hk_bps if not sids else 0.0))
        if modes:
            warnings.append("no mode of the operational mix (nominal / imaging / downlink with a share of orbit): stored HK uses the largest mode rate")
    stored_mb = store_mix_bps * DAY_S / MB + (svc["events_mb_per_day"] if sids else 0.0)

    # ── real-time profiles
    cmode = _contact_mode(modes)
    profiles = []
    for p in _profile_rows(rows):
        b = profile_bps(p, sids, cmode, svc)
        alloc = _num(p.get("allocation_bps"))
        profiles.append({"name": p.get("name"), "description": p.get("description"), "designed_bps": round(b["designed_bps"], 1),
                         "sids_bps": round(b["sids_bps"], 1), "services_bps": round(b["services_bps"], 1),
                         "allocation_bps": alloc, "pass_bps": round(alloc if alloc else b["designed_bps"], 1),
                         "reserve_bps": round(alloc - b["designed_bps"], 1) if alloc else None})
    prof = {p["name"]: p for p in profiles}
    full = prof.get("FULL") or {"pass_bps": 0.0, "designed_bps": 0.0}
    lean = prof.get("LEAN") or full
    diag_rt_contact = sum(_bps(s["bytes"], rt_period(s, cmode)) for s in diag) if cmode else 0.0
    share = float(c["downlink_budget"]["hk_share_percent"]) / 100.0
    tier_list = [t for t in (tiers or []) if _num(t.get("bps"))]
    for p in profiles:
        p["tier_fit"] = [{"tier": t.get("name"), "bps": t["bps"], "hk_budget_bps": round(float(t["bps"]) * fr["frame_efficiency"] * share, 1),
                          "ok": p["pass_bps"] <= float(t["bps"]) * fr["frame_efficiency"] * share} for t in tier_list]

    # ── contacts, capacity
    acq, avail = fr["acquisition_s"], fr["availability"]
    st_list = stations or []
    control = {s["id"] for s in st_list if s.get("control")} or ({st_list[0]["id"]} if st_list else set())
    control_lon = next((float(s.get("lon") or 0.0) for s in st_list if s["id"] in control), 0.0)
    if utc_offset_h is None:
        utc_offset_h = round(control_lon / 15.0)
    windows = list(getattr(contacts, "windows", []) or [])
    days = float(getattr(contacts, "days", 1.0) or 1.0)
    pc_rows = cm.live_data(rows, "pass_classes") or [dict(p) for p in defaults()["pass_classes"]]
    plan = cm.singleton(rows, "pass_plan")
    classes = classify_windows(windows, days, pc_rows, control, control_lon)
    pc_by = {p.get("name"): p for p in pc_rows}

    def usable_s(w) -> float:
        return max(0.0, w.duration_s - acq)

    union_min = sum(w.duration_s for w in windows) / 60.0 / days if windows else 0.0
    usable_min = sum(usable_s(w) for w in windows) / 60.0 / days * avail if windows else 0.0
    cap_mb = usable_min * 60.0 * info / MB
    raw_mb = union_min * 60.0 * fr["raw_rate_bps"] / MB
    if not windows:
        warnings.append("no contact plan (no ground station or no visible pass): downlink capacity is 0")

    def bps_of_class(name: str) -> float:
        p = pc_by.get(name) or {}
        pr = prof.get(str(p.get("rt_profile") or "FULL").split()[0]) or full
        return float(pr["pass_bps"])

    per_class: dict[str, dict] = {}
    for w, k in zip(windows, classes):
        r = per_class.setdefault(k, {"name": k, "windows": 0, "usable_s": 0.0})
        r["windows"] += 1
        r["usable_s"] += usable_s(w)
    pass_rows = []
    for name, r in per_class.items():
        u_min = r["usable_s"] / 60.0 / days * avail
        p = pc_by.get(name) or {}
        pass_rows.append({"name": name, "per_day": round(r["windows"] / days, 2), "usable_min_per_day": round(u_min, 2),
                          "rt_profile": p.get("rt_profile"), "rt_bps": bps_of_class(name), "order": p.get("order") or ["VC2", "VC1"],
                          "rt_mb_per_day": round(bps_of_class(name) * u_min * 60 / MB, 3), "delayed_hk": p.get("delayed_hk")})
    ops_usable_min = sum(r["usable_min_per_day"] for r in pass_rows if r["name"] == "OPS")
    rt_c1 = sum(r["rt_mb_per_day"] for r in pass_rows)
    rt_c0 = full["pass_bps"] * usable_min * 60 / MB

    # ── science and the closure cases
    sci = science(rows, sc)
    sci_mb = sci["on_channel_mb_per_day"]
    diag_orbit_mb = sum(_bps(s["bytes"], store_period(s, cmode)) for s in diag) * T / MB if cmode else 0.0
    diag_campaign_mb = diag_rt_contact * ops_usable_min * 60 / MB + diag_orbit_mb
    comm = next((m for m in modes if m.get("kind") == "commissioning"), None)
    comm_extra = ((by_mode[comm["id"]]["store_bps"] - store_mix_bps) * DAY_S / MB) if comm else 0.0

    margin_need = _gate_margin(gate)

    def case(cid: str, label: dict, rt_mb: float, sci_ch: float, cap: float = cap_mb, other: float = 0.0) -> dict:
        dem = rt_mb + stored_mb + sci_ch + other
        mg = 100.0 * (cap - dem) / cap if cap > 0 else None
        return {"id": cid, "label": label, "capacity_mb": round(cap, 2), "rt_hk_mb": round(rt_mb, 2),
                "stored_hk_mb": round(stored_mb, 2), "science_mb": round(sci_ch, 2), "other_mb": round(other, 2),
                "demand_mb": round(dem, 2), "margin_pct": round(mg, 1) if mg is not None else None,
                "status": ("not_evaluated" if mg is None else "pass" if mg >= margin_need else "warn" if mg >= 0 else "fail")}

    cases = [
        case("C0", cm.bi("FULL real-time HK on every pass", "TM de servitude temps réel FULL à chaque passage"), rt_c0, sci_mb),
        case("C1", cm.bi("Per-pass profiles (FULL on operations passes, LEAN on the rest): baseline",
                         "Profils par passage (FULL aux passages d’exploitation, LEAN ailleurs) : référence"), rt_c1, sci_mb),
        case("C2", cm.bi("C1 + diagnostics campaign (real time on the operations passes + 1 orbit stored)",
                         "C1 + campagne de diagnostic (temps réel aux passages d’exploitation + 1 orbite stockée)"),
             rt_c1, sci_mb, other=diag_campaign_mb),
        case("C3", cm.bi("Commissioning day: no science, FULL and diagnostics on every pass, 2 orbits of diagnostics stored",
                         "Journée de recette : pas de science, FULL et diagnostic à chaque passage, 2 orbites de diagnostic stockées"),
             rt_c0 + diag_rt_contact * usable_min * 60 / MB, 0.0, other=2 * diag_orbit_mb + max(0.0, comm_extra)),
    ]
    for dg in degraded or []:
        u = max(0.0, (float(dg["union_min_per_day"]) - float(dg["windows_per_day"]) * acq / 60.0) * avail)
        cap_d = u * 60 * info / MB
        rt_d = (full["pass_bps"] * ops_usable_min + lean["pass_bps"] * max(0.0, u - ops_usable_min)) * 60 / MB
        cases.append(case(f"C4-{_slug(dg['station'])}", cm.bi(f"C1 with {dg['station']} out", f"C1 sans {dg['station']}"),
                          rt_d, sci_mb, cap=cap_d))
    lower = sorted([float(t["bps"]) for t in tier_list if 0 < float(t["bps"]) < fr["raw_rate_bps"]], reverse=True)
    if lower and lower[0] >= 4 * 1200:
        r2 = lower[0]
        cases.append(case("C5", cm.bi(f"C1 at the {r2 / 1000:g} kbit/s fallback rate", f"C1 au débit de repli de {r2 / 1000:g} kbit/s"),
                          rt_c1, sci_mb, cap=usable_min * 60 * r2 * fr["frame_efficiency"] / MB))
    if sci["raw_mb_per_day"]:
        cases.append(case("C6", cm.bi("C1 with the planned products uncompressed", "C1 avec les produits prévus non compressés"),
                          rt_c1, sci["raw_mb_per_day"] / sci["cfdp_efficiency"]))
    if sc:
        cases.append(case("SCENARIO", cm.bi("Scenario", "Scénario"), rt_c0 if sc.get("rt_policy") == "full_every_pass" else rt_c1,
                          sci_mb, other=float(_num(sc.get("other_mb")) or 0.0) + (diag_campaign_mb if sc.get("diagnostics") else 0.0)))
    closure = next(x for x in cases if x["id"] == ("SCENARIO" if sc else "C1"))
    fit10 = (cap_mb * (1 - margin_need / 100) - rt_c1 - stored_mb) * sci["cfdp_efficiency"] if cap_mb else 0.0

    # ── stores
    stores = _stores(rows, mode_rows, modes, store_mix_bps, svc, sids, T, sci)

    # ── day in the life and backlog
    dil = _day_in_the_life(windows, classes, days, usable_s, fr, prof, pc_by, stored_mb, plan, utc_offset_h, st_list,
                           sci["cfdp_efficiency"])
    backlog = _backlog(windows, classes, days, usable_s, fr, prof, pc_by, stored_mb, sci, avail, plan)

    return {
        "status": "designed" if designed else ("not_designed" if not sids else "legacy"),
        "hk_source": "hk_rows" if sids else "mode_rules.data.housekeeping_bps",
        "packet": {"overhead_bytes": ovh, "breakdown": overhead_breakdown(cm.singleton(rows, "settings"), c)},
        "sids": sid_rows, "modes": mode_rows,
        "mix": [{"mode_id": m["id"], "name": m.get("name"), "share": round(f, 4)} for m, f in mix],
        "services": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in svc.items() if k != "source"},
        "profiles": profiles,
        "realtime": {"contact_mode_id": (cmode or {}).get("id"), "full_designed_bps": full.get("designed_bps"),
                     "full_allocation_bps": full.get("allocation_bps"), "lean_bps": lean.get("designed_bps"),
                     "diag_bps": round(diag_rt_contact, 1),
                     "with_diag_bps": round((full.get("designed_bps") or 0) + diag_rt_contact, 1)},
        "stored": {"mix_bps": round(store_mix_bps, 2), "mb_per_day": round(stored_mb, 3),
                   "events_mb_per_day": round(svc["events_mb_per_day"], 4),
                   "diag_mb_per_orbit": round(diag_orbit_mb, 3)},
        "framing": fr,
        "contacts": {"days": days, "union_min_per_day": round(union_min, 2),
                     "windows_per_day": round(len(windows) / days, 2) if windows else 0.0,
                     "union": dict(getattr(contacts, "union", {}) or {}),
                     "stations": [{"id": k, **v} for k, v in (getattr(contacts, "stations", {}) or {}).items()]},
        "capacity": {"union_min_per_day": round(union_min, 2), "usable_min_per_day": round(usable_min, 2),
                     "raw_mb_per_day": round(raw_mb, 2), "capacity_mb_per_day": round(cap_mb, 2),
                     # wave 3 (3.H2): after the real-time HK of the passes (C1), and the allocatable share
                     "remaining_after_realtime_hk_mb_per_day": round(max(0.0, cap_mb - rt_c1), 2),
                     "allocatable_percent": _allocatable_pct(),
                     "allocatable_mb_per_day": round(cap_mb * _allocatable_pct() / 100.0, 2)},
        "science": {**sci, "largest_with_margin_mb_per_day": round(max(0.0, fit10), 2)},
        "pass_classes": pass_rows,
        "cases": cases, "closure": closure, "margin_required_percent": margin_need,
        "stores": stores, "day_in_the_life": dil, "backlog": backlog,
        "scenario": sc or None, "warnings": warnings,
    }


def _allocatable_pct() -> float:
    return float(_num(defaults().get("allocatable_percent")) or 90.0)


def _gate_margin(gate: str | None) -> float:
    m = defaults().get("daily_margin_percent") or {}
    return float(m.get(str(gate or "").lower(), m.get("default", 10)))


def _stores(rows, mode_rows, modes, store_mix_bps, svc, sids, T, sci) -> list[dict]:
    from .margin_policy import CONFIG as MP
    from . import rule_config as rc
    try:
        smargin = float(rc.load(MP)["data_handling"]["storage_margin_percent"]["value"])
    except Exception:  # noqa: BLE001
        smargin = 50.0
    min_days = float(defaults().get("min_store_days") or 7)
    got = cm.live_data(rows, "stores") or ([dict(s) for s in defaults()["stores"]] if sids else [])
    by_kind = {}
    for r in mode_rows:
        by_kind.setdefault(r["kind"], r)
    out = []
    for s in got:
        content = s.get("content") or {}
        size = _num(s.get("size_mb"))
        if size is None and _num(s.get("size_gb")) is not None:
            size = float(s["size_gb"]) * 1000.0
        row = {"id": s.get("id"), "name": s.get("name"), "size_mb": size, "circular": bool(s.get("circular")),
               "location": s.get("location"), "content": content, "fill_mb_per_day": {}, "days_held": {}, "_id": s.get("_id")}
        if content.get("stored_routine") or content.get("sids"):
            want = set(content.get("sids") or [])
            pick = [x for x in sids if x["enabled"]["stored"] and not x["diagnostic"]
                    and (not want or x.get("store_sid") in want or x.get("sid") in want)]
            rate = {m["id"]: sum(_bps(x["bytes"], store_period(x, m)) for x in pick) for m in modes}
            mix = operational_mix(modes)
            mix_bps = sum(rate[m["id"]] * f for m, f in mix) if mix else store_mix_bps
            fills = {"nominal_mix": mix_bps * DAY_S / MB}
            for k in ("leop", "commissioning", "safe", "survival"):
                if k in by_kind:
                    fills[k] = rate.get(by_kind[k]["id"], 0.0) * DAY_S / MB
            row["fill_mb_per_day"] = {k: round(v, 3) for k, v in fills.items()}
            row["days_held"] = {k: (round(size / v, 1) if v > 0 and size else None) for k, v in fills.items()}
            sizing = defaults().get("store_sizing_modes") or list(fills)
            worst = max((v for k, v in fills.items() if k in sizing), default=0.0)
            need = worst * min_days * (1 + smargin / 100)
            row["check"] = {"rule": "TMTC-STORE", "min_days": min_days, "worst_mb_per_day": round(worst, 3), "sizing_modes": sizing,
                            "need_mb": round(need, 2), "ok": (size or 0) >= need if worst > 0 else None,
                            "storage_margin_percent": smargin}
        elif 5 in (content.get("services") or []):
            ev = svc["events_mb_per_day"]
            row["fill_mb_per_day"] = {"nominal_mix": round(ev, 4)}
            row["days_held"] = {"nominal_mix": round(size / ev, 0) if ev and size else None}
        elif content.get("stored_diagnostic"):
            cm_ = _contact_mode(modes)
            per_orbit = sum(_bps(x["bytes"], store_period(x, cm_)) for x in sids if x["diagnostic"]) * T / MB if cm_ else 0.0
            row["fill_mb_per_orbit"] = round(per_orbit, 3)
            row["orbits_held"] = round(size / per_orbit, 1) if per_orbit and size else None
        elif content.get("payload") or str(s.get("name") or "").upper().startswith("PAYLOAD"):
            raw = sci["raw_mb_per_day"] or sci["delivered_mb_per_day"]
            row["fill_mb_per_day"] = {"nominal_mix": raw}
            row["days_held"] = {"nominal_mix": round(size / raw, 1) if raw and size else None}
        out.append(row)
    return out


def _day_in_the_life(windows, classes, days, usable_s, fr, prof, pc_by, stored_mb, plan, utc_offset_h, st_list,
                     cfdp: float = 1.0) -> dict:
    from .ground_scheduler import PassSlot, allocate_passes
    if not windows:
        return {"day_index": None, "windows": [], "totals": {}}
    nd = int(days)
    mean = sum(w.duration_s for w in windows) / days
    best = None
    for d in range(1, max(2, nd - 1)):
        lo, hi = d * DAY_S - utc_offset_h * 3600, (d + 1) * DAY_S - utc_offset_h * 3600
        tot = sum(w.duration_s for w in windows if lo <= w.start_s < hi)
        if best is None or abs(tot - mean) < best[0]:
            best = (abs(tot - mean), d, lo, hi)
    _, d, lo, hi = best
    idx = [i for i, w in enumerate(windows) if lo <= w.start_s < hi]
    ov = (plan or {}).get("overrides") or {}
    names = {s["id"]: s.get("name") or s["id"] for s in st_list}
    info = fr["information_rate_bps"]

    def p_of(k: str) -> dict:
        return pc_by.get(k) or {}

    def rt_of(k: str) -> float:
        return float((prof.get(str(p_of(k).get("rt_profile") or "FULL").split()[0]) or {"pass_bps": 0.0})["pass_bps"])
    # steady state: the delayed-HK queue is served from the previous day's start; payload always has data
    slots, meta = [], []
    for i, w in enumerate(windows):
        if not (lo - DAY_S <= w.start_s < hi):
            continue
        k = classes[i]
        o = ov.get(str(i - idx[0])) if i in idx else None
        if o and o.get("class") in pc_by:
            k = o["class"]
        p = pc_by.get(k) or {}
        order = tuple(p.get("order") or ("VC2", "VC1"))
        if o and o.get("first") in ("VC1", "VC2"):
            order = (o["first"], "VC2" if o["first"] == "VC1" else "VC1")
        pr = prof.get(str(p.get("rt_profile") or "FULL").split()[0]) or {"pass_bps": 0.0}
        slots.append(PassSlot(start_s=w.start_s, usable_s=usable_s(w), rt_bps=float(pr["pass_bps"]), order=order, label=str(i)))
        meta.append((i, k, order))
    res = allocate_passes(slots, info, {"VC1": stored_mb * MB / DAY_S, "VC2": 0.0},
                          initial_bits={"VC1": 0.0, "VC2": 1e15}, efficiency={"VC2": 1.0}, t0_s=lo - DAY_S)
    rows = []
    for (i, k, order), r in zip(meta, res["slots"]):
        if i not in idx:
            continue
        w = windows[i]
        t_loc = (w.start_s / 3600.0 + utc_offset_h) % 24
        rows.append({"index": i - idx[0], "start_s": round(w.start_s - lo, 1), "local": f"{int(t_loc):02d}:{int(round((t_loc % 1) * 60)) % 60:02d}",
                     "minutes": round(w.duration_s / 60, 1), "max_elevation_deg": w.max_elevation_deg,
                     "stations": [names.get(s, s) for s in w.stations], "class": k, "first_vc": order[0],
                     "usable_min": round(usable_s(w) / 60, 1), "channel_mb": round(r["capacity_bits"] / MB, 2),
                     "rt_hk_mb": round(r["sent_bits"].get("VC0", 0) / MB, 3), "delayed_hk_mb": round(r["sent_bits"].get("VC1", 0) / MB, 3),
                     "payload_mb": round(r["sent_bits"].get("VC2", 0) / MB * cfdp, 2),
                     "payload_channel_mb": round(r["sent_bits"].get("VC2", 0) / MB, 3),
                     "idle_mb": round(r["idle_bits"] / MB, 3), "rt_profile": str(p_of(k).get("rt_profile") or "FULL"),
                     "rt_bps": round(rt_of(k), 1), "order": list(order), "override": bool(ov.get(str(i - idx[0]))),
                     "above_30deg_min": w.min_above_30deg})
    tot = {k: round(sum(x[k] for x in rows), 2) for k in ("minutes", "usable_min", "channel_mb", "rt_hk_mb", "delayed_hk_mb", "payload_mb")}
    return {"day_index": d, "utc_offset_h": utc_offset_h, "windows": rows, "totals": tot,
            "after_availability": {k: round(tot[k] * fr["availability"], 2) for k in ("usable_min", "channel_mb", "payload_mb")}}


def _backlog(windows, classes, days, usable_s, fr, prof, pc_by, stored_mb, sci, avail, plan) -> dict:
    """End-of-day levels of the delayed-HK (VC1) and payload (VC2) queues over 7 days."""
    from .ground_scheduler import PassSlot, allocate_passes
    nd = min(7, int(days))
    if not windows or nd < 1:
        return {"days": [], "vc1_mb": [], "vc2_mb": []}
    slots = []
    for w, k in zip(windows, classes):
        if w.start_s >= nd * DAY_S:
            break
        p = pc_by.get(k) or {}
        pr = prof.get(str(p.get("rt_profile") or "FULL").split()[0]) or {"pass_bps": 0.0}
        slots.append(PassSlot(start_s=w.start_s, usable_s=usable_s(w) * avail, rt_bps=float(pr["pass_bps"]),
                              order=tuple(p.get("order") or ("VC2", "VC1"))))
    gen = {"VC1": stored_mb * MB / DAY_S, "VC2": sci["delivered_mb_per_day"] * MB / DAY_S}
    out1, out2 = [], []
    for d in range(1, nd + 1):
        res = allocate_passes([s for s in slots if s.start_s < d * DAY_S], fr["information_rate_bps"], gen,
                              horizon_s=d * DAY_S, efficiency={"VC2": sci["cfdp_efficiency"]})
        out1.append(round(res["levels_bits"]["VC1"] / MB, 3))
        out2.append(round(res["levels_bits"]["VC2"] / MB, 3))
    return {"days": list(range(1, nd + 1)), "vc1_mb": out1, "vc2_mb": out2,
            "growing": bool(out2 and out2[-1] > out2[0] + 0.5 * (sci["delivered_mb_per_day"] or 0))}


# ───────────────────────────────────────────────────────────── study loader

async def for_study(study_id: str, scenario: dict | None = None, *, days: float = 30.0, step_s: float = 10.0,
                    rows: list[dict] | None = None, include_degraded: bool = True, gate: str | None = None) -> dict[str, Any]:
    """The data budget of a stored study (CDR rows, modes, ground network, link). ``gate``: the
    margin-ladder step of the closure statuses (default: the study's current gate)."""
    from ..db import cdr_repo
    from .analysis_context import build_context
    rows = rows if rows is not None else await cdr_repo.list_rows(study_id)
    ctx = await build_context(study_id)
    return from_context(ctx, rows, scenario, days=days, step_s=step_s, include_degraded=include_degraded, gate=gate,
                        study_id=study_id)


def from_context(ctx, rows: list[dict], scenario: dict | None = None, *, days: float = 30.0, step_s: float = 10.0,
                 include_degraded: bool = True, gate: str | None = None, study_id: str | None = None) -> dict[str, Any]:
    """``for_study`` on an already loaded ``AnalysisContext`` and CDR rows (synchronous: the
    diagram builders call it)."""
    from . import ground_closure as gc
    from .ground_scheduler import contact_statistics
    from .mode_model import cfg as mode_cfg
    study_id = study_id or getattr(ctx, "study_id", None)
    warnings: list[str] = []
    net = gc.network(ctx, warnings)
    modes = [_mode_dict(m) for m in study_modes(ctx.elements)]
    stats = contact_statistics(net["orbit"], net["included"], days=days, step_s=step_s, ltan_h=net["ltan_h"],
                               epoch=net["epoch"]) if net["included"] else None
    degraded = []
    if include_degraded and len(net["included"]) > 1:
        for gs in net["included"]:
            rest = [g for g in net["included"] if g.id != gs.id]
            s2 = contact_statistics(net["orbit"], rest, days=days, step_s=step_s, ltan_h=net["ltan_h"], epoch=net["epoch"])
            degraded.append({"station": gs.name, "union_min_per_day": s2.union["min_per_day"],
                             "windows_per_day": s2.union["windows_per_day"], "longest_gap_h": s2.union["longest_gap_h"]})
        degraded.sort(key=lambda x: x["union_min_per_day"])
        degraded = degraded[:1]          # the worst single-station loss
    tiers = [{"name": t.get("name"), "bps": t.get("bps")} for t in cm.live_data(rows, "rate_tiers")]
    stations = [{"id": g.id, "name": g.name, "lon": g.longitude_deg, "control": g.id in net["control"]} for g in net["included"]]
    if gate is None:
        try:
            from ..routers.gates import study_margin_gate
            gate = study_margin_gate(ctx.study)
        except Exception:  # noqa: BLE001
            gate = None
    res = compute(rows, modes, contacts=stats, link_rate_bps=net["link"].downlink_bps, period_s=ctx.orbit.get("period_s") or 5700.0,
                  stations=stations, tiers=tiers, scenario=scenario, degraded=degraded, gate=gate,
                  fallback_hk_bps=float(mode_cfg()["data"]["housekeeping_bps"]["value"]))
    res["warnings"] = warnings + res["warnings"]
    res["link"] = {"band": net["link"].band, "rate_bps": net["link"].downlink_bps, "rate_source": net["link"].source.get("downlink_rate")}
    res["network"] = {"stations": net["rows"], "excluded": [r["name"] for r in net["rows"] if r["status"] == "excluded"],
                      "ltan_h": net["ltan_h"], "epoch": list(net["epoch"]),
                      "orbit": {"altitude_km": net["orbit"].altitude_km, "inclination_deg": net["orbit"].inclination_deg}}
    res["degraded"] = degraded
    res["study_id"] = study_id
    res["margin_gate"] = gate
    return res


# ───────────────────────────────────────────────────────────── downstream views (W3.05)

def ops_pass(b: dict) -> dict | None:
    """One real operations pass of the day in the life (the first OPS window of the day: the
    morning pass after the imaging), for the ``ops_pass`` diagram and the ConOps: duration,
    usable time, stations, real-time profile, VC order and the channel split VC0 / VC1 / VC2
    (MB on the channel and minutes at the information rate). ``None`` without a contact plan."""
    wins = (b.get("day_in_the_life") or {}).get("windows") or []
    if not wins:
        return None
    w = next((x for x in wins if x.get("class") == "OPS"), None) or max(wins, key=lambda x: x.get("usable_min") or 0)
    fr = b.get("framing") or {}
    info = float(fr.get("information_rate_bps") or 0.0)

    def mins(mb: float) -> float:
        return round(mb * MB / info / 60.0, 2) if info else 0.0
    vc0, vc1 = float(w.get("rt_hk_mb") or 0.0), float(w.get("delayed_hk_mb") or 0.0)
    vc2 = float(w.get("payload_channel_mb") if w.get("payload_channel_mb") is not None else (w.get("payload_mb") or 0.0))
    idle = float(w.get("idle_mb") or 0.0)
    order = list(w.get("order") or ["VC0", w.get("first_vc") or "VC1"])
    vcs = [{"vc": "VC0", "content": "real-time HK", "mb": round(vc0, 3), "min": mins(vc0)},
           {"vc": "VC1", "content": "delayed HK", "mb": round(vc1, 3), "min": mins(vc1)},
           {"vc": "VC2", "content": "payload files", "mb": round(vc2, 3), "min": mins(vc2), "delivered_mb": w.get("payload_mb")}]
    return {"index": w.get("index"), "local": w.get("local"), "class": w.get("class"), "minutes": w.get("minutes"),
            "usable_min": w.get("usable_min"), "acquisition_s": fr.get("acquisition_s"), "stations": w.get("stations") or [],
            "max_elevation_deg": w.get("max_elevation_deg"), "rt_profile": w.get("rt_profile"), "rt_bps": w.get("rt_bps"),
            "first_vc": w.get("first_vc"), "order": ["VC0", *[v for v in order if v != "VC0"]], "channel_mb": w.get("channel_mb"),
            "idle_mb": round(idle, 3), "information_rate_bps": info, "vcs": vcs,
            "rate_bps": (b.get("link") or {}).get("rate_bps"), "band": (b.get("link") or {}).get("band"),
            "utc_offset_h": (b.get("day_in_the_life") or {}).get("utc_offset_h")}


def gate_check(b: dict | None, gate: str | None) -> dict:
    """The PDR / CDR data-budget question (W3.05): does the daily budget (HK + science) close with
    the gate's margin in the diagnostics-campaign case (C2, else the closure case), and does every
    sized HK store hold ``min_store_days`` at its worst sizing rate?"""
    need = _gate_margin(gate)
    n_days = float(defaults().get("min_store_days") or 7)
    if not b:
        return {"gate": gate, "ok": None, "reason": "no data budget", "required_percent": need, "store_days": n_days}
    cases = {c["id"]: c for c in b.get("cases") or []}
    case = cases.get("C2") or b.get("closure") or {}
    mg = case.get("margin_pct")
    closes = None if mg is None else mg >= need
    stores = []
    for s in b.get("stores") or []:
        chk = s.get("check")
        if not chk:
            continue
        held = [v for k, v in (s.get("days_held") or {}).items() if k in (chk.get("sizing_modes") or []) and v is not None]
        stores.append({"name": s.get("name"), "size_mb": s.get("size_mb"), "days_held_worst": min(held) if held else None,
                       "need_mb": chk.get("need_mb"), "ok": chk.get("ok")})
    stores_ok = (all(x["ok"] is not False for x in stores) and any(x["ok"] for x in stores)) if stores else None
    ok = bool(closes) and bool(stores_ok)
    return {"gate": gate, "ok": ok if closes is not None else None, "case": case.get("id"), "margin_pct": mg,
            "required_percent": need, "closes": closes, "store_days": n_days, "stores": stores, "stores_ok": stores_ok,
            "status": b.get("status")}


def study_modes(elements: list[dict]) -> list[dict]:
    ms = [e for e in elements if e.get("element_type") == "mode" and not e.get("deleted_at")]

    def order(m: dict) -> float:
        o = (m.get("performance") or {}).get("order")
        return float(o) if isinstance(o, (int, float)) else 999.0
    return sorted(ms, key=lambda m: (order(m), m.get("name") or ""))


def _mode_dict(m: dict) -> dict:
    p = m.get("performance") or {}
    return {"id": m["id"], "name": m.get("name"), "kind": p.get("mode_kind") or "custom", "phase": p.get("phase") or "",
            "orbit_fraction": p.get("orbit_fraction"), "template_key": p.get("template_key"),
            "data_rate_bps": p.get("data_rate_bps")}


# ───────────────────────────────────────────────────────────── design-loop overlay (wave 3, 3.H1)

#: design-state paths the tier-1 agents read from the data budget (``AG/tier1/data.py``, ``link.py``)
DESIGN_PATHS = ("data.science_raw_mb_per_day", "data.science_delivered_mb_per_day", "data.science_on_channel_mb_per_day",
                "data.hk_stored_mb_per_day", "data.hk_realtime_mb_per_day", "data.capacity_mb_per_day",
                "data.demand_mb_per_day", "data.margin_pct", "data.compression_ratio", "link.frame_efficiency")


def design_overlay(b: dict | None) -> dict[str, float]:
    """The data budget as design-loop parameters (A1, data and link part): the science product set
    (raw, delivered after compression, on the channel), the housekeeping, the capacity of the union
    of the passes and the closure case. The design loop then compares the delivered science with
    the capacity instead of summing the payloads' acquired volumes (the "Phase 0 estimate").
    Empty when the study has no contact plan or no budget."""
    if not b:
        return {}
    cl = b.get("closure") or {}
    cap = b.get("capacity") or {}
    sci = b.get("science") or {}
    fr = b.get("framing") or {}
    st = b.get("stored") or {}
    vals = {
        "data.science_raw_mb_per_day": sci.get("raw_mb_per_day"),
        "data.science_delivered_mb_per_day": sci.get("delivered_mb_per_day"),
        "data.science_on_channel_mb_per_day": sci.get("on_channel_mb_per_day"),
        "data.hk_stored_mb_per_day": st.get("mb_per_day"),
        "data.hk_realtime_mb_per_day": cl.get("rt_hk_mb"),
        "data.capacity_mb_per_day": cap.get("capacity_mb_per_day") if cap.get("union_min_per_day") else None,
        "data.demand_mb_per_day": cl.get("demand_mb"),
        "data.margin_pct": cl.get("margin_pct"),
        "data.compression_ratio": sci.get("compression_ratio"),
        "link.frame_efficiency": fr.get("frame_efficiency") if fr.get("designed") else None,
    }
    out = {k: float(v) for k, v in vals.items() if _num(v) is not None}
    if "data.capacity_mb_per_day" not in out:          # no contact plan: the loop keeps its own estimate
        for k in ("data.capacity_mb_per_day", "data.demand_mb_per_day", "data.margin_pct"):
            out.pop(k, None)
    return out


async def design_overlay_for_study(study_id: str) -> dict[str, float]:
    """``design_overlay`` of a stored study (never raises: {} when the budget cannot be built)."""
    try:
        return design_overlay(await for_study(study_id, include_degraded=False))
    except Exception:  # noqa: BLE001
        return {}
