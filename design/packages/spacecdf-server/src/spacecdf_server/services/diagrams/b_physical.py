"""Physical block diagram (system level and unit drill-down) and the N² chart.

Unlike the Interfaces tab (siblings of one parent), these draw every accepted or suggested
link of the spacecraft, including unit-to-unit links that cross subsystem boundaries, and
the links to elements of other segments (ground station, launcher)."""
from __future__ import annotations

import math
from typing import Any

from . import layout as L
from .base import DOMAIN_STYLE, TYPE_CODE, TYPE_LABEL, Diagram, T, clip, prov, text_w, type_legend
from .data import DiagramData


def _scope(d: DiagramData) -> tuple[dict | None, list[dict], list[dict]]:
    """(spacecraft, its subsystems, its units). Falls back to every space subsystem/unit."""
    from ..product_tree import primary_spacecraft, subtree_ids
    sc = None
    try:
        sc = primary_spacecraft(d.elements)
    except Exception:  # noqa: BLE001
        sc = None
    if sc is not None:
        ids = subtree_ids(d.elements, sc["id"])
        pool = [e for e in d.elements if e["id"] in ids]
    else:
        pool = [e for e in d.elements if d.segment(e) == "space"]
    subs = [e for e in pool if e.get("element_type") == "subsystem"]
    units = [e for e in pool if e.get("element_type") in ("component", "equipment")]
    return sc, subs, units


def _owner_sub(d: DiagramData, e: dict, subs_ids: set[str]) -> str | None:
    s = d.subsystem_of(e)
    return s["id"] if s is not None and s["id"] in subs_ids else None


