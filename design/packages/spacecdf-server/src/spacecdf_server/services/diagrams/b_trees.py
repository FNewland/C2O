"""Product tree, function tree, function × product allocation matrix, requirement tree."""
from __future__ import annotations

from typing import Any

from . import layout as L
from .base import DOMAIN_STYLE, Diagram, T, clip, plain, prov, text_w
from .data import DiagramData

TREE_TYPES = ("mission", "segment", "system", "subsystem", "component", "equipment")
# English text is the key (vocab.ts)
LEVEL_LABEL = {"mission": "Mission", "segment": "Segment", "system": "System / element", "subsystem": "Subsystem",
               "component": "Equipment", "equipment": "Equipment"}


def box_size(label: Any, sub: Any = None, *, minw: float = 92, maxw: float = 240, badges: Any = 0) -> tuple[float, float]:
    bl = badges if isinstance(badges, list) else []
    bw = sum(text_w(b, 12) + 14 for b in bl)
    w = max(text_w(clip(label, 30), 13, True), text_w(sub, 12) if sub else 0, bw) + 24
    h = 30 + (16 if sub else 0) + (16 if badges else 0)
    return max(minw, min(maxw, w)), h


def _fmt(v: Any, d: int = 1) -> str:
    try:
        return f"{float(v):.{d}f}"
    except (TypeError, ValueError):
        return ""


# ───────────────────────────────────────────────────────────── product tree

