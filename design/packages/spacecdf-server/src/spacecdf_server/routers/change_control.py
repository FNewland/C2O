"""Change-control flow for change proposals (PI addendum: ECP-01 and ECP-02 decided on camera). Owner D (3.D7): impact preview (L's 3.L6), the affected seats' agreement, the board decision and the new baseline; table ``change_approvals`` (D's class in ``db/models_changes.py``). The proposals themselves are L's (``routers/changes.py``).

STEP 0 STUB (wave 3, PI addendum): the routes exist so the other agents and the frontend can code
against them; the owner replaces each body.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "D", "3.D7"


@router.get("/studies/{study_id}/changes/{change_id}/control")
async def get_change_control(study_id: str, change_id: str) -> dict:
    """TODO(D, 3.D7): the flow state: affected seats, their decisions, the board decision, baseline."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/changes/{change_id}/control/start")
async def start_change_control(study_id: str, change_id: str) -> dict:
    """TODO(D, 3.D7): run the impact preview and name the affected seats."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/changes/{change_id}/control/agree")
async def agree_change(study_id: str, change_id: str, body: dict[str, Any]) -> dict:
    """TODO(D, 3.D7): an affected seat agrees or objects."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/changes/{change_id}/control/decide")
async def decide_change(study_id: str, change_id: str, body: dict[str, Any]) -> dict:
    """TODO(D, 3.D7): the board approves or rejects; approve updates the baseline."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
