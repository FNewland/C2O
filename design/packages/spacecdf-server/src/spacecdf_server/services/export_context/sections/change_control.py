"""Section ``change_control``: the change-control flow of each change proposal: affected seats
and their answers, the impact the board saw, the board decision and the baseline revision it
produced. Owner: D (3.D7; ``services/change_control.py``)."""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    if ctx.study is None:
        return empty()
    from ...change_control import list_all
    items = await list_all(ctx.study_id)
    counts: dict[str, int] = {"total": len(items)}
    for i in items:
        counts[i["state"]] = counts.get(i["state"], 0) + 1
    return {"items": items, "counts": counts}
