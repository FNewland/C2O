"""Exchange items + ICD API (SCDF-160 §1.2, §3).

An exchange item is *what* flows over an interface (data, power, rf, …) with
typed properties. Interfaces carry ``exchange_item_ids_json``; the ICD is the
projection interface × exchange item × properties.

Routes (mounted under ``/api``):
    POST   /exchange-items/ ?study_id=       create
    GET    /exchange-items/{id}
    PATCH  /exchange-items/{id}               {version?, ...}
    DELETE /exchange-items/{id}
    GET    /studies/{id}/exchange-items       ?kind=
    PATCH  /interfaces/{id}/exchange-items    {exchange_item_ids}
    GET    /studies/{id}/icd                  rows
    GET    /studies/{id}/icd.csv
"""
from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..db import exchange_item_repo as repo
from ..db.exchange_item_repo import EXCHANGE_ITEM_KINDS
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)

router = APIRouter()


class ExchangeItemCreate(BaseModel):
    name: str
    kind: str = "data"
    description: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)
    external_id: str | None = None
    external_ids: dict[str, Any] | None = None


class ExchangeItemUpdate(BaseModel):
    version: int | None = None
    name: str | None = None
    kind: str | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None
    external_id: str | None = None
    external_ids: dict[str, Any] | None = None


class InterfaceExchangeItems(BaseModel):
    exchange_item_ids: list[str]


def _map_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if "not found" in msg:
        return HTTPException(404, msg)
    if "Version conflict" in msg:
        return HTTPException(409, msg)
    return HTTPException(400, msg)


# ─── CRUD ───

@router.post("/exchange-items/")
async def create_exchange_item(body: ExchangeItemCreate, study_id: str = Query(...)) -> dict:
    if body.kind not in EXCHANGE_ITEM_KINDS:
        raise HTTPException(400, f"kind must be one of {EXCHANGE_ITEM_KINDS}")
    payload = {"study_id": study_id, **body.model_dump()}
    if payload.get("external_ids") is None:
        payload["external_ids"] = {}
    try:
        item = await repo.create_exchange_item(payload)
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(study_id, "exchange_item_created", "exchange_item", item["id"], item)
    return item


@router.get("/exchange-items/{item_id}")
async def get_exchange_item(item_id: str) -> dict:
    item = await repo.get_exchange_item(item_id)
    if item is None:
        raise HTTPException(404, f"Exchange item {item_id} not found")
    return item


@router.patch("/exchange-items/{item_id}")
async def update_exchange_item(item_id: str, body: ExchangeItemUpdate) -> dict:
    updates = body.model_dump(exclude_unset=True, exclude={"version"})
    try:
        item = await repo.update_exchange_item(item_id, updates, expected_version=body.version)
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(item["study_id"], "exchange_item_updated", "exchange_item", item_id, item)
    return item


@router.delete("/exchange-items/{item_id}")
async def delete_exchange_item(item_id: str) -> dict:
    item = await repo.get_exchange_item(item_id)
    if item is None:
        raise HTTPException(404, f"Exchange item {item_id} not found")
    await repo.soft_delete_exchange_item(item_id)
    # Drop the id from any interface that referenced it (cache + DB)
    from .elements import _interfaces, set_interface_exchange_items
    detached = 0
    for iface in list(_interfaces.values()):
        if iface.get("study_id") != item["study_id"] or iface.get("deleted_at"):
            continue
        ids = _iface_item_ids(iface)
        if item_id in ids:
            await set_interface_exchange_items(iface["id"], [i for i in ids if i != item_id])
            detached += 1
    result = {"id": item_id, "deleted": True, "interfaces_detached": detached}
    await broadcast_mutation(item["study_id"], "exchange_item_deleted", "exchange_item", item_id, result)
    return result


@router.get("/studies/{study_id}/exchange-items")
async def list_exchange_items(study_id: str, kind: str | None = None) -> list[dict]:
    if kind is not None and kind not in EXCHANGE_ITEM_KINDS:
        raise HTTPException(400, f"kind must be one of {EXCHANGE_ITEM_KINDS}")
    return await repo.list_exchange_items_by_study(study_id, kind=kind)


# ─── Interface ↔ exchange items ───

