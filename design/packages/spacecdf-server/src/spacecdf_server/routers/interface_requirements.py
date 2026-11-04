"""Interface requirement routes (design rules IF-01 … IF-05).

    GET   /api/studies/{sid}/interface-requirements                 IRs + IRD status (PDR-EC-02)
    POST  /api/studies/{sid}/interface-requirements                 IF-02: IR naming two elements → interface
    POST  /api/studies/{sid}/interface-requirements/sync            re-apply IF-01/03/04 to the study
    POST  /api/studies/{sid}/interface-requirements/{rid}/accept-update   take the re-rendered text / retire
    POST  /api/studies/{sid}/interface-requirements/{rid}/dismiss-update  keep the current text
    GET   /api/studies/{sid}/interfaces/{iid}/requirements          IRs of one interface + agreement
    POST  /api/studies/{sid}/interfaces/{iid}/agreement             {side?: provider|consumer|both, agree?: bool}
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class IRCreate(BaseModel):
    from_element_id: str
    to_element_id: str
    interface_type: str
    subtype: str | None = None
    text: str
    verification_method: str | None = "T"
    code: str | None = None


class AgreementBody(BaseModel):
    side: str | None = None          # provider | consumer | both (default: the sides you hold)
    agree: bool = True


async def _reqs(study_id: str) -> list[dict]:
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    return [r for r in _requirements.values() if r.get("study_id") == study_id]


def _iface_or_404(study_id: str, iid: str) -> dict:
    from . import elements as el
    i = el._interfaces.get(iid)
    if not i or i.get("study_id") != study_id or i.get("deleted_at"):
        raise HTTPException(404, f"Interface {iid} not found")
    return i


def _ir_view(r: dict, ifaces: dict[str, dict]) -> dict:
    ir = r.get("ir_json") or {}
    i = ifaces.get(ir.get("interface_id") or "")
    return {**r, "interface": ({"id": i["id"], "name": i.get("name"), "type": i.get("type"), "status": i.get("status"),
                                "from_element_id": i["from_element_id"], "to_element_id": i["to_element_id"]}
                               if i and not i.get("deleted_at") else None)}


@router.get("/studies/{study_id}/interface-requirements")
async def list_irs(study_id: str) -> dict:
    """Interface requirements of the study with their interface, and the IRD status."""
    from ..services.interface_requirements import agreement_view, interface_irs, ird_status
    from . import elements as el
    reqs = await _reqs(study_id)
    ifaces = {i["id"]: i for i in el._interfaces.values() if i.get("study_id") == study_id}
    els = {e["id"]: e for e in el._elements.values() if e.get("study_id") == study_id}
    irs = [r for r in reqs if r.get("level") == "interface" and r.get("status") != "retired"]
    by_if = interface_irs(reqs)
    agreements = {iid: agreement_view(i, by_if.get(iid, []), els)
                  for iid, i in ifaces.items() if i.get("status") == "accepted" and not i.get("deleted_at")}
    return {"requirements": [_ir_view(r, ifaces) for r in sorted(irs, key=lambda x: x.get("code") or "")],
            "status": ird_status(list(ifaces.values()), reqs), "agreements": agreements}


@router.post("/studies/{study_id}/interface-requirements/sync")
async def sync_irs(study_id: str) -> dict:
    from ..services.interface_requirements import sync
    return await sync(study_id)


@router.post("/studies/{study_id}/interface-requirements")
async def create_ir(study_id: str, body: IRCreate) -> dict:
    """IF-02: an interface requirement between two elements; links the existing interface of
    that type between them or proposes one (suggested, origin ``rule:IF-02``)."""
    from spacecdf_common.models.interface_types import canonical_interface_type
    from ..db.requirement_repo import db_create_requirement
    from ..services.interface_requirements import _next_code, link_or_propose_interface, owner_seat
    from . import elements as el
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    itype = canonical_interface_type(body.interface_type)
    if not itype:
        raise HTTPException(400, f"unknown interface type {body.interface_type!r}")
    for eid in (body.from_element_id, body.to_element_id):
        e = el._elements.get(eid)
        if not e or e.get("study_id") != study_id or e.get("deleted_at"):
            raise HTTPException(400, f"element {eid} not found in this study")
    if body.from_element_id == body.to_element_id:
        raise HTTPException(400, "an interface needs two different elements")
    els = {e["id"]: e for e in el._elements.values() if e.get("study_id") == study_id}
    rid = f"REQ-{uuid4().hex[:8]}"
    req = {
        "id": rid, "study_id": study_id, "parent_id": None, "element_id": body.to_element_id, "level": "interface",
        "code": body.code or _next_code(study_id, itype, _requirements), "text": body.text, "rationale": "interface",
        "threshold_param_path": None, "threshold_op": None, "threshold_value": None,
        "verification_method": body.verification_method, "verification_phase": "CDR",
        "responsible_position": owner_seat(els.get(body.to_element_id), els), "status": "draft",
        "derived_from_requirement_id": None, "objective_id": None, "external_id": None,
        "ir_json": {"origin": "user", "interface_type": itype, "subtype": body.subtype, "edited": True,
                    "endpoints": {"from_element_id": body.from_element_id, "to_element_id": body.to_element_id}},
    }
    _requirements[rid] = req
    await db_create_requirement(req)
    iface, created = await link_or_propose_interface(req)
    return {"requirement": req, "interface": iface, "created_interface": created}


async def _ir_or_404(study_id: str, rid: str) -> dict:
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    r = _requirements.get(rid)
    if not r or r.get("study_id") != study_id or r.get("level") != "interface":
        raise HTTPException(404, f"Interface requirement {rid} not found")
    return r


@router.post("/studies/{study_id}/interface-requirements/{rid}/accept-update")
async def accept_update(study_id: str, rid: str) -> dict:
    """Take the rule's re-rendered text (review "stale"), or retire it (review "retire")."""
    from ..db.requirement_repo import db_update_requirement
    r = await _ir_or_404(study_id, rid)
    ir = dict(r.get("ir_json") or {})
    if ir.get("review") == "retire":
        r["status"] = "retired"
    elif ir.get("review") == "stale" and ir.get("proposed_text"):
        r["text"] = ir["proposed_text"].get("en") or r["text"]
        ir.update({"text_i18n": ir["proposed_text"], "inputs_hash": ir.get("proposed_hash"),
                   "missing": ir.get("proposed_missing") or [], "edited": False})
    else:
        raise HTTPException(409, "Nothing to update")
    ir.update({"review": None, "proposed_text": None, "proposed_hash": None})
    r["ir_json"] = ir
    await db_update_requirement(rid, r)
    return r


