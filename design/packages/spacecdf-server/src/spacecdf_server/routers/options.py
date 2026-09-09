"""Options API (SCDF-172 §1.4) — design options / variants.

Routes (mounted under ``/api``):
    GET    /studies/{study_id}/options                     list (baseline created lazily, first)
    POST   /studies/{study_id}/options   {name, description?, branch_from?}
    GET    /options/{option_id}
    PATCH  /options/{option_id}          {name?, description?}
    DELETE /options/{option_id}                            soft delete (+ its override rows); 409 for the baseline
    POST   /options/{option_id}/branch   {name, description?} copy the option's overrides into a new option
    GET    /studies/{study_id}/options/compare?a=&b=        see ``services/options.compare_options``
    GET    /studies/{study_id}/options/{option_id}/overrides  the option's own parameter rows (evaluated view)

Semantics (``db/option_repo``): baseline = parameter rows with ``option_id``
NULL; an option row shadows the baseline row of the same (element,
definition); reads for X = baseline ∪ X-overrides; writes with
``option_id=X`` go to the X row only. Parameter routes accept
``?option_id=`` (``routers/parameters.py``), design/analysis runs already do.

Broadcasts (``_arcadia_events.broadcast_mutation``): ``option_created`` /
``option_updated`` / ``option_deleted`` with ``target_kind='option'``.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import option_repo
from ..services import equations
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)

router = APIRouter()


class OptionCreate(BaseModel):
    name: str
    description: str | None = None
    branch_from: str | None = None      # option id to copy overrides from (baseline → nothing)


class OptionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class OptionBranch(BaseModel):
    name: str
    description: str | None = None


async def _option_or_404(option_id: str) -> dict:
    opt = await option_repo.get_option(option_id)
    if opt is None:
        raise HTTPException(404, f"Option {option_id} not found")
    return opt


@router.get("/studies/{study_id}/options")
async def list_options(study_id: str) -> list[dict]:
    return await option_repo.list_options(study_id)


@router.post("/studies/{study_id}/options")
async def create_option(study_id: str, body: OptionCreate) -> dict:
    try:
        if body.branch_from:
            src = await _option_or_404(body.branch_from)
            if src["study_id"] != study_id:
                raise HTTPException(400, "branch_from belongs to another study")
            opt = await option_repo.branch_option(study_id, body.branch_from, body.name, body.description or "")
        else:
            opt = await option_repo.create_option(study_id, body.name, body.description or "")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    await broadcast_mutation(study_id, "option_created", "option", opt["id"], opt)
    return opt


# NOTE: static sub-paths before the ``{option_id}`` ones.
@router.get("/studies/{study_id}/options/compare")
async def compare_options(study_id: str, a: str | None = Query(None), b: str | None = Query(None)) -> dict:
    from ..services.options import compare_options as _compare
    for oid in (a, b):
        if oid:
            opt = await _option_or_404(oid)
            if opt["study_id"] != study_id:
                raise HTTPException(400, f"option {oid} belongs to another study")
    return await _compare(study_id, a or None, b or None)


@router.get("/studies/{study_id}/options/{option_id}/overrides")
async def list_option_overrides(study_id: str, option_id: str) -> list[dict]:
    """Evaluated view (same shape as ``/elements/{id}/parameters``) of the rows
    the option owns. Empty for the baseline."""
    opt = await _option_or_404(option_id)
    if opt["study_id"] != study_id:
        raise HTTPException(400, "option belongs to another study")
    rows = await option_repo.list_option_overrides(study_id, option_id)
    if not rows:
        return []
    own = {r["id"] for r in rows}
    res = await equations.evaluate_study(study_id, option_id=option_id)
    return [p for p in res.get("parameters", []) if p["id"] in own]


@router.get("/options/{option_id}")
async def get_option(option_id: str) -> dict:
    return await _option_or_404(option_id)


@router.patch("/options/{option_id}")
async def update_option(option_id: str, body: OptionUpdate) -> dict:
    await _option_or_404(option_id)
    try:
        opt = await option_repo.update_option(option_id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    await broadcast_mutation(opt["study_id"], "option_updated", "option", option_id, opt)
    return opt


@router.delete("/options/{option_id}")
async def delete_option(option_id: str) -> dict:
    opt = await _option_or_404(option_id)
    if opt.get("is_baseline"):
        raise HTTPException(409, "the baseline cannot be deleted")
    deleted = await option_repo.soft_delete_option(option_id)
    await broadcast_mutation(opt["study_id"], "option_deleted", "option", option_id, {"id": option_id})
    return {"id": option_id, "deleted": deleted}


@router.post("/options/{option_id}/branch")
async def branch_option(option_id: str, body: OptionBranch) -> dict:
    src = await _option_or_404(option_id)
    try:
        opt = await option_repo.branch_option(src["study_id"], option_id, body.name, body.description or "")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    await broadcast_mutation(src["study_id"], "option_created", "option", opt["id"], opt)
    return opt
