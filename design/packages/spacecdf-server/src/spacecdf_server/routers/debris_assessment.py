"""Debris assessment in the tool (PI addendum). Owner L (3.L8): DRAMA/DAS-like lifetime, casualty risk and collision probability, accepted at SRR; table ``debris_assessments`` (``db/models_debris.py``).

STEP 0 STUB (wave 3, PI addendum): the routes exist so the other agents and the frontend can code
against them; the owner replaces each body.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "L", "3.L8"


@router.get("/studies/{study_id}/debris-assessment")
async def get_debris_assessment(study_id: str) -> dict:
    """TODO(L, 3.L8): the latest assessment and its acceptance."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/debris-assessment/run")
async def run_debris_assessment(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(L, 3.L8): lifetime with / without the device, casualty risk, collision probability."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/debris-assessment/accept")
async def accept_debris_assessment(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(L, 3.L8): accepted by a seat at a gate."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
