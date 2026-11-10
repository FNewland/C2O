"""ICD issue control (PI addendum). Owner R (3.R6): issue / revision, state (draft, Issue A, baselined) and the sign-off of both owning seats per ICD; table ``icd_issues`` (``db/models_icd.py``). PDR-EC-02 and the SRR/PDR criteria read it.

STEP 0 STUB (wave 3, PI addendum): the routes exist so the other agents and the frontend can code
against them; the owner replaces each body.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "R", "3.R6"


@router.get("/studies/{study_id}/icds")
async def list_icds(study_id: str) -> dict:
    """TODO(R, 3.R6): every ICD with its latest issue, state and the two sign-offs."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/icds/{icd_ref}/issue")
async def raise_icd_issue(study_id: str, icd_ref: str, body: dict[str, Any]) -> dict:
    """TODO(R, 3.R6): raise the next issue (draft -> Issue A -> B), keeping the history."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/icds/{icd_ref}/signoff")
async def sign_icd(study_id: str, icd_ref: str, body: dict[str, Any]) -> dict:
    """TODO(R, 3.R6): the provider or consumer seat signs the current issue; both signed -> agreed."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.get("/studies/{study_id}/icds/{icd_ref}/history")
async def icd_history(study_id: str, icd_ref: str) -> dict:
    """TODO(R, 3.R6): every issue of one ICD."""
    return stub_list(study_id, OWNER, WP)
