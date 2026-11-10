"""Open-item register (negotiation #5; SE matrix #20). Owner D (3.D4).

Mounted under ``/api``:

* ``GET   /studies/{sid}/open-items?blocks_gate=&exact=&include_closed=``  the joined register
  (``services/open_items.py``): stored items, RIDs and actions, conditional decisions, undecided
  gate trades and change proposals, with the gate each blocks
* ``POST  /studies/{sid}/open-items``                 a new stored item (PI or seat decision, action …)
* ``PATCH /studies/{sid}/open-items/{id}``            update a stored item (close it with a resolution)
* ``POST  /studies/{sid}/open-items/import``          many items in one call (``{"items": [...]}``;
  NUMBERS ``open_decisions`` shape accepted: ``id``, ``owner``, ``question``)

Items that live elsewhere (RIDs, trades, change proposals) are listed with ``editable: false`` and
are changed where they live.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ..services import open_items as oi
from ._wave3_stub import study_or_404

router = APIRouter()


async def _broadcast(study_id: str) -> None:
    from .gates import _broadcast as bc
    await bc(study_id, "study_records_changed", {"kind": "open_items"})


@router.get("/studies/{study_id}/open-items")
async def list_open_items(study_id: str, blocks_gate: str | None = Query(None), exact: bool = Query(False),
                          include_closed: bool = Query(False)) -> dict:
    """Every open item (``include_closed`` adds the closed ones), filtered by the gate it blocks:
    that gate or an earlier one (``exact``: that gate only)."""
    study = study_or_404(study_id)
    reg = await oi.register(study_id, study, blocks_gate=blocks_gate, exact=exact, include_closed=include_closed)
    return {"study_id": study_id, **reg}


@router.post("/studies/{study_id}/open-items")
async def create_open_item(study_id: str, body: dict[str, Any]) -> dict:
    study_or_404(study_id)
    try:
        row = await oi.create(study_id, body or {})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await _broadcast(study_id)
    return row


@router.patch("/studies/{study_id}/open-items/{item_id}")
async def update_open_item(study_id: str, item_id: str, body: dict[str, Any]) -> dict:
    study_or_404(study_id)
    if ":" in item_id:
        raise HTTPException(409, {"code": "not_editable", "message": "This item lives in the review record, a trade or "
                                  "the change register; change it there"})
    try:
        row = await oi.update(study_id, item_id, body or {})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if row is None:
        raise HTTPException(404, f"Open item {item_id} not found")
    await _broadcast(study_id)
    return row


@router.post("/studies/{study_id}/open-items/import")
async def import_open_items(study_id: str, body: dict[str, Any]) -> dict:
    """NUMBERS ``open_decisions`` (or any list of items) in one call (seed S3)."""
    study_or_404(study_id)
    items = (body or {}).get("items") or (body or {}).get("open_decisions") or []
    if not isinstance(items, list) or len(items) > 500:
        raise HTTPException(422, "items must be a list of at most 500 objects")
    try:
        res = await oi.import_items(study_id, items, replace=bool((body or {}).get("replace")))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if res["added"] or res["replaced"]:
        await _broadcast(study_id)
    return res
