"""Negotiation records (negotiation #1). Owner H (3.H6).

    GET    /api/studies/{id}/negotiations                    every record, live values, sign-off state, templates
    POST   /api/studies/{id}/negotiations                    {template: N1|N3|N7|GS4} or the fields of a record
    GET    /api/studies/{id}/negotiations/{rid}
    PATCH  /api/studies/{id}/negotiations/{rid}              fields; {recompute_options: true}; a substantive change
                                                             clears the sign-offs
    POST   /api/studies/{id}/negotiations/{rid}/signoff      {seat, agree?: true, by?, note?}
    POST   /api/studies/{id}/negotiations/{rid}/reopen       {reason, by?}
    DELETE /api/studies/{id}/negotiations/{rid}

The write routes answer the record with its live values; ``?live=false`` answers the plain record
(no live computation: the seed and scripted callers). Table ``negotiation_records`` (``db/models_negotiation.py``); the logic is ``services/negotiations.py``.
In a study with seats you sign for the seat you hold; the instructor may record any seat (IF-05).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from ._lookup import study_or_404

router = APIRouter()
OWNER, WP = "H", "3.H6"


async def _broadcast(study_id: str) -> None:
    try:
        from .gates import _broadcast as bc
        await bc(study_id, "study_records_changed", {"kind": "negotiations"})
    except Exception:  # noqa: BLE001
        pass


def _templates() -> list[dict]:
    from ..services.negotiations import TEMPLATES
    return [{"code": k, "issue": v["issue"], "seats": v["seats"], "parameters": v["parameters"]} for k, v in TEMPLATES.items()]


async def _person_name(request: Request, study_id: str, body: dict) -> str:
    try:
        from ..seats.service import seat_ctx
        ctx = await seat_ctx(request, study_id)
        return body.get("by") or ctx.person.name or ""
    except Exception:  # noqa: BLE001
        return str(body.get("by") or "")


@router.get("/studies/{study_id}/negotiations")
async def list_negotiations(study_id: str) -> dict:
    """Every record with its live parameter values, sign-off state and reopen trigger."""
    from ..services import negotiations as ns
    study_or_404(study_id)
    recs = await ns.list_records(study_id)
    items = await ns.views(study_id, recs)
    return {"study_id": study_id, "items": items, "counts": ns.counts(recs), "templates": _templates(),
            "owner": OWNER, "work_package": WP}


@router.post("/studies/{study_id}/negotiations")
async def create_negotiation(study_id: str, body: dict[str, Any], request: Request, live: bool = Query(True)) -> dict:
    """A record from a template (options computed from the study) or from the fields given."""
    from ..services import negotiations as ns
    study_or_404(study_id)
    if not body:
        raise HTTPException(422, "Give a template (N1, N3, N7, GS4) or the fields of a record")
    try:
        rec = await ns.create(study_id, body, by=await _person_name(request, study_id, body))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await _broadcast(study_id)
    return (await ns.views(study_id, [rec]))[0] if live else rec


async def _one(study_id: str, record_id: str) -> dict:
    from ..services import negotiations as ns
    study_or_404(study_id)
    rec = await ns.get_record(study_id, record_id)
    if rec is None:
        raise HTTPException(404, f"Negotiation {record_id} not found in study {study_id}")
    return rec


@router.get("/studies/{study_id}/negotiations/{record_id}")
async def get_negotiation(study_id: str, record_id: str) -> dict:
    from ..services import negotiations as ns
    return (await ns.views(study_id, [await _one(study_id, record_id)]))[0]


@router.patch("/studies/{study_id}/negotiations/{record_id}")
async def update_negotiation(study_id: str, record_id: str, body: dict[str, Any], request: Request,
                             live: bool = Query(True)) -> dict:
    from ..services import negotiations as ns
    await _one(study_id, record_id)
    try:
        rec = await ns.update(study_id, record_id, body, by=await _person_name(request, study_id, body))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await _broadcast(study_id)
    return (await ns.views(study_id, [rec]))[0] if live else rec


@router.delete("/studies/{study_id}/negotiations/{record_id}")
async def delete_negotiation(study_id: str, record_id: str) -> dict:
    from ..services import negotiations as ns
    await _one(study_id, record_id)
    await ns.delete(study_id, record_id)
    await _broadcast(study_id)
    return {"deleted": record_id}


@router.post("/studies/{study_id}/negotiations/{record_id}/signoff")
async def sign_negotiation(study_id: str, record_id: str, body: dict[str, Any], request: Request,
                           live: bool = Query(True)) -> dict:
    """One sign-off per seat; "agreed" when every seat has signed the current version. With seats
    enabled you sign for the seat you hold (the instructor may record any seat)."""
    from ..seats.service import _http, seat_ctx
    from ..services import negotiations as ns
    rec = await _one(study_id, record_id)
    seat = str(body.get("seat") or "")
    ctx = await seat_ctx(request, study_id)
    if not seat and ctx.enabled:
        seat = next((s for s in rec["seats"] if ctx.holds(s)), "")
    if not seat:
        raise HTTPException(422, "Name the seat that signs")
    if ctx.enabled and not ctx.instructor and not ctx.holds(seat):
        raise _http(403, "not_party", "Only the seat itself records its sign-off", seat=seat)
    try:
        out = await ns.sign(study_id, record_id, seat, agree=bool(body.get("agree", True)),
                            by=body.get("by") or ctx.person.name or "", note=str(body.get("note") or ""))
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    if ctx.enabled:
        try:
            from ..seats import store
            await store.log_event(study_id, seat, ctx.person, "sign_negotiation" if body.get("agree", True) else "withdraw_negotiation",
                                  out.get("code") or record_id, {"negotiation_id": record_id})
        except Exception:  # noqa: BLE001
            pass
    await _broadcast(study_id)
    return (await ns.views(study_id, [out]))[0] if live else out


@router.post("/studies/{study_id}/negotiations/{record_id}/reopen")
async def reopen_negotiation(study_id: str, record_id: str, body: dict[str, Any], request: Request) -> dict:
    """Reopen an agreement (the trigger fired, or new evidence): the sign-offs are cleared."""
    from ..services import negotiations as ns
    await _one(study_id, record_id)
    try:
        out = await ns.reopen(study_id, record_id, reason=str(body.get("reason") or ""),
                              by=await _person_name(request, study_id, body))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await _broadcast(study_id)
    return (await ns.views(study_id, [out]))[0]
