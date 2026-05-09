"""SpaceCDF — FMECA Router (SCDF-231/232/233).

POST /api/fmeca/analyze — run failure mode analysis for spacecraft subsystems.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
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
