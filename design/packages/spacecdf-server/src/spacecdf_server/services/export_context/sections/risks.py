"""Section ``risks``: the study risk register, sorted by likelihood x consequence (highest first),
then id. Owner: X (export core)."""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {"total": 0, "open": 0}}


def _score(r: dict) -> int:
    try:
        return int(r.get("likelihood") or 0) * int(r.get("consequence") or 0)
    except (TypeError, ValueError):
        return 0


async def collect(ctx) -> dict:
    risks = list(getattr(ctx.study, "risk_register", None) or []) if ctx.study is not None else []
    items = [{**r, "score": _score(r)} for r in risks if isinstance(r, dict)]
    items.sort(key=lambda r: (-r["score"], str(r.get("id") or "")))
    return {"items": items, "counts": {"total": len(items),
                                       "open": sum(1 for r in items if (r.get("status") or "open") == "open")}}
