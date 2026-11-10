"""ConOps diagrams: mission phase timeline, mode state diagram, operations scenario swimlane."""
from __future__ import annotations

import math
from typing import Any

from . import layout as L
from .base import Diagram, T, clip, plain, prov, text_w
from .data import DiagramData

# English text is the key (vocab.ts)
PHASE_LABEL = {"leop": "LEOP", "commissioning": "Commissioning", "transfer": "Transfer", "nominal": "Nominal operations",
               "extended": "Extended mission", "disposal": "Disposal"}
PHASE_ORDER = ["leop", "commissioning", "transfer", "nominal", "extended", "disposal"]
#: C2O default phase durations (days) when the study has no ConOps phases (EOSAT-1 class)
DEFAULT_DAYS = {"leop": 3.0, "commissioning": 30.0, "nominal": None, "disposal": 30.0}
KIND_STYLE = {"leop": "cat1", "commissioning": "cat3", "nominal": "default", "imaging": "cat6", "downlink": "cat2",
              "safe": "caution", "survival": "alarm", "custom": "default"}
CONTINGENCY = {"safe", "survival"}
#: W7.01: a ConOps phase without its own mode list shows the Modes-tab modes of its phase
MODE_PHASES = {"transfer": ("nominal",), "extended": ("nominal",)}
# English text is the key (vocab.ts)
TRIGGER_SHORT = {"ground_tc": "TC", "autonomous": "auto", "timer": "timer", "event": "event"}


def _kind(m: dict) -> str:
    return (m.get("performance") or {}).get("mode_kind") or "custom"


def _phase(m: dict) -> str:
    return (m.get("performance") or {}).get("phase") or ""


def _days(v: float) -> str:
    if v >= 365:
        return f"{v / 365:.1f} y"
    if v >= 1:
        return f"{v:g} d"
    return f"{v * 24:g} h"


# ───────────────────────────────────────────────────────────── phase timeline

