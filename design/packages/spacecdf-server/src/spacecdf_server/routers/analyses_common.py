"""Cross-analysis routes (SCDF-170 §1.2): conflicts and last-run listing.

    GET  /api/studies/{study_id}/conflicts?option_id=      {design: [...], analysis: [...]}
    POST /api/conflicts/{conflict_id}/resolve              mark an analysis conflict resolved
    GET  /api/studies/{study_id}/analyses?option_id=       last run per analysis with ``stale``
    GET  /api/studies/{study_id}/analyses/{analysis}       last run of one analysis (404 if never run)

``design`` conflicts are the cross-domain conflicts of the last design loop —
``routers/design.py`` publishes them through ``ResultsSink`` under
``analysis='design_loop'`` (the frontend ``ConflictsPanel`` reads them from
the design-run response in ``designStore``; this route is the persisted
equivalent so the panel can be refreshed after a reload). ``analysis`` holds
every other analysis' conflicts.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..db import analysis_repo
from ..services import analysis_results

router = APIRouter()

DESIGN_LOOP = "design_loop"


@router.get("/studies/{study_id}/conflicts")
async def get_study_conflicts(study_id: str, option_id: str | None = Query(None),
                              include_resolved: bool = Query(False)) -> dict:
    rows = await analysis_repo.list_conflicts(study_id, option_id=option_id, include_resolved=include_resolved)
    return {
        "study_id": study_id,
        "option_id": option_id,
        "design": [c for c in rows if c["analysis"] == DESIGN_LOOP],
        "analysis": [c for c in rows if c["analysis"] != DESIGN_LOOP],
    }


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str) -> dict:
    row = await analysis_results.resolve_conflict(conflict_id)
    if row is None:
        raise HTTPException(404, f"Conflict {conflict_id} not found")
    return row


@router.get("/studies/{study_id}/analyses")
async def list_study_analyses(study_id: str, option_id: str | None = Query(None)) -> list[dict]:
    return await analysis_results.list_analyses(study_id, option_id=option_id)


@router.get("/studies/{study_id}/analyses/{analysis}")
async def get_study_analysis(study_id: str, analysis: str, option_id: str | None = Query(None)) -> dict:
    run = await analysis_results.get_last_run(study_id, analysis, option_id=option_id)
    if run is None:
        raise HTTPException(404, f"No {analysis} run for study {study_id}")
    return run
