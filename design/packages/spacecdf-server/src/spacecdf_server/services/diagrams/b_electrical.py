"""Electrical power block diagram, switch matrix (lines × modes) and data-bus topology,
from the Electrical tab's stored rails, power lines, buses and nodes (design rules §2.1, §2.4)."""
from __future__ import annotations

from typing import Any

from . import layout as L
from .base import DOMAIN_STYLE, Diagram, T, clip, prov, text_w, type_legend
from .data import DiagramData


def _cls(e: dict) -> str:
    try:
        from ..mode_model import unit_class
        return unit_class(e)
    except Exception:  # noqa: BLE001
        return "generic"


def _num(v: Any) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _amps(a: float | None) -> str:
    return "" if a is None else (f"{a:.2f} A" if a < 10 else f"{a:.1f} A")


def _rail_label(r: dict) -> str:
    v = _num(r.get("voltage_v"))
    return r.get("name") or (f"{v:g} V" if v is not None else "rail")


# ───────────────────────────────────────────────────────────── power block diagram

def power(d: DiagramData, **_: Any) -> dict:
    D = Diagram("power", T("Electrical power block diagram"), "graph",
                T("Arrays → regulator and battery → rails → switched lines (LCL rating) → loads"))
    D.source("power rails", "power lines", "elements")
    rails = d.electrical.get("rails") or []
    lines = sorted(d.electrical.get("lines") or [], key=lambda x: (x.get("line_no") or 0, x.get("name") or ""))
    idx = d.by_id
    units = d.units()
    arrays = [u for u in units if _cls(u) == "solar_array"]
    batteries = [u for u in units if _cls(u) == "battery"]
    eps_ids = {r.get("eps_element_id") for r in rails + lines if r.get("eps_element_id") in idx}
    if not eps_ids:
        eps_ids = {u["id"] for u in units if _cls(u) == "eps"}
    if not rails and not lines:
        D.empty(T("No rails or power lines yet: open Electrical and press Propose."))
        D.gap("no_rails", T("missing: power rails and lines (Electrical → Propose)"), severity="alarm", fix="electrical")
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

    for a in arrays:
        p = _num((a.get("performance") or {}).get("power_eol_w")) or _num(a.get("power_avg_w"))
        add(a["id"], 0, label=clip(a.get("name"), 24), sub=T("{{w}} W EOL", w=f"{p:.0f}") if p else T("solar array"),
            style="cat4", p=prov("element", a["id"]))
    if not arrays:
        add("arrays?", 0, label=T("Solar arrays"), sub=T("not in the model"), style="muted", p=prov("derived"))
    for eid in sorted(eps_ids):
        add(eid, 1, label=clip(idx[eid].get("name"), 24), sub=T("PCDU / regulator"), style="emph", p=prov("element", eid))
    if not eps_ids:
        add("eps?", 1, label=T("EPS / PCDU"), sub=T("not in the model"), style="muted", p=prov("derived"))
    eps_main = sorted(eps_ids)[0] if eps_ids else "eps?"
    for b in batteries:
        wh = _num((b.get("performance") or {}).get("capacity_wh"))
        add(b["id"], 0, label=clip(b.get("name"), 24), sub=T("{{wh}} Wh", wh=f"{wh:.0f}") if wh else T("battery"),
            style="cat4", p=prov("element", b["id"]))
    for a in (arrays or [{"id": "arrays?"}]):
        edges.append((a["id"], eps_main, {"itype": "power", "arrow": "end", "p": prov("derived")}))
    for b in batteries:
        edges.append((b["id"], eps_main, {"itype": "power", "arrow": "both", "p": prov("derived")}))
    for r in rails:
        v = _num(r.get("voltage_v"))
        sub = T("regulated") if r.get("regulated") else T("unregulated")
        badges = [_amps(_num(r.get("max_current_a")))] if r.get("max_current_a") else []
        add(f"rail:{r['id']}", 2, label=_rail_label(r) if r.get("name") else f"{v:g} V", sub=sub, badges=badges,
            style="cat4" if r.get("status") != "suggested" else "muted",
            p=prov("rail", r["id"], origin=r.get("origin"), status=r.get("status")))
        edges.append((r.get("eps_element_id") if r.get("eps_element_id") in info else eps_main, f"rail:{r['id']}",
                      {"itype": "power", "arrow": "end", "p": prov("rail", r["id"])}))
    rail_by = {r["id"]: r for r in rails}
    load_seen: set[str] = set()
    for ln in lines:
        lid = f"line:{ln['id']}"
        lcl = _num(ln.get("lcl_limit_a"))
        name = ln.get("name") or f"L{ln.get('line_no') or '?'}"
        badges = [f"LCL {_amps(lcl)}" if lcl else "LCL ?"]
        if ln.get("default_on_separation"):
            badges.append("ON@sep")
        add(lid, 3, label=clip(name, 22), sub=T("switched") if ln.get("switchable", True) else T("always on"),
            badges=badges, style="default" if lcl else "caution",
            p=prov("line", ln["id"], origin=ln.get("origin"), status=ln.get("status")))
        src = f"rail:{ln['rail_id']}" if ln.get("rail_id") in rail_by else (
            ln.get("eps_element_id") if ln.get("eps_element_id") in info else eps_main)
        edges.append((src, lid, {"itype": "power", "arrow": "end", "p": prov("line", ln["id"])}))
        for le in ln.get("load_element_ids") or []:
            if le not in idx:
                continue
            e = idx[le]
            pw = _num(e.get("power_avg_w"))
            add(le, 4, label=clip(e.get("name"), 24), sub=T("{{w}} W avg", w=f"{pw:.1f}") if pw else None,
                style=DOMAIN_STYLE.get(d.domain(e) or "", "default"), p=prov("element", le))
            load_seen.add(le)
            edges.append((lid, le, {"itype": "power", "arrow": "end", "p": prov("line", ln["id"])}))

    def size(nid: str) -> tuple[float, float]:
        i = info[nid]
        w = max(text_w(i["label"], 13, True), text_w(i.get("sub") or "", 12), 60 * len(i.get("badges") or [])) + 22
        return min(210.0, max(100.0, w)), 30 + (16 if i.get("sub") else 0) + (16 if i.get("badges") else 0)

    pos, routed = L.layered(nodes, [(a, b) for a, b, _ in edges], size, ranks=ranks, rank_gap=58, node_gap=10)
    for nid in nodes:
        b, i = pos[nid], info[nid]
        el = idx.get(nid)
        D.node(nid, i["label"], b["x"], b["y"], b["w"], b["h"], sub=i.get("sub"), badges=i.get("badges"),
               style=i["style"], p=i["p"], ref={"kind": "element", "id": nid} if el else None)
    for k, (r, (a, b, kw)) in enumerate(zip(routed, edges)):
        D.edge(f"e{k}", a, b, r["points"], itype=kw["itype"], arrow=kw["arrow"], p=kw["p"])
    for x, lab in ((0, T("Sources")), (1, T("Regulation")), (2, T("Rails")), (3, T("Switched lines")), (4, T("Loads"))):
        xs = [pos[n]["x"] + pos[n]["w"] / 2 for n in nodes if ranks[n] == x]
        if xs:
            D.label(sum(xs) / len(xs), 12, lab, anchor="middle", size=12, weight=600, style="text3")
    for b in pos.values():
        b["y"] += 14
    for n in D.m["nodes"]:
        n["y"] += 14
    for e in D.m["edges"]:
        e["points"] = [[x, y + 14] for x, y in e["points"]]
    D.legend(type_legend(["power"]) + [{"kind": "box", "style": "caution", "label": T("Line without LCL rating")},
                                       {"kind": "box", "style": "muted", "label": T("Not in the model / suggested")}])
    consumers = [u for u in units if (_num(u.get("power_avg_w")) or 0) > 0 and _cls(u) not in ("solar_array", "battery", "eps")]
    unfed = [u for u in consumers if u["id"] not in load_seen]
    no_lcl = [ln for ln in lines if not _num(ln.get("lcl_limit_a"))]
    no_cap = [r for r in rails if not _num(r.get("max_current_a"))]
    if not arrays:
        D.gap("no_arrays", T("missing: solar array units"), severity="warn", fix="blocks")
    if not batteries:
        D.gap("no_battery", T("missing: battery unit"), severity="warn", fix="blocks")
    if unfed:
        D.gap("unfed_loads", T("missing: power line for {{n}} loads ({{names}})", n=len(unfed),
                               names=", ".join(clip(u.get("name"), 14) for u in unfed[:3])), len(unfed), fix="electrical")
    if no_lcl:
        D.gap("lcl", T("missing: LCL rating for {{n}} lines", n=len(no_lcl)), len(no_lcl), fix="electrical")
    if no_cap:
        D.gap("rail_cap", T("missing: current rating for {{n}} rails", n=len(no_cap)), len(no_cap), severity="info",
              fix="electrical")
    D.completeness(len(consumers) + len(lines), len(consumers) - len(unfed) + len(lines) - len(no_lcl))
    D.table([T("Line"), T("Rail"), T("LCL (A)"), T("Switched"), T("On at separation"), T("Loads")],
            [[ln.get("name") or f"L{ln.get('line_no')}", _rail_label(rail_by[ln["rail_id"]]) if ln.get("rail_id") in rail_by else "",
              f"{_num(ln.get('lcl_limit_a')):g}" if _num(ln.get("lcl_limit_a")) else "—",
              T("Yes") if ln.get("switchable", True) else T("No"), T("Yes") if ln.get("default_on_separation") else T("No"),
              ", ".join((idx.get(x) or {}).get("name", "?") for x in ln.get("load_element_ids") or [])] for ln in lines])
    return D.finish()


