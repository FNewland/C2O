"""RF block diagram, thermal node diagram, stack elevation, ground segment, verification
matrix (VCD) and the 5 × 5 risk matrix."""
from __future__ import annotations

import math
from typing import Any

from . import layout as L
from .base import DOMAIN_STYLE, Diagram, T, clip, plain, prov, text_w, type_legend
from .data import DiagramData


def _cls(e: dict) -> str:
    try:
        from ..mode_model import unit_class
        return unit_class(e)
    except Exception:  # noqa: BLE001
        return "generic"


def _kbperf(e: dict) -> dict:
    try:
        from ..rule_inputs import kb_component
        kb = kb_component(e) or {}
    except Exception:  # noqa: BLE001
        kb = {}
    return {**(kb.get("performance") or {}), **(e.get("performance") or {})}


def _rate(bps: Any) -> str:
    try:
        v = float(bps)
    except (TypeError, ValueError):
        return ""
    if v >= 1e6:
        return f"{v / 1e6:g} Mbit/s"
    if v >= 1e3:
        return f"{v / 1e3:g} kbit/s"
    return f"{v:g} bit/s"


def _size(label: Any, sub: Any = None, badges: list | None = None, minw: float = 110) -> tuple[float, float]:
    w = max(text_w(label, 13, True), text_w(sub, 12) if sub else 0, 58 * len(badges or [])) + 22
    return min(220.0, max(minw, w)), 30 + (16 if sub else 0) + (16 if badges else 0)


def _shift(D: Diagram, dy: float) -> None:
    for n in D.m["nodes"]:
        n["y"] += dy
    for g in D.m["groups"]:
        g["y"] += dy
    for e in D.m["edges"]:
        e["points"] = [[x, y + dy] for x, y in e["points"]]


def _station_rows(d: DiagramData) -> list[dict]:
    link, stations, _ = d.link()
    rows: list[dict] = []
    try:
        if link is not None and d.ctx is not None:
            from ...routers.modes import _station_rows as sr
            warn: list[str] = []
            rows = sr(d.ctx, link, warn)
    except Exception:  # noqa: BLE001
        rows = []
    by = {r.get("name"): r for r in rows}
    out = []
    for s in stations:
        r = by.get(s.get("name")) or {}
        out.append({**s, **{k: r.get(k) for k in ("contacts_per_day", "contact_min_per_day", "margin_db", "status")}})
    return out


# ───────────────────────────────────────────────────────────── RF

