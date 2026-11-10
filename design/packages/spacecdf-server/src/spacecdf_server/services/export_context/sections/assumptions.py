"""Section ``assumptions``: the assumption register: statement, what it affects, the evidence that
would replace it, owner seat, due gate, status. Owner: S (3.S6).

Shape: ``{"items": [assumption], "counts": {total, open, due_by_gate, by_owner}}``; ``due_by_gate``
counts the open ones due at or before the export's gate (the pack appendix, X 3.X2).
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    from ....routers.assumptions import due_by, list_assumptions
    items = await list_assumptions(ctx.study_id)
    op = [a for a in items if a["status"] == "open"]
    by_owner: dict[str, int] = {}
    for a in op:
        by_owner[a["owner_seat"] or "?"] = by_owner.get(a["owner_seat"] or "?", 0) + 1
    return {"items": items, "counts": {"total": len(items), "open": len(op),
                                       "due_by_gate": sum(1 for a in op if ctx.gate and due_by(a, ctx.gate)),
                                       "by_owner": by_owner}}