@router.post("/studies/{study_id}/interface-requirements/{rid}/dismiss-update")
async def dismiss_update(study_id: str, rid: str) -> dict:
    """Keep the current text; the rule will not flag it again until its inputs change again."""
    from ..db.requirement_repo import db_update_requirement
    r = await _ir_or_404(study_id, rid)
    ir = dict(r.get("ir_json") or {})
    if not ir.get("review"):
        raise HTTPException(409, "Nothing to dismiss")
    if ir.get("review") == "stale":
        ir["inputs_hash"] = ir.get("proposed_hash")
        ir["edited"] = True
    ir.update({"review": None, "proposed_text": None, "proposed_hash": None})
    r["ir_json"] = ir
    await db_update_requirement(rid, r)
    return r


@router.get("/studies/{study_id}/interfaces/{iid}/requirements")
async def interface_requirements(study_id: str, iid: str) -> dict:
    """The interface requirements allocated to one interface, and its agreement."""
    from ..services.interface_requirements import agreement_view
    from . import elements as el
    i = _iface_or_404(study_id, iid)
    els = {e["id"]: e for e in el._elements.values() if e.get("study_id") == study_id}
    irs = [r for r in await _reqs(study_id) if r.get("level") == "interface" and r.get("status") != "retired"
           and (r.get("ir_json") or {}).get("interface_id") == iid]
    return {"interface_id": iid, "requirements": sorted(irs, key=lambda x: x.get("code") or ""),
            "agreement": agreement_view(i, irs, els)}


@router.post("/studies/{study_id}/interfaces/{iid}/agreement")
async def agree(study_id: str, iid: str, body: AgreementBody, request: Request) -> dict:
    """IF-05: the provider and consumer seats each agree (or withdraw agreement on) an
    accepted interface. In a study with seats you agree for the side(s) whose seat you
    hold; the instructor may record either side."""
    from ..seats.service import _http, seat_ctx
    from ..services.interface_requirements import agreement_hash, agreement_view
    from . import elements as el
    i = _iface_or_404(study_id, iid)
    if i.get("status") != "accepted":
        raise HTTPException(409, "Only an accepted interface can be agreed")
    els = {e["id"]: e for e in el._elements.values() if e.get("study_id") == study_id}
    view = agreement_view(i, [], els)
    ag = {"provider_seat": view["provider_seat"], "consumer_seat": view["consumer_seat"],
          "provider": view["provider"], "consumer": view["consumer"]}
    ctx = await seat_ctx(request, study_id)
    sides = ["provider", "consumer"] if body.side in (None, "both") else [body.side]
    if any(s not in ("provider", "consumer") for s in sides):
        raise HTTPException(400, "side must be provider, consumer or both")
    if ctx.enabled and not ctx.instructor:
        allowed = [s for s in sides if ctx.holds(ag.get(f"{s}_seat"))]
        if body.side not in (None, "both") and not allowed:
            raise _http(403, "not_party", "Only the seat on that side of the interface records its agreement",
                        seat=ag.get(f"{sides[0]}_seat"))
        sides = allowed
        if not sides:
            raise _http(403, "not_party", "You hold neither seat of this interface")
    stamp = {"by": ctx.person.name, "at": datetime.now(timezone.utc).isoformat()}
    for s in sides:
        ag[s] = ({**stamp, "seat": ag.get(f"{s}_seat")} if body.agree else None)
    ag["inputs_hash"] = agreement_hash(i)
    i["agreement_json"] = ag
    await el.save_interface(i)
    if ctx.enabled:
        from ..seats import store
        seat = next((ag.get(f"{s}_seat") for s in sides if ctx.holds(ag.get(f"{s}_seat"))), "instructor")
        await store.log_event(study_id, seat or "", ctx.person, "agree" if body.agree else "withdraw_agreement",
                              i.get("name") or iid, {"interface_id": iid, "sides": sides})
    irs = [r for r in await _reqs(study_id) if r.get("level") == "interface" and r.get("status") != "retired"
           and (r.get("ir_json") or {}).get("interface_id") == iid]
    return {"interface_id": iid, "agreement": agreement_view(i, irs, els)}

