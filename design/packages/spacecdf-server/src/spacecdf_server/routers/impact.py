"""Key numbers and the "who is affected" impact preview (negotiation #3). Owner L (3.L6).

* ``GET  /studies/{study_id}/key-numbers`` — the study's key numbers (``services/key_numbers.py``);
  ``?data=false`` skips the contact prediction and data budget (fast).
* ``POST /studies/{study_id}/impact/preview`` — a proposed change evaluated as a dry run
  (``services/impact_preview.py``): Δ of every key number that moves, with the seats that own them.
  Nothing is written.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ..services.key_numbers import key_numbers
from ._wave3_stub import study_or_404

router = APIRouter()
OWNER, WP = "L", "3.L6"


@router.get("/studies/{study_id}/key-numbers")
async def get_key_numbers(study_id: str, gate: str | None = Query(None), data: bool = Query(True)) -> dict:
    study_or_404(study_id)
    return {"study_id": study_id, "items": await key_numbers(study_id, gate=gate, data=data)}


@router.post("/studies/{study_id}/impact/preview")
async def impact_preview(study_id: str, body: dict[str, Any]) -> dict:
    """A proposed change (station, mode share, mode member, element, pending change, orbit,
    allocation) as a dry run: Δ key numbers by owning seat."""
    from ..services.impact_preview import PreviewError, preview
    study_or_404(study_id)
    try:
        return await preview(study_id, body or {})
    except PreviewError as exc:
        raise HTTPException(422, str(exc)) from None
