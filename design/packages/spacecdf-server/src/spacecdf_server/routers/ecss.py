"""SpaceCDF — ECSS compliance API.

Exposes the ECSS review-gate deliverable expectations to the frontend so
that the Compliance Panel can show, for a given study phase, which DRDs
are expected at the next review gate and which SpaceCDF currently covers.

Reference sources (via ~/.claude/skills/ecss-standards/):
  - ECSS-E-ST-10C Rev.1 Annex A (Table A-1, informative)
  - ECSS-M-ST-10C Rev.1 (project phase / review-gate structure)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..services.ecss_gates import compliance_summary, list_phases
from .studies import get_study_store

router = APIRouter()


@router.get("/phases")
async def get_phases() -> list[str]:
    """Return the list of configured phase ids (phase_0, phase_a, ...)."""
    return list_phases()


@router.get("/compliance/{phase_id}")
async def get_phase_compliance(phase_id: str) -> dict:
    """Return the expected DRDs + SpaceCDF coverage for a given phase."""
    summary = compliance_summary(phase_id)
    if not summary.get("found"):
        raise HTTPException(status_code=404, detail=f"Unknown phase: {phase_id}")
    return summary


@router.get("/compliance/by-study/{study_id}")
async def get_study_compliance(study_id: str) -> dict:
    """Return DRD compliance for the phase of the named study.

    Convenience endpoint — the frontend doesn't need to know the study's
    current phase; it just asks "what does this study owe at its next gate?"
    """
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    # StudyPhase is a str Enum, so .value is the config key (phase_0, phase_a, phase_b1)
    phase_id = study.phase.value if hasattr(study.phase, "value") else str(study.phase)
    summary = compliance_summary(phase_id)
    summary["study_id"] = study_id
    summary["study_name"] = study.name
    return summary