def _iface_item_ids(iface: dict) -> list[str]:
    ids = iface.get("exchange_item_ids_json")
    if ids is None:
        ids = iface.get("exchange_item_ids")
    return list(ids or [])


@router.patch("/interfaces/{interface_id}/exchange-items")
async def set_exchange_items_on_interface(interface_id: str, body: InterfaceExchangeItems) -> dict:
    from .elements import _interfaces, set_interface_exchange_items
    iface = _interfaces.get(interface_id)
    if not iface or iface.get("deleted_at"):
        raise HTTPException(404, f"Interface {interface_id} not found")
    if body.exchange_item_ids:
        found = {i["id"] for i in await repo.list_exchange_items_by_ids(body.exchange_item_ids)}
        missing = [i for i in body.exchange_item_ids if i not in found]
        if missing:
            raise HTTPException(400, f"Unknown exchange items: {missing}")
    try:
        iface = await set_interface_exchange_items(interface_id, body.exchange_item_ids)
    except KeyError:
        raise HTTPException(404, f"Interface {interface_id} not found")
    await broadcast_mutation(iface.get("study_id"), "interface_exchange_items_updated", "interface",
                             interface_id, {"exchange_item_ids": _iface_item_ids(iface)})
    return iface


@router.get("/interfaces/{interface_id}/exchange-items")
async def list_exchange_items_on_interface(interface_id: str) -> list[dict]:
    from .elements import _interfaces
    iface = _interfaces.get(interface_id)
    if not iface or iface.get("deleted_at"):
        raise HTTPException(404, f"Interface {interface_id} not found")
    ids = _iface_item_ids(iface)
    by_id = {i["id"]: i for i in await repo.list_exchange_items_by_ids(ids)}
    return [by_id[i] for i in ids if i in by_id]


# ─── ICD ───

async def build_icd_rows(study_id: str) -> list[dict]:
    """Interface × exchange item rows. Interfaces without exchange items yield
    one row with ``exchange_item=None`` so the ICD is complete."""
    from .elements import _elements, _interfaces

    items = await repo.load_all_exchange_items(study_id)

    def _el(eid: str | None) -> dict:
        el = _elements.get(eid) if eid else None
        return {"id": eid, "name": el.get("name") if el else None}

    rows: list[dict] = []
    ifaces = [i for i in _interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")]
    ifaces.sort(key=lambda i: (i.get("name") or "", i["id"]))
    for iface in ifaces:
        base = {
            "interface_id": iface["id"],
            "name": iface.get("name") or "",
            "interface_type": iface.get("interface_type"),
            "direction": iface.get("direction"),
            "from_element": _el(iface.get("from_element_id")),
            "to_element": _el(iface.get("to_element_id")),
            "interface_properties": iface.get("properties") or {},
        }
        ids = [i for i in _iface_item_ids(iface) if i in items]
        if not ids:
            rows.append({**base, "exchange_item": None})
            continue
        for iid in ids:
            it = items[iid]
            rows.append({**base, "exchange_item": {
                "id": it["id"], "name": it.get("name"), "kind": it.get("kind"),
                "properties": it.get("properties") or {},
            }})
    return rows


@router.get("/studies/{study_id}/icd")
async def get_icd(study_id: str) -> list[dict]:
    return await build_icd_rows(study_id)


@router.get("/studies/{study_id}/icd.csv")
async def get_icd_csv(study_id: str) -> Response:
    rows = await build_icd_rows(study_id)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["interface_id", "interface", "interface_type", "direction", "from_element_id", "from_element",
                "to_element_id", "to_element", "exchange_item_id", "exchange_item", "kind", "properties"])
    for r in rows:
        xi = r.get("exchange_item") or {}
        w.writerow([
            r["interface_id"], r["name"], r["interface_type"], r.get("direction") or "",
            r["from_element"]["id"] or "", r["from_element"]["name"] or "",
            r["to_element"]["id"] or "", r["to_element"]["name"] or "",
            xi.get("id") or "", xi.get("name") or "", xi.get("kind") or "",
            json.dumps(xi.get("properties") or {}, sort_keys=True) if xi else "",
        ])
    return Response(
        content=buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="icd_{study_id}.csv"'},
    )
