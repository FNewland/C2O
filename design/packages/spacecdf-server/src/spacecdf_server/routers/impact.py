"""Key numbers and the "who is affected" impact preview (negotiation #3). Owner L (3.L6).

``GET /studies/{study_id}/key-numbers`` is real from step 0 (``services/key_numbers.py``);
``POST /studies/{study_id}/impact/preview`` is a STEP 0 STUB.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..services.key_numbers import key_numbers
from ._wave3_stub import not_implemented, study_or_404

router = APIRouter()
OWNER, WP = "L", "3.L6"


@router.get("/studies/{study_id}/key-numbers")
async def get_key_numbers(study_id: str, gate: str | None = Query(None)) -> dict:
    study_or_404(study_id)
    return {"study_id": study_id, "items": await key_numbers(study_id, gate=gate)}


@router.post("/studies/{study_id}/impact/preview")
async def impact_preview(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(L, 3.L6): evaluate a proposed change in a dry-run transaction; Δ key numbers by seat."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
