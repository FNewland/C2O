"""SpaceCDF — TM/TC database export generated from the study's SIDs (W4.05, Nov 2026).

``tables(rows, modes)`` gives the database as plain tables:

* ``parameters`` — id, name, subsystem, type, bits, unit, calibration, range, SIDs that carry it;
  the points listed inline in a SID (``params``) are exported too, numbered after the SID;
* ``sids`` — one row per real-time SID and one per stored copy: APID, size, enable flags,
  diagnostic / beacon flags, store, and one interval column per mode (``-`` = disabled);
* ``stores``, ``rt_profiles``, ``services`` (PUS services used), ``events``, ``commands``.

``to_csv`` writes one CSV with a ``table`` column per section; ``to_xlsx`` one sheet per table.
The numbers come from ``data_budget.sid_table`` (packet size with the settings' overhead).
"""
from __future__ import annotations

import csv
import io
from typing import Any

from . import cdr_model as cm
from . import data_budget as dbs


def _desc(d: Any) -> str:
    return d.get("en", "") if isinstance(d, dict) else str(d or "")


def _fmt(v: Any) -> Any:
    if v is None:
        return "-"
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def tables(rows: list[dict], modes: list[dict]) -> dict[str, Any]:
    sids, ovh = dbs.sid_table(rows)
    hk = {h.get("sid"): h for h in cm.live_data(rows, "hk")}
    params = cm.live_data(rows, "parameters")
    in_sid: dict[Any, list] = {}
    for h in hk.values():
        for pid in h.get("parameter_ids") or []:
            in_sid.setdefault(pid, []).append(h.get("sid"))
    prm = []
    for p in sorted(params, key=lambda x: x.get("param_id") or 0):
        cal = p.get("calibration") or {}
        prm.append({"param_id": f"0x{int(p['param_id']):04X}" if isinstance(p.get("param_id"), int) else p.get("param_id"),
                    "name": p.get("name"), "subsystem": p.get("subsystem"), "type": p.get("type"), "bits": p.get("bits"),
                    "unit": p.get("unit") or "", "calibration": cal.get("type") or "none",
                    "scale": cal.get("scale") if cal.get("type") == "linear" else None,
                    "range": "…".join(str(x) for x in p.get("range")) if isinstance(p.get("range"), list) else "",
                    "sids": " ".join(str(x) for x in in_sid.get(p.get("param_id"), [])), "description": _desc(p.get("description")),
                    "tags": " ".join(p.get("tags") or [])})
    for h in hk.values():
        for i, p in enumerate(h.get("params") or []):
            prm.append({"param_id": f"SID{h.get('sid')}.{i + 1:02d}", "name": p.get("name"), "subsystem": h.get("subsystem"),
                        "type": p.get("type"), "bits": p.get("bits"), "unit": p.get("unit") or "", "calibration": "",
                        "scale": None, "range": "", "sids": str(h.get("sid")), "description": p.get("note") or "",
                        "tags": "diagnostic" if h.get("diagnostic") else ""})
    mcols = [(m["id"], m.get("name") or m["id"]) for m in modes]
    sid_rows = []
    for s in sids:
        base = {"apid": f"0x{int(s['apid']):03X}" if isinstance(s.get("apid"), int) else s.get("apid"),
                "name": s["name"], "subsystem": s.get("subsystem"), "packet_bytes": s["bytes"], "parameters": s["n_parameters"],
                "diagnostic": s["diagnostic"], "beacon": s["beacon"]}
        rt = {f"interval_s[{name}]": _fmt(dbs.rt_period(s, {"id": mid, "name": name, "kind": _kind(modes, mid)}))
              for mid, name in mcols}
        sid_rows.append({"sid": s["sid"], "copy": "real-time", **base, "enabled": s["enabled"]["realtime"], "store_id": "",
                         **rt, "auto_disable_s": _fmt(s.get("auto_disable_s"))})
        if s.get("store_sid") is not None:
            st = {f"interval_s[{name}]": _fmt(dbs.store_period(s, {"id": mid, "name": name, "kind": _kind(modes, mid)}))
                  for mid, name in mcols}
            sid_rows.append({"sid": s["store_sid"], "copy": f"stored (of {s['sid']})", **base, "enabled": s["enabled"]["stored"],
                             "store_id": s.get("store_id"), **st, "auto_disable_s": _fmt(s.get("auto_disable_s"))})
    stores = [{"id": x.get("id"), "name": x.get("name"), "size_mb": x.get("size_mb") or (x.get("size_gb") and x["size_gb"] * 1000),
               "circular": x.get("circular"), "location": x.get("location") or "",
               "content": ", ".join(f"{k}={v}" for k, v in (x.get("content") or {}).items()) if isinstance(x.get("content"), dict) else str(x.get("content") or "")}
              for x in cm.live_data(rows, "stores")]
    profiles = [{"name": p.get("name"), "allocation_bps": p.get("allocation_bps"),
                 "intervals_s": " ".join(f"{k}:{v}" for k, v in (p.get("intervals_s") or {}).items()),
                 "mode_intervals": p.get("mode_intervals"), "description": _desc(p.get("description"))}
                for p in cm.live_data(rows, "rt_profiles")]
    services = [{"service": s.get("service"), "name": _desc(s.get("name")), "used": s.get("used")}
                for s in sorted(cm.live_data(rows, "services"), key=lambda x: x.get("service") or 0)]
    events = [{"event_id": f"0x{int(e['event_id']):04X}" if isinstance(e.get("event_id"), int) else e.get("event_id"),
               "name": e.get("name"), "subsystem": e.get("subsystem"), "severity": e.get("severity"),
               "description": _desc(e.get("description"))} for e in cm.live_data(rows, "events")]
    commands = [{"name": t.get("name"), "service": t.get("service"), "subtype": t.get("subtype"), "func_id": t.get("func_id"),
                 "criticality": t.get("criticality"), "arm_execute": t.get("arm_execute"),
                 "args": "; ".join(str(a.get("name")) for a in t.get("args") or []), "description": _desc(t.get("description"))}
                for t in cm.live_data(rows, "commands")]
    st = cm.singleton(rows, "settings")
    return {"settings": {"spacecraft_id": st.get("spacecraft_id"), "pus_version": st.get("pus_version"),
                         "time_code": st.get("time_code"), "packet_overhead_bytes": ovh},
            "modes": [{"id": m["id"], "name": m.get("name"), "kind": m.get("kind")} for m in modes],
            "parameters": prm, "sids": sid_rows, "stores": stores, "rt_profiles": profiles, "services": services,
            "events": events, "commands": commands}


