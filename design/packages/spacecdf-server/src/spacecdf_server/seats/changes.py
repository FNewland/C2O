"""Edits under ownership (REDESIGN_DECISIONS.md ruling 5): log direct edits, store the edits
of another seat's parameters as pending changes, and apply a pending change on acceptance.

Until a pending change is accepted nothing in the model changes, so every analysis, budget
and gate keeps reading the owner's value.
"""
from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from . import config as cfg
from . import store
from .service import param_keys


def change_fields(new: dict[str, Any]) -> list[str]:
    """The parameter names a change touches (a parameter change carries its name in ``_name``;
    an electrical or CDR change its collection and row in ``_entity`` / ``_id``)."""
    if "_name" in (new or {}):
        return [new["_name"]]
    return [k for k in (new or {}) if k not in ("_entity", "_id")]


def _jsonable(v: Any) -> Any:
    return jsonable_encoder(v)


async def log_direct_edit(request: Request, decision: dict[str, Any], element: dict[str, Any],
                          old: dict[str, Any], new: dict[str, Any], kind: str = "element_fields") -> None:
    """Every write in a seat study records person and seat (owner seat when held, else active)."""
    ctx = decision["ctx"]
    if decision["mode"] == "open" or not ctx.enabled:
        return
    owner = decision.get("owner")
    seat = owner if ctx.holds(owner) else (ctx.active or ("instructor" if ctx.instructor else ""))
    fields = list(new.keys())
    await store.log_event(element["study_id"], seat, ctx.person, "edit", element.get("name") or element["id"], {
        "kind": kind, "element_id": element["id"], "fields": fields, "param_keys": param_keys(owner, fields),
        "old": _jsonable(old), "new": _jsonable(new), "owner_seat": owner, "active_seat": ctx.active})
    try:
        request.state.seat_logged = True
    except Exception:  # noqa: BLE001
        pass


async def propose(request: Request, decision: dict[str, Any], element: dict[str, Any], kind: str,
                  old: dict[str, Any], new: dict[str, Any], option_id: str | None = None) -> dict[str, Any]:
    ctx = decision["ctx"]
    owner = decision["owner"]
    by_seat = ctx.active or ("instructor" if ctx.instructor else "")
    fields = change_fields(new)
    pc = await store.add_pending({
        "study_id": element["study_id"], "owner_seat": owner, "kind": kind, "element_id": element["id"],
        "element_name": element.get("name", ""), "param_keys": param_keys(owner, fields),
        "old": _jsonable(old), "new": _jsonable(new), "option_id": option_id,
        "by_person": ctx.person.id, "by_name": ctx.person.name, "by_seat": by_seat})
    await store.log_event(element["study_id"], by_seat, ctx.person, "propose", element.get("name") or element["id"], {
        "pending_id": pc["id"], "kind": kind, "element_id": element["id"], "fields": fields,
        "param_keys": pc["param_keys"], "owner_seat": owner, "old": pc["old"], "new": pc["new"]})
    try:
        request.state.seat_logged = True
    except Exception:  # noqa: BLE001
        pass
    from .router import broadcast_team
    await broadcast_team(element["study_id"], "pending")
    return pc


def pending_response(body: dict[str, Any], pc: dict[str, Any]) -> JSONResponse:
    """202 Accepted: the unchanged object (the owner's value stands) plus the pending change."""
    out = dict(body)
    out["pending_change"] = {**pc, "owner_label": cfg.label(pc["owner_seat"])}
    return JSONResponse(status_code=202, content=jsonable_encoder(out))


async def apply_pending(pc: dict[str, Any]) -> dict[str, Any]:
    """Apply an accepted pending change to the model (same code paths as a direct edit)."""
    from fastapi import HTTPException

    from ..routers import elements as el_router
    from ..routers import parameters as p_router
    if pc["kind"] == "electrical":
        # rails / power lines / buses / nodes / ports (routers/electrical.py)
        from ..routers.electrical import apply_change
        new = dict(pc.get("new") or {})
        kind, row_id = new.pop("_entity"), new.pop("_id")
        return await apply_change(pc["study_id"], kind, row_id, new)
    if pc["kind"] == "cdr":
        # TM/TC database, FDIR, AOCS, TT&C, line-state and operations rows (routers/cdr.py)
        from ..routers.cdr import apply_change as cdr_apply
        new = dict(pc.get("new") or {})
        new.pop("_entity", None)
        return await cdr_apply(pc["study_id"], new.pop("_id"), new)
    el = el_router._elements.get(pc["element_id"])
    if el is None or el.get("deleted_at"):
        raise HTTPException(409, {"code": "element_gone", "message": "The element no longer exists"})
    new = dict(pc.get("new") or {})
    if pc["kind"] == "element_fields":
        return await el_router.apply_element_update(el, new)
    if pc["kind"] == "element_param":
        name = new.pop("_name")
        return await p_router.put_param(pc["element_id"], name, p_router.ParameterUpsert(**new), pc.get("option_id"))
    if pc["kind"] == "element_param_delete":
        return await p_router.delete_param(pc["element_id"], new["_name"], pc.get("option_id"))
    raise HTTPException(400, f"unknown change kind {pc['kind']}")
