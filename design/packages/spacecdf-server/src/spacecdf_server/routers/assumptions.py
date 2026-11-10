"""Assumption register (SE-08, register part). Owner S (3.S6).

STEP 0 STUB (wave 3): table ``se_assumptions`` (``db/models_se.py``).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "S", "3.S6"


@router.get("/studies/{study_id}/assumptions")
async def list_assumptions(study_id: str) -> dict:
    """TODO(S, 3.S6): ASM rows: statement, affects, replace_with, owner seat, due gate, status."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/assumptions")
async def create_assumption(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S6)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.patch("/studies/{study_id}/assumptions/{assumption_id}")
async def update_assumption(study_id: str, assumption_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S6)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/assumptions/import")
async def import_assumptions(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(S, 3.S6): the [ASSUMPTION] tags of budgets.yaml and the requirement rows whose
    open_item_note names an assumption, in one call (seed S3)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