def product_tree(d: DiagramData, **_: Any) -> dict:
    D = Diagram("product_tree", T("Product tree"), "graph",
                T("ECSS-M-ST-10C product tree: mission → segment → system → subsystem → equipment"))
    D.source("elements")
    els = [e for e in d.elements if (e.get("element_type") or "") in TREE_TYPES]
    if not els:
        D.empty(T("No product tree yet: add the mission, segments and spacecraft in Blocks."))
        D.gap("no_elements", T("missing: product tree elements"), severity="alarm", fix="blocks")
        return D.finish()
    ids = {e["id"] for e in els}
    idx = {e["id"]: e for e in els}
    kids: dict[str, list[str]] = {}
    roots = []
    for e in sorted(els, key=lambda e: (e.get("element_type") != "mission", e.get("name") or "")):
        p = e.get("parent_id")
        if p in ids:
            kids.setdefault(p, []).append(e["id"])
        else:
            roots.append(e["id"])

    def label(eid: str) -> tuple[Any, Any, list]:
        e = idx[eid]
        q = int(e.get("quantity") or 1)
        lab = clip(e.get("name") or "?", 30) + (f" ×{q}" if q > 1 else "")
        badges = []
        if e.get("element_type") in ("component", "equipment"):
            if e.get("mass_kg"):
                badges.append(f"{_fmt(e['mass_kg'], 2)} kg")
            if e.get("kb_component_id"):
                badges.append("KB")
        return lab, T(LEVEL_LABEL.get(e.get("element_type") or "", "Equipment")), badges

    def size(eid: str) -> tuple[float, float]:
        lab, sub, b = label(eid)
        return box_size(lab, sub, badges=b)

    def stack(eid: str, depth: int) -> bool:
        ch = kids.get(eid, [])
        return bool(ch) and all(idx[c].get("element_type") in ("component", "equipment") and not kids.get(c) for c in ch)

    pos, edges = L.tree(roots, lambda n: kids.get(n, []), size, stack_fn=stack, hgap=14, vgap=30, y0=16)
    rows = []
    for eid, b in pos.items():
        e = idx[eid]
        lab, sub, badges = label(eid)
        D.node(eid, lab, b["x"], b["y"], b["w"], b["h"], sub=sub, badges=badges,
               style=DOMAIN_STYLE.get(d.domain(e) or "", "default") if e.get("element_type") in ("subsystem", "component") else
               ("emph" if e.get("element_type") in ("mission", "segment") else "default"),
               ref={"kind": "element", "id": eid}, p=prov("element", eid))
        rows.append([e.get("name") or "", T(LEVEL_LABEL.get(e.get("element_type") or "", "Equipment")),
                     (idx.get(e.get("parent_id") or "") or {}).get("name", ""), str(e.get("quantity") or 1),
                     _fmt(e.get("mass_kg"), 2), e.get("kb_component_id") or ""])
    for i, ed in enumerate(edges):
        D.edge(f"t{i}", ed["from"], ed["to"], ed["points"], arrow="none",
               style={"type": "tree", "dash": "", "width": 1.2, "color": "line"})
    # gaps
    subs = [e for e in els if e.get("element_type") == "subsystem"]
    units = [e for e in els if e.get("element_type") in ("component", "equipment")]
    empty_subs = [s for s in subs if not kids.get(s["id"])]
    no_mass = [u for u in units if not u.get("mass_kg")]
    if not subs:
        D.gap("no_subsystems", T("missing: subsystems under the spacecraft"), severity="alarm", fix="blocks")
    if empty_subs:
        D.gap("empty_subsystems", T("missing: equipment in {{n}} subsystems ({{names}})", n=len(empty_subs),
                                    names=", ".join(clip(s.get("name"), 16) for s in empty_subs[:4])),
              len(empty_subs), fix="blocks")
    if no_mass:
        D.gap("unit_mass", T("missing: mass for {{n}} units", n=len(no_mass)), len(no_mass), fix="blocks")
    try:
        from ..product_tree import misplaced
        bad = misplaced(els)
        if bad:
            D.gap("tree_level", T("{{n}} elements sit at the wrong product-tree level", n=len(bad)), len(bad),
                  severity="alarm", fix="blocks")
    except Exception:  # noqa: BLE001
        pass
    D.completeness(len(subs) + len(units), len(subs) - len(empty_subs) + len(units) - len(no_mass))
    D.table([T("Element"), T("Level"), T("Parent"), T("Qty"), T("Mass (kg)"), T("KB part")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── function tree

def _product_functions(d: DiagramData) -> list[dict]:
    """The functions of the product (wave 3, 3.R1): the processes the v2 import carries
    (``function_type == "process"``, e.g. "Manage the project") and their sub-functions are not
    allocated to a product, so the tree and the allocation matrix leave them out."""
    proc = {f["id"] for f in d.functions if f.get("function_type") == "process"}
    by_id = {f["id"]: f for f in d.functions}

    def under_process(f: dict) -> bool:
        seen = set()
        while f is not None and f["id"] not in seen:
            if f["id"] in proc:
                return True
            seen.add(f["id"])
            f = by_id.get(f.get("parent_id") or "")
        return False
    return [f for f in d.functions if not under_process(f)] if proc else list(d.functions)

def function_tree(d: DiagramData, **_: Any) -> dict:
    D = Diagram("function_tree", T("Function tree"), "graph",
                T("Functions decomposed to leaves; the allocated product is shown under each function"))
    D.source("functions", "function allocations")
    fns = _product_functions(d)
    if not fns:
        D.empty(T("No functions yet: build the function tree in Functions."))
        D.gap("no_functions", T("missing: function tree"), severity="alarm", fix="functions")
        return D.finish()
    ids = {f["id"] for f in fns}
    idx = {f["id"]: f for f in fns}
    kids: dict[str, list[str]] = {}
    roots = []
    for f in sorted(fns, key=lambda f: (f.get("created_at") or "", f.get("name") or "")):
        if f.get("parent_id") in ids:
            kids.setdefault(f["parent_id"], []).append(f["id"])
        else:
            roots.append(f["id"])
    els = d.by_id
    alloc: dict[str, list[str]] = {}
    for a in d.allocations:
        if a.get("element_id") in els:
            alloc.setdefault(a["function_id"], []).append(els[a["element_id"]].get("name") or "?")

    def sub(fid: str) -> Any:
        al = alloc.get(fid)
        if al:
            return "→ " + clip(", ".join(al), 28)
        return T("unallocated") if not kids.get(fid) else None

    def size(fid: str) -> tuple[float, float]:
        return box_size(idx[fid].get("name") or "?", sub(fid))

    def stack(fid: str, depth: int) -> bool:
        ch = kids.get(fid, [])
        return bool(ch) and all(not kids.get(c) for c in ch) and len(ch) > 2

    pos, edges = L.tree(roots, lambda n: kids.get(n, []), size, stack_fn=stack, hgap=14, vgap=30)
    leaves = [f for f in fns if not kids.get(f["id"])]
    unalloc = [f for f in leaves if not alloc.get(f["id"])]
    rows = []
    for fid, b in pos.items():
        f = idx[fid]
        leaf = not kids.get(fid)
        style = "caution" if leaf and not alloc.get(fid) else ("emph" if fid in roots else "default")
        D.node(fid, clip(f.get("name") or "?", 30), b["x"], b["y"], b["w"], b["h"], sub=sub(fid), style=style,
               badges=[f.get("layer")] if f.get("layer") and f.get("layer") != "SA" else [],
               ref={"kind": "function", "id": fid}, p=prov("function", fid))
        rows.append([f.get("name") or "", (idx.get(f.get("parent_id") or "") or {}).get("name", ""),
                     f.get("layer") or "", ", ".join(alloc.get(fid, [])) or ("—" if not leaf else T("unallocated"))])
    for i, ed in enumerate(edges):
        D.edge(f"t{i}", ed["from"], ed["to"], ed["points"], arrow="none",
               style={"type": "tree", "dash": "", "width": 1.2, "color": "line"})
    if unalloc:
        D.gap("unallocated", T("missing: allocation for {{n}} leaf functions", n=len(unalloc)), len(unalloc),
              fix="functions")
    D.legend([{"kind": "box", "style": "caution", "label": T("Leaf function not allocated to a product")}])
    D.completeness(len(leaves), len(leaves) - len(unalloc))
    D.table([T("Function"), T("Parent"), T("Layer"), T("Allocated to")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── allocation matrix

def allocation(d: DiagramData, **_: Any) -> dict:
    D = Diagram("allocation", T("Function × product allocation"), "matrix",
                T("Rows: leaf functions; columns: products they are allocated to"))
    D.source("functions", "function allocations", "elements")
    fns = _product_functions(d)
    if not fns:
        D.empty(T("No functions yet: build the function tree in Functions."))
        D.gap("no_functions", T("missing: function tree"), severity="alarm", fix="functions")
        return D.finish()
    parents = {f.get("parent_id") for f in fns}
    leaves = [f for f in fns if f["id"] not in parents]
    els = d.by_id
    pairs = {(a["function_id"], a["element_id"]) for a in d.allocations if a.get("element_id") in els}
    col_ids = sorted({e for _, e in pairs}, key=lambda e: (d.domain(els[e]) or "zz", els[e].get("name") or ""))
    subs = [e for e in d.elements if e.get("element_type") == "subsystem" and d.segment(e) == "space"]
    for s in subs:   # subsystems without any function still get a column (shows the gap)
        if s["id"] not in col_ids:
            col_ids.append(s["id"])
    cw, rh = 26.0, 22.0
    label_w = min(300.0, max((text_w(clip(f.get("name"), 40), 12) for f in leaves), default=120) + 16)
    head_h = min(170.0, max((text_w(clip(els[c].get("name"), 26), 12) for c in col_ids), default=60) + 14)
    x0, y0 = 16 + label_w, 16 + head_h
    for j, cid in enumerate(col_ids):
        e = els[cid]
        D.label(x0 + j * cw + cw / 2 + 4, y0 - 6, clip(e.get("name"), 26), rotate=-60, size=12)
    rows = []
    has_fn = set()
    for i, f in enumerate(leaves):
        y = y0 + i * rh
        D.label(16 + label_w - 8, y + rh / 2 + 4, clip(f.get("name"), 40), anchor="end", size=12,
                style="text" if any((f["id"], c) in pairs for c in col_ids) else "caution")
        mine = []
        for j, cid in enumerate(col_ids):
            on = (f["id"], cid) in pairs
            if on:
                has_fn.add(cid)
                mine.append(els[cid].get("name") or "")
            D.cell(x0 + j * cw, y, cw, rh, text="●" if on else None, style="on" if on else ("band" if i % 2 else "cell"),
                   title=f"{f.get('name')} → {els[cid].get('name')}" if on else None)
        rows.append([f.get("name") or "", ", ".join(mine) or T("unallocated")])
    unalloc = [r for r in rows if not isinstance(r[1], str)]
    covered = {(d.subsystem_of(els[c]) or {}).get("id") for c in has_fn}
    no_fn = [c for c in col_ids if c not in has_fn and c not in covered and els[c].get("element_type") == "subsystem"]
    if unalloc:
        D.gap("unallocated", T("missing: allocation for {{n}} leaf functions", n=len(unalloc)), len(unalloc), fix="functions")
    if no_fn:
        D.gap("subsystem_no_function", T("{{n}} subsystems carry no function", n=len(no_fn)), len(no_fn), severity="info")
    D.completeness(len(leaves), len(leaves) - len(unalloc))
    D.table([T("Function"), T("Allocated to")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── requirement tree

def req_tree(d: DiagramData, **_: Any) -> dict:
    D = Diagram("req_tree", T("Requirement tree and traceability"), "graph",
                T("Objectives → requirements by parent chain; level, verification method and status per requirement"))
    D.source("requirements", "mission objectives", "verification items")
    reqs = d.requirements
    if not reqs:
        D.empty(T("No requirements yet: write or generate them in Requirements."))
        D.gap("no_requirements", T("missing: requirements"), severity="alarm", fix="requirements")
        return D.finish()
    ids = {r["id"] for r in reqs}
    idx = {r["id"]: r for r in reqs}
    kids: dict[str, list[str]] = {}
    roots_r = []
    for r in sorted(reqs, key=lambda r: (r.get("code") or "", r["id"])):
        if r.get("parent_id") in ids:
            kids.setdefault(r["parent_id"], []).append(r["id"])
        else:
            roots_r.append(r["id"])
    objectives = []
    mn = getattr(d.study, "mission_need", None) if d.study is not None else None
    for o in (getattr(mn, "objectives", None) or []):
        objectives.append({"id": f"obj:{getattr(o, 'id', '')}", "oid": getattr(o, "id", ""), "text": getattr(o, "text", ""),
                           "traced": list(getattr(o, "traced_to_requirements", None) or [])})
    under: dict[str, list[str]] = {o["id"]: [] for o in objectives}
    traced = set()
    for o in objectives:
        for rid in roots_r:
            r = idx[rid]
            if r.get("objective_id") == o["oid"] or rid in o["traced"]:
                under[o["id"]].append(rid)
                traced.add(rid)
    loose = [rid for rid in roots_r if rid not in traced]
    roots = [o["id"] for o in objectives]
    if loose:
        roots.append("obj:none")
        under["obj:none"] = loose

    def children(n: str) -> list[str]:
        return under.get(n, []) if n.startswith("obj:") else kids.get(n, [])

    vitems = {v.get("requirement_id"): v for v in d.verification}

    def label(n: str) -> str:
        if n == "obj:none":
            return plain(T("Not traced to an objective"))
        if n.startswith("obj:"):
            o = next(o for o in objectives if o["id"] == n)
            return clip(f"{o['oid']}  {o['text']}", 70)
        r = idx[n]
        return clip(f"{r.get('code') or n}  {r.get('text') or ''}", 70)

    pos, edges, depth = L.indented(roots, children, row_h=26, indent=24, box_h=20,
                                   width=lambda n: min(480.0, text_w(label(n), 12) + 20))
    rows = []
    for n, b in pos.items():
        if n.startswith("obj:"):
            lab = T("Not traced to an objective") if n == "obj:none" else label(n)
            D.node(n, lab, b["x"], b["y"], b["w"], b["h"], shape="pill",
                   style="caution" if n == "obj:none" else "emph", p=prov("conops" if n != "obj:none" else "derived", n[4:]))
            continue
        r = idx[n]
        vm = (vitems.get(n) or {}).get("method") or r.get("verification_method")
        st = r.get("status") or "draft"
        style = {"violated": "alarm", "verified": "ok", "approved": "default"}.get(st, "default")
        if r.get("level") == "interface":
            style = "cat2"
        D.node(n, label(n), b["x"], b["y"], b["w"], b["h"], shape="row", style=style,
               badges=[r.get("level") or "", vm or "?"], ref={"kind": "requirement", "id": n},
               p=prov("requirement", n, status=st))
        rows.append([r.get("code") or n, r.get("level") or "", clip(r.get("text"), 90),
                     (idx.get(r.get("parent_id") or "") or {}).get("code", ""), vm or "—", st])
    for i, ed in enumerate(edges):
        D.edge(f"t{i}", ed["from"], ed["to"], ed["points"], arrow="none",
               style={"type": "tree", "dash": "", "width": 1.0, "color": "line"})
    no_vm = [r for r in reqs if not ((vitems.get(r["id"]) or {}).get("method") or r.get("verification_method"))]
    loose_all = len(loose)
    if loose_all:
        D.gap("untraced", T("{{n}} top requirements not traced to an objective", n=loose_all), loose_all, fix="requirements")
    if no_vm:
        D.gap("no_method", T("missing: verification method for {{n}} requirements", n=len(no_vm)), len(no_vm), fix="requirements")
    D.legend([{"kind": "box", "style": "cat2", "label": T("Interface requirement")},
              {"kind": "box", "style": "alarm", "label": T("Violated")},
              {"kind": "box", "style": "ok", "label": T("Verified")}])
    D.completeness(len(reqs) * 2, (len(reqs) - len(no_vm)) + (len(reqs) - loose_all))
    D.table([T("Code"), T("Level"), T("Text"), T("Parent"), T("Method"), T("Status")], rows)
    return D.finish()
