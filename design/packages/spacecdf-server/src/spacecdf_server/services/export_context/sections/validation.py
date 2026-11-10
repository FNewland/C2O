"""Section ``validation``: the validation activities (V1 …) with performer and stage, the
need-validation rows and the coverage of the objectives. Owner: S (3.S5).

Shape: ``{"items": [activity], "need_validation": [row], "coverage": {objectives, primary,
uncovered_primary, needs, ok, …}, "counts": {activities, need_validation, engineers_only},
"stages": [...], "stage_labels": {...}}`` (``routers/validation.py``). The VP docx Validation
chapter (A, 3.A4) and the MRD need-validation table (X, 3.X2) read it.
"""
from __future__ import annotations


def empty() -> dict:
    return {"items": [], "need_validation": [], "coverage": {}, "counts": {}}


async def collect(ctx) -> dict:
    from ....routers import validation as v
    items = await v.list_activities(ctx.study_id)
    nv = await v.list_need_validation(ctx.study_id)
    cov = await v.coverage(ctx.study_id)
    return {"items": items, "need_validation": nv, "coverage": cov,
            "counts": {"activities": len(items), "need_validation": len(nv),
                       "engineers_only": sum(1 for a in items if a["engineers_only"])},
            "stages": list(v.STAGES), "stage_labels": v.STAGE_LABEL}
