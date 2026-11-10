"""Sensitivity view on the real services (negotiation #4). Owner H (3.H5).

STEP 0 STUB (wave 3); the service goes in ``services/sensitivity.py`` (H). Disposal figures come
from L's ``services/regulatory.py`` (3.L3).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from ._wave3_stub import stub_list

router = APIRouter()
OWNER, WP = "H", "3.H5"


@router.get("/studies/{study_id}/sensitivity")
async def sensitivity(study_id: str, parameter: str = Query("science_target")) -> dict:
    """TODO(H, 3.H5): margin against science target, compression ratio, rate tier, imaging share."""
    return stub_list(study_id, OWNER, WP, parameter=parameter)


@router.get("/studies/{study_id}/sensitivity/altitude")
async def altitude_sweep(study_id: str) -> dict:
    """TODO(H, 3.H5): GSD, swath, contacts, decay with and without the sail, eclipse, link margin."""
    return stub_list(study_id, OWNER, WP)
