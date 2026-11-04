"""Deterministic layouts for the diagram models (no layout engine on the client).

* :func:`tree` — top-down tree; from ``stack_depth`` on, children stack vertically under
  their parent (org-chart style) so wide equipment levels stay readable.
* :func:`indented` — an outline tree (one row per item), for long requirement lists.
* :func:`layered` — left-to-right layers with barycentre ordering and orthogonal edges.
* :func:`grid_route` — boxes (or groups of boxes) on a grid with orthogonal edges routed
  through the channels between the cells, so no edge crosses a box.

All functions return plain coordinates; ``Diagram`` turns them into nodes and edges.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

Box = dict[str, float]


# ───────────────────────────────────────────────────────────── trees

def tree(roots: list[str], children: Callable[[str], list[str]], size: Callable[[str], tuple[float, float]],
         *, stack_depth: int = 99, stack_fn: Callable[[str, int], bool] | None = None, hgap: float = 16, vgap: float = 34, indent: float = 18, svgap: float = 8,
         x0: float = 16, y0: float = 16) -> tuple[dict[str, Box], list[dict]]:
    """Positions ``{id: {x,y,w,h}}`` and edges ``[{from,to,points}]``."""
    pos: dict[str, Box] = {}
    edges: list[dict] = []

    def stacked(nid: str, depth: int) -> bool:
        return stack_fn(nid, depth) if stack_fn else depth + 1 >= stack_depth

    def measure(nid: str, depth: int) -> tuple[float, float]:
        w, h = size(nid)
        kids = children(nid)
        if not kids:
            return w, h
        if stacked(nid, depth):
            ws, hs = zip(*(measure(k, depth + 1) for k in kids))
            return max(w, indent + max(ws)), h + sum(hs) + svgap * len(kids)
        dims = [measure(k, depth + 1) for k in kids]
        return max(w, sum(d[0] for d in dims) + hgap * (len(dims) - 1)), h + vgap + max(d[1] for d in dims)

    def place(nid: str, depth: int, x: float, y: float) -> float:
        """Place the subtree with its left edge at x; returns its width."""
        w, h = size(nid)
        kids = children(nid)
        sw, _ = measure(nid, depth)
        if not kids:
            pos[nid] = {"x": x, "y": y, "w": w, "h": h}
            return sw
        if stacked(nid, depth):
            pos[nid] = {"x": x, "y": y, "w": w, "h": h}
            cy = y + h + svgap
            for k in kids:
                _, kh = measure(k, depth + 1)
                place(k, depth + 1, x + indent, cy)
                kb = pos[k]
                sx = x + min(10.0, w / 2)
                edges.append({"from": nid, "to": k, "points": [(sx, y + h), (sx, kb["y"] + kb["h"] / 2),
                                                               (kb["x"], kb["y"] + kb["h"] / 2)]})
                cy += kh + svgap
            return sw
        dims = [measure(k, depth + 1) for k in kids]
        total = sum(d[0] for d in dims) + hgap * (len(dims) - 1)
        cx = x + (sw - total) / 2
        centres = []
        for k, d in zip(kids, dims):
            place(k, depth + 1, cx, y + h + vgap)
            centres.append(pos[k]["x"] + pos[k]["w"] / 2)
            cx += d[0] + hgap
        # parent centred over the span of its children's boxes
        mid = (centres[0] + centres[-1]) / 2
        pos[nid] = {"x": mid - w / 2, "y": y, "w": w, "h": h}
        by = y + h + vgap / 2
        for k in kids:
            kb = pos[k]
            kx = kb["x"] + kb["w"] / 2
            edges.append({"from": nid, "to": k, "points": [(mid, y + h), (mid, by), (kx, by), (kx, kb["y"])]})
        return sw

    x = x0
    for r in roots:
        x += place(r, 0, x, y0) + hgap * 2
    # normalise: no negative x
    minx = min((b["x"] for b in pos.values()), default=x0)
    if minx < x0:
        dx = x0 - minx
        for b in pos.values():
            b["x"] += dx
        for e in edges:
            e["points"] = [(px + dx, py) for px, py in e["points"]]
    return pos, edges


def indented(roots: list[str], children: Callable[[str], list[str]], *, row_h: float = 26, indent: float = 22,
             x0: float = 16, y0: float = 16, box_h: float = 20, width: Callable[[str], float] | None = None
             ) -> tuple[dict[str, Box], list[dict], dict[str, int]]:
    """Outline tree: positions, connector edges and the depth of every item."""
    pos: dict[str, Box] = {}
    depth: dict[str, int] = {}
    edges: list[dict] = []
    row = [0]

    def walk(nid: str, d: int, parent: str | None) -> None:
        y = y0 + row[0] * row_h
        row[0] += 1
        x = x0 + d * indent
        pos[nid] = {"x": x, "y": y, "w": width(nid) if width else 200, "h": box_h}
        depth[nid] = d
        if parent is not None:
            pb = pos[parent]
            sx = pb["x"] + 8
            edges.append({"from": parent, "to": nid, "points": [(sx, pb["y"] + box_h), (sx, y + box_h / 2),
                                                                (x, y + box_h / 2)]})
        for k in children(nid):
            walk(k, d + 1, nid)

    for r in roots:
        walk(r, 0, None)
    return pos, edges, depth


# ───────────────────────────────────────────────────────────── layered (left → right)

def layered(nodes: list[str], edges: list[tuple[str, str]], size: Callable[[str], tuple[float, float]], *,
            ranks: dict[str, int] | None = None, rank_gap: float = 70, node_gap: float = 14,
            x0: float = 16, y0: float = 16, sweeps: int = 6, lane: float = 6) -> tuple[dict[str, Box], list[dict]]:
    """Layered layout. ``ranks`` fixes the column of some nodes; the others get the
    longest-path rank from the edges (cycles broken by ignoring back edges)."""
    succ: dict[str, list[str]] = defaultdict(list)
    pred: dict[str, list[str]] = defaultdict(list)
    for a, b in edges:
        if a in nodes and b in nodes and a != b:
            succ[a].append(b)
            pred[b].append(a)
    rank: dict[str, int] = dict(ranks or {})
    # longest path from sources (DFS with an on-stack set to skip back edges)
    order: list[str] = []
    state: dict[str, int] = {}

    def dfs(n: str) -> None:
        state[n] = 1
        for m in succ[n]:
            if state.get(m) == 1:
                continue
            if m not in state:
                dfs(m)
        state[n] = 2
        order.append(n)

    for n in nodes:
        if n not in state:
            dfs(n)
    for n in reversed(order):
        if n in (ranks or {}):
            continue
        ps = [rank[p] for p in pred[n] if p in rank and order.index(p) > order.index(n)]
        rank[n] = (max(ps) + 1) if ps else rank.get(n, 0)
    for n in nodes:
        rank.setdefault(n, 0)
    cols: dict[int, list[str]] = defaultdict(list)
    for n in nodes:
        cols[rank[n]].append(n)
    rmax = max(cols) if cols else 0
    # barycentre sweeps
    idx = {n: i for c in cols.values() for i, n in enumerate(c)}
    for s in range(sweeps):
        rng = range(1, rmax + 1) if s % 2 == 0 else range(rmax - 1, -1, -1)
        for r in rng:
            nb = pred if s % 2 == 0 else succ

            def bc(n: str) -> float:
                v = [idx[m] for m in nb[n] if m in idx and rank[m] != r]
                return sum(v) / len(v) if v else idx[n]
            cols[r].sort(key=bc)
            for i, n in enumerate(cols[r]):
                idx[n] = i
    # x per rank
    widths = {r: max((size(n)[0] for n in cols.get(r, [])), default=0) for r in range(rmax + 1)}
    xs: dict[int, float] = {}
    x = x0
    for r in range(rmax + 1):
        xs[r] = x
        x += widths[r] + rank_gap
    # y: stack each column, then pull towards neighbours' centres (two passes), no overlap
    pos: dict[str, Box] = {}
    for r in range(rmax + 1):
        y = y0
        for n in cols.get(r, []):
            w, h = size(n)
            pos[n] = {"x": xs[r] + (widths[r] - w) / 2, "y": y, "w": w, "h": h}
            y += h + node_gap
    # alternate pulls (towards successors right-to-left, towards predecessors left-to-right);
    # the last pass is left-to-right so a node with one predecessor lines up with it
    passes = []
    for _ in range(3):
        passes += [("succ", r) for r in range(rmax, -1, -1)] + [("pred", r) for r in range(rmax + 1)]
    for which, r in passes:
        col = cols.get(r, [])
        want = []
        for n in col:
            nb = [m for m in (pred[n] if which == "pred" else succ[n]) if m in pos and rank[m] != r]
            c = (sum(pos[m]["y"] + pos[m]["h"] / 2 for m in nb) / len(nb)) if nb else pos[n]["y"] + pos[n]["h"] / 2
            want.append(c - pos[n]["h"] / 2)
        ys = list(want)
        for i in range(1, len(col)):
            ys[i] = max(ys[i], ys[i - 1] + pos[col[i - 1]]["h"] + node_gap)
        # pull the block back up as far as the wants allow (keeps it centred on its targets)
        if col:
            excess = sum(y - w for y, w in zip(ys, want)) / len(col)
            if excess > 0:
                ys = [y - excess for y in ys]
                for i in range(1, len(col)):
                    ys[i] = max(ys[i], ys[i - 1] + pos[col[i - 1]]["h"] + node_gap)
        for n, yy in zip(col, ys):
            pos[n]["y"] = yy
    miny = min((b["y"] for b in pos.values()), default=y0)
    for b in pos.values():
        b["y"] += y0 - miny
    # orthogonal edges: right side → mid channel (lane per edge) → left side
    out: list[dict] = []
    per_gap: dict[int, int] = defaultdict(int)
    plan = []
    for a, b in edges:
        if a not in pos or b not in pos:
            continue
        plan.append((a, b))
        per_gap[rank[a]] += 1
    used: dict[int, int] = defaultdict(int)
    for a, b in plan:
        pa, pb = pos[a], pos[b]
        ra = rank[a]
        n = per_gap[ra]
        k = used[ra]
        used[ra] += 1
        off = (k - (n - 1) / 2) * min(lane, (rank_gap - 20) / max(n, 1))
        sy = pa["y"] + pa["h"] / 2
        ty = pb["y"] + pb["h"] / 2
        if rank[b] > ra:
            sx = pa["x"] + pa["w"]
            tx = pb["x"]
            mx = xs[ra] + widths[ra] + rank_gap / 2 + off
            pts = [(sx, sy), (mx, sy), (mx, ty), (tx, ty)] if abs(sy - ty) > 0.5 else [(sx, sy), (tx, ty)]
        else:  # same or backward rank: loop below both boxes
            sx = pa["x"] + pa["w"] / 2
            tx = pb["x"] + pb["w"] / 2
            by = max(pa["y"] + pa["h"], pb["y"] + pb["h"]) + 12 + abs(off)
            pts = [(sx, pa["y"] + pa["h"]), (sx, by), (tx, by), (tx, pb["y"] + pb["h"])]
        out.append({"from": a, "to": b, "points": pts})
    return pos, out


# ───────────────────────────────────────────────────────────── grid with channel routing

def grid_route(cells: list[dict], links: list[dict], *, cols: int, cgap: float = 28, lane: float = 5,
               x0: float = 16, y0: float = 16, side_pad: float = 6) -> tuple[dict[str, Box], dict[str, Box], list[dict]]:
    """Place ``cells`` (each ``{id, w, h, items: [{id, w, h}] | None}``) on a grid of ``cols``
    columns and route ``links`` (``{id, from, to}`` between item ids or cell ids) orthogonally
    through the channels between cells.

    A cell with ``items`` is a group: its items stack inside it (header ``head`` px). Returns
    (cell boxes, item boxes, routed links ``{id, from, to, points}``).
    Channels widen with the number of lanes they carry, so parallel edges never overlap.
    """
    head = 22.0
    ipad = 8.0
    igap = 8.0
    # measure groups
    for c in cells:
        if c.get("items"):
            c["w"] = max(c.get("w", 0), max(i["w"] for i in c["items"]) + 2 * ipad)
            c["h"] = head + sum(i["h"] for i in c["items"]) + igap * (len(c["items"]) - 1) + ipad
    rows = (len(cells) + cols - 1) // cols
    grid = [[None] * cols for _ in range(rows)]
    for i, c in enumerate(cells):
        grid[i // cols][i % cols] = c
        c["_r"], c["_c"] = i // cols, i % cols
    owner: dict[str, dict] = {}
    for c in cells:
        owner[c["id"]] = c
        for it in c.get("items") or []:
            owner[it["id"]] = c

    def endpoint_cell(eid: str) -> dict | None:
        return owner.get(eid)

    # plan channel usage: vertical channel v ∈ 0..cols (left of column v), horizontal h ∈ 0..rows
    vcount: dict[int, int] = defaultdict(int)
    hcount: dict[int, int] = defaultdict(int)
    plans = []
    for ln in links:
        ca, cb = endpoint_cell(ln["from"]), endpoint_cell(ln["to"])
        if ca is None or cb is None:
            continue
        if ca is cb:
            va = vb = ca["_c"] + 1
            hk = None
        else:
            if ca["_c"] < cb["_c"]:
                va, vb = ca["_c"] + 1, cb["_c"]
            elif ca["_c"] > cb["_c"]:
                va, vb = ca["_c"], cb["_c"] + 1
            else:
                va = vb = ca["_c"] + 1
            if va == vb:
                hk = None
            elif ca["_r"] == cb["_r"]:
                hk = None if abs(va - vb) == 0 else ca["_r"] + 1   # below the row
            else:
                hk = min(ca["_r"], cb["_r"]) + 1
            if hk is None and va != vb:
                hk = ca["_r"] + 1
        plans.append((ln, ca, cb, va, vb, hk))
        vcount[va] += 1
        if vb != va:
            vcount[vb] += 1
        if hk is not None:
            hcount[hk] += 1
    vw = {v: cgap + lane * vcount.get(v, 0) for v in range(cols + 1)}
    hh = {h: cgap * 0.8 + lane * hcount.get(h, 0) for h in range(rows + 1)}
    colw = [max((grid[r][c]["w"] for r in range(rows) if grid[r][c]), default=0) for c in range(cols)]
    rowh = [max((grid[r][c]["h"] for c in range(cols) if grid[r][c]), default=0) for r in range(rows)]
    vx: dict[int, float] = {}
    x = x0
    for c in range(cols):
        vx[c] = x
        x += vw[c]
        for r in range(rows):
            if grid[r][c]:
                grid[r][c]["_x"] = x
        x += colw[c]
    vx[cols] = x
    hy: dict[int, float] = {}
    y = y0
    for r in range(rows):
        hy[r] = y
        y += hh[r]
        for c in range(cols):
            if grid[r][c]:
                grid[r][c]["_y"] = y
        y += rowh[r]
    hy[rows] = y
    cbox: dict[str, Box] = {}
    ibox: dict[str, Box] = {}
    for c in cells:
        cw = colw[c["_c"]] if c.get("items") else c["w"]
        cbox[c["id"]] = {"x": c["_x"] + (colw[c["_c"]] - cw) / 2, "y": c["_y"], "w": cw, "h": c["h"]}
        if c.get("items"):
            yy = c["_y"] + head
            for it in c["items"]:
                ibox[it["id"]] = {"x": cbox[c["id"]]["x"] + ipad, "y": yy, "w": cbox[c["id"]]["w"] - 2 * ipad,
                                  "h": it["h"]}
                yy += it["h"] + igap

    def box(eid: str) -> Box:
        return ibox.get(eid) or cbox[eid]

    vused: dict[int, int] = defaultdict(int)
    hused: dict[int, int] = defaultdict(int)
    # per-box side slots so several edges leaving one box do not start at the same point
    side_n: dict[tuple[str, str], int] = defaultdict(int)
    side_k: dict[tuple[str, str], int] = defaultdict(int)

    def side_of(eid: str, v: int) -> str:
        b = box(eid)
        return "R" if vx[v] >= b["x"] + b["w"] - 1 else "L"
    for ln, ca, cb, va, vb, hk in plans:
        side_n[(ln["from"], side_of(ln["from"], va))] += 1
        side_n[(ln["to"], side_of(ln["to"], vb))] += 1

    def lane_x(v: int) -> float:
        k = vused[v]
        vused[v] += 1
        n = vcount[v]
        return vx[v] + vw[v] / 2 + (k - (n - 1) / 2) * lane

    def lane_y(h: int) -> float:
        k = hused[h]
        hused[h] += 1
        n = hcount[h]
        return hy[h] + hh[h] / 2 + (k - (n - 1) / 2) * lane

    def port(eid: str, v: int) -> tuple[float, float]:
        b = box(eid)
        s = side_of(eid, v)
        n = side_n[(eid, s)]
        k = side_k[(eid, s)]
        side_k[(eid, s)] += 1
        usable = max(4.0, b["h"] - 2 * side_pad)
        y = b["y"] + side_pad + usable * (k + 1) / (n + 1)
        return (b["x"] + b["w"] if s == "R" else b["x"]), y

    routed = []
    for ln, ca, cb, va, vb, hk in plans:
        sx, sy = port(ln["from"], va)
        tx, ty = port(ln["to"], vb)
        if va == vb:
            lx = lane_x(va)
            pts = [(sx, sy), (lx, sy), (lx, ty), (tx, ty)]
        else:
            lxa = lane_x(va)
            lxb = lane_x(vb)
            ly = lane_y(hk) if hk is not None else (sy + ty) / 2
            pts = [(sx, sy), (lxa, sy), (lxa, ly), (lxb, ly), (lxb, ty), (tx, ty)]
        routed.append({"id": ln["id"], "from": ln["from"], "to": ln["to"], "points": pts})
    return cbox, ibox, routed


def bbox(boxes: list[Box]) -> Box:
    if not boxes:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    x0 = min(b["x"] for b in boxes)
    y0 = min(b["y"] for b in boxes)
    x1 = max(b["x"] + b["w"] for b in boxes)
    y1 = max(b["y"] + b["h"] for b in boxes)
    return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}


def border_point(b: Box, toward: tuple[float, float]) -> tuple[float, float]:
    """Where the segment from the box centre to ``toward`` leaves the box."""
    cx, cy = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (b["w"] / 2) / abs(dx) if dx else float("inf")
    sy = (b["h"] / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s

