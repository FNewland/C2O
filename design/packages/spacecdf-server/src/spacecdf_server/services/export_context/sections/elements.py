"""Section ``elements``: the product tree (live elements, sorted by tree depth then name), the
accepted/suggested interfaces, the budget allocations (mass, power... per element) and counts.
Owner: X (export core)."""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "interfaces": [], "allocations": [], "counts": {}}


def _depths(els: list[dict]) -> dict[str, int]:
    idx = {e["id"]: e for e in els if e.get("id")}
    out: dict[str, int] = {}
    for e in els:
        d, cur, seen = 0, e, 0
        while cur.get("parent_id") in idx and seen < 50:
            cur = idx[cur["parent_id"]]
            d += 1
            seen += 1
        out[e["id"]] = d
    return out


async def collect(ctx) -> dict:
    els = [e for e in ctx.elements if e.get("id")]
    depth = _depths(els)
    items = sorted(els, key=lambda e: (depth.get(e["id"], 0), str(e.get("name") or ""), e["id"]))
    counts: dict[str, int] = {}
    for e in items:
        t = str(e.get("element_type") or "unknown")
        counts[t] = counts.get(t, 0) + 1
    ifs = sorted(ctx.interfaces, key=lambda i: (str(i.get("name") or ""), str(i.get("id") or "")))
    try:
        from ....routers.elements import _budget_allocations
        ids = {e["id"] for e in items}
        allocs = [dict(a) for a in _budget_allocations
                  if a.get("study_id") == ctx.study_id or a.get("element_id") in ids]
    except Exception:  # noqa: BLE001 — allocations are optional
        allocs = []
    allocs.sort(key=lambda a: (str(a.get("budget_type") or ""), str(a.get("element_id") or "")))
    return {"items": [{**e, "depth": depth.get(e["id"], 0)} for e in items], "interfaces": ifs,
            "allocations": allocs, "counts": counts}
