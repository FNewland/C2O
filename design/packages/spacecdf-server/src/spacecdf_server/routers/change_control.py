"""Change-control flow of a change proposal (PI addendum: ECP-01 and ECP-02 decided on camera).
Owner D (3.D7; ``services/change_control.py``). The proposals themselves are L's
(``routers/changes.py``, table ``change_proposals``); the flow is kept in ``change_approvals``.

Mounted under ``/api`` (``change_id`` is the proposal id or its code, e.g. ``ECP-02``):

* ``GET  /studies/{sid}/changes/{change_id}/control``          the flow: state, impact, seats, board, baseline
* ``POST /studies/{sid}/changes/{change_id}/control/start``    impact preview + affected seats (``{"seats": []}``
                                                               adds seats)
* ``POST /studies/{sid}/changes/{change_id}/control/agree``    ``{"seat", "decision": agree|object, "note"}``
* ``POST /studies/{sid}/changes/{change_id}/control/decide``   ``{"decision": approve|reject, "note",
                                                               "apply": [{code, text …}]}`` (Team leader or
                                                               instructor; approval updates the baseline)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..services import change_control as cc
from ._lookup import study_or_404

router = APIRouter()


def _http(exc: cc.ChangeControlError) -> HTTPException:
    return HTTPException(exc.status, {"code": exc.code, "message": str(exc), **exc.extra})


def _who(request: Request, body_by: str = "") -> str:
    from .gates import _who as who
    return who(request, body_by)


async def _done(study_id: str, out: dict) -> dict:
    from .gates import _broadcast
    await _broadcast(study_id, "study_records_changed", {"kind": "change_control"})
    return out


@router.get("/studies/{study_id}/changes/{change_id}/control")
async def get_change_control(study_id: str, change_id: str) -> dict:
    study_or_404(study_id)
    try:
        return await cc.view(study_id, change_id)
    except cc.ChangeControlError as exc:
        raise _http(exc) from exc


class StartBody(BaseModel):
    seats: list[str] = Field(default_factory=list, max_length=20)
    by: str = Field("", max_length=120)


@router.post("/studies/{study_id}/changes/{change_id}/control/start")
async def start_change_control(study_id: str, change_id: str, request: Request, body: StartBody | None = None) -> dict:
    study_or_404(study_id)
    body = body or StartBody()
    try:
        return await _done(study_id, await cc.start(study_id, change_id, seats=body.seats, by=_who(request, body.by)))
    except cc.ChangeControlError as exc:
        raise _http(exc) from exc


class AgreeBody(BaseModel):
    seat: str = Field("", max_length=48)
    decision: str = "agree"
    note: str = Field("", max_length=4000)
    by: str = Field("", max_length=120)


@router.post("/studies/{study_id}/changes/{change_id}/control/agree")
async def agree_change(study_id: str, change_id: str, body: AgreeBody, request: Request) -> dict:
    """An affected seat agrees or objects. In a seat study the person must hold that seat (or be
    the Team leader or the instructor); ``seat`` defaults to the active seat."""
    study_or_404(study_id)
    from ..seats.service import seat_ctx
    ctx = await seat_ctx(request, study_id)
    seat = body.seat or (ctx.active or "")
    if ctx.enabled and not (ctx.instructor or ctx.holds(seat) or ctx.holds("team_leader")):
        raise HTTPException(403, {"code": "seat_only", "message": f"Only the {seat} seat answers for it"})
    if not seat:
        raise HTTPException(422, "seat is required")
    try:
        return await _done(study_id, await cc.agree(study_id, change_id, seat, body.decision, body.note,
                                                    _who(request, body.by)))
    except cc.ChangeControlError as exc:
        raise _http(exc) from exc


class DecideBody(BaseModel):
    decision: str
    note: str = Field("", max_length=4000)
    apply: list[dict[str, Any]] | None = Field(None, max_length=100)
    by: str = Field("", max_length=120)


@router.post("/studies/{study_id}/changes/{change_id}/control/decide")
async def decide_change(study_id: str, change_id: str, body: DecideBody, request: Request) -> dict:
    """The board decides (Team leader or instructor in a seat study). ``approve`` needs every
    affected seat's agreement and saves the new baseline revision."""
    study = study_or_404(study_id)
    from ..seats.service import require_gate_role
    await require_gate_role(request, study_id)
    try:
        return await _done(study_id, await cc.decide(study_id, change_id, body.decision, note=body.note,
                                                     by=_who(request, body.by), apply=body.apply, study=study))
    except cc.ChangeControlError as exc:
        raise _http(exc) from exc
