"""Section ``trades``: the study's trade studies (W6.01): ``items`` = one per trade, in id order,
``{id, state, version, evaluation, element_names}`` (``services/trades.py``: weights from the
pairwise comparison, weighted totals, thresholds, winner and weight sensitivity). The legacy
single Pugh record reads as T-01. Owner: D."""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "counts": {"total": 0, "decided": 0}}


async def collect(ctx) -> dict:
    from ...trades import evaluate, normalise_records
    recs = normalise_records(getattr(ctx.study, "trade_records", None)) if ctx.study is not None else {}
    names = {e.get("id"): e.get("name") for e in ctx.elements or []}
    items = []
    for k, v in recs.items():
        st = v.get("state") or {}
        items.append({"id": k, "state": st, "version": int(v.get("version") or 0), "evaluation": evaluate(st),
                      "element_names": {e: names.get(e, e) for e in (st.get("links") or {}).get("elements") or []}})
    return {"items": items,
            "counts": {"total": len(items), "decided": sum(1 for i in items if i["state"].get("status") == "decided")}}
