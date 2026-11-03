"""Per-subsystem TRUTH views for the instructor console (tick thread only).

Each builder reads the simulator's own state — model internals, not
telemetry — and returns a JSON-safe dict the console draws as a picture
(INSTRUCTOR_CONSOLE_DESIGN.md §6). Nothing here is ever added to
``_build_state_summary()``: that document crosses the space link to the
ground and is served to student consoles.
"""
from __future__ import annotations

import math
from typing import Any, Optional

from . import divergence as dv
from . import taxonomy as tx


def _num(v, digits: int = 3) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return round(f, digits) if math.isfinite(f) else None


def _st(engine, name):
    m = engine.subsystems.get(name)
    return getattr(m, "_state", None) if m is not None else None


# ── limits for the overview tiles (instructor-side, same as the old cards) ──
LIMITS = {
    "soc": {"alarm_low": 30.0, "warn_low": 50.0},
    "point": {"warn_high": 0.5, "alarm_high": 2.0},
    "rate": {"warn_high": 0.5, "alarm_high": 2.0},
    "temp_obc": {"warn_low": -10.0, "warn_high": 50.0, "alarm_low": -20.0, "alarm_high": 60.0},
    "temp_battery": {"warn_low": 5.0, "warn_high": 35.0, "alarm_low": 0.0, "alarm_high": 40.0},
    "cpu": {"warn_high": 60.0, "alarm_high": 80.0},
    "store": {"warn_high": 80.0, "alarm_high": 95.0},
    "margin": {"warn_low": 6.0, "alarm_low": 3.0},
}


def level(v: Optional[float], lim: dict) -> str:
    """ok | caution | alarm for a value against a band (None -> nodata)."""
    if v is None:
        return "nodata"
    if ("alarm_low" in lim and v < lim["alarm_low"]) or ("alarm_high" in lim and v > lim["alarm_high"]):
        return "alarm"
    if ("warn_low" in lim and v < lim["warn_low"]) or ("warn_high" in lim and v > lim["warn_high"]):
        return "caution"
    return "ok"


_ORDER = {"nodata": 0, "ok": 1, "caution": 2, "alarm": 3}


def worst(*levels: str) -> str:
    return max(levels, key=lambda s: _ORDER.get(s, 0)) if levels else "nodata"


# ─────────────────────────────────────────────────────────────────────────

def thermal(engine) -> dict[str, Any]:
    """The 16-node network: node temperatures (truth), conductors with the
    heat flowing along them, heater states and sensor offsets."""
    tcs = engine.subsystems.get("tcs")
    st = _st(engine, "tcs")
    if tcs is None or st is None:
        return {"available": False}
    sol = getattr(tcs, "_solver", None)
    net = getattr(tcs, "_net", None)
    temps = {}
    if sol is not None:
        try:
            temps = {k: _num(v, 2) for k, v in sol.temps_c().items()}
        except Exception:  # noqa: BLE001
            temps = {}
    if "fpa" not in temps:
        temps["fpa"] = _num(getattr(st, "temp_fpa", None), 2)
    links = []
    if net is not None and sol is not None:
        names = list(net.names)
        T = list(sol.T)
        for i, j, g in net.conductors:
            links.append({"a": names[i], "b": names[j], "kind": "cond", "g": _num(g, 3),
                          # heat flowing a -> b (W)
                          "w": _num(g * (T[i] - T[j]), 3)})
        sigma = 5.670374419e-8
        for i, j, ea in net.radiators:
            links.append({"a": names[i], "b": names[j], "kind": "rad", "g": _num(ea, 4),
                          "w": _num(ea * sigma * (T[i] ** 4 - T[j] ** 4), 3)})
    published = {z: f"0x{pid:04X}" for z, pid, _lbl in dv._TCS_ZONES}
    drift = dict(getattr(st, "sensor_drift", {}) or {})
    heaters = []
    for h in ("battery", "obc", "thruster"):
        heaters.append({
            "id": h, "on": bool(getattr(st, f"htr_{h}", False)),
            "failed": bool(getattr(st, f"htr_{h}_failed", False)),
            "stuck_on": bool(getattr(st, f"htr_{h}_stuck_on", False)),
            "open_circuit": bool(getattr(st, f"htr_{h}_open_circuit", False)),
            "duty_pct": _num(getattr(st, f"htr_duty_{h}", None), 1),
            "node": h,
        })
    return {
        "available": True,
        "nodes": [{"id": n, "t": temps.get(n), "published": published.get(n),
                   "sensor_offset": _num(drift.get(n), 2)} for n in temps],
        "links": links, "heaters": heaters,
        "cooler": {"on": bool(getattr(st, "cooler_fpa", False)),
                   "failed": bool(getattr(st, "cooler_failed", False))},
        "heater_power_w": _num(getattr(st, "htr_total_power_w", None), 2),
    }


