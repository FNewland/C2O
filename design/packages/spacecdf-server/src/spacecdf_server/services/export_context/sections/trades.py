"""Section ``trades``: trade studies. Today the study holds one record per key in
``study.trade_records`` (only ``pugh``); W6.01 turns this into a list keyed T-01... Owner: D."""
from __future__ import annotations


def empty() -> dict:
    return {"items": []}


async def collect(ctx) -> dict:
    recs = dict(getattr(ctx.study, "trade_records", None) or {}) if ctx.study is not None else {}
    items = [{"id": k, **(v if isinstance(v, dict) else {"state": v})} for k, v in sorted(recs.items())]
    return {"items": items}
