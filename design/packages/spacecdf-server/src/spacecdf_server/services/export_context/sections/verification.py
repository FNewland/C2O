"""Section ``verification``: the verification items (method, stage, status, evidence) of the
study. Owner: X (collector); verification-item fields belong to R (W2.02/W2.13), AIT tests to A."""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    from ....db import verification_repo
    items = await verification_repo.list_by_study(ctx.study_id)
    items = sorted(items, key=lambda v: (str(v.get("requirement_id") or ""), str(v.get("id") or "")))
    counts: dict[str, int] = {}
    for v in items:
        st = str(v.get("status") or "unknown")
        counts[st] = counts.get(st, 0) + 1
    return {"items": items, "counts": counts}