def attitude(engine, rec) -> dict[str, Any]:
    st = _st(engine, "aocs")
    m = engine.subsystems.get("aocs")
    if st is None:
        return {"available": False}
    q_true = [float(x) for x in (st.q_true or [0, 0, 0, 1])]
    q_ref = [float(x) for x in (st.q_ref or [0, 0, 0, 1])]
    q_est = dv._q_est(engine)
    from smo_common import attitude as att
    import numpy as np

    def rpy(q, ref):
        """z-y-x angles of q relative to ref (deg)."""
        try:
            e = att.quat_mult(att.quat_conj(np.asarray(ref, float)), np.asarray(q, float)) \
                if hasattr(att, "quat_conj") else None
        except Exception:  # noqa: BLE001
            e = None
        if e is None:
            return None
        x, y, z, w = [float(v) for v in e]
        if w < 0:
            x, y, z, w = -x, -y, -z, -w
        roll = math.degrees(math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)))
        s = max(-1.0, min(1.0, 2 * (w * y - z * x)))
        pitch = math.degrees(math.asin(s))
        yaw = math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
        return [_num(roll, 4), _num(pitch, 4), _num(yaw, 4)]

    om_true = [math.degrees(float(v)) for v in (st.omega_true or [0, 0, 0])]
    om_est = None
    if m is not None and getattr(m, "_omega_est", None) is not None:
        try:
            om_est = [math.degrees(float(v)) for v in m._omega_est]
        except Exception:  # noqa: BLE001
            om_est = None
    know = dv._quat_angle_deg(q_est, q_true) if q_est else None
    return {
        "available": True,
        "mode": int(engine.params.get(0x020F, 0) or 0),
        "mode_name": {0: "OFF", 1: "SAFE_BOOT", 2: "DETUMBLE", 3: "COARSE_SUN", 4: "NOMINAL",
                      5: "FINE_POINT", 6: "SLEW", 7: "DESAT", 8: "ECLIPSE",
                      9: "INERTIAL"}.get(int(engine.params.get(0x020F, 0) or 0), "?"),
        "mode_change_reason": str(getattr(st, "mode_change_reason", "") or ""),
        "q_true": [_num(v, 6) for v in q_true],
        "q_est": [_num(v, 6) for v in q_est] if q_est else None,
        "q_ref": [_num(v, 6) for v in q_ref],
        "rpy_true": rpy(q_true, q_ref),
        "rpy_est": rpy(q_est, q_ref) if q_est else None,
        "point_err_true": _num(dv._quat_angle_deg(q_true, q_ref), 4),
        "point_err_est": _num(engine.params.get(0x02A8), 4),
        "knowledge_err": _num(know, 4),
        "knowledge_3sig_arcsec": _num(engine.params.get(0x02A7), 1),
        "rates_true": [_num(v, 5) for v in om_true],
        "rates_est": [_num(v, 5) for v in om_est] if om_est else None,
        "est_source": str(getattr(st, "est_source", "") or ""),
        "st_status": [int(getattr(st, "st1_status", 0) or 0), int(getattr(st, "st2_status", 0) or 0)],
        "css_valid": bool(getattr(st, "css_valid", False)),
        "mag_valid": bool(getattr(st, "mag_valid", False)),
        "gyro_bias_injected": [_num(v, 4) for v in (getattr(m, "_gyro_bias_inject", None) or [0, 0, 0])],
        "wheels": [{"id": f"RW{i + 1}",
                    "rpm": _num(engine.params.get(0x0207 + i), 0),
                    "enabled": bool((getattr(st, "rw_enabled", None) or [True] * 4)[i])
                    if i < len(getattr(st, "rw_enabled", []) or []) else None}
                   for i in range(4)],
        "frame": int(getattr(st, "pointing_frame", 1) or 0),
    }


