"""Validation activities and need validation (right side of the V). Owner S (3.S5).

STEP 0 STUB (wave 3): tables ``se_validation_activities`` and ``se_need_validation``
(``db/models_se.py``). ``coverage`` is the evidence function R wires into the SRR/FRR
validation criteria (3.R4).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "S", "3.S5"


@router.get("/studies/{study_id}/validation/activities")
async def list_validation_activities(study_id: str) -> dict:
    """TODO(S, 3.S5): V1… rows with objectives, needs, MOE, method, stage, performer, status."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/validation/activities")
async def create_validation_activity(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S5)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.patch("/studies/{study_id}/validation/activities/{activity_id}")
async def update_validation_activity(study_id: str, activity_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S5)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/validation/propose")
async def propose_validation(study_id: str) -> dict:
    """TODO(S, 3.S5): one proposed activity per primary objective."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/validation/import")
async def import_validation(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S5): the v2 validation plan V1–V7 and the need-validation rows in one call (seed S3)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.get("/studies/{study_id}/validation/need-validation")
async def list_need_validation(study_id: str) -> dict:
    """TODO(S, 3.S5): one row per stakeholder need."""
    return stub_list(study_id, OWNER, WP)


@router.get("/studies/{study_id}/validation/coverage")
async def validation_coverage(study_id: str) -> dict:
    """TODO(S, 3.S5): per objective, its activities and whether a stakeholder performs one."""
    return stub_list(study_id, OWNER, WP, objectives={})
