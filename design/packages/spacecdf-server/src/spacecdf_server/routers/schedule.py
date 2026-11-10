"""Schedule-lite API (W11a): project settings, milestones, work packages, long-lead items, cost.

    GET    /api/studies/{sid}/schedule                  settings, milestones, WBS, long-lead items, cost
    PUT    /api/studies/{sid}/schedule/settings         start date, currency, launch provided …
    POST   /api/studies/{sid}/schedule/propose          milestones from the gate profile (+ QR, AR, FRR,
                                                        models, launch) and the WBS from the product tree
    POST   /api/studies/{sid}/schedule/{kind}           kind = milestones | work_packages
    PATCH  /api/studies/{sid}/schedule/{kind}/{id}
    DELETE /api/studies/{sid}/schedule/{kind}/{id}
    GET    /api/studies/{sid}/cost                      bottom-up cost from the selected equipment

Services: ``services/schedule.py`` and ``services/cost_engine.study_cost``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services import schedule as svc

router = APIRouter()
KINDS = ("milestones", "work_packages")


def _require_study(study_id: str) -> None:
    from .elements import _elements
    from .studies import get_study_store
    if get_study_store().get(study_id) is None and not any(e.get("study_id") == study_id for e in _elements.values()):
        raise HTTPException(404, f"Study {study_id} not found")


def _kind(kind: str) -> str:
    if kind not in KINDS:
        raise HTTPException(404, f"unknown schedule table {kind!r}; valid: {list(KINDS)}")
    return kind


class SettingsBody(BaseModel):
    start_date: str | None = None
    currency: str | None = None
    eur_to_cad: float | None = None
    launch_provided: bool | None = None
    launch_cost_keur: float | None = None
    notes: str | None = None


class RowBody(BaseModel):
    code: str | None = None
    kind: str | None = None
    gate_id: str | None = None
    name: str | None = None
    name_fr: str | None = None
    month: int | None = None
    date: str | None = None
    status: str | None = None
    parent_code: str | None = None
    element_id: str | None = None
    owner_seat: str | None = None
    start_month: int | None = None
    end_month: int | None = None
    deliverables: list[str] | None = None
    order: int | None = None


class ProposeBody(BaseModel):
    replace: bool = False


@router.get("/studies/{study_id}/schedule")
async def get_schedule(study_id: str) -> dict:
    _require_study(study_id)
    return await svc.schedule_summary(study_id)


@router.put("/studies/{study_id}/schedule/settings")
async def put_settings(study_id: str, body: SettingsBody) -> dict:
    _require_study(study_id)
    data = body.model_dump(exclude_unset=True)
    if "currency" in data and str(data["currency"] or "").upper() not in ("EUR", "CAD"):
        raise HTTPException(422, "currency must be EUR or CAD")
    if data.get("start_date") and not svc.add_months(str(data["start_date"]), 0):
        raise HTTPException(422, "start_date must be YYYY-MM or YYYY-MM-DD")
    return await svc.put_settings(study_id, data)


@router.post("/studies/{study_id}/schedule/propose")
async def propose(study_id: str, body: ProposeBody | None = None) -> dict:
    _require_study(study_id)
    return await svc.propose(study_id, replace=bool(body and body.replace))


@router.post("/studies/{study_id}/schedule/{kind}")
async def add_row(study_id: str, kind: str, body: RowBody) -> dict:
    _require_study(study_id)
    if not body.code:
        raise HTTPException(422, "code is required")
    return await svc.upsert(study_id, _kind(kind), body.model_dump(exclude_none=True))


@router.patch("/studies/{study_id}/schedule/{kind}/{row_id}")
async def patch_row(study_id: str, kind: str, row_id: str, body: RowBody) -> dict:
    out = await svc.upsert(study_id, _kind(kind), body.model_dump(exclude_unset=True), row_id)
    if out is None:
        raise HTTPException(404, "row not found")
    return out


@router.delete("/studies/{study_id}/schedule/{kind}/{row_id}")
async def delete_row(study_id: str, kind: str, row_id: str) -> dict:
    if not await svc.delete_row(study_id, _kind(kind), row_id):
        raise HTTPException(404, "row not found")
    return {"deleted": row_id}


@router.get("/studies/{study_id}/cost")
async def study_cost(study_id: str) -> dict[str, Any]:
    _require_study(study_id)
    from ..services.cost_engine import study_cost as compute
    return await compute(study_id, await svc.get_settings(study_id))


# ─── wave 3, step 0 (PI addendum): cost pricing with labour, test campaigns and reserve (A) ───

@router.get("/studies/{study_id}/cost/items")
async def list_cost_items(study_id: str) -> dict:
    """TODO(A, 3.A7): the priced lines (``cost_items``): labour, test campaigns, hardware, reserve;
    launch zero when provided."""
    from ._wave3_stub import stub_list
    return stub_list(study_id, "A", "3.A7", total_keur=None)


@router.post("/studies/{study_id}/cost/items")
async def create_cost_item(study_id: str, body: dict) -> dict:
    """TODO(A, 3.A7)."""
    from ._wave3_stub import not_implemented, study_or_404
    study_or_404(study_id)
    raise not_implemented("A", "3.A7")


@router.post("/studies/{study_id}/cost/price")
async def price_cost_model(study_id: str) -> dict:
    """TODO(A, 3.A7): propose the priced lines from the WBS, the AIT test matrix and a reference class."""
    from ._wave3_stub import not_implemented, study_or_404
    study_or_404(study_id)
    raise not_implemented("A", "3.A7")