def orbit(engine, rec) -> dict[str, Any]:
    o = engine.orbit.state
    p = engine.params
    gate = int(p.get(0x052B, 0) or 0)
    in_geo = bool(o.in_contact)
    override = bool(getattr(engine, "_override_passes", False))
    chain = [
        {"id": "geometry", "label": "Station in view", "ok": in_geo or override,
         "note": "pass override" if (override and not in_geo) else ""},
        {"id": "line", "label": "ttc_tx power line on", "ok": bool(gate & 0x02)},
        {"id": "pa", "label": "PA on", "ok": bool(gate & 0x01)},
        {"id": "radio", "label": "Selected transponder alive",
         "ok": bool(engine._ttc_radio_alive(selected=True))},
        {"id": "antenna", "label": "S-band antenna deployed", "ok": bool(gate & 0x40)},
        {"id": "radiating", "label": "S-band radiating", "ok": bool(gate & 0x08)},
    ]
    try:
        trans = engine._get_eclipse_transition()
    except Exception:  # noqa: BLE001
        trans = {}
    contacts = _contacts_cached(engine, rec)
    station = engine._station_measurements() if hasattr(engine, "_station_measurements") else {}
    return {
        "lat": _num(o.lat_deg, 3), "lon": _num(o.lon_deg, 3), "alt_km": _num(o.alt_km, 2),
        "in_eclipse": bool(o.in_eclipse),
        "sun_fraction": _num(getattr(o, "sun_fraction", 0.0 if o.in_eclipse else 1.0), 3),
        "time_to_eclipse_entry_s": _num(trans.get("time_to_eclipse_entry_s"), 0),
        "time_to_eclipse_exit_s": _num(trans.get("time_to_eclipse_exit_s"), 0),
        "geometric_contact": in_geo,
        "station": getattr(o, "active_gs", None) or "",
        "elevation_deg": _num(o.gs_elevation_deg, 1) if in_geo else None,
        "range_km": _num(o.gs_range_km, 1) if in_geo else None,
        "elevations": {k: _num(v, 1) for k, v in (getattr(o, "gs_elevations_deg", {}) or {}).items()},
        "override": override,
        "downlink": bool(engine.downlink_active),
        "uplink": bool(engine.uplink_active),
        "beacon_only": bool(int(p.get(0x0311, 1) or 0) == 0 and p.get(0x0527)),
        "chain": chain,
        "margin_db": _num(p.get(0x0503), 1) if (in_geo or override) else None,
        "tm_rate_bps": int(engine._current_tm_rate_bps()) if hasattr(engine, "_current_tm_rate_bps") else None,
        "tm_tier": engine._current_tm_tier()[1] if hasattr(engine, "_current_tm_tier") else None,
        "station_rx": {k: station.get(k) for k in ("signal", "reason", "rssi_dbm",
                                                   "margin_db", "eb_n0_db") if k in station},
        "contacts": contacts,
        "ground_last_rx_s": (None if rec.ground.last_rx_ts is None
                             else _num(rec.now_ts() - rec.ground.last_rx_ts, 1)),
    }


def _contacts_cached(engine, rec) -> list[dict]:
    """Next contact windows (all stations, 4 h), recomputed every 2 sim-min."""
    now = rec.now_ts()
    cache = getattr(rec, "_contacts_cache", None)
    ver = int(getattr(engine.orbit, "epoch_version", 0) or 0)
    if cache and cache[1] == ver and 0 <= now - cache[0] < 120:
        return cache[2]
    try:
        wins = engine.orbit.contact_windows(duration_s=4 * 3600.0, step_s=60.0)
    except Exception:  # noqa: BLE001
        wins = []
    out = [{"station": w.get("gs_name"), "aos": w.get("aos"), "los": w.get("los"),
            "max_el": w.get("max_elevation_deg")} for w in wins[:12]]
    rec._contacts_cache = (now, ver, out)
    return out


