"""Electrical and data-handling routes (design rules EI-01, EI-02, EB-08, EI-10).

    GET    /api/studies/{sid}/electrical                    rails, lines, buses, nodes, ports, checks, profile
    POST   /api/studies/{sid}/electrical/propose            {dry_run?} → created/updated/removed/…
    GET    /api/studies/{sid}/electrical/checks
    POST   /api/studies/{sid}/electrical/{kind}             create (origin user, accepted)
    PATCH  /api/studies/{sid}/electrical/{kind}/{id}        fields, status, accept_update / dismiss_update
    DELETE /api/studies/{sid}/electrical/{kind}/{id}

``kind``: rails | lines | buses | nodes | ports. Ownership (REDESIGN_DECISIONS.md ruling 5):
rails and lines belong to the seat that owns the EPS element (Power), buses and nodes to the
seat that owns the bus master (Comms & OBDH), ports to the element's seat. Another seat's
edit is refused with 409 ``owned_by_other_seat`` first, then stored as a pending change
(``X-C2O-Confirm-Review: 1``) the owner accepts or rejects. The Team leader may accept or
reject proposals for any seat.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..db import electrical_repo as repo

logger = logging.getLogger(__name__)
router = APIRouter()
_locks: dict[str, asyncio.Lock] = {}


class ProposeBody(BaseModel):
    dry_run: bool = False


def _kind_or_404(kind: str) -> str:
    if kind not in repo.KINDS:
        raise HTTPException(404, f"unknown collection {kind!r}; one of {list(repo.KINDS)}")
    return kind


def _study_elements(study_id: str) -> list[dict]:
    from . import elements as el
    return [e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


def _study_interfaces(study_id: str) -> list[dict]:
    from . import elements as el
    return [i for i in el._interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")]


def _context(elements: list[dict]):
    from ..services.interface_proposer import Context, RuleConfigError, load_rules
    try:
        return Context(elements, load_rules())
    except RuleConfigError:
        return None


async def _broadcast(study_id: str, what: str) -> None:
    try:
        from .ws import _broadcast_study
        await _broadcast_study(study_id, {"type": "electrical_changed", "what": what})
    except Exception:
        logger.debug("electrical broadcast failed", exc_info=True)


async def run_electrical(study_id: str, *, dry_run: bool = False) -> dict:
    """Plan, reconcile and (unless ``dry_run``) apply the electrical/data proposals. Idempotent."""
    from ..services.electrical_rules import load_config, plan, reconcile
    lock = _locks.setdefault(study_id, asyncio.Lock())
    async with lock:
        elements = _study_elements(study_id)
        interfaces = _study_interfaces(study_id)
        ctx = _context(elements)
        cfg = load_config()
        existing = await repo.load_all(study_id)
        desired = plan(study_id, elements, interfaces, cfg, existing, ctx)
        ops = reconcile(desired, existing, cfg)
        summary = {"created": len(ops["create"]), "updated": len(ops["update"]), "removed": len(ops["remove"]),
                   "unchanged": ops["unchanged"], "skipped_rejected": ops["skipped_rejected"], "dry_run": dry_run}
        if dry_run:
            summary["operations"] = jsonable_encoder({k: ops[k] for k in ("create", "update", "remove")})
            return summary
        for kind, row in ops["create"]:
            await repo.create_row(kind, {**row, "study_id": study_id})
        for kind, rid, changes in ops["update"]:
            await repo.update_row(kind, rid, changes)
        for kind, rid in ops["remove"]:
            await repo.soft_delete_row(kind, rid)
    if ops["create"] or ops["update"] or ops["remove"]:
        from ..services.interface_requirements import after_study_change
        await after_study_change(study_id)
        await _broadcast(study_id, "proposed")
    return summary


async def electrical_view(study_id: str) -> dict:
    from ..services.electrical_rules import load_config, run_checks
    from ..services.interface_proposer import kb_profile
    elements = _study_elements(study_id)
    ctx = _context(elements)
    cfg = load_config()
    rows = await repo.load_all(study_id)
    checks = run_checks(elements, _study_interfaces(study_id), rows, cfg, ctx)
    profile = {k: v for k, v in (kb_profile(ctx) if ctx else {}).items()}
    return {
        **rows,
        "checks": checks,
        "profile": profile,
        "spacecraft_class": ctx.spacecraft_class if ctx else None,
        "protocols": cfg.get("protocols") or {},
        "inhibit_ids": sorted({i for p in ((cfg.get("power") or {}).get("line_policy") or {}).values()
                               for i in (p or {}).get("inhibits") or []}),
    }


@router.get("/studies/{study_id}/electrical")
async def get_electrical(study_id: str) -> dict:
    """Rails, power lines, buses, nodes and ports of the study, with the checks."""
    return await electrical_view(study_id)


@router.get("/studies/{study_id}/electrical/checks")
async def get_checks(study_id: str) -> list[dict]:
    return (await electrical_view(study_id))["checks"]


@router.post("/studies/{study_id}/electrical/propose")
async def propose(study_id: str, body: ProposeBody | None = None) -> dict:
    """Propose rails, power lines, buses, bus nodes (addresses) and ports from the links.

    New rows are ``suggested`` with ``origin = rule:<id>``; accepted and edited rows are never
    changed (a moved input marks them ``review = "stale"``); rejected rows are never proposed
    again. Running it twice changes nothing."""
    body = body or ProposeBody()
    return await run_electrical(study_id, dry_run=body.dry_run)


# ── ownership ──────────────────────────────────────────────────────────────

async def _owner_element(kind: str, row: dict) -> str | None:
    if kind in ("rails", "lines"):
        return row.get("eps_element_id")
    if kind == "buses":
        return row.get("master_element_id")
    if kind == "nodes":
        bus = await repo.get_row("buses", row.get("bus_id") or "")
        return (bus or {}).get("master_element_id") or row.get("element_id")
    return row.get("element_id")


async def _decide(request: Request, study_id: str, owner_el_id: str | None, *, review_only: bool) -> dict:
    """``{"mode": open|direct|pending, ...}`` per ruling 5 (raises the 403/409)."""
    from ..seats import config as seat_cfg
    from ..seats.identity import confirmed_review
    from ..seats.service import _http, owner_of_element, seat_ctx
    from . import elements as el
    ctx = await seat_ctx(request, study_id)
    if not ctx.enabled:
        return {"mode": "open", "ctx": ctx, "owner": None}
    element = el._elements.get(owner_el_id or "")
    owner = owner_of_element(ctx.state, element, el._elements) if element else None
    if owner is None or ctx.holds(owner) or ctx.instructor or (review_only and ctx.holds("team_leader")):
        return {"mode": "direct", "ctx": ctx, "owner": owner, "element": element}
    if ctx.active_kind not in seat_cfg.EDITING_KINDS:
        raise _http(403, "read_only_seat", "Your seat cannot edit design parameters")
    if not confirmed_review(request):
        raise _http(409, "owned_by_other_seat",
                    f"Owned by {seat_cfg.label(owner)['en']} — your change goes to them for review",
                    owner_seat=owner, owner_label=seat_cfg.label(owner), element_name=(element or {}).get("name", ""))
    return {"mode": "pending", "ctx": ctx, "owner": owner, "element": element}


async def _pending(request: Request, decision: dict, kind: str, row: dict, changes: dict) -> JSONResponse:
    from ..seats import changes as seat_changes
    element = decision.get("element") or {"id": "", "study_id": row.get("study_id"), "name": ""}
    pc = await seat_changes.propose(request, decision, element, "electrical",
                                    {k: row.get(k) for k in changes}, {"_entity": kind, "_id": row["id"], **changes})
    return seat_changes.pending_response(row, pc)


# ── CRUD ───────────────────────────────────────────────────────────────────

def _clean(kind: str, body: dict) -> dict:
    from ..services.electrical_rules import EDITABLE
    out = {k: body[k] for k in EDITABLE[kind] if k in body}
    if "address" in out and isinstance(out["address"], str):
        s = out["address"].strip()
        try:
            out["address"] = int(s, 16) if s.lower().startswith("0x") else int(s)
        except ValueError as e:
            raise HTTPException(400, f"address must be an integer or 0x.. hex (got {s!r})") from e
    for k in ("inhibits", "load_element_ids", "interface_ids"):
        if k in out and not isinstance(out[k], list):
            raise HTTPException(400, f"{k} must be a list")
    return out


async def apply_change(study_id: str, kind: str, row_id: str, changes: dict) -> dict:
    """Apply a (reviewed) change: fields, status, accept/dismiss update. Shared by PATCH and
    the pending-change acceptance."""
    row = await repo.get_row(kind, row_id)
    if row is None or row.get("deleted_at") or row.get("study_id") != study_id:
        raise HTTPException(404, f"{kind} {row_id} not found")
    upd: dict[str, Any] = {}
    if changes.get("accept_update"):
        prop = row.get("proposed") or {}
        if row.get("review") == "orphan":
            upd["status"] = "rejected"
        upd.update({k: v for k, v in prop.items()})
        from ..services.electrical_rules import inputs_hash
        if prop:
            upd["inputs_hash"] = inputs_hash(kind, {**row, **prop})
        upd.update({"review": None, "proposed": None, "edited": False})
    elif changes.get("dismiss_update"):
        from ..services.electrical_rules import inputs_hash
        prop = row.get("proposed") or {}
        if prop:
            upd["inputs_hash"] = inputs_hash(kind, {**row, **prop})
        upd.update({"review": None, "proposed": None})
    fields = _clean(kind, changes)
    if fields:
        upd.update(fields)
        if any(row.get(k) != v for k, v in fields.items()):
            upd["edited"] = True
            if row.get("status") == "suggested":
                upd["status"] = "accepted"
    if "status" in changes:
        if changes["status"] not in ("suggested", "accepted", "rejected"):
            raise HTTPException(400, "status must be suggested, accepted or rejected")
        upd["status"] = changes["status"]
    if not upd:
        return row
    out = await repo.update_row(kind, row_id, upd)
    from ..services.interface_requirements import after_study_change
    await after_study_change(study_id)
    await _broadcast(study_id, kind)
    return out


@router.post("/studies/{study_id}/electrical/{kind}")
async def create_row(study_id: str, kind: str, body: dict[str, Any], request: Request) -> Any:
    _kind_or_404(kind)
    fields = _clean(kind, body)
    required = {"rails": ("voltage_v",), "lines": (), "buses": ("protocol",), "nodes": ("bus_id", "element_id"),
                "ports": ("element_id", "kind")}[kind]
    for k in required:
        if fields.get(k) in (None, ""):
            raise HTTPException(400, f"{k} is required")
    row = {**fields, "study_id": study_id, "origin": "user", "status": "accepted", "edited": False}
    owner_el = await _owner_element(kind, row)
    decision = await _decide(request, study_id, owner_el, review_only=False)
    if decision["mode"] == "pending":
        raise HTTPException(409, {"code": "owned_by_other_seat", "message": "Ask the owning seat to add it"})
    out = await repo.create_row(kind, row)
    from ..services.interface_requirements import after_study_change
    await after_study_change(study_id)
    await _broadcast(study_id, kind)
    return out


@router.patch("/studies/{study_id}/electrical/{kind}/{row_id}")
async def patch_row(study_id: str, kind: str, row_id: str, body: dict[str, Any], request: Request) -> Any:
    """Edit fields (the row becomes the user's: ``edited``, a suggestion becomes accepted),
    accept/reject a proposal (``status``), or take / dismiss the rule's new values on a stale
    row (``accept_update`` / ``dismiss_update``)."""
    _kind_or_404(kind)
    row = await repo.get_row(kind, row_id)
    if row is None or row.get("deleted_at") or row.get("study_id") != study_id:
        raise HTTPException(404, f"{kind} {row_id} not found")
    if body.get("version") is not None and int(body["version"]) != int(row.get("version") or 1):
        raise HTTPException(409, {"error": "version_conflict", "your_version": body["version"],
                                  "current_version": row.get("version"), "current_state": jsonable_encoder(row)})
    review_only = set(body) - {"version"} <= {"status", "accept_update", "dismiss_update"}
    decision = await _decide(request, study_id, await _owner_element(kind, row), review_only=review_only)
    changes = {k: v for k, v in body.items() if k != "version"}
    if decision["mode"] == "pending":
        return await _pending(request, decision, kind, row, changes)
    return await apply_change(study_id, kind, row_id, changes)


@router.delete("/studies/{study_id}/electrical/{kind}/{row_id}")
async def delete_row(study_id: str, kind: str, row_id: str, request: Request) -> dict:
    """Delete a user row. A rule row is rejected instead (so it is not proposed again)."""
    _kind_or_404(kind)
    row = await repo.get_row(kind, row_id)
    if row is None or row.get("study_id") != study_id:
        raise HTTPException(404)
    decision = await _decide(request, study_id, await _owner_element(kind, row), review_only=False)
    if decision["mode"] == "pending":
        raise HTTPException(409, {"code": "owned_by_other_seat", "message": "Ask the owning seat to delete it"})
    if str(row.get("origin") or "").startswith("rule:"):
        await repo.update_row(kind, row_id, {"status": "rejected"})
        result = {"id": row_id, "rejected": True}
    else:
        await repo.soft_delete_row(kind, row_id)
        result = {"id": row_id, "deleted": True}
    from ..services.interface_requirements import after_study_change
    await after_study_change(study_id)
    await _broadcast(study_id, kind)
    return result
