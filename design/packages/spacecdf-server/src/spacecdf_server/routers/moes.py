"""Stakeholders (categories, authority, engagement) and measures of effectiveness. Owner S (3.S3).

STEP 0 STUB (wave 3): the routes exist so the other agents and the frontend can code against
them; agent S replaces each body (table ``se_moes`` in ``db/models_se.py``; stakeholders in
``MissionNeed``).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "S", "3.S3"


@router.get("/studies/{study_id}/moes")
async def list_moes(study_id: str) -> dict:
    """TODO(S, 3.S3): every MOE: {id, code, measure, threshold, objectives, needs, defined_by, placeholder}."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/moes")
async def create_moe(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S3)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.patch("/studies/{study_id}/moes/{moe_id}")
async def update_moe(study_id: str, moe_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S3)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.delete("/studies/{study_id}/moes/{moe_id}")
async def delete_moe(study_id: str, moe_id: str) -> dict:
    """TODO(S, 3.S3)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/stakeholders/import")
async def import_stakeholders(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S3): ``stakeholders.yaml`` (stakeholders, needs, MOEs) in one call (seed S0)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