def phases(d: DiagramData, **_: Any) -> dict:
    D = Diagram("phases", T("Mission phase timeline"), "timeline",
                T("Phases on a compressed time scale (width grows with the logarithm of the duration); modes used in each phase below"))
    conops = getattr(d.study, "conops", None) if d.study is not None else None
    cphases = list(getattr(conops, "phases", None) or [])
    life_y = None
    req = getattr(d.study, "requirements", None) if d.study is not None else None
    for k in ("design_lifetime_years", "mission_duration_years", "lifetime_years"):
        v = getattr(req, k, None) if req is not None else None
        if isinstance(v, (int, float)) and v > 0:
            life_y = float(v)
            break
    items: list[dict] = []
    if cphases:
        D.source("ConOps phases")
        cmodes = {getattr(m, "id", ""): getattr(m, "name", "") for m in (getattr(conops, "modes", None) or [])}
        for p in cphases:
            pt = getattr(getattr(p, "phase_type", None), "value", None) or str(getattr(p, "phase_type", "nominal"))
            items.append({"key": pt, "name": getattr(p, "name", "") or plain(T(PHASE_LABEL.get(pt, "Nominal operations"))),
                          "days": float(getattr(p, "duration_days", 0) or 0), "src": prov("conops", getattr(p, "id", "") or pt),
                          "modes": [cmodes.get(mid, mid) for mid in (getattr(p, "modes", None) or [])]
                          or [m.get("name") or "" for m in d.modes if _phase(m) in MODE_PHASES.get(pt, (pt,))],
                          "entry": getattr(p, "entry_criteria", ""), "exit": getattr(p, "exit_criteria", "")})
    else:
        D.source("modes (phase attribute)", "C2O default durations")
        keys = [k for k in PHASE_ORDER if any(_phase(m) == k for m in d.modes)]
        for k in ("leop", "commissioning", "nominal", "disposal"):
            if k not in keys:
                keys.append(k)
        keys.sort(key=PHASE_ORDER.index)
        for k in keys:
            days = DEFAULT_DAYS.get(k)
            if k == "nominal":
                days = (life_y or 2.0) * 365.0
            items.append({"key": k, "name": T(PHASE_LABEL.get(k, k)), "days": float(days or 30.0),
                          "src": prov("template", k, note="C2O default duration") if k != "nominal" or not life_y
                          else prov("parameter", "design_lifetime_years"),
                          "modes": [m.get("name") or "" for m in d.modes if _phase(m) == k], "entry": "", "exit": ""})
        D.gap("phase_durations", T("missing: ConOps phases with durations (C2O defaults shown)"), severity="warn", fix="conops")
    x = 16.0
    y_axis, y_band, bh = 34.0, 46.0, 50.0
    cum = 0.0
    rows = []
    D.label(16, 18, T("Time from separation"), size=12, style="text3")
    max_modes = max((len(it["modes"]) for it in items), default=0)
    for i, it in enumerate(items):
        w = max(118.0, 90.0 + 70.0 * math.log10(1 + max(it["days"], 0.0)), text_w(it["name"], 13, True) + 20)
        style = {"leop": "cat1", "commissioning": "cat3", "nominal": "ok", "extended": "cat5", "disposal": "cat8",
                 "transfer": "cat7"}.get(it["key"], "default")
        D.node(f"ph{i}", it["name"], x, y_band, w - 4, bh, sub=_days(it["days"]) if it["days"] else T("duration not set"),
               shape="band", style=style, p=it["src"])
        D.label(x, y_axis, f"L+{_days(cum)}" if cum else "L+0", size=12, style="text3")
        my = y_band + bh + 10
        for j, mn in enumerate(it["modes"][:8]):
            D.node(f"ph{i}m{j}", clip(mn, 16), x + 4, my, w - 12, 22, shape="chip", style="default", p=prov("mode"))
            my += 26
        rows.append([it["name"], _days(it["days"]) if it["days"] else "—", f"L+{_days(cum)}" if cum else "L+0",
                     ", ".join(it["modes"]) or "—", it["entry"] or "", it["exit"] or ""])
        cum += it["days"]
        x += w
    D.label(x, y_axis, f"L+{_days(cum)}", size=12, style="text3", anchor="end")
    # contingency row: modes available in any phase
    cont = [m for m in d.modes if _phase(m) == "any" or _kind(m) in CONTINGENCY]
    yc = y_band + bh + 18 + 26 * min(max_modes, 8)
    if cont:
        D.label(16, yc + 4, T("Any phase (contingency)"), size=12, style="text3")
        cx = 16.0
        for j, m in enumerate(cont):
            w = text_w(m.get("name"), 12) + 24
            D.node(f"cont{j}", m.get("name") or "", cx, yc + 12, w, 22, shape="chip", style=KIND_STYLE.get(_kind(m), "default"),
                   ref={"kind": "element", "id": m["id"]}, p=prov("mode", m["id"]))
            cx += w + 8
    if not d.modes:
        D.gap("no_modes", T("missing: modes"), severity="warn", fix="modes")
    D.completeness(len(items) * 2, sum(1 for it in items if it["days"]) + sum(1 for it in items if it["modes"]))
    D.table([T("Phase"), T("Duration"), T("Starts"), T("Modes"), T("Entry"), T("Exit")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── mode state diagram

def modes(d: DiagramData, **_: Any) -> dict:
    D = Diagram("modes", T("Mode state diagram"), "graph",
                T("Modes and transitions with their trigger; contingency modes in the bottom row"))
    D.source("modes", "mode transitions")
    ms = d.modes
    if not ms:
        D.empty(T("No modes yet: create the mode set in Modes."))
        D.gap("no_modes", T("missing: modes"), severity="alarm", fix="modes")
        return D.finish()
    ids = {m["id"] for m in ms}
    tr = [t for t in d.transitions if t.get("from_mode_id") in ids and t.get("to_mode_id") in ids]
    initial = [m["id"] for m in ms if (m.get("performance") or {}).get("initial")] or \
              [m["id"] for m in ms if _kind(m) == "leop"] or [ms[0]["id"]]
    cont = [m["id"] for m in ms if _kind(m) in CONTINGENCY]
    main = [m["id"] for m in ms if m["id"] not in cont]
    rank: dict[str, int] = {i: 0 for i in initial if i in main}
    frontier = list(rank)
    while frontier:
        nxt = []
        for cur in frontier:
            for t in tr:
                b = t["to_mode_id"]
                if t["from_mode_id"] == cur and b in main and b not in rank:
                    rank[b] = rank[cur] + 1
                    nxt.append(b)
        frontier = nxt
    rmax = max(rank.values(), default=0)
    for m in main:
        if m not in rank:
            rank[m] = rmax + 1
    idx = {m["id"]: m for m in ms}

    def size(mid: str) -> tuple[float, float]:
        return max(118.0, text_w(idx[mid].get("name"), 13, True) + 26), 46

    cols: dict[int, list[str]] = {}
    for m in main:
        cols.setdefault(rank[m], []).append(m)
    def edge_text(t: dict) -> str:
        g = t.get("guard") or {}
        gt = g.get("text") or (f"{g.get('param')} {g.get('op')} {g.get('value')}{g.get('unit') or ''}" if g.get("param") else "")
        short = plain(T(TRIGGER_SHORT.get(t.get("trigger") or "", "TC")))
        return f"{short}: {clip(gt, 22)}" if gt else short
    pos: dict[str, dict] = {}
    x = 52.0
    lab_w = [text_w(edge_text(t), 12) for t in tr if t["to_mode_id"] not in cont and rank.get(t["to_mode_id"], -1) != rank.get(t["from_mode_id"], -2)]
    colgap = max(92.0, min(220.0, max(lab_w, default=0) + 36))
    tallest = 0.0
    for r in sorted(cols):
        w = max(size(m)[0] for m in cols[r])
        y = 24.0
        for m in cols[r]:
            pos[m] = {"x": x + (w - size(m)[0]) / 2, "y": y, "w": size(m)[0], "h": 46}
            y += 46 + 50
        tallest = max(tallest, y)
        x += w + colgap
    total_w = x - colgap
    # centre each column vertically on the tallest one
    for r, col in cols.items():
        h = len(col) * 96 - 50
        off = ((tallest - 24 - 50) - h) / 2
        for m in col:
            pos[m]["y"] += off
    yc = tallest + 40
    if cont:
        cw = sum(size(m)[0] for m in cont) + 60 * (len(cont) - 1)
        cx = 16 + max(0.0, (total_w - 16 - cw) / 2)
        for m in cont:
            w = size(m)[0]
            pos[m] = {"x": cx, "y": yc, "w": w, "h": 46}
            cx += w + 60
    for m in ms:
        b = pos[m["id"]]
        p = m.get("performance") or {}
        sub = " · ".join(x for x in (p.get("pointing"), (f"{p['orbit_fraction'] * 100:.0f} %" if isinstance(p.get("orbit_fraction"), (int, float))
                                                          and p.get("orbit_fraction") < 1 else None)) if x)
        D.node(m["id"], m.get("name") or "?", b["x"], b["y"], b["w"], b["h"], shape="state",
               style=KIND_STYLE.get(_kind(m), "default"), sub=sub or None,
               ref={"kind": "element", "id": m["id"]},
               p=prov("mode", m["id"]))
    for k, i0 in enumerate(i for i in initial if i in pos):
        b = pos[i0]
        cy0 = b["y"] + b["h"] / 2
        D.node(f"init{k}", "", 14, cy0 - 7, 14, 14, shape="dot", style="default", p=prov("mode", i0, note="initial mode"),
               title=T("initial"))
        D.edge(f"init{k}e", f"init{k}", i0, [(28, cy0), (b["x"], cy0)],
               style={"type": "transition", "dash": "", "width": 1.3, "color": "text2"})
    if cont:
        D.group("cont", T("Contingency modes"), 8, yc - 22, max(total_w, max(pos[m]["x"] + pos[m]["w"] for m in cont)) + 4,
                46 + 30, style="lane")
    pairs = {(t["from_mode_id"], t["to_mode_id"]) for t in tr}
    rows = []
    for k, t in enumerate(tr):
        a, b = t["from_mode_id"], t["to_mode_id"]
        pa, pb = pos[a], pos[b]
        ca = (pa["x"] + pa["w"] / 2, pa["y"] + pa["h"] / 2)
        cb = (pb["x"] + pb["w"] / 2, pb["y"] + pb["h"] / 2)
        if a == b:
            continue
        dx, dy = cb[0] - ca[0], cb[1] - ca[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        bend = 26.0 if (b, a) in pairs else (10.0 if abs(dx) < 1 or abs(dy) < 1 else 0.0)
        if b in cont and a not in cont:
            bend = 0.0
        mid = ((ca[0] + cb[0]) / 2 + nx * bend * 2, (ca[1] + cb[1]) / 2 + ny * bend * 2)
        s = L.border_point(pa, mid)
        e = L.border_point(pb, mid)
        g = t.get("guard") or {}
        gtxt = g.get("text") or (f"{g.get('param')} {g.get('op')} {g.get('value')}{g.get('unit') or ''}" if g.get("param") else "")
        to_cont = b in cont
        D.edge(t["id"], a, b, [s, mid, e] if bend else [s, e], curve=bool(bend),
               label=None if to_cont else (T(TRIGGER_SHORT.get(t.get("trigger") or "", "TC")) if not gtxt else
                                           edge_text(t)),
               style={"type": "transition", "dash": "4 3" if to_cont else "", "width": 1.3,
                      "color": "alarm" if to_cont and _kind(idx[b]) == "survival" else ("caution" if to_cont else "text2")},
               p=prov("transition", t["id"], origin=t.get("origin")))
        rows.append([idx[a].get("name") or "", idx[b].get("name") or "", T(TRIGGER_SHORT.get(t.get("trigger") or "", "TC")),
                     gtxt or "—", t.get("origin") or ""])
    D.legend([{"kind": "line", "label": T("Transition (label: trigger and guard)"), "dash": "", "width": 1.3, "color": "text2"},
              {"kind": "line", "label": T("Transition into a contingency mode"), "dash": "4 3", "width": 1.3, "color": "caution"},
              {"kind": "dot", "label": T("initial")}, {"kind": "box", "style": "caution", "label": T("Safe")}, {"kind": "box", "style": "alarm", "label": T("Survival")}])
    try:
        from ..mode_model import validate_machine
        for f in validate_machine(ms, d.transitions, ()):
            if f["id"] == "MM-AUTO-NO-GUARD":
                continue
            D.gap(f["id"], f["text"], 1, severity="alarm" if f.get("severity") == "major" else "warn", fix="modes")
    except Exception:  # noqa: BLE001
        pass
    if not tr:
        D.gap("no_transitions", T("missing: mode transitions"), severity="alarm", fix="modes")
    unguarded = [t for t in tr if t.get("trigger") in ("autonomous", "event") and not (t.get("guard") or {}).get("param")
                 and not (t.get("guard") or {}).get("text")]
    if unguarded:
        D.gap("unguarded", T("missing: guard for {{n}} autonomous transitions", n=len(unguarded)), len(unguarded), fix="modes")
    D.completeness(len(ms) + len(tr), len(ms) + len(tr) - len(unguarded) - sum(1 for g in D.m["gaps"] if g["code"] == "MM-UNREACHABLE"))
    D.table([T("From"), T("To"), T("Trigger"), T("Guard"), T("Origin")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── ops scenario swimlane

def ops_pass(d: DiagramData, **_: Any) -> dict:
    D = Diagram("ops_pass", T("Operations scenario — one ground-station pass"), "swimlane",
                T("Seats and segments over a downlink pass; timings from the contact analysis, rates from the link model"))
    D.source("ground stations", "link inputs", "modes", "C2O pass template")
    link, stations, warns = d.link()
    band, rate, link_src = mission_link(d, link)
    st = next((s for s in stations if not s.get("_default") and _has_band(s, band)),
              next((s for s in stations if not s.get("_default")), stations[0] if stations else None))
    pass_min = 8.0
    contact_src = prov("template", note="C2O default pass length")
    try:
        if st is not None and d.ctx is not None:
            from .. import ground_closure as gc
            orbit = gc.OrbitParams(altitude_km=float(d.ctx.orbit.get("altitude_km") or 500.0),
                                   inclination_deg=float(d.ctx.orbit.get("inclination_deg") or 97.4),
                                   period_s=float(d.ctx.orbit.get("period_s") or 0.0))
            gs = gc.station_to_ground_station(st, band)
            minutes, n = gc._contact_minutes(orbit, gs, (rate or 1e6) / 1e6)
            if n:
                pass_min = max(3.0, minutes / n)
                contact_src = prov("derived", st.get("id") or st.get("name"), note="contact prediction")
    except Exception:  # noqa: BLE001
        pass
    dump = max(1.0, pass_min - 3.0)
    vol_mb = (rate or 0) * dump * 60 / 8e6
    st_name = (st or {}).get("name") or plain(T("Ground station"))
    lanes = [("sc", T("Spacecraft")), ("gs", T("Ground station")), ("mcc", T("Mission control")), ("ops", T("Operators"))]
    steps = [
        ("ops", -15.0, 6.0, T("Pass plan approved"), None),
        ("mcc", -8.0, 4.0, T("Schedule and antenna pointing sent"), None),
        ("gs", 0.0, 1.0, T("AOS: carrier lock ({{band}}-band)", band=band or "?"), None),
        ("sc", 0.5, 1.5, T("Beacon and housekeeping TM"), None),
        ("mcc", 1.5, 1.5, T("TC uplink: time-tagged plan"), None),
        ("sc", 2.5, dump, T("Payload data dump at {{rate}}", rate=_rate_txt(rate)), None),
        ("gs", 2.5 + dump - 0.2, 0.6, T("LOS"), None),
        ("mcc", 3.0 + dump, 4.0, T("Data to processing; pass report"), None),
        ("ops", 4.5 + dump, 5.0, T("Review pass, plan next"), None),
    ]
    t0, t1 = -16.0, 15.0 + dump
    lane_h, x0, px = 76.0, 140.0, 30.0
    width = (t1 - t0) * px
    y0 = 40.0
    for i, (lid, lab) in enumerate(lanes):
        y = y0 + i * lane_h
        D.group(f"lane:{lid}", lab, 8, y, x0 + width - 8, lane_h - 4, style="lane", p=prov("template"))
    # time axis
    for t in range(int(math.ceil(t0 / 5) * 5), int(t1) + 1, 5):
        x = x0 + (t - t0) * px
        D.label(x, y0 - 10, f"{t:+d} min" if t else "AOS", anchor="middle", size=12, style="text3")
        D.cell(x - 0.5, y0, 1, lane_h * len(lanes) - 4, style="grid")
    lane_y = {lid: y0 + i * lane_h for i, (lid, _) in enumerate(lanes)}
    prev = None
    rows = []
    lane_end: dict[tuple[str, int], float] = {}
    for k, (lid, ts, dur, lab, _) in enumerate(steps):
        x = x0 + (ts - t0) * px
        w = max(dur * px, text_w(lab, 12) + 14)
        sub = 0 if lane_end.get((lid, 0), -1e9) <= x - 4 else 1
        lane_end[(lid, sub)] = x + w
        y = lane_y[lid] + 22 + sub * 26
        D.node(f"s{k}", lab, x, y, w, 24, shape="step", style="accent" if lid == "sc" else "default",
               p=contact_src if k in (2, 6) else prov("template"))
        if prev is not None:
            pa = prev
            sx = max(pa["x"] + 8, min(pa["x"] + pa["w"] - 8, x + 6))
            D.edge(f"m{k}", f"s{k - 1}", f"s{k}", [(sx, pa["y"] + (24 if pa["y"] < y else 0)),
                                                    (x + 6, y if pa["y"] < y else y + 24)] if pa["y"] != y else
                   [(pa["x"] + pa["w"], pa["y"] + 12), (x, y + 12)],
                   style={"type": "message", "dash": "", "width": 1.1, "color": "text3"})
        prev = {"x": x, "y": y, "w": w}
        rows.append([dict(lanes)[lid], f"{ts:+.1f} min", f"{dur:.1f} min", lab])
    D.label(x0, y0 + lane_h * len(lanes) + 14,
            T("Pass {{min}} min at {{station}}; dump {{vol}} MB per pass", min=f"{pass_min:.1f}", station=st_name,
              vol=f"{vol_mb:.0f}"), size=12, style="text2")
    if not stations or all(s.get("_default") for s in stations):
        D.gap("no_station", T("missing: ground station selection (catalogue default used)"), fix="ground")
    if link_src == "fallback":
        D.gap("no_rate", T("missing: downlink rate in the model (fallback rate used)"), fix="analyses")
    if not any(_kind(m) == "downlink" for m in d.modes):
        D.gap("no_downlink_mode", T("missing: a downlink mode"), severity="info", fix="modes")
    D.gap("template", T("Scenario steps are the C2O pass template; timings and rates come from the model"), severity="info")
    D.completeness(3, sum([bool(stations) and not all(s.get("_default") for s in stations),
                           bool(rate) and link_src != "fallback",
                           any(_kind(m) == "downlink" for m in d.modes)]))
    D.table([T("Lane"), T("Start"), T("Duration"), T("Step")], rows)
    _ = warns
    return D.finish()


def _band_of_mhz(mhz: Any) -> str | None:
    try:
        f = float(mhz)
    except (TypeError, ValueError):
        return None
    if f <= 0:
        return None
    from .. import ground_closure as gc
    return gc._link_band(f / 1000.0)


def mission_link(d: DiagramData, link: Any = None) -> tuple[str | None, float | None, str]:
    """(band, downlink rate in bit/s, source) of the operations pass, from the mission first:

    1. the design link case (``requirements.link``: band, downlink frequency and rate, which the
       link-budget tool's "Apply" writes);
    2. the mission constraints (``downlink_band_mhz`` / ``downlink_frequency_mhz`` / ``band``);
    3. the analysis link model (``ground_closure``), whose frequency falls back to a class default
       (X-band) when the model has none, so it is the last resort for the band.

    Source is ``design_case``, ``constraints``, ``model`` or ``fallback`` (no rate anywhere)."""
    req = getattr(getattr(d, "study", None), "requirements", None)
    dl = getattr(req, "link", None)
    cons = getattr(req, "constraints", None) or {}
    band = (getattr(dl, "band", None) or _band_of_mhz(getattr(dl, "downlink_frequency_mhz", None))) if dl else None
    src = "design_case" if band else ""
    if not band:
        rng = cons.get("downlink_band_mhz")
        mid = (sum(float(x) for x in rng) / len(rng)) if isinstance(rng, (list, tuple)) and rng else None
        band = cons.get("band") or cons.get("link_band") or _band_of_mhz(cons.get("downlink_frequency_mhz")) \
            or _band_of_mhz(mid)
        src = "constraints" if band else ""
    model_fallback = link is None or (getattr(link, "source", {}) or {}).get("downlink_rate") == "fallback"
    if not band and link is not None:
        band, src = getattr(link, "band", None), "model"
    rate = None
    try:
        rate = float(getattr(dl, "downlink_rate_bps", None) or 0) or None if dl else None
    except (TypeError, ValueError):
        rate = None
    if rate:
        src = src or "design_case"
    elif link is not None and not model_fallback:
        rate = getattr(link, "downlink_bps", None)
        src = src or "model"
    else:
        rate = getattr(link, "downlink_bps", None) if link is not None else None
        src = "fallback"
    return (str(band) if band else None), rate, src


def _has_band(st: dict, band: str | None) -> bool:
    if not band:
        return True
    have = [str(b).upper().split()[0] for b in (st.get("bands") or ([st["band"]] if st.get("band") else [])) if str(b)]
    return not have or band.upper() in have


def _rate_txt(bps: float | None) -> str:
    if not bps:
        return "?"
    return f"{bps / 1e6:g} Mbit/s" if bps >= 1e6 else f"{bps / 1e3:g} kbit/s"
