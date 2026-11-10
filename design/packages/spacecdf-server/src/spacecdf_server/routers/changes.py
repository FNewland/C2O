"""Change proposals register (ECP / CR). Owner L (3.L4).

STEP 0 STUB (wave 3): table ``change_proposals`` (``db/models_changes.py``, L's class only).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "L", "3.L4"


@router.get("/studies/{study_id}/changes")
async def list_changes(study_id: str) -> dict:
    """TODO(L, 3.L4): ECP and CR records with class, impact, affected requirements, status."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/changes")
async def create_change(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(L, 3.L4)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.patch("/studies/{study_id}/changes/{change_id}")
async def update_change(study_id: str, change_id: str, body: dict[str, Any]) -> dict:
    """TODO(L, 3.L4)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/changes/import")
async def import_changes(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(L, 3.L4): risks.yaml configuration_management.change_records in one call (seed S3)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/changes/from-trade/{trade_id}")
async def change_from_trade(study_id: str, trade_id: str) -> dict:
    """TODO(L, 3.L4): "Raise change from trade" on a decided trade."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
