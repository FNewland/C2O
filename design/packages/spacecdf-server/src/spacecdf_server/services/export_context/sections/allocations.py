"""Section ``allocations``: the allocation ledger: lines per element and budget type with owner,
status and sign-off, the Systems reserve and the closure per budget. Owner: A (3.A2).

Shape (``services/allocation_ledger.list_lines``)::

    items:   [{element_code, budget_type, mode_key, value, unit, cbe, margined, requirement_code,
               owner_seat, status, agreed_by, agreed_at, version, rationale, ...}]
    reserve: {mass|power_avg|data: {value, unit, limit, sum_allocations, with_system_margin, ...}}
    closure: {mass|power_avg|data: {lines, sum, system_margin_percent, with_system_margin, limit,
              reserve, closes, unit}}
    counts:  {lines, by_type{}, by_status{}}
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "reserve": {}, "closure": {}, "counts": {}}


_KEEP = ("id", "element_id", "element_code", "line_kind", "budget_type", "mode_key", "value", "unit", "cbe",
         "margined", "requirement_id", "requirement_code", "budget_ref", "owner_seat", "status", "agreed_by",
         "agreed_at", "rationale", "version", "type_label")


async def collect(ctx) -> dict:
    from ...allocation_ledger import list_lines
    led = await list_lines(ctx.study_id)
    if not led["items"] and not led["reserve"]:
        return {"status": "empty", **empty()}
    items = [{k: ln.get(k) for k in _KEEP} for ln in led["items"]]
    for it, ln in zip(items, led["items"]):
        it["history_length"] = len(ln.get("history_json") or [])
        sync = (ln.get("data_json") or {}).get("requirement_sync")
        if sync:
            it["requirement_sync"] = sync
    return {"status": "ok", "items": items, "reserve": led["reserve"], "closure": led["closure"],
            "counts": led["counts"]}
