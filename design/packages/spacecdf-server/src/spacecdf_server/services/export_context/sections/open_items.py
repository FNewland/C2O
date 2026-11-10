"""Section ``open_items``: the open-item register (RIDs, actions, conditional decisions, PI and
seat decisions, undecided gate trades, change proposals) by the gate each blocks, open and closed.
Owner: D (3.D4; ``services/open_items.py``)."""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "by_gate": {}, "counts": {}}


async def collect(ctx) -> dict:
    if ctx.study is None:
        return empty()
    from ...open_items import register
    reg = await register(ctx.study_id, ctx.study, include_closed=True)
    open_ = [i for i in reg["items"] if i["status"] == "open"]
    by_gate: dict[str, list[str]] = {}
    for i in open_:
        by_gate.setdefault(i.get("blocks_gate") or "", []).append(i["code"] or i["id"])
    counts = {**reg["counts"], "open": len(open_), "closed": len(reg["items"]) - len(open_)}
    return {"items": reg["items"], "by_gate": by_gate, "counts": counts}