def rf(d: DiagramData, **_: Any) -> dict:
    D = Diagram("rf", T("RF block diagram"), "graph",
                T("On-board chain → space–ground link → ground chain; bands and the data-rate ladder of each transceiver"))
    D.source("elements", "interfaces", "KB parts", "link inputs", "ground stations")
    units = d.units()
    obcs = [u for u in units if _cls(u) == "obc"]
    trx = [u for u in units if _cls(u) in ("transmitter", "receiver")]
    ants = [u for u in units if _cls(u) == "antenna"]
    link, _, _ = d.link()
    stations = _station_rows(d)
    if not trx:
        D.empty(T("No transceiver in the design yet: add a TT&C radio from the KB."))
        D.gap("no_transceiver", T("missing: transceiver"), severity="alarm", fix="blocks")
        return D.finish()
    nodes: list[str] = []
    ranks: dict[str, int] = {}
    info: dict[str, dict] = {}
    edges: list[tuple[str, str, dict]] = []

    def add(nid: str, rank: int, **kw: Any) -> None:
        if nid not in info:
            nodes.append(nid)
            ranks[nid] = rank
            info[nid] = kw

    for o in obcs[:2]:
        add(o["id"], 0, label=clip(o.get("name"), 24), sub=T("TM/TC source"), style="cat3", p=prov("element", o["id"]))
    tiers_missing = 0
    ladder_rows = []
    for t in trx:
        pf = _kbperf(t)
        band = pf.get("band") or pf.get("frequency_band") or "?"
        f = pf.get("frequency_mhz")
        tiers = pf.get("rate_tiers") or pf.get("data_rates_bps")
        badges = [f"{band}-band" + (f" {f:g} MHz" if isinstance(f, (int, float)) else "")]
        if pf.get("tx_power_dbm") is not None:
            badges.append(f"{pf['tx_power_dbm']:g} dBm")
        if isinstance(tiers, list) and tiers:
            for k, tr in enumerate(tiers):
                nm = tr.get("name") if isinstance(tr, dict) else f"T{k + 1}"
                bps = tr.get("bps") if isinstance(tr, dict) else tr
                ladder_rows.append([t.get("name") or "", nm, _rate(bps)])
        else:
            tiers_missing += 1
            if pf.get("data_rate_bps"):
                ladder_rows.append([t.get("name") or "", T("single rate"), _rate(pf.get("data_rate_bps"))])
        add(t["id"], 1, label=clip(t.get("name"), 24), sub=_rate(pf.get("data_rate_bps")) or T("rate not set"),
            badges=badges, style="cat2", p=prov("element", t["id"], note="KB performance"))
        for o in obcs[:2]:
            edges.append((o["id"], t["id"], {"itype": "data", "arrow": "both", "p": prov("derived")}))
    for a in ants:
        pf = _kbperf(a)
        g = pf.get("gain_dbi")
        add(a["id"], 2, label=clip(a.get("name"), 24), sub=T("{{g}} dBi", g=f"{g:g}") if isinstance(g, (int, float)) else T("antenna"),
            badges=[f"{pf['band']}-band"] if pf.get("band") else None, style="cat6", p=prov("element", a["id"]))
    rf_ifs = [i for i in d.interfaces if i.get("interface_type") == "rf"
              and i.get("from_element_id") in info and i.get("to_element_id") in info]
    for i in rf_ifs:
        edges.append((i["from_element_id"], i["to_element_id"],
                      {"itype": "rf", "arrow": "both", "faded": i.get("status") == "suggested",
                       "p": prov("interface", i["id"], status=i.get("status"))}))
    if not rf_ifs:
        for t in trx:
            for a in ants:
                edges.append((t["id"], a["id"], {"itype": "rf", "arrow": "both", "p": prov("derived", note="assumed coax")}))
    if not ants:
        add("ant?", 2, label=T("Antenna"), sub=T("not in the model"), style="muted", p=prov("derived"))
        for t in trx:
            edges.append((t["id"], "ant?", {"itype": "rf", "arrow": "both", "p": prov("derived")}))
    sats = [a["id"] for a in ants] or ["ant?"]
    band = getattr(link, "band", None) if link else None
    rate = getattr(link, "downlink_bps", None) if link else None
    for k, s in enumerate(stations[:3] or [None]):
        sid = f"gs{k}"
        if s is None:
            add(sid, 3, label=T("Ground station"), sub=T("not selected"), style="muted", p=prov("derived"))
        else:
            dia = s.get("antenna_diameter_m") or s.get("dish_m")
            badges = [f"{dia:g} m"] if isinstance(dia, (int, float)) else []
            if s.get("margin_db") is not None:
                badges.append(f"{s['margin_db']:+.1f} dB")
            add(sid, 3, label=clip(s.get("name"), 24), sub=", ".join(str(b) for b in (s.get("bands") or [])) or None,
                badges=badges, style="muted" if s.get("_default") else "cat5",
                p=prov("kb" if s.get("_default") else "element", s.get("id") or s.get("name"),
                       note="catalogue default" if s.get("_default") else None))
        for a in sats[:1]:
            lab = " · ".join(x for x in ((f"{band}-band" if band else ""), _rate(rate)) if x)
            edges.append((a, sid, {"itype": "rf", "arrow": "both", "p": prov("derived", note="link inputs")}))
    add("bb", 4, label=T("Baseband / modem"), sub=T("ground chain"), style="muted", p=prov("template"))
    add("mcc", 5, label=T("Mission control"), sub=T("TM/TC"), style="muted", p=prov("template"))
    for k in range(min(3, max(1, len(stations)))):
        edges.append((f"gs{k}", "bb", {"itype": "rf", "arrow": "both", "p": prov("template")}))
    edges.append(("bb", "mcc", {"itype": "data", "arrow": "both", "p": prov("template")}))

    def size(nid: str) -> tuple[float, float]:
        i = info[nid]
        return _size(i["label"], i.get("sub"), i.get("badges"))

    pos, routed = L.layered(nodes, [(a, b) for a, b, _ in edges], size, ranks=ranks, rank_gap=64, node_gap=14, y0=40)
    for nid in nodes:
        b, i = pos[nid], info[nid]
        D.node(nid, i["label"], b["x"], b["y"], b["w"], b["h"], sub=i.get("sub"), badges=i.get("badges"), style=i["style"],
               p=i["p"], ref={"kind": "element", "id": nid} if nid in d.by_id else None)
    for k, (r, (a, b, kw)) in enumerate(zip(routed, edges)):
        D.edge(f"e{k}", a, b, r["points"], itype=kw["itype"], arrow=kw["arrow"], label=kw.get("label"),
               faded=kw.get("faded", False), p=kw["p"])
    xs = [pos[n]["x"] for n in nodes if ranks[n] == 3]
    if xs:
        xm = min(xs) - 32
        D.label(xm - 70, 22, T("Space segment"), anchor="middle", size=12, weight=600, style="text3")
        D.label(xm + 70, 22, T("Ground segment"), anchor="middle", size=12, weight=600, style="text3")
        D.cell(xm, 30, 1, max(pos[n]["y"] + pos[n]["h"] for n in nodes) - 20, style="divider")
        link_lab = " · ".join(x for x in ((f"{band}-band" if band else ""), _rate(rate)) if x)
        if link_lab:
            D.label(xm, max(pos[n]["y"] + pos[n]["h"] for n in nodes) + 26, link_lab, anchor="middle", size=12,
                    weight=600, style="type:rf")
    # rate ladder table drawn under the chain
    if ladder_rows:
        y = max(pos[n]["y"] + pos[n]["h"] for n in nodes) + 30
        D.label(16, y, T("Data-rate ladder"), size=12, weight=600, style="text3")
        for k, row in enumerate(ladder_rows):
            D.label(16, y + 20 + k * 18, f"{row[0]} — {plain(row[1])}: {row[2]}", size=12)
    D.legend(type_legend(["data", "rf"]) + [{"kind": "box", "style": "muted", "label": T("Template / not in the model")}])
    if tiers_missing:
        D.gap("rate_tiers", T("missing: data-rate tiers (beacon / low / high) for {{n}} transceivers", n=tiers_missing),
              tiers_missing, fix="blocks")
    if not ants:
        D.gap("no_antenna", T("missing: antenna units"), fix="blocks")
    if not stations or all(s.get("_default") for s in stations):
        D.gap("no_station", T("missing: ground station selection (catalogue default used)"), fix="ground")
    if not rf_ifs and ants:
        D.gap("rf_links", T("missing: RF links between transceivers and antennas (assumed)"), severity="info", fix="interfaces")
    D.completeness(len(trx) * 2 + 2, len(trx) * 2 - tiers_missing + bool(ants) + bool(stations and not all(s.get("_default") for s in stations)))
    D.table([T("Unit"), T("Tier"), T("Rate")], ladder_rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── thermal

def thermal(d: DiagramData, **_: Any) -> dict:
    D = Diagram("thermal", T("Thermal node diagram"), "graph",
                T("Lumped network from the thermal closure: nodes coloured by the worse of hot and cold margin; conductive links in W/K"))
    th = d.thermal()
    if th is None or not th.nodes:
        D.empty(T("No thermal network: the spacecraft needs subsystems with equipment."))
        D.gap("no_thermal", T("missing: thermal network (subsystems and equipment)"), severity="alarm", fix="blocks")
        return D.finish()
    D.source("thermal closure (derived, not stored)", "heaters")
    D.m["notes"].append(T("Derived on the fly from the current design (physics closure); not a stored thermal model."))
    nodes = th.nodes

    def nid(n: Any) -> str:
        return "chassis" if n.kind == "structure" else n.element_id

    struct = [n for n in nodes if n.kind == "structure"]
    subs = [n for n in nodes if n.kind == "subsystem"]
    comps = [n for n in nodes if n.kind == "component"]
    idx = d.by_id
    heaters: dict[str, list[dict]] = {}
    for h in d.heaters:
        heaters.setdefault(h.get("element_id"), []).append(h)
    parent_of = {c.element_id: (d.subsystem_of(idx[c.element_id]) or {}).get("id") for c in comps if c.element_id in idx}
    n1 = max(1, len(subs))
    # ellipses (x radius 1.6 × y radius): the boxes are wider than tall
    r1 = max(120.0, n1 * 130 / (2 * math.pi))
    r2 = max(r1 + 110, len(comps) * 125 / (2 * math.pi))
    ex = 1.6
    cx = r2 * ex + 110
    cy = r2 + 90
    ang: dict[str, float] = {}
    pos: dict[str, dict] = {}
    for k, s in enumerate(subs):
        a = -math.pi / 2 + 2 * math.pi * (k + 0.5) / n1
        ang[s.element_id] = a
    comps_sorted = sorted(comps, key=lambda c: (ang.get(parent_of.get(c.element_id) or "", 9), c.name))

    def node_box(n: Any, x: float, y: float) -> dict:
        w = max(120.0, min(190.0, text_w(clip(n.name, 24), 13, True) + 22))
        return {"x": x - w / 2, "y": y - 23, "w": w, "h": 46}
    for s in struct:
        pos[nid(s)] = node_box(s, cx, cy)
    for s in subs:
        a = ang[s.element_id]
        pos[nid(s)] = node_box(s, cx + ex * r1 * math.cos(a), cy + r1 * math.sin(a))
    nc = max(1, len(comps_sorted))
    for k, c in enumerate(comps_sorted):
        a = -math.pi / 2 + 2 * math.pi * (k + 0.5) / nc
        pos[nid(c)] = node_box(c, cx + ex * r2 * math.cos(a), cy + r2 * math.sin(a))
    # space sink
    pos["space"] = {"x": cx - 70, "y": 10, "w": 140, "h": 34}
    rows = []
    worst = None
    for n in nodes:
        m = min(n.margin_hot_c, n.margin_cold_c)
        worst = m if worst is None else min(worst, m)
        style = "alarm" if m < 0 else ("caution" if m < 5 else "ok")
        b = pos[nid(n)]
        hs = heaters.get(n.element_id) or []
        badges = [f"{n.t_cold_c:.0f}…{n.t_hot_c:.0f} °C"]
        if hs:
            badges.append(f"H {sum(float(h.get('power_w') or 0) for h in hs):.1f} W")
        D.node(nid(n), clip(n.name, 24), b["x"], b["y"], b["w"], b["h"], style=style, badges=badges,
               sub=T("margin {{m}} K", m=f"{m:+.1f}"), shape="round",
               ref={"kind": "element", "id": n.element_id} if n.element_id in idx else None,
               p=prov("thermal_closure", n.element_id, note=n.allow_source))
        rows.append([n.name, n.kind, f"{n.dissipation_hot_w:.2f}", f"{n.t_hot_c:.1f}", f"{n.t_cold_c:.1f}",
                     f"{n.allow_min_c:g}…{n.allow_max_c:g}", f"{m:+.1f}", f"{sum(float(h.get('power_w') or 0) for h in hs):.2f}" if hs else "—"])
    D.node("space", T("Space sink (3 K)"), pos["space"]["x"], pos["space"]["y"], 140, 34, shape="round", style="muted",
           p=prov("derived"))
    for k, c in enumerate(th.conductances):
        a, b = c["a"], c["b"]
        if a not in pos or b not in pos:
            continue
        pa, pb = pos[a], pos[b]
        s = L.border_point(pa, (pb["x"] + pb["w"] / 2, pb["y"] + pb["h"] / 2))
        e = L.border_point(pb, (pa["x"] + pa["w"] / 2, pa["y"] + pa["h"] / 2))
        g = float(c.get("w_per_k") or 0)
        D.edge(f"g{k}", a, b, [s, e], itype="thermal", arrow="none", label=None,
               style={"type": "thermal", "dash": "", "width": max(0.8, min(3.5, 1.2 + math.log10(max(g, 0.01)) * 0.8)),
                      "color": "type:thermal"}, p=prov("thermal_closure"))
    for n in struct + subs:
        b = pos[nid(n)]
        s = L.border_point(b, (cx, 27))
        e = L.border_point(pos["space"], (b["x"] + b["w"] / 2, b["y"] + b["h"] / 2))
        D.edge(f"rad:{nid(n)}", nid(n), "space", [s, e], arrow="end",
               style={"type": "radiative", "dash": "2 3", "width": 1.0, "color": "text3"}, p=prov("thermal_closure"))
    D.legend([{"kind": "line", "label": T("Conductive link (width grows with conductance; values in the table)"), "dash": "", "width": 1.8,
               "color": "type:thermal"},
              {"kind": "line", "label": T("Radiation to space (subsystem level shown)"), "dash": "2 3", "width": 1.0, "color": "text3"},
              {"kind": "box", "style": "ok", "label": T("Margin ≥ 5 K")}, {"kind": "box", "style": "caution", "label": T("Margin 0–5 K")},
              {"kind": "box", "style": "alarm", "label": T("Negative margin")}])
    neg = [n for n in nodes if min(n.margin_hot_c, n.margin_cold_c) < 0]
    if neg:
        D.gap("negative_margin", T("{{n}} nodes outside their allowable range", n=len(neg)), len(neg), severity="alarm",
              fix="analyses")
    cold = [n for n in neg if n.margin_cold_c < 0 and n.element_id not in heaters]
    if cold:
        D.gap("heaters", T("missing: heater for {{n}} cold nodes (Modes → design rules)", n=len(cold)), len(cold), fix="modes")
    default_allow = [n for n in nodes if "default" in (n.allow_source or "") and n.kind != "structure"]
    if default_allow:
        D.gap("allowables", T("{{n}} nodes use class-default allowable ranges", n=len(default_allow)), len(default_allow),
              severity="info")
    D.gap("not_stored", T("Thermal nodes are derived, not stored: persist a thermal model to baseline them"), severity="info")
    D.completeness(len(nodes), len(nodes) - len(neg))
    names = {nid(n): n.name for n in nodes}
    for c in th.conductances:
        rows.append([f"{names.get(c['a'], c['a'])} ↔ {names.get(c['b'], c['b'])}", T("link"), "", "", "", "",
                     f"{float(c.get('w_per_k') or 0):.3g} W/K", ""])
    D.table([T("Node"), T("Kind"), T("Hot dissipation (W)"), T("Hot (°C)"), T("Cold (°C)"), T("Allowable (°C)"),
             T("Margin (K)"), T("Heater (W)")], rows)
    _ = DOMAIN_STYLE
    return D.finish()


# ───────────────────────────────────────────────────────────── stack elevation

SUB_STYLE = {"payload": "cat6", "obdh": "cat3", "obc": "cat3", "aocs": "cat1", "power": "cat4", "eps": "cat4",
             "thermal": "cat5", "ttc": "cat2", "comms": "cat2", "propulsion": "cat7", "structure": "cat8"}


def stack(d: DiagramData, **_: Any) -> dict:
    D = Diagram("stack", T("Mechanical stack — elevation"), "elevation",
                T("Front (X–Z) and side (Y–Z) views of the stack layout, CoG and the CDS CoG box"))
    st = d.stack or {}
    if not st.get("applicable"):
        D.empty(T("The stack builder applies to CubeSat form factors: pick a CubeSat structure from the KB."))
        D.gap("not_cubesat", T("missing: CubeSat form factor (structure part)"), severity="warn", fix="spacecraft")
        return D.finish()
    D.source("stack layout", "CDS envelope")
    env = st["envelope"]
    real = st.get("real")
    sx, sy, sz = env["size_mm"]
    s = min(1.6, 520.0 / sz)
    gap_v = 150.0
    ox1, oy = 80.0, 52.0
    ox2 = ox1 + sx * s + gap_v
    views = [("X", 0, ox1, sx, T("Front view (X–Z)")), ("Y", 1, ox2, sy, T("Side view (Y–Z)"))]
    for ax, k, ox, w, lab in views:
        D.label(ox, oy - 26, lab, size=12, weight=600)
        D.group(f"env{ax}", "", ox, oy, w * s, sz * s, style="envelope", p=prov("stack", note=env["sources"]["envelope"]))
        # z ruler
        for zmm in range(0, int(sz) + 1, 50):
            y = oy + sz * s - zmm * s
            D.label(ox - 6, y + 4, f"{zmm}", anchor="end", size=12, style="text3")
            D.cell(ox - 3, y, 3, 0.8, style="grid")
    D.label(ox1 - 40, oy - 8, "mm", size=12, style="text3")
    if real is None:
        D.gap("no_layout", T("missing: stack layout (Spacecraft → Stack → Auto-place, then Approve)"), severity="alarm",
              fix="spacecraft")
        D.completeness(1, 0)
        return D.finish()
    if st.get("which") != "approved":
        D.gap("not_approved", T("Stack layout is a proposal, not approved by the Structures seat"), fix="spacecraft")
    rows = []
    placements = [p for p in real.get("placements") or [] if not p.get("distributed")]
    placements.sort(key=lambda p: -(p["size_mm"][0] * p["size_mm"][1] * p["size_mm"][2]))
    taken: dict[str, list[tuple[float, float, float, float]]] = {"X": [], "Y": []}
    for p in placements[::-1]:   # small parts claim their label first
        p["_lab"] = {}
        for ax, k, ox, w, _ in views:
            c, z = p["center_mm"], p["size_mm"]
            x = ox + (c[k] + w / 2 - z[k] / 2) * s
            y = oy + (sz - (c[2] + sz / 2 - z[2] / 2) - z[2]) * s
            hw, hh = max(2.0, z[k] * s), max(2.0, z[2] * s)
            lw = min(hw - 6, text_w(p["name"], 12))
            box = (x + hw / 2 - lw / 2, y + hh / 2 - 9, lw, 18)
            free = hh >= 15 and hw >= 40 and not any(not (box[0] + box[2] < t[0] or t[0] + t[2] < box[0] or
                                                           box[1] + box[3] < t[1] or t[1] + t[3] < box[1]) for t in taken[ax])
            if free:
                taken[ax].append(box)
            p["_lab"][ax] = free
    for p in placements:
        c, z = p["center_mm"], p["size_mm"]
        for ax, k, ox, w, _ in views:
            xmm = c[k] + w / 2 - z[k] / 2
            zmm = c[2] + sz / 2 - z[2] / 2
            x = ox + xmm * s
            y = oy + (sz - zmm - z[2]) * s
            hw = max(2.0, z[k] * s)
            hh = max(2.0, z[2] * s)
            show = p["_lab"][ax]
            D.node(f"{p['id']}#{ax}", clip(p["name"], max(4, int(hw / 7))) if show else "", x, y, hw, hh, shape="part",
                   style=SUB_STYLE.get(p.get("subsystem") or "", "default") if p.get("fits", True) else "alarm",
                   ref={"kind": "element", "id": p["element_id"]}, p=prov("stack", p["id"], origin=p.get("origin")),
                   title=p["name"])
        rows.append([p["name"], p.get("mount_class") or "", p.get("face") or (f"col {p.get('column')}" if p.get("column") is not None else ""),
                     " × ".join(f"{v:.0f}" for v in p["size_mm"]), f"{p['center_mm'][2]:+.0f}", f"{p.get('mass_kg', 0):.3f}",
                     T("Yes") if p.get("fits", True) else T("No")])
    cog = real.get("cog_mm") or [0, 0, 0]
    lim = env.get("cog_limits_mm") or [20, 20, 20]
    for ax, k, ox, w, _ in views:
        cxp = ox + (cog[k] + w / 2) * s
        cyp = oy + (sz / 2 - cog[2]) * s
        D.node(f"cogbox{ax}", "", ox + (w / 2 - lim[k]) * s, oy + (sz / 2 - lim[2]) * s, 2 * lim[k] * s, 2 * lim[2] * s,
               shape="part", style="cogbox", p=prov("stack", note=env["sources"]["cog"]), title=T("CDS CoG box"))
        D.node(f"cog{ax}", "", cxp - 6, cyp - 6, 12, 12, shape="cog", style="accent", p=prov("stack", note="CoG"))
    D.label(ox1, oy + sz * s + 22, T("CoG ({{x}}, {{y}}, {{z}}) mm; mass {{m}} kg", x=f"{cog[0]:+.1f}", y=f"{cog[1]:+.1f}",
                                     z=f"{cog[2]:+.1f}", m=f"{real.get('mass_kg', 0):.2f}"), size=12)
    D.legend([{"kind": "box", "style": "alarm", "label": T("Does not fit")},
              {"kind": "box", "style": "cogbox", "label": T("CDS CoG box")},
              {"kind": "box", "style": "accent", "label": T("Centre of gravity")}])
    misfit = [p for p in placements if not p.get("fits", True)]
    assumed = [p for p in placements if p.get("assumptions")]
    if misfit:
        D.gap("misfit", T("{{n}} units do not fit their slot or face", n=len(misfit)), len(misfit), severity="alarm", fix="spacecraft")
    if assumed:
        D.gap("assumed_dims", T("missing: KB dimensions for {{n}} units (assumed)", n=len(assumed)), len(assumed),
              severity="info", fix="blocks")
    D.completeness(len(placements), len(placements) - len(misfit))
    D.table([T("Unit"), T("Mount"), T("Where"), T("Size (mm)"), T("Z centre (mm)"), T("Mass (kg)"), T("Fits")], rows)
    D.m["options"] = {"which": st.get("which"), "form_factor": st.get("form_factor"), "geometry": True}
    return D.finish()


# ───────────────────────────────────────────────────────────── ground segment

def ground(d: DiagramData, **_: Any) -> dict:
    D = Diagram("ground", T("Ground segment diagram"), "graph",
                T("Spacecraft → ground stations → mission control → data users, with link bands and contact statistics"))
    D.source("elements", "ground stations", "link inputs", "ConOps data pipeline")
    link, _, _ = d.link()
    stations = _station_rows(d)
    idx = d.by_id
    scs = [e for e in d.elements if e.get("element_type") == "system" and d.segment(e) == "space"]
    station_ids = {s.get("element_id") or s.get("id") for s in stations}
    gnd = [e for e in d.elements if e.get("element_type") == "system" and d.segment(e) in ("ground", "operations")
           and e["id"] not in station_ids and not e.get("kb_component_id")
           and e.get("name") not in ("Ground Station", "DSN Ground Station")]
    users = [e for e in d.elements if e.get("element_type") == "system" and d.segment(e) == "user"]
    conops = getattr(d.study, "conops", None) if d.study is not None else None
    pipeline = list(getattr(conops, "data_pipeline", None) or [])
    nodes: list[str] = []
    ranks: dict[str, int] = {}
    info: dict[str, dict] = {}
    edges: list[tuple[str, str, dict]] = []

    def add(nid: str, rank: int, **kw: Any) -> None:
        if nid not in info:
            nodes.append(nid)
            ranks[nid] = rank
            info[nid] = kw
    for s in scs or [None]:
        if s is None:
            add("sc?", 0, label=T("Spacecraft"), sub=T("not in the model"), style="muted", p=prov("derived"))
        else:
            q = int(s.get("quantity") or 1)
            add(s["id"], 0, label=clip(s.get("name"), 24) + (f" ×{q}" if q > 1 else ""), sub=T("space segment"), style="emph",
                p=prov("element", s["id"]))
    band = getattr(link, "band", None) if link else None
    rate = getattr(link, "downlink_bps", None) if link else None
    for k, s in enumerate(stations[:6] or [None]):
        sid = f"gs{k}"
        if s is None:
            add(sid, 1, label=T("Ground station"), sub=T("not selected"), style="muted", p=prov("derived"))
        else:
            badges = []
            if s.get("contacts_per_day") is not None:
                badges.append(f"{s['contacts_per_day']}/d")
            if s.get("contact_min_per_day") is not None:
                badges.append(f"{s['contact_min_per_day']:.0f} min/d")
            lat, lon = s.get("latitude_deg") or s.get("lat"), s.get("longitude_deg") or s.get("lon")
            sub = f"{lat:.1f}°, {lon:.1f}°" if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) else None
            add(sid, 1, label=clip(s.get("name"), 24), sub=sub, badges=badges,
                style="muted" if s.get("_default") or s.get("status") == "excluded" else "cat5",
                p=prov("kb" if s.get("_default") else "element", s.get("element_id") or s.get("id") or s.get("name"),
                       note="catalogue default" if s.get("_default") else None))
        for sc in (scs or [{"id": "sc?"}]):
            edges.append((sc["id"], sid, {"itype": "rf", "arrow": "both", "p": prov("derived")}))
    mcc_ids = []
    for g in gnd:
        add(g["id"], 2, label=clip(g.get("name"), 24), sub=T("ground system"), style="cat5", p=prov("element", g["id"]))
        mcc_ids.append(g["id"])
    if not mcc_ids:
        add("mcc?", 2, label=T("Mission control centre"), sub=T("not modelled"), style="muted", p=prov("template"))
        mcc_ids = ["mcc?"]
    for k in range(max(1, min(6, len(stations)))):
        edges.append((f"gs{k}", mcc_ids[0], {"itype": "data", "arrow": "both", "label": T("TM/TC") if k == 0 else None,
                                             "p": prov("template")}))
    tail = []
    for u in users:
        add(u["id"], 3, label=clip(u.get("name"), 24), sub=T("user segment"), style="cat6", p=prov("element", u["id"]))
        tail.append(u["id"])
    for k, p in enumerate(pipeline[:5]):
        nid = f"dp{k}"
        add(nid, 3, label=clip(getattr(p, "name", "") or "?", 24), sub=getattr(p, "data_level", None) or None, style="cat6",
            p=prov("conops", getattr(p, "name", "")))
        tail.append(nid)
    if not tail:
        add("users?", 3, label=T("Data users"), sub=T("not modelled"), style="muted", p=prov("template"))
        tail = ["users?"]
    for t in tail:
        edges.append((mcc_ids[0], t, {"itype": "data", "arrow": "end", "label": None, "p": prov("template")}))

    def size(nid: str) -> tuple[float, float]:
        i = info[nid]
        return _size(i["label"], i.get("sub"), i.get("badges"), minw=120)

    pos, routed = L.layered(nodes, [(a, b) for a, b, _ in edges], size, ranks=ranks, rank_gap=86, node_gap=14, y0=36)
    for nid in nodes:
        b, i = pos[nid], info[nid]
        D.node(nid, i["label"], b["x"], b["y"], b["w"], b["h"], sub=i.get("sub"), badges=i.get("badges"), style=i["style"],
               p=i["p"], ref={"kind": "element", "id": nid} if nid in idx else None)
    for k, (r, (a, b, kw)) in enumerate(zip(routed, edges)):
        D.edge(f"e{k}", a, b, r["points"], itype=kw["itype"], arrow=kw["arrow"], label=kw.get("label"), p=kw["p"])
    link_lab = " · ".join(x for x in ((f"{band}-band" if band else ""), _rate(rate)) if x)
    sx = [pos[n]["x"] + pos[n]["w"] for n in nodes if ranks[n] == 0]
    gx = [pos[n]["x"] for n in nodes if ranks[n] == 1]
    if link_lab and sx and gx:
        D.label((max(sx) + min(gx)) / 2, max(pos[n]["y"] + pos[n]["h"] for n in nodes) + 22, link_lab, anchor="middle",
                size=12, weight=600, style="type:rf")
    for rk, lab in ((0, T("Space")), (1, T("Ground stations")), (2, T("Operations")), (3, T("Users and data"))):
        xs = [pos[n]["x"] + pos[n]["w"] / 2 for n in nodes if ranks[n] == rk]
        if xs:
            D.label(sum(xs) / len(xs), 18, lab, anchor="middle", size=12, weight=600, style="text3")
    D.legend(type_legend(["rf", "data"]) + [{"kind": "box", "style": "muted", "label": T("Template / not in the model")}])
    rows = [[s.get("name") or "", ", ".join(str(b) for b in (s.get("bands") or [])), str(s.get("contacts_per_day") or "—"),
             f"{s['contact_min_per_day']:.1f}" if s.get("contact_min_per_day") is not None else "—",
             f"{s['margin_db']:+.1f}" if s.get("margin_db") is not None else "—",
             T("catalogue default") if s.get("_default") else T("selected")] for s in stations]
    if not stations or all(s.get("_default") for s in stations):
        D.gap("no_station", T("missing: ground station selection (catalogue default used)"), fix="ground")
    if mcc_ids == ["mcc?"]:
        D.gap("no_mcc", T("missing: mission control centre element"), fix="blocks")
    if tail == ["users?"]:
        D.gap("no_users", T("missing: data users / data pipeline"), severity="info", fix="conops")
    D.completeness(3, sum([bool(stations) and not all(s.get("_default") for s in stations), mcc_ids != ["mcc?"], tail != ["users?"]]))
    D.table([T("Station"), T("Bands"), T("Contacts per day"), T("Contact min per day"), T("Margin (dB)"), T("Source")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── verification matrix

METHODS = ["A", "T", "I", "R", "D"]
# English text is the key (vocab.ts)
METHOD_LABEL = {"A": "Analysis", "T": "Test", "I": "Inspection", "R": "Review of design", "D": "Demonstration"}
STATUS_STYLE = {"passed": "ok", "failed": "alarm", "in_progress": "caution", "waived": "muted", "planned": "cell"}


def vcd(d: DiagramData, **_: Any) -> dict:
    D = Diagram("vcd", T("Verification matrix (VCD)"), "matrix",
                T("Requirement × verification method, with level, phase and status (ECSS-E-ST-10-02C)"))
    D.source("requirements", "verification items")
    reqs = sorted(d.requirements, key=lambda r: (r.get("code") or "", r["id"]))
    if not reqs:
        D.empty(T("No requirements yet: write or generate them in Requirements."))
        D.gap("no_requirements", T("missing: requirements"), severity="alarm", fix="requirements")
        return D.finish()
    items: dict[str, list[dict]] = {}
    for v in d.verification:
        items.setdefault(v.get("requirement_id"), []).append(v)
    label_w = min(380.0, max(text_w(f"{r.get('code') or ''}  {clip(r.get('text'), 44)}", 12) for r in reqs) + 16)
    cw, rh = 30.0, 22.0
    x0, y0 = 16 + label_w, 58.0
    extra = [(T("Level"), 78.0), (T("Phase"), 56.0), (T("Status"), 92.0)]
    for j, m in enumerate(METHODS):
        D.label(x0 + j * cw + cw / 2, y0 - 10, m, anchor="middle", size=12, weight=600)
    xe = x0 + len(METHODS) * cw + 8
    for lab, w in extra:
        D.label(xe + 4, y0 - 10, lab, size=12, weight=600, style="text3")
        xe += w
    rows = []
    no_item = 0
    counts = {m: 0 for m in METHODS}
    for i, r in enumerate(reqs):
        y = y0 + i * rh
        its = items.get(r["id"]) or []
        methods = {v.get("method") for v in its if v.get("method")} or ({r.get("verification_method")} - {None, ""})
        if not its:
            no_item += 1
        D.label(16 + label_w - 8, y + rh / 2 + 4, f"{r.get('code') or r['id']}  {clip(r.get('text'), 44)}", anchor="end", size=12,
                style="text" if methods else "caution")
        for j, m in enumerate(METHODS):
            on = m in methods
            counts[m] += int(on)
            D.cell(x0 + j * cw, y, cw, rh, text="●" if on else None, style="on" if on else ("band" if i % 2 else "cell"),
                   title=plain(T(METHOD_LABEL[m])) if on else None)
        lvl = ", ".join(sorted({v.get("level") for v in its if v.get("level")})) or (r.get("level") or "")
        ph = ", ".join(sorted({v.get("phase") for v in its if v.get("phase")})) or (r.get("verification_phase") or "—")
        stt = (its[0].get("status") if its else None) or "—"
        xe = x0 + len(METHODS) * cw + 8
        for txt, (lab, w), style in ((lvl, extra[0], "cell"), (ph, extra[1], "cell"),
                                     (stt, extra[2], STATUS_STYLE.get(stt, "unknown" if stt == "—" else "cell"))):
            D.cell(xe, y, w - 2, rh, text=clip(txt, 12), style=style)
            xe += w
        rows.append([r.get("code") or r["id"], clip(r.get("text"), 100), "".join(m for m in METHODS if m in methods) or "—",
                     lvl or "—", ph, stt])
    D.label(16, y0 + len(reqs) * rh + 18, T("Σ per method: {{s}}", s="  ".join(f"{m} {counts[m]}" for m in METHODS)), size=12)
    D.legend([{"kind": "box", "style": "on", "label": T("Method planned")}, {"kind": "box", "style": "ok", "label": T("Passed")},
              {"kind": "box", "style": "alarm", "label": T("Failed")}, {"kind": "box", "style": "unknown", "label": T("No verification item")}])
    no_m = [r for r in rows if r[2] == "—"]
    if no_item:
        D.gap("no_item", T("missing: verification items for {{n}} requirements (V&V → Run)", n=no_item), no_item, fix="vv")
    if no_m:
        D.gap("no_method", T("missing: verification method for {{n}} requirements", n=len(no_m)), len(no_m), fix="requirements")
    failed = [r for r in rows if r[5] == "failed"]
    if failed:
        D.gap("failed", T("{{n}} verifications failed", n=len(failed)), len(failed), severity="alarm", fix="vv")
    D.completeness(len(reqs) * 2, (len(reqs) - no_item) + (len(reqs) - len(no_m)))
    D.table([T("Code"), T("Text"), T("Methods"), T("Level"), T("Phase"), T("Status")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── risk matrix

def risk(d: DiagramData, **_: Any) -> dict:
    D = Diagram("risk", T("Risk matrix (5 × 5)"), "matrix",
                T("Likelihood × consequence per ECSS-M-ST-80C; count and risk ids per cell"))
    D.source("risk register")
    risks = [r for r in d.risks if (r.get("status") or "open") not in ("closed", "retired")]
    cs = 76.0
    x0, y0 = 110.0, 40.0
    grid: dict[tuple[int, int], list[dict]] = {}
    for r in risks:
        try:
            lk, cq = int(r.get("likelihood") or 0), int(r.get("consequence") or 0)
        except (TypeError, ValueError):
            continue
        if 1 <= lk <= 5 and 1 <= cq <= 5:
            grid.setdefault((lk, cq), []).append(r)
    for lk in range(5, 0, -1):
        y = y0 + (5 - lk) * cs
        D.label(x0 - 10, y + cs / 2 + 4, str(lk), anchor="end", size=12, weight=600)
        for cq in range(1, 6):
            x = x0 + (cq - 1) * cs
            score = lk * cq
            style = "risk-low" if score <= 4 else "risk-med" if score <= 9 else "risk-high" if score <= 15 else "risk-vhigh"
            here = grid.get((lk, cq), [])
            D.cell(x, y, cs, cs, style=style, text=(str(len(here)) if here else None),
                   sub=", ".join(str(r.get("id") or "") for r in here[:3]) + ("…" if len(here) > 3 else "") if here else None,
                   title=f"L{lk} × C{cq} = {score}")
    for cq in range(1, 6):
        D.label(x0 + (cq - 1) * cs + cs / 2, y0 + 5 * cs + 18, str(cq), anchor="middle", size=12, weight=600)
    D.label(x0 + 2.5 * cs, y0 + 5 * cs + 38, T("Consequence"), anchor="middle", size=12, style="text3")
    D.label(30, y0 + 2.5 * cs + 30, T("Likelihood"), anchor="middle", size=12, style="text3", rotate=-90)
    D.legend([{"kind": "box", "style": "risk-low", "label": T("Low (≤ 4)")}, {"kind": "box", "style": "risk-med", "label": T("Medium (5–9)")},
              {"kind": "box", "style": "risk-high", "label": T("High (10–15)")}, {"kind": "box", "style": "risk-vhigh", "label": T("Very high (≥ 16)")}])
    rows = [[str(r.get("id") or ""), clip(r.get("description") or r.get("title") or "", 90), str(r.get("likelihood") or ""),
             str(r.get("consequence") or ""), r.get("mitigation") or "—", r.get("status") or "open"] for r in risks]
    if not risks:
        D.gap("no_risks", T("missing: risk register entries"), severity="warn", fix="risks")
    no_mit = [r for r in risks if not (r.get("mitigation") or "").strip()]
    if no_mit:
        D.gap("no_mitigation", T("missing: mitigation for {{n}} risks", n=len(no_mit)), len(no_mit), fix="risks")
    high = [r for r in risks if int(r.get("likelihood") or 0) * int(r.get("consequence") or 0) >= 16]
    if high:
        D.gap("very_high", T("{{n}} very high risks open", n=len(high)), len(high), severity="alarm", fix="risks")
    D.completeness(max(1, len(risks)), len(risks) - len(no_mit) if risks else 0)
    D.table([T("Id"), T("Risk"), T("L"), T("C"), T("Mitigation"), T("Status")], rows)
    return D.finish()
