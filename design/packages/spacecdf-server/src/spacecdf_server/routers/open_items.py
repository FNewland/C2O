"""Open-item register (negotiation #5). Owner D (3.D4).

STEP 0 STUB (wave 3): table ``open_items`` (``db/models_changes.py``, D's class only). The
register joins RIDs, actions, conditional decisions, PI and seat decisions and change proposals.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "D", "3.D4"


@router.get("/studies/{study_id}/open-items")
async def list_open_items(study_id: str, blocks_gate: str | None = Query(None)) -> dict:
    """TODO(D, 3.D4): every open item, filtered by the gate it blocks."""
    return stub_list(study_id, OWNER, WP, blocks_gate=blocks_gate)


@router.post("/studies/{study_id}/open-items")
async def create_open_item(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(D, 3.D4)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.patch("/studies/{study_id}/open-items/{item_id}")
async def update_open_item(study_id: str, item_id: str, body: dict[str, Any]) -> dict:
    """TODO(D, 3.D4)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/open-items/import")
async def import_open_items(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(D, 3.D4): NUMBERS open_decisions in one call (seed S3)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