def block(d: DiagramData, level: str = "unit", focus: str | None = None, types: str | None = None, **_: Any) -> dict:
    level = "system" if level == "system" else "unit"
    title = T("Physical block diagram — system level") if level == "system" else T("Physical block diagram — equipment level")
    D = Diagram("block", title, "graph",
                T("Interfaces coded by type (colour and line pattern); links across subsystems included"))
    D.source("elements", "interfaces")
    sc, subs, units = _scope(d)
    if not subs and not units:
        D.empty(T("No spacecraft subsystems or equipment yet."))
        D.gap("no_elements", T("missing: subsystems and equipment"), severity="alarm", fix="blocks")
        return D.finish()
    #: mechanical mounts and conductive paths (every unit to the structure) are drawn in the
    #: stack and thermal diagrams; the equipment-level block diagram hides them unless asked
    hidden_default = {"mechanical", "thermal"} if level == "unit" and not types else set()
    want_types = set((types or "").split(",")) - {"", "all"}
    idx = d.by_id
    sub_ids = {s["id"] for s in subs}
    unit_ids = {u["id"] for u in units}
    scope_ids = sub_ids | unit_ids | ({sc["id"]} if sc else set())
    # external elements: other segments linked to the spacecraft
    ext: dict[str, dict] = {}
    links = []
    hidden: list[dict] = []
    for i in d.interfaces:
        a, b = i.get("from_element_id"), i.get("to_element_id")
        if a not in idx or b not in idx:
            continue
        ina, inb = a in scope_ids, b in scope_ids
        if not (ina or inb):
            continue
        if want_types and i.get("interface_type") not in want_types:
            continue
        if i.get("interface_type") in hidden_default:
            hidden.append(i)
            continue
        for x, inside in ((a, ina), (b, inb)):
            if not inside:
                ext[x] = idx[x]
        links.append(i)
    sorted_subs = sorted(subs, key=lambda s: (list(DOMAIN_STYLE).index(s.get("subsystem_domain"))
                                              if s.get("subsystem_domain") in DOMAIN_STYLE else 99, s.get("name") or ""))

    def endpoint(eid: str) -> str | None:
        """Display node of an interface end."""
        if eid in ext:
            return f"x:{eid}"
        e = idx[eid]
        if level == "system":
            if eid in sub_ids:
                return eid
            s = _owner_sub(d, e, sub_ids)
            return s or (f"x:{eid}" if eid == (sc or {}).get("id") else None)
        if eid in unit_ids or eid in sub_ids:
            return eid
        if sc and eid == sc["id"]:
            return "sc"
        return None

    shown_links = []
    for i in links:
        a, b = endpoint(i["from_element_id"]), endpoint(i["to_element_id"])
        if a is None or b is None or a == b:
            continue
        shown_links.append((i, a, b))

    focus_sub = focus if focus in sub_ids else None
    if focus_sub:
        D.m["title"] = T("Physical block diagram — {{name}} and its links", name=idx[focus_sub].get("name") or "")
        mine = {u["id"] for u in units if _owner_sub(d, u, sub_ids) == focus_sub} | {focus_sub}
        shown_links = [(i, a, b) for i, a, b in shown_links if a in mine or b in mine]
        keep = mine | {a for _, a, _ in shown_links} | {b for _, _, b in shown_links}
    else:
        keep = None

    cells: list[dict] = []
    if level == "system":
        for s in sorted_subs:
            lab = clip(s.get("name"), 22)
            n_units = sum(1 for u in units if _owner_sub(d, u, sub_ids) == s["id"])
            cells.append({"id": s["id"], "w": max(120.0, text_w(lab, 13, True) + 24), "h": 46, "items": None,
                          "label": lab, "sub": T("{{n}} units", n=n_units), "el": s})
        for eid, e in ext.items():
            cells.append({"id": f"x:{eid}", "w": max(120.0, text_w(clip(e.get('name'), 22), 13, True) + 24), "h": 46,
                          "items": None, "label": clip(e.get("name"), 22), "sub": T("External"), "el": e})
        # aggregate per (a, b, type)
        agg: dict[tuple, list] = {}
        for i, a, b in shown_links:
            key = (min(a, b), max(a, b), i.get("interface_type") or "data")
            agg.setdefault(key, []).append(i)
        rlinks = [{"id": f"{k[0]}|{k[1]}|{k[2]}", "from": k[0], "to": k[1]} for k in agg]
    else:
        deg: dict[str, int] = {}
        for _, a, b in shown_links:
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1

        def uh(eid: str) -> float:
            """Unit height grows with its link count so the ports stay apart."""
            return max(28.0, min(96.0, 5.0 * deg.get(eid, 0) + 8))
        groups: dict[str, list[dict]] = {}
        loose: list[dict] = []
        for u in units:
            s = _owner_sub(d, u, sub_ids)
            if keep is not None and u["id"] not in keep:
                continue
            (groups.setdefault(s, []) if s else loose).append(u)
        for s in sorted_subs:
            items = groups.get(s["id"], [])
            if keep is not None and s["id"] not in keep and not items:
                continue
            its = [{"id": u["id"], "w": min(190.0, max(110.0, text_w(clip(u.get("name"), 26), 12, True) + 22)), "h": uh(u["id"]),
                    "el": u} for u in sorted(items, key=lambda u: u.get("name") or "")]
            if not its:
                its = [{"id": f"empty:{s['id']}", "w": 110, "h": 24, "el": None}]
            cells.append({"id": s["id"], "w": 0, "h": 0, "items": its, "label": clip(s.get("name"), 24), "el": s})
        if loose:
            cells.append({"id": "loose", "w": 0, "h": 0, "label": T("Not in a subsystem"), "el": None,
                          "items": [{"id": u["id"], "w": 150, "h": 28, "el": u} for u in loose]})
        if ext or any(a == "sc" or b == "sc" for _, a, b in shown_links):
            its = [{"id": f"x:{eid}", "w": min(190.0, max(110.0, text_w(clip(e.get('name'), 26), 12, True) + 22)), "h": 28,
                    "el": e} for eid, e in ext.items()]
            if any(a == "sc" or b == "sc" for _, a, b in shown_links):
                its.insert(0, {"id": "sc", "w": 150, "h": 28, "el": sc})
            cells.append({"id": "ext", "w": 0, "h": 0, "items": its, "label": T("Spacecraft level and external"), "el": None})
        present = {c["id"] for c in cells} | {it["id"] for c in cells for it in (c.get("items") or [])}
        shown_links = [(i, a, b) for i, a, b in shown_links if a in present and b in present]
        rlinks = [{"id": i["id"], "from": a, "to": b} for i, a, b in shown_links]
    if not cells:
        D.empty(T("Nothing to draw for this selection."))
        return D.finish()
    ncols = max(1, min(4, math.ceil(math.sqrt(len(cells) * 1.4))))
    cbox, ibox, routed = L.grid_route(cells, rlinks, cols=ncols, cgap=26, lane=4, y0=16)
    for c in cells:
        b = cbox[c["id"]]
        e = c.get("el")
        if c.get("items") is None:
            dom = (e or {}).get("subsystem_domain")
            D.node(c["id"], c["label"], b["x"], b["y"], b["w"], b["h"], sub=c.get("sub"),
                   style=DOMAIN_STYLE.get(dom or "", "muted" if c["id"].startswith("x:") else "default"),
                   ref={"kind": "element", "id": e["id"]} if e else None, p=prov("element", (e or {}).get("id")))
            continue
        dom = (e or {}).get("subsystem_domain")
        D.group(c["id"], c["label"], b["x"], b["y"], b["w"], b["h"],
                style="group-" + DOMAIN_STYLE.get(dom or "", "default") if dom else "group",
                ref={"kind": "element", "id": e["id"]} if e else None, p=prov("element", (e or {}).get("id")))
        for it in c["items"]:
            ib = ibox[it["id"]]
            ue = it.get("el")
            if ue is None:
                D.node(it["id"], T("no equipment"), ib["x"], ib["y"], ib["w"], ib["h"], style="muted", group=c["id"],
                       p=prov("derived"))
                continue
            q = int(ue.get("quantity") or 1)
            D.node(it["id"], clip(ue.get("name"), 26) + (f" ×{q}" if q > 1 else ""), ib["x"], ib["y"], ib["w"], ib["h"],
                   style=DOMAIN_STYLE.get(d.domain(ue) or "", "default") if c["id"] != "ext" else "muted", group=c["id"],
                   ref={"kind": "element", "id": ue["id"]}, p=prov("element", ue["id"]))
    types_used = []
    rows = []
    if level == "system":
        for r in routed:
            a, b, t = r["id"].split("|")
            ifs = agg[(a, b, t)]
            types_used.append(t)
            sugg = all(i.get("status") == "suggested" for i in ifs)
            D.edge(r["id"], a, b, r["points"], itype=t, arrow="none", label=f"×{len(ifs)}" if len(ifs) > 1 else None,
                   faded=sugg, p=prov("interface", ",".join(i["id"] for i in ifs[:20]),
                                      status="suggested" if sugg else "accepted"))
    else:
        by_id = {i["id"]: (i, a, b) for i, a, b in shown_links}
        for r in routed:
            i, a, b = by_id[r["id"]]
            t = i.get("interface_type") or "data"
            types_used.append(t)
            dirn = i.get("direction") or "bidirectional"
            D.edge(i["id"], a, b, r["points"], itype=t,
                   arrow="both" if dirn == "bidirectional" else ("end" if dirn != "reverse" else "start"),
                   faded=i.get("status") == "suggested",
                   p=prov("interface", i["id"], origin=i.get("origin"), status=i.get("status")))
    for i, a, b in shown_links:
        rows.append([idx[i["from_element_id"]].get("name") or "", idx[i["to_element_id"]].get("name") or "",
                     T(TYPE_LABEL.get(i.get("interface_type") or "data", "Data")), i.get("subtype") or "",
                     i.get("name") or "", T("Yes") if (_owner_sub(d, idx[i["from_element_id"]], sub_ids)
                                                       != _owner_sub(d, idx[i["to_element_id"]], sub_ids)) else T("No"),
                     i.get("status") or ""])
    leg = type_legend(types_used)
    if any(i.get("status") == "suggested" for i, _, _ in shown_links):
        leg.append({"kind": "line", "type": "data", "faded": True, "label": T("Faded: suggested, not yet accepted"),
                    "dash": "", "width": 1.4})
    D.legend(leg)
    linked = {i["from_element_id"] for i, _, _ in shown_links} | {i["to_element_id"] for i, _, _ in shown_links} \
        | {i["from_element_id"] for i in hidden} | {i["to_element_id"] for i in hidden}
    isolated = [u for u in units if u["id"] not in linked and (keep is None or u["id"] in keep)]
    sugg = [i for i, _, _ in shown_links if i.get("status") == "suggested"]
    if isolated and not want_types:
        D.gap("isolated_units", T("missing: interfaces for {{n}} units ({{names}})", n=len(isolated),
                                  names=", ".join(clip(u.get("name"), 14) for u in isolated[:3])), len(isolated),
              fix="interfaces")
    if sugg:
        D.gap("suggested_links", T("{{n}} links still suggested (accept or reject them in Interfaces)", n=len(sugg)),
              len(sugg), severity="info", fix="interfaces")
    if hidden:
        D.gap("hidden_types", T("{{n}} mechanical and thermal links hidden here (see the stack and thermal diagrams)",
                                n=len(hidden)), len(hidden), severity="info")
    D.completeness(len(units), len(units) - len(isolated))
    D.table([T("From"), T("To"), T("Type"), T("Subtype"), T("Name"), T("Crosses subsystems"), T("Status")], rows)
    D.m["options"] = {"level": level, "focus": focus_sub, "types": sorted(want_types) or None,
                    "hidden_types": sorted(hidden_default), "subsystems": [{"id": s["id"], "name": s.get("name")}
                                                                          for s in sorted_subs]}
    return D.finish()