def _kind(modes: list[dict], mid: str) -> str | None:
    return next((m.get("kind") for m in modes if m["id"] == mid), None)


SECTIONS = ("parameters", "sids", "stores", "rt_profiles", "services", "events", "commands")


def to_csv(data: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["table", "settings"] + [f"{k}={v}" for k, v in data["settings"].items()])
    for sec in SECTIONS:
        rows = data.get(sec) or []
        if not rows:
            continue
        cols = list(rows[0].keys())
        for r in rows[1:]:
            for k in r:
                if k not in cols:
                    cols.append(k)
        w.writerow(["table"] + cols)
        for r in rows:
            w.writerow([sec] + ["" if r.get(k) is None else r.get(k) for k in cols])
    return buf.getvalue()


def to_xlsx(data: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "settings"
    for k, v in data["settings"].items():
        ws.append([k, v])
    for sec in SECTIONS:
        rows = data.get(sec) or []
        sh = wb.create_sheet(sec)
        if not rows:
            sh.append(["(empty)"])
            continue
        cols = list(rows[0].keys())
        for r in rows[1:]:
            for k in r:
                if k not in cols:
                    cols.append(k)
        sh.append(cols)
        for cell in sh[1]:
            cell.font = Font(bold=True)
        for r in rows:
            sh.append([("" if r.get(k) is None else (r.get(k) if not isinstance(r.get(k), (list, dict)) else str(r.get(k))))
                       for k in cols])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
