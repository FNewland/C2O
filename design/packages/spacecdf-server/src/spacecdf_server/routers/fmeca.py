"""SpaceCDF — FMECA Router (SCDF-231/232/233, study-driven run SCDF-177).

POST /api/fmeca/analyze — bare catalogue analysis (ad-hoc, no study).

Study-driven closure (``study_router``, mounted under ``/api`` by
``routers.analyses_physics`` so the paths match the other analyses):
    POST /api/studies/{study_id}/analyses/fmeca/run?option_id=   body {critical: [function ids|names]}
    GET  /api/studies/{study_id}/analyses/fmeca?option_id=
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.fmeca import (
    FailureMode,
    FMECAResult,
    analyze_redundancy,
    compute_rpn,
    get_failure_catalogue,
    propagate_effects,
    run_fmeca,
)

router = APIRouter()  # prefix set in app.py
study_router = APIRouter()  # SCDF-177 — included by routers.analyses_physics (prefix /api)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class FMECARequest(BaseModel):
    """Request body for FMECA analysis."""
    spacecraft_class: str = Field("cubesat", description="Spacecraft class")
    subsystems: list[str] | None = Field(
        None, description="Subsystems to analyse (None = all)"
    )
    include_redundancy: bool = Field(
        True, description="Include redundancy recommendations"
    )
    design_state: dict[str, Any] | None = Field(
        None, description="Current design state for redundancy analysis"
    )


class FailureModeOut(BaseModel):
    """A single failure mode in the response."""
    id: str
    component: str
    mode: str
    cause: str
    local_effect: str
    system_effect: str
    severity: int
    occurrence: int
    detection: int
    rpn: int
    mitigation: str


class RedundancyRecommendation(BaseModel):
    """A redundancy recommendation."""
    failure_mode_id: str
    component: str
    current_rpn: int
    recommendation: str
    expected_rpn_reduction: int


class FMECAResponse(BaseModel):
    """Response from FMECA analysis."""
    failure_modes: list[FailureModeOut]
    total_rpn: int
    critical_count: int
    top_risks: list[FailureModeOut]
    redundancy_recommendations: list[RedundancyRecommendation] = []


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=FMECAResponse)
async def analyze_fmeca(req: FMECARequest) -> FMECAResponse:
    """Run FMECA analysis for the specified spacecraft class and subsystems."""
    try:
        result = run_fmeca(
            spacecraft_class=req.spacecraft_class,
            subsystems=req.subsystems,
            design_state=req.design_state,
        )

        # Build redundancy recommendations if requested
        redundancy_recs: list[RedundancyRecommendation] = []
        if req.include_redundancy:
            recs = analyze_redundancy(
                result.failure_modes,
                design_state=req.design_state,
            )
            redundancy_recs = [
                RedundancyRecommendation(**r) for r in recs
            ]

        def _fm_to_out(fm: FailureMode) -> FailureModeOut:
            return FailureModeOut(
                id=fm.id,
                component=fm.component,
                mode=fm.mode,
                cause=fm.cause,
                local_effect=fm.local_effect,
                system_effect=fm.system_effect,
                severity=fm.severity,
                occurrence=fm.occurrence,
                detection=fm.detection,
                rpn=fm.rpn,
                mitigation=fm.mitigation,
            )

        return FMECAResponse(
            failure_modes=[_fm_to_out(fm) for fm in result.failure_modes],
            total_rpn=result.total_rpn,
            critical_count=result.critical_count,
            top_risks=[_fm_to_out(fm) for fm in result.top_risks],
            redundancy_recommendations=redundancy_recs,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# SCDF-177 — study-driven FMECA closure
# ---------------------------------------------------------------------------

class FMECARunBody(BaseModel):
    """Optional body: the functions (ids or names) whose loss is mission-critical."""
    critical: list[str] = Field(default_factory=list)


@study_router.post("/studies/{study_id}/analyses/fmeca/run")
async def run_fmeca_closure_route(study_id: str, body: FMECARunBody | None = None,
                                  option_id: str | None = Query(None)) -> dict:
    from ..db import analysis_repo  # noqa: F401  (kept symmetrical with the other analysis routers)
    from ..services.analysis_context import build_context, context_hash
    from ..services.analysis_results import ResultsSink, finish_run, input_keys_for, refresh_inputs_hash, start_run
    from ..services.fmeca_closure import ANALYSIS, run_fmeca_closure
    from ._arcadia_events import broadcast_mutation

    ctx = await build_context(study_id, option_id=option_id)
    if not ctx.elements:
        raise HTTPException(400, f"Study {study_id} has no design elements")
    run_id = await start_run(study_id, ANALYSIS, context_hash(ctx, input_keys_for(ANALYSIS)), option_id)
    try:
        out = run_fmeca_closure(ctx, critical=(body.critical if body else None))
        pub = await ResultsSink().publish(study_id, ANALYSIS, parameters=out.parameters, conflicts=out.conflicts,
                                          notes=out.warnings, option_id=option_id, run_id=run_id, ctx=ctx)
        summary = {**out.summary, "parameters_written": len(pub.written), "shadowed": [s["name"] for s in pub.shadowed],
                   "conflicts": len(pub.conflicts)}
        run = await finish_run(run_id, "ok", summary=summary, series=out.series)
        await refresh_inputs_hash(run_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("FMECA closure failed for %s", study_id)
        await finish_run(run_id, "failed", summary={"error": str(exc)})
        await broadcast_mutation(study_id, "analysis_completed", "analysis", ANALYSIS,
                                 {"run_id": run_id, "option_id": option_id, "status": "failed", "error": str(exc)})
        raise HTTPException(500, f"FMECA closure failed: {exc}") from exc
    return {
        "run_id": run_id, "analysis": ANALYSIS, "option_id": option_id, "status": run["status"],
        "summary": summary, "modes": out.series["modes"],
        "parameters": [{"name": w["name"], "value": w["value"], "element_id": w["element_id"]} for w in pub.written],
        "shadowed": [{"name": s["name"], "value": s["value"], "element_id": s["element_id"]} for s in pub.shadowed],
        "conflicts": pub.conflicts, "warnings": out.warnings, "stale": False,
    }


@study_router.get("/studies/{study_id}/analyses/fmeca")
async def get_fmeca_closure(study_id: str, option_id: str | None = Query(None)) -> dict:
    from ..db import analysis_repo
    from ..services import analysis_results
    from ..services.fmeca_closure import ANALYSIS

    run = await analysis_results.get_last_run(study_id, ANALYSIS, option_id=option_id)
    if run is None:
        raise HTTPException(404, f"No {ANALYSIS} run for study {study_id}")
    run["conflicts"] = await analysis_repo.list_conflicts(study_id, option_id=option_id, analysis=ANALYSIS)
    series = analysis_results.load_series(run.get("series_ref"))
    run["modes"] = (series or {}).get("modes") or []
    return run