def n2(d: DiagramData, level: str = "unit", **_: Any) -> dict:
    level = "system" if level == "system" else "unit"
    D = Diagram("n2", T("N² chart"), "matrix",
                T("Row element sends to column element; type codes in the cells (P power, D data, RF, M mechanical, Th thermal, S discrete)"))
    D.source("elements", "interfaces")
    sc, subs, units = _scope(d)
    sub_ids = {s["id"] for s in subs}
    idx = d.by_id
    if level == "system":
        items = sorted(subs, key=lambda s: (list(DOMAIN_STYLE).index(s.get("subsystem_domain"))
                                            if s.get("subsystem_domain") in DOMAIN_STYLE else 99, s.get("name") or ""))
    else:
        items = sorted(units, key=lambda u: (list(DOMAIN_STYLE).index(d.domain(u)) if d.domain(u) in DOMAIN_STYLE else 99,
                                             u.get("name") or ""))
    if len(items) < 2:
        D.empty(T("An N² chart needs at least two elements."))
        D.gap("no_elements", T("missing: subsystems and equipment"), severity="alarm", fix="blocks")
        return D.finish()
    pos = {e["id"]: k for k, e in enumerate(items)}

    def rep(eid: str) -> str | None:
        if eid in pos:
            return eid
        e = idx.get(eid)
        if e is None:
            return None
        if level == "system":
            s = _owner_sub(d, e, sub_ids)
            return s if s in pos else None
        return None

    cells: dict[tuple[int, int], dict[str, list[str]]] = {}
    for i in d.interfaces:
        a, b = rep(i.get("from_element_id")), rep(i.get("to_element_id"))
        if a is None or b is None or a == b:
            continue
        t = i.get("interface_type") or "data"
        pairs = [(pos[a], pos[b])]
        if (i.get("direction") or "bidirectional") == "bidirectional":
            pairs.append((pos[b], pos[a]))
        for p in pairs:
            cells.setdefault(p, {}).setdefault(t, []).append(i["id"])
    n = len(items)
    cs = 34.0 if n <= 18 else 28.0
    label_w = min(230.0, max(text_w(f"{k + 1}  {clip(e.get('name'), 28)}", 12) for k, e in enumerate(items)) + 18)
    x0, y0 = 16 + label_w, 40.0
    rows = []
    for k, e in enumerate(items):
        dom = d.domain(e) if level == "unit" else e.get("subsystem_domain")
        D.label(16 + label_w - 8, y0 + k * cs + cs / 2 + 4, f"{clip(e.get('name'), 28)}  {k + 1}", anchor="end", size=12)
        D.label(x0 + k * cs + cs / 2, y0 - 8, str(k + 1), anchor="middle", size=12, weight=600)
        for j in range(n):
            x, y = x0 + j * cs, y0 + k * cs
            if j == k:
                D.cell(x, y, cs, cs, text=str(k + 1), style="diag-" + DOMAIN_STYLE.get(dom or "", "default"),
                       title=e.get("name"))
                continue
            got = cells.get((k, j))
            if got:
                codes = [{"type": t, "c": TYPE_CODE.get(t, "?")} for t in sorted(got, key=lambda t: list(TYPE_CODE).index(t)
                                                                                   if t in TYPE_CODE else 99)]
                D.cell(x, y, cs, cs, style="n2", codes=codes,
                       title=f"{e.get('name')} → {items[j].get('name')}: " + ", ".join(TYPE_LABEL.get(t, t) for t in got),
                       ids=[x for v in got.values() for x in v][:12])
                rows.append([e.get("name") or "", items[j].get("name") or "",
                             ", ".join(TYPE_CODE.get(t, t) for t in got), str(sum(len(v) for v in got.values()))])
            else:
                D.cell(x, y, cs, cs, style="band" if (k + j) % 2 else "cell")
    D.legend(type_legend([t for v in cells.values() for t in v]))
    # domain bands under the header (grouping)
    linked = {k for k, _ in cells} | {j for _, j in cells}
    lonely = [items[k] for k in range(n) if k not in linked]
    if lonely:
        D.gap("isolated_units", T("missing: interfaces for {{n}} units ({{names}})", n=len(lonely),
                                  names=", ".join(clip(u.get("name"), 14) for u in lonely[:3])), len(lonely), fix="interfaces")
    D.completeness(n, n - len(lonely))
    D.table([T("From"), T("To"), T("Types"), T("Links")], rows)
    D.m["options"] = {"level": level}
    return D.finish()
