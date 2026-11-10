"""Negotiation records (negotiation #1). Owner H (3.H6).

STEP 0 STUB (wave 3): table ``negotiation_records`` (``db/models_negotiation.py``); coupled
parameters quote ``services/key_numbers.key_numbers``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "H", "3.H6"


@router.get("/studies/{study_id}/negotiations")
async def list_negotiations(study_id: str) -> dict:
    """TODO(H, 3.H6): every record with its live parameter values and sign-off state."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/negotiations")
async def create_negotiation(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(H, 3.H6)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.get("/studies/{study_id}/negotiations/{record_id}")
async def get_negotiation(study_id: str, record_id: str) -> dict:
    """TODO(H, 3.H6)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.patch("/studies/{study_id}/negotiations/{record_id}")
async def update_negotiation(study_id: str, record_id: str, body: dict[str, Any]) -> dict:
    """TODO(H, 3.H6)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/negotiations/{record_id}/signoff")
async def sign_negotiation(study_id: str, record_id: str, body: dict[str, Any]) -> dict:
    """TODO(H, 3.H6): one sign-off per seat; "agreed" when every seat has signed."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/negotiations/{record_id}/reopen")
async def reopen_negotiation(study_id: str, record_id: str, body: dict[str, Any]) -> dict:
    """TODO(H, 3.H6)."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