def obc(engine, rec) -> dict[str, Any]:
    p = engine.params
    st = _st(engine, "obdh")
    fd = engine.fdir_status() if hasattr(engine, "fdir_status") else {}
    clock = engine._build_clock_truth() if hasattr(engine, "_build_clock_truth") else {}
    trans = []
    with rec._lock:
        items = [i for i in rec._items if i["lane"] in ("phase", "proc") and i["seg"] == rec.segment]
    for i in items[-12:]:
        trans.append({"ts": i["ts"], "t": i["t"], "kind": i["kind"], "text": i["text"],
                      "trigger": (i.get("data") or {}).get("trigger")})
    return {
        "phase": int(getattr(engine, "_spacecraft_phase", 6)),
        "sc_mode": int(getattr(engine, "sc_mode", 0)),
        "obdh_mode": int(p.get(0x0300, 0) or 0),
        "sw_image": int(p.get(0x0311, 1) or 0),
        "boot_state": int(p.get(0x0A15, 0) or 0) if p.get(0x0A15) is not None else None,
        "cpu": _num(p.get(0x0302), 1), "mem": _num(p.get(0x0303), 1),
        "reboots": int(p.get(0x030A, 0) or 0),
        "active_bus": int(getattr(st, "active_bus", 0) or 0) if st else None,
        "bus_status": [int(getattr(st, "bus_a_status", 0) or 0), int(getattr(st, "bus_b_status", 0) or 0)] if st else None,
        "fdir": {"enabled": fd.get("enabled"), "level": fd.get("level"),
                 "load_shed_stage": fd.get("load_shed_stage"),
                 "triggered": list((fd.get("triggered_rules") or {}).keys())[:20],
                 "active_faults": list(fd.get("active_faults") or [])[:20],
                 "pending_cascades": fd.get("pending_cascades") or [],
                 "recovery": fd.get("recovery") or [],
                 "procedures": fd.get("procedures") or []},
        "transitions": trans,
        "clock": {"offset_s": _num(clock.get("offset_s"), 3),
                  "drift_ppm": _num(clock.get("drift_ppm"), 3),
                  "time_ref_name": clock.get("time_ref_name"),
                  "time_since_sync_s": clock.get("time_since_sync_s"),
                  "obc_time_s": clock.get("obc_time_s"), "sim_time": clock.get("sim_time")},
    }


def storage(engine, rec) -> dict[str, Any]:
    stores = []
    try:
        stores = engine._tm_storage.get_status() or []
    except Exception:  # noqa: BLE001
        stores = []
    pst = _st(engine, "payload")
    pending = getattr(engine, "_dump_pending", None) or []
    return {
        "stores": [{k: s.get(k) for k in ("id", "name", "count", "capacity", "enabled",
                                          "fill_pct", "overflow", "circular")} for s in stores],
        "dump_pending_packets": len(pending),
        "dump_active_stores": sorted(getattr(engine, "_dump_active_stores", set()) or []),
        "rt_backlog": len(getattr(engine, "_rt_pending", None) or []),
        "tm_queue_drops": int(getattr(engine, "tm_queue_drops", 0) or 0),
        "payload": {
            "mode": int(engine.params.get(0x0600, 0) or 0),
            "store_used_pct": _num(getattr(pst, "store_used_pct", None), 1) if pst else None,
            "mem_used_mb": _num(getattr(pst, "mem_used_mb", None), 1) if pst else None,
            "mem_total_mb": _num(getattr(pst, "mem_total_mb", None), 1) if pst else None,
            "image_count": int(getattr(pst, "image_count", 0) or 0) if pst else None,
            "bad_segments": list(getattr(pst, "bad_segments", []) or []) if pst else [],
        },
        "ground": {"packets": rec.ground.packets, "playback_packets": rec.ground.playback_packets},
    }


def power(engine) -> dict[str, Any]:
    """Model truth for the power flow; the console draws it with the shared
    powerflow.js from /api/state params plus these model-only values."""
    st = _st(engine, "eps")
    if st is None:
        return {"available": False}
    return {
        "available": True,
        "soc": _num(st.bat_soc_pct, 2), "bus_v": _num(st.bus_voltage, 2),
        "p_gen": _num(st.power_gen_w, 2), "p_cons": _num(st.power_cons_w, 2),
        "bat_current": _num(getattr(st, "bat_current", None), 3),
        "sun_fraction": _num(getattr(st, "sun_fraction", None), 3),
        "shed_stage": int(getattr(st, "load_shed_stage", 0) or 0),
        "sa_degradation": [_num(getattr(st, "sa_a_degradation", None), 3),
                           _num(getattr(st, "sa_b_degradation", None), 3)],
        "oc_trips": dict(getattr(st, "oc_trip_flags", {}) or {}),
        "lines": dict(getattr(st, "power_lines", {}) or {}),
        "line_currents": {k: _num(v, 3) for k, v in (getattr(st, "line_currents", {}) or {}).items()},
    }


