"""Section ``changes``: the change proposals (ECP / CR): class, impact, affected requirements, source
trade, status, decision gate. Owner: L (3.L4).

``items`` are the records of ``routers/changes.py`` (newest code last); ``counts`` totals by status
and kind, plus ``open`` (proposed or under review) and ``blocks`` (open records by decision gate,
for the open-item register and the gate checklists).
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    from ....routers.changes import counts_of, list_records
    items = await list_records(ctx.study_id)
    counts = counts_of(items)
    blocks: dict[str, list[str]] = {}
    for it in items:
        if it["status"] in ("proposed", "under_review") and it.get("decision_gate"):
            blocks.setdefault(it["decision_gate"], []).append(it["code"])
    counts["blocks"] = blocks
    return {"status": "ok", "owner": "L", "work_package": "3.L4", "items": items, "counts": counts}
