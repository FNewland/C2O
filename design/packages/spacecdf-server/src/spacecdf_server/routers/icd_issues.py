"""ICD issue control (PI addendum, 3.R6, owner R): issue / revision, state (draft, Issue A, B …,
baselined) and the sign-off of both owning seats per ICD; table ``icd_issues``
(``db/models_icd.py``). The service is ``services/interface_requirements.py`` (section "ICD issue
control"); PDR-EC-02 reads ``icd_status``.

    GET  /api/studies/{sid}/icds                       every ICD: latest issue, state, the two sign-offs
    POST /api/studies/{sid}/icds/inventory             {icd_refs[], required_at?}: put ICDs under issue control
    POST /api/studies/{sid}/icds/{icd_ref}/issue       {issue?, revision?, baseline?, change_note?, provider_seat?, consumer_seat?}
    POST /api/studies/{sid}/icds/{icd_ref}/signoff     {side?: provider|consumer|both, agree?: bool}
    GET  /api/studies/{sid}/icds/{icd_ref}/history     every issue of one ICD

In a study with seats, a member signs for the side whose seat they hold; the instructor may
sign either side (as the IF-05 interface agreement).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ._lookup import study_or_404

router = APIRouter()


class InventoryBody(BaseModel):
    icd_refs: list[str]
    required_at: str | None = "pdr"


class IssueBody(BaseModel):
    issue: str | None = None
    revision: bool = False
    baseline: bool = False
    change_note: str = ""
    provider_seat: str | None = None
    consumer_seat: str | None = None


class SignoffBody(BaseModel):
    side: str | None = None          # provider | consumer | both (default: the sides you hold)
    agree: bool = True


@router.get("/studies/{study_id}/icds")
async def list_icds(study_id: str, gate: str | None = None) -> dict:
    """Every ICD with its latest issue, state and the two sign-offs, the inventory under issue
    control and the unsigned ICDs by seat."""
    from ..services.interface_requirements import icd_status
    study_or_404(study_id)
    return await icd_status(study_id, gate=gate)


@router.post("/studies/{study_id}/icds/inventory")
async def declare_icds(study_id: str, body: InventoryBody) -> dict:
    from ..services.interface_requirements import icd_declare
    study_or_404(study_id)
    try:
        res = await icd_declare(study_id, body.icd_refs, body.required_at)
    except KeyError as exc:
        raise HTTPException(404, f"No requirement cites ICD {exc.args[0]}")
    await _broadcast(study_id, "icds_declared", res)
    return res


@router.post("/studies/{study_id}/icds/{icd_ref}/issue")
async def raise_icd_issue(study_id: str, icd_ref: str, body: IssueBody, request: Request) -> dict:
    """Raise the next issue (draft → Issue A → B …), a revision, or baseline the signed issue;
    the previous issue is kept as history."""
    from ..services.interface_requirements import icd_raise
    study_or_404(study_id)
    person, _ctx = await _person(request, study_id)
    try:
        res = await icd_raise(study_id, icd_ref, issue=body.issue, baseline=body.baseline, revision=body.revision,
                              note=body.change_note, provider_seat=body.provider_seat,
                              consumer_seat=body.consumer_seat, by=person)
    except KeyError as exc:
        raise HTTPException(404, f"No requirement cites ICD {exc.args[0]}")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    await _broadcast(study_id, "icd_issued", res)
    return res


@router.post("/studies/{study_id}/icds/{icd_ref}/signoff")
async def sign_icd(study_id: str, icd_ref: str, body: SignoffBody, request: Request) -> dict:
    """The provider or consumer seat signs the current issue; both signed → agreed."""
    from ..seats.service import _http
    from ..services.interface_requirements import icd_key, icd_sign, icd_status
    study_or_404(study_id)
    st = await icd_status(study_id)
    item = next((i for i in st["items"] if i["icd_ref"] == icd_key(icd_ref)), None)
    if item is None or not item["controlled"]:
        raise HTTPException(404, f"ICD {icd_key(icd_ref)} is not under issue control")
    sides = ["provider", "consumer"] if body.side in (None, "both") else [body.side]
    if any(s not in ("provider", "consumer") for s in sides):
        raise HTTPException(400, "side must be provider, consumer or both")
    person, ctx = await _person(request, study_id)
    if ctx is not None and ctx.enabled and not ctx.instructor:
        allowed = [s for s in sides if ctx.holds(item.get(f"{s}_seat"))]
        if body.side not in (None, "both") and not allowed:
            raise _http(403, "not_party", "Only the seat on that side of the ICD signs it",
                        seat=item.get(f"{sides[0]}_seat"))
        sides = allowed
        if not sides:
            raise _http(403, "not_party", "You hold neither seat of this ICD")
    try:
        res = await icd_sign(study_id, icd_ref, sides, body.agree, person)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    if ctx is not None and ctx.enabled:
        from ..seats import store
        seat = next((item.get(f"{s}_seat") for s in sides if ctx.holds(item.get(f"{s}_seat"))), "instructor")
        await store.log_event(study_id, seat or "", ctx.person, "sign_icd" if body.agree else "withdraw_icd",
                              res["icd_ref"], {"sides": sides, "issue": res.get("issue")})
    await _broadcast(study_id, "icd_signed", res)
    return res


@router.get("/studies/{study_id}/icds/{icd_ref}/history")
async def icd_history(study_id: str, icd_ref: str) -> dict:
    """Every issue of one ICD, oldest first."""
    from ..services.interface_requirements import icd_history as hist, icd_key
    study_or_404(study_id)
    return {"study_id": study_id, "icd_ref": icd_key(icd_ref), "items": await hist(study_id, icd_ref)}


async def _person(request: Request, study_id: str) -> tuple[str, Any]:
    try:
        from ..seats.service import seat_ctx
        ctx = await seat_ctx(request, study_id)
        return (ctx.person.name if ctx and ctx.person else ""), ctx
    except Exception:  # noqa: BLE001 — no seats: anonymous
        return "", None


async def _broadcast(study_id: str, event: str, payload: dict) -> None:
    from ._arcadia_events import broadcast_mutation
    await broadcast_mutation(study_id, event, "icd", payload.get("icd_ref") or study_id, payload)