def overview(engine, rec, rows: list[dict]) -> dict[str, Any]:
    """Level-1 tiles: one per subsystem, grey unless something is off."""
    p = engine.params
    o = engine.orbit.state
    injected: dict[str, int] = {}
    for rec_f in rec._failures.values():
        if rec_f.get("cleared_ts") is None:
            injected[rec_f["subsystem"]] = injected.get(rec_f["subsystem"], 0) + 1
    div = dv.summarise(rows)["by_subsystem"]

    def tile(tid, label, view, headline, value, unit, digits, lvl, extra=""):
        d = div.get(tid, {})
        return {"id": tid, "label": label, "view": view,
                "headline": headline, "value": _num(value, digits), "unit": unit,
                "digits": digits, "state": lvl, "injected": injected.get(tid, 0),
                "div_injected": d.get("injected", 0), "div_estimator": d.get("estimator", 0),
                "div_delay": d.get("delay", 0), "note": extra}

    eps = _st(engine, "eps")
    soc = getattr(eps, "bat_soc_pct", None) if eps else None
    tcs = _st(engine, "tcs")
    point = dv._true_point_err(engine)
    rates = [abs(float(v)) for v in (getattr(_st(engine, "aocs"), "omega_true", None) or [])]
    rate = math.degrees(max(rates)) if rates else None
    t_obc = getattr(tcs, "temp_obc", None) if tcs else None
    t_bat = getattr(tcs, "temp_battery", None) if tcs else None
    store = p.get(0x0604)
    margin = p.get(0x0503) if engine.downlink_active else None
    fd_level = int(p.get(0x0700, 0) or 0)
    tiles = [
        tile("eps", "EPS", "power", "SoC", soc, "%", 1, level(soc, LIMITS["soc"]),
             "eclipse" if o.in_eclipse else ""),
        tile("aocs", "AOCS", "attitude", "Pointing (true)", point, "°", 3,
             worst(level(point, LIMITS["point"]) if int(p.get(0x020F, 0) or 0) >= 4 else "ok",
                   level(rate, LIMITS["rate"]))),
        tile("tcs", "TCS", "thermal", "OBC", t_obc, "°C", 1,
             worst(level(t_obc, LIMITS["temp_obc"]), level(t_bat, LIMITS["temp_battery"]))),
        tile("obdh", "OBC / FDIR", "obc", "Mode", None, "", 0,
             "alarm" if engine.sc_mode == 3 else
             "caution" if (engine.sc_mode == 0 and getattr(engine, "_spacecraft_phase", 6) >= 6)
             or fd_level > 0 else "ok",
             f"{dv.SC_MODE_NAMES.get(engine.sc_mode, '?')}"),
        tile("ttc", "TT&C / link", "orbit", "Margin", margin, "dB", 1,
             level(margin, LIMITS["margin"]) if margin is not None else "ok",
             "downlink" if engine.downlink_active else "no downlink"),
        tile("payload", "Payload / storage", "storage", "Store", store, "%", 1,
             level(store, LIMITS["store"])),
        tile("prop", "Propulsion", "power", "Tank", p.get(0x0B01), "bar", 2, "ok"),
    ]
    for t in tiles:
        if t["injected"] and t["state"] == "ok":
            t["state"] = "injected"
    return {"tiles": tiles,
            "orbit": {"in_eclipse": bool(o.in_eclipse), "contact": bool(engine.downlink_active),
                      "station": getattr(o, "active_gs", None) or "",
                      "override": bool(getattr(engine, "_override_passes", False))}}


def build_views(engine, rec, rows: list[dict], now: float) -> dict[str, Any]:
    return {
        "overview": overview(engine, rec, rows),
        "power": power(engine),
        "thermal": thermal(engine),
        "attitude": attitude(engine, rec),
        "orbit": orbit(engine, rec),
        "obc": obc(engine, rec),
        "storage": storage(engine, rec),
        "taxonomy_version": 1,
        "elements": [e["id"] for e in tx.ELEMENTS],
    }