# ───────────────────────────────────────────────────────────── switch matrix

def switch_matrix(d: DiagramData, **_: Any) -> dict:
    D = Diagram("switch_matrix", T("Switch matrix — power lines × modes"), "matrix",
                T("ON where a load on the line is powered in the mode; line current from the mode power at the rail voltage"))
    D.source("power lines", "mode × unit matrix")
    lines = sorted(d.electrical.get("lines") or [], key=lambda x: (x.get("line_no") or 0, x.get("name") or ""))
    modes = d.modes
    if not lines:
        D.empty(T("No power lines yet: open Electrical and press Propose."))
        D.gap("no_lines", T("missing: power lines (Electrical → Propose)"), severity="alarm", fix="electrical")
        return D.finish()
    if not modes:
        D.empty(T("No modes yet: create the mode set in Modes."))
        D.gap("no_modes", T("missing: modes"), severity="alarm", fix="modes")
        return D.finish()
    idx = d.by_id
    rails = {r["id"]: r for r in d.electrical.get("rails") or []}
    mem: dict[tuple[str, str], dict] = {(m["mode_id"], m["element_id"]): m for m in d.members}
    modes_with_rows = {m["mode_id"] for m in d.members}
    label_w = max(text_w(f"{ln.get('name') or ''}", 12) for ln in lines) + 120
    cw, rh = 84.0, 26.0
    x0, y0 = 16 + label_w, 56.0
    D.label(16, y0 - 12, T("Line"), size=12, weight=600, style="text3")
    D.label(16 + label_w - 64, y0 - 12, T("LCL"), size=12, weight=600, style="text3")
    for j, m in enumerate(modes):
        D.label(x0 + j * cw + cw / 2, y0 - 12, clip(m.get("name"), 12), anchor="middle", size=12, weight=600)
    totals_w = [0.0] * len(modes)
    totals_a = [0.0] * len(modes)
    rows = []
    over = 0
    for i, ln in enumerate(lines):
        y = y0 + i * rh
        rail = rails.get(ln.get("rail_id") or "")
        v = _num((rail or {}).get("voltage_v")) or None
        lcl = _num(ln.get("lcl_limit_a"))
        D.label(16, y + rh / 2 + 4, clip(ln.get("name") or f"L{ln.get('line_no')}", 30) + (f"  ({_rail_label(rail)})" if rail else ""),
                size=12)
        D.label(16 + label_w - 64, y + rh / 2 + 4, _amps(lcl) or "?", size=12, style="text2" if lcl else "caution")
        row = [ln.get("name") or f"L{ln.get('line_no')}", _amps(lcl) or "—"]
        loads = [x for x in ln.get("load_element_ids") or [] if x in idx]
        for j, m in enumerate(modes):
            x = x0 + j * cw
            if m["id"] not in modes_with_rows:
                D.cell(x, y, cw, rh, text="?", style="unknown", title=None)
                row.append("?")
                continue
            w = 0.0
            on = not ln.get("switchable", True)
            for le in loads:
                r = mem.get((m["id"], le))
                if r is None or not r.get("is_active", True) or (r.get("power_state") or "nominal") == "off":
                    continue
                on = True
                pw = _num(r.get("power_w_in_mode"))
                w += pw if pw is not None else (_num(idx[le].get("power_avg_w")) or 0.0)
            amps = (w / v) if (v and w) else None
            bad = bool(amps and lcl and amps > lcl)
            over += int(bad)
            txt = ("ON" + (f" {amps:.2f}A" if amps else "")) if on else "off"
            D.cell(x, y, cw, rh, text=txt, style="alarm" if bad else ("on" if on else "off"),
                   title=f"{ln.get('name')} · {m.get('name')}: {w:.1f} W" if on else None)
            totals_w[j] += w
            totals_a[j] += amps or 0.0
            row.append(txt)
        rows.append(row)
    yt = y0 + len(lines) * rh + 6
    D.label(16, yt + rh / 2 + 4, T("Σ switched load (W)"), size=12, weight=600)
    D.label(16, yt + rh * 1.5 + 4, T("Σ line current (A)"), size=12, weight=600)
    for j in range(len(modes)):
        D.cell(x0 + j * cw, yt, cw, rh, text=f"{totals_w[j]:.1f}", style="total")
        D.cell(x0 + j * cw, yt + rh, cw, rh, text=f"{totals_a[j]:.2f}", style="total")
    rows.append([T("Σ switched load (W)"), ""] + [f"{x:.1f}" for x in totals_w])
    D.legend([{"kind": "box", "style": "on", "label": T("Line ON")}, {"kind": "box", "style": "off", "label": T("Line off")},
              {"kind": "box", "style": "alarm", "label": T("Current above the LCL rating")},
              {"kind": "box", "style": "unknown", "label": T("No unit power states for the mode")}])
    no_rows = [m for m in modes if m["id"] not in modes_with_rows]
    if no_rows:
        D.gap("mode_states", T("missing: unit power states for {{n}} modes (Modes → Propose)", n=len(no_rows)), len(no_rows),
              fix="modes")
    if over:
        D.gap("lcl_exceeded", T("{{n}} line/mode cells exceed the LCL rating", n=over), over, severity="alarm", fix="electrical")
    empty = [ln for ln in lines if not ln.get("load_element_ids")]
    if empty:
        D.gap("empty_lines", T("{{n}} lines carry no load", n=len(empty)), len(empty), severity="info", fix="electrical")
    D.completeness(len(modes), len(modes) - len(no_rows))
    D.table([T("Line"), T("LCL")] + [m.get("name") or "" for m in modes], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── data bus topology

def _rate(bps: Any) -> str:
    v = _num(bps)
    if not v:
        return ""
    if v >= 1e6:
        return f"{v / 1e6:g} Mbit/s"
    if v >= 1e3:
        return f"{v / 1e3:g} kbit/s"
    return f"{v:g} bit/s"


def data_bus(d: DiagramData, **_: Any) -> dict:
    D = Diagram("data_bus", T("Data-handling block diagram — bus topology"), "graph",
                T("Each bus is a trunk; nodes with their addresses and rates; master in bold; point-to-point links below"))
    D.source("data buses", "bus nodes", "interfaces")
    buses = d.electrical.get("buses") or []
    nodes = d.electrical.get("nodes") or []
    idx = d.by_id
    if not buses:
        D.empty(T("No data buses yet: open Electrical (Data) and press Propose."))
        D.gap("no_buses", T("missing: data buses (Data → Propose)"), severity="alarm", fix="data")
    # order: nominal then its redundant twin
    order: list[dict] = []
    seen: set[str] = set()
    for b in sorted(buses, key=lambda b: (b.get("protocol") or "", b.get("segment") or "", b.get("name") or "")):
        if b["id"] in seen:
            continue
        order.append(b)
        seen.add(b["id"])
        twin = next((x for x in buses if x.get("redundant_with_id") == b["id"] or b.get("redundant_with_id") == x["id"]), None)
        if twin and twin["id"] not in seen:
            order.append(twin)
            seen.add(twin["id"])
    y = 30.0
    rows = []
    covered_ifaces: set[str] = set()
    no_addr = 0
    for b in order:
        mine = [n for n in nodes if n.get("bus_id") == b["id"] and n.get("element_id") in idx]
        mine.sort(key=lambda n: (n.get("role") != "master", n.get("address") if n.get("address") is not None else 1e9))
        x = 220.0
        boxes = []
        for n in mine:
            e = idx[n["element_id"]]
            lab = clip(e.get("name"), 22)
            w = max(104.0, text_w(lab, 13, True) + 22)
            boxes.append((n, e, x, w))
            x += w + 14
        trunk_y = y + 88
        x1 = max(x, 420.0)
        proto = b.get("protocol") or "?"
        head = f"{b.get('name') or proto} · {proto}" + (f" · {_rate(b.get('bit_rate_bps'))}" if b.get("bit_rate_bps") else "")
        D.label(16, trunk_y - 6, clip(head, 27), size=12, weight=600)
        D.label(16, trunk_y + 12, T("segment {{s}}", s=b.get("segment") or "A") if b.get("redundancy", "none") == "none"
                else T("segment {{s}} ({{r}} redundant)", s=b.get("segment") or "A", r=b.get("redundancy")), size=12, style="text3")
        D.node(f"bus:{b['id']}", "", 210, trunk_y - 3, x1 - 210, 6, shape="trunk", style="type-data",
               p=prov("bus", b["id"], origin=b.get("origin"), status=b.get("status")))
        for n, e, bx, w in boxes:
            master = n.get("role") == "master"
            addr = n.get("address")
            if addr is None:
                no_addr += 1
            badges = [f"0x{int(addr):02X}" if addr is not None else T("no address")]
            if n.get("data_rate_bps"):
                badges.append(_rate(n.get("data_rate_bps")))
            D.node(f"n:{n['id']}", clip(e.get("name"), 22), bx, y, w, 52 if master else 46, sub=T("master") if master else None,
                   badges=badges, style="accent" if master else (DOMAIN_STYLE.get(d.domain(e) or "", "default")
                                                                 if addr is not None else "caution"),
                   ref={"kind": "element", "id": e["id"]}, p=prov("node", n["id"], origin=n.get("origin"), status=n.get("status")))
            D.edge(f"drop:{n['id']}", f"n:{n['id']}", f"bus:{b['id']}", [(bx + w / 2, y + (52 if master else 46)), (bx + w / 2, trunk_y)],
                   itype="data", arrow="none")
            if n.get("interface_id"):
                covered_ifaces.add(n["interface_id"])
            rows.append([b.get("name") or proto, proto, e.get("name") or "", T("master") if master else T("node"),
                         f"0x{int(addr):02X}" if addr is not None else "—", _rate(n.get("data_rate_bps")) or "—",
                         _rate(b.get("bit_rate_bps")) or "—"])
        y = trunk_y + 40
    # point-to-point data links (data interfaces not carried by a bus node)
    bus_members = {(n.get("bus_id"), n.get("element_id")) for n in nodes}
    on_bus = {n.get("element_id") for n in nodes}
    protocols = {b.get("protocol") for b in buses}
    # a data link whose protocol is a bus's is carried by that bus (subsystem-level summary links included)
    p2p = [i for i in d.interfaces if i.get("interface_type") == "data" and i["id"] not in covered_ifaces
           and (i.get("properties") or {}).get("protocol") not in protocols
           and i.get("from_element_id") in idx and i.get("to_element_id") in idx]
    _ = (bus_members, on_bus)
    if p2p:
        D.label(16, y + 4, T("Point-to-point data links"), size=12, weight=600, style="text3")
        y += 16
        for k, i in enumerate(p2p[:24]):
            a, b2 = idx[i["from_element_id"]], idx[i["to_element_id"]]
            props = i.get("properties") or {}
            la, lb = clip(a.get("name"), 22), clip(b2.get("name"), 22)
            wa, wb = max(110.0, text_w(la, 13, True) + 22), max(110.0, text_w(lb, 13, True) + 22)
            D.node(f"pa{k}", la, 210, y, wa, 28, style=DOMAIN_STYLE.get(d.domain(a) or "", "default"),
                   ref={"kind": "element", "id": a["id"]}, p=prov("element", a["id"]))
            bx = 210 + wa + 150
            D.node(f"pb{k}", lb, bx, y, wb, 28, style=DOMAIN_STYLE.get(d.domain(b2) or "", "default"),
                   ref={"kind": "element", "id": b2["id"]}, p=prov("element", b2["id"]))
            lab = " · ".join(x for x in (props.get("protocol"), _rate(props.get("data_rate_bps"))) if x)
            D.edge(f"p2p{k}", f"pa{k}", f"pb{k}", [(210 + wa, y + 14), (bx, y + 14)], itype="data",
                   arrow="both" if (i.get("direction") or "bidirectional") == "bidirectional" else "end",
                   label=lab or None, faded=i.get("status") == "suggested", p=prov("interface", i["id"], status=i.get("status")))
            rows.append([T("point-to-point"), props.get("protocol") or "?", f"{a.get('name')} → {b2.get('name')}", "", "",
                         _rate(props.get("data_rate_bps")) or "—", ""])
            y += 38
    D.legend(type_legend(["data"]) + [{"kind": "box", "style": "accent", "label": T("Bus master")},
                                      {"kind": "box", "style": "caution", "label": T("Node without an address")}])
    if no_addr:
        D.gap("addresses", T("missing: bus addresses for {{n}} units", n=no_addr), no_addr, fix="data")
    no_rate = [b for b in buses if not b.get("bit_rate_bps")]
    if no_rate:
        D.gap("bit_rate", T("missing: bit rate for {{n}} buses", n=len(no_rate)), len(no_rate), fix="data")
    no_master = [b for b in buses if not any(n.get("bus_id") == b["id"] and n.get("role") == "master" for n in nodes)]
    if no_master:
        D.gap("no_master", T("{{n}} buses have no master node", n=len(no_master)), len(no_master), fix="data")
    D.completeness(len(nodes) + len(buses), len(nodes) - no_addr + len(buses) - len(no_rate))
    D.table([T("Bus"), T("Protocol"), T("Unit"), T("Role"), T("Address"), T("Node rate"), T("Bus rate")], rows)
    return D.finish()
