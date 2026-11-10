"""Section ``functions``: the function tree of the Functions tab, flattened in tree order
(``depth`` per row), with the elements each function is allocated to. Owner: X (collector)."""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {"total": 0, "allocated": 0}}


async def collect(ctx) -> dict:
    from ....db import function_repo as repo
    fns = [f for f in await repo.list_functions_by_study(ctx.study_id) if not f.get("deleted_at")]
    allocs = await repo.list_allocations_by_study(ctx.study_id)
    names = {e.get("id"): e.get("name") for e in ctx.elements}
    by_fn: dict[str, list[str]] = {}
    for a in allocs:
        el = names.get(a.get("element_id"))
        if el:
            by_fn.setdefault(a.get("function_id"), []).append(el)
    kids: dict = {}
    ids = {f.get("id") for f in fns}
    for f in fns:
        kids.setdefault(f.get("parent_id") if f.get("parent_id") in ids else None, []).append(f)
    out: list[dict] = []

    def walk(parent, depth):
        for f in sorted(kids.get(parent, []), key=lambda x: (str(x.get("code") or ""), str(x.get("name") or ""))):
            out.append({"id": f.get("id"), "code": f.get("code"), "name": f.get("name"),
                        "description": f.get("description"), "layer": f.get("layer"), "depth": depth,
                        "allocated_to": sorted(by_fn.get(f.get("id"), []))})
            if depth < 30:
                walk(f.get("id"), depth + 1)

    walk(None, 0)
    return {"items": out, "counts": {"total": len(out), "allocated": sum(1 for f in out if f["allocated_to"])}}
