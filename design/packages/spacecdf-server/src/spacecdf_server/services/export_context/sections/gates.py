"""Section ``gates``: the gate profile, each gate's state, readiness and must-pass summary, the
current gate, the stored gate records (history, baselines, the review record: chair note and
go / no-go) and the RID / action log of the review record (W4.08). Owner: D."""
from __future__ import annotations

import copy


def empty() -> dict:
    return {"profile": None, "current_gate": None, "gates": [], "records": {}, "rids": [],
            "rid_counts": {"total": 0, "open": 0}}


async def collect(ctx) -> dict:
    if ctx.study is None:
        return empty()
    from ....routers.gates import list_review_items, study_gates
    from ...gate_reviews import RID_OPEN
    res = await study_gates(ctx.study_id)
    rids = await list_review_items(ctx.study_id)
    return {"profile": res.get("profile"), "current_gate": res.get("current_gate"),
            "gates": res.get("gates") or [],
            "records": copy.deepcopy(dict(getattr(ctx.study, "gate_states", None) or {})),
            "rids": rids,
            "rid_counts": {"total": len(rids), "open": sum(1 for r in rids if r["status"] in RID_OPEN)}}
