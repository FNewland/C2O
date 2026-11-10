"""Section ``decisions``: the study's decision records (``study.decision_records``). Logbook
entries kept by the logbook service are added by W12.07. A decided trade (W6) writes its record here
(``POST /studies/{id}/trades/{tid}/decision``). Owner: D."""
from __future__ import annotations

from ._util import dump


def empty() -> dict:
    return {"items": []}


async def collect(ctx) -> dict:
    recs = getattr(ctx.study, "decision_records", None) or [] if ctx.study is not None else []
    return {"items": dump(list(recs))}
