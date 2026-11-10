"""Functions API — Arcadia functional analysis on the spine (SCDF-160 §1.1, §3).

Functions, ports, allocations (function → element per layer), functional
exchanges (port → port) and realizations (SA→LA→PA). Rows are the truth
(``db/function_repo``); no in-memory cache. Mutations are broadcast to the
study WebSocket like ``routers/elements.py`` does.

Routes (mounted under ``/api``):
    POST   /functions/                          ?study_id=   create
    GET    /functions/{id}                       (+ ports + allocations)
    PATCH  /functions/{id}                       {version, ...}
    DELETE /functions/{id}                       soft delete (cascades to ports/exchanges)
    GET    /studies/{id}/functions               flat list, ?layer=
    GET    /studies/{id}/functions/tree          nested, with allocations + ports
    POST   /studies/{id}/functions/migrate-legacy
    POST   /functions/{id}/ports  /  PATCH,DELETE /function-ports/{id}
    POST   /functions/{id}/allocate {element_id, layer}  /  DELETE /functions/{id}/allocate/{layer}
    POST   /functional-exchanges/ ?study_id=  /  GET,PATCH,DELETE /functional-exchanges/{id}
    GET    /studies/{id}/functional-exchanges
    POST   /realizations/ ?study_id=  /  DELETE /realizations/{id}
    GET    /studies/{id}/realizations  /  GET /realizations/for/{kind}/{id}
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..db import function_repo as repo
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)

router = APIRouter()

LAYERS = ("OA", "SA", "LA", "PA")


# ─── Pydantic models ───

class FunctionCreate(BaseModel):
    name: str
    description: str = ""
    parent_id: str | None = None
    layer: str = "SA"
    function_type: str | None = None
    level: int = 0
    is_leaf: bool = False
    position_responsible: str | None = None
    external_id: str | None = None
    external_ids: dict[str, Any] | None = None


class FunctionUpdate(BaseModel):
    version: int
    name: str | None = None
    description: str | None = None
    parent_id: str | None = None
    layer: str | None = None
    function_type: str | None = None
    level: int | None = None
    is_leaf: bool | None = None
    position_responsible: str | None = None
    external_id: str | None = None
    external_ids: dict[str, Any] | None = None


class PortCreate(BaseModel):
    name: str
    direction: str = "out"
    exchange_item_ids: list[str] = Field(default_factory=list)


class PortUpdate(BaseModel):
    name: str | None = None
    direction: str | None = None
    exchange_item_ids: list[str] | None = None


class AllocateBody(BaseModel):
    element_id: str
    layer: str = "SA"


class FunctionalExchangeCreate(BaseModel):
    name: str = ""
    from_port_id: str
    to_port_id: str
    exchange_item_ids: list[str] = Field(default_factory=list)
    realized_by_interface_id: str | None = None
    external_id: str | None = None


class FunctionalExchangeUpdate(BaseModel):
    version: int | None = None
    name: str | None = None
    from_port_id: str | None = None
    to_port_id: str | None = None
    exchange_item_ids: list[str] | None = None
    realized_by_interface_id: str | None = None
    external_id: str | None = None


class RealizationCreate(BaseModel):
    source_kind: str  # function|element
    source_id: str
    target_kind: str
    target_id: str


# ─── Helpers ───

def _check_layer(layer: str | None) -> None:
    if layer is not None and layer not in LAYERS:
        raise HTTPException(400, f"layer must be one of {LAYERS}")


def _map_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if "not found" in msg:
        return HTTPException(404, msg)
    if "Version conflict" in msg:
        return HTTPException(409, msg)
    return HTTPException(400, msg)


def _element_summary(element_id: str | None) -> dict | None:
    if not element_id:
        return None
    from .elements import _elements
    el = _elements.get(element_id)
    if not el:
        return {"id": element_id, "name": None, "element_type": None, "subsystem_domain": None}
    return {
        "id": el["id"], "name": el.get("name"),
        "element_type": el.get("element_type"), "subsystem_domain": el.get("subsystem_domain"),
    }


def _element_exists(element_id: str) -> bool:
    from .elements import _elements
    el = _elements.get(element_id)
    return bool(el) and not el.get("deleted_at")


def _study_of_element(element_id: str) -> str | None:
    from .elements import _elements
    el = _elements.get(element_id)
    return el.get("study_id") if el else None


def _decorate_allocation(a: dict) -> dict:
    return {**a, "element": _element_summary(a.get("element_id"))}


async def _get_or_404(function_id: str) -> dict:
    fn = await repo.get_function(function_id)
    if fn is None:
        raise HTTPException(404, f"Function {function_id} not found")
    return fn


async def _assert_parent(study_id: str, parent_id: str | None, self_id: str | None = None) -> None:
    if not parent_id:
        return
    if parent_id == self_id:
        raise HTTPException(400, "A function cannot be its own parent")
    parent = await repo.get_function(parent_id)
    if parent is None or parent.get("study_id") != study_id:
        raise HTTPException(400, f"Parent function {parent_id} not found in study {study_id}")
    # Cycle guard
    if self_id:
        cur = parent
        while cur and cur.get("parent_id"):
            if cur["parent_id"] == self_id:
                raise HTTPException(400, "parent_id would create a cycle")
            cur = await repo.get_function(cur["parent_id"])


# ─── Functions CRUD ───

@router.post("/functions/")
async def create_function(body: FunctionCreate, study_id: str = Query(...)) -> dict:
    _check_layer(body.layer)
    await _assert_parent(study_id, body.parent_id)
    payload = {"study_id": study_id, **body.model_dump()}
    if payload.get("external_ids") is None:
        payload["external_ids"] = {}
    try:
        fn = await repo.create_function(payload)
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(study_id, "function_created", "function", fn["id"], fn)
    return fn


@router.get("/functions/{function_id}")
async def get_function(function_id: str) -> dict:
    fn = await _get_or_404(function_id)
    fn["ports"] = await repo.list_ports_by_function(function_id)
    fn["allocations"] = [_decorate_allocation(a) for a in await repo.list_allocations_by_function(function_id)]
    return fn


@router.patch("/functions/{function_id}")
async def update_function(function_id: str, body: FunctionUpdate) -> dict:
    fn = await _get_or_404(function_id)
    updates = body.model_dump(exclude_unset=True, exclude={"version"})
    _check_layer(updates.get("layer"))
    if "parent_id" in updates:
        await _assert_parent(fn["study_id"], updates["parent_id"], self_id=function_id)
    try:
        updated = await repo.update_function(function_id, updates, expected_version=body.version)
    except ValueError as exc:
        if "Version conflict" in str(exc):
            raise HTTPException(409, {
                "error": "version_conflict", "your_version": body.version,
                "current_version": fn["version"], "current_state": fn,
            })
        raise _map_error(exc)
    await broadcast_mutation(fn["study_id"], "function_updated", "function", function_id, updated)
    return updated


@router.delete("/functions/{function_id}")
async def delete_function(function_id: str) -> dict:
    fn = await _get_or_404(function_id)
    study_id = fn["study_id"]

    # Collect descendants (cascade)
    all_fns = await repo.list_functions_by_study(study_id)
    children_of: dict[str | None, list[str]] = {}
    for f in all_fns:
        children_of.setdefault(f.get("parent_id"), []).append(f["id"])
    to_delete: list[str] = []
    stack = [function_id]
    while stack:
        cur = stack.pop()
        for c in children_of.get(cur, []):
            to_delete.append(c)
            stack.append(c)

    port_ids: set[str] = set()
    for fid in [function_id, *to_delete]:
        for p in await repo.list_ports_by_function(fid):
            port_ids.add(p["id"])

    exchanges_deleted = 0
    if port_ids:
        for fx in await repo.list_functional_exchanges_by_study(study_id):
            if fx.get("from_port_id") in port_ids or fx.get("to_port_id") in port_ids:
                if await repo.soft_delete_functional_exchange(fx["id"]):
                    exchanges_deleted += 1
    for pid in port_ids:
        await repo.soft_delete_function_port(pid)
    for fid in [function_id, *to_delete]:
        for a in await repo.list_allocations_by_function(fid):
            await repo.unallocate_function(fid, a.get("layer") or "SA")
        await repo.soft_delete_function(fid)

    result = {
        "id": function_id, "deleted": True, "children_deleted": len(to_delete),
        "ports_deleted": len(port_ids), "exchanges_deleted": exchanges_deleted,
    }
    await broadcast_mutation(study_id, "function_deleted", "function", function_id, result)
    return result


@router.get("/studies/{study_id}/functions")
async def list_functions(study_id: str, layer: str | None = None) -> list[dict]:
    _check_layer(layer)
    return await repo.list_functions_by_study(study_id, layer=layer)


@router.get("/studies/{study_id}/functions/tree")
async def get_function_tree(study_id: str, layer: str | None = None) -> list[dict]:
    """Nested function tree with ``ports``, ``allocations`` (decorated with the
    element summary) and ``children``."""
    _check_layer(layer)
    fns = await repo.list_functions_by_study(study_id, layer=layer)
    ports = await repo.load_all_function_ports(study_id)
    allocs = await repo.list_allocations_by_study(study_id)

    ports_by_fn: dict[str, list[dict]] = {}
    for p in ports.values():
        ports_by_fn.setdefault(p["function_id"], []).append(p)
    allocs_by_fn: dict[str, list[dict]] = {}
    for a in allocs:
        allocs_by_fn.setdefault(a["function_id"], []).append(_decorate_allocation(a))

    by_id = {
        f["id"]: {
            **f,
            "ports": sorted(ports_by_fn.get(f["id"], []), key=lambda p: p.get("name") or ""),
            "allocations": allocs_by_fn.get(f["id"], []),
            "children": [],
        }
        for f in fns
    }
    roots: list[dict] = []
    for f in fns:
        node = by_id[f["id"]]
        pid = f.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(node)
        else:
            roots.append(node)

    def _sort(nodes: list[dict]) -> None:
        nodes.sort(key=lambda n: (n.get("created_at") or "", n.get("name") or ""))
        for n in nodes:
            _sort(n["children"])
    _sort(roots)
    return roots


@router.post("/studies/{study_id}/functions/migrate-legacy")
async def migrate_legacy_functions(study_id: str) -> dict:
    """Import ``study.functional_decomposition.functions`` (JSON) into rows."""
    from ..services.function_migration import migrate_study_functions
    from .elements import _elements
    from .studies import get_study_store

    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(404, f"Study {study_id} not found")
    fd = getattr(study, "functional_decomposition", None)
    legacy = [f.model_dump() for f in getattr(fd, "functions", [])] if fd else []
    elements_by_id = {eid: e for eid, e in _elements.items() if e.get("study_id") == study_id}
    counts = await migrate_study_functions(study_id, legacy, elements_by_id)
    result = {"study_id": study_id, "legacy_functions": len(legacy), **counts}
    await broadcast_mutation(study_id, "functions_migrated", "function", study_id, result)
    return result


# ─── Ports ───

@router.post("/functions/{function_id}/ports")
async def create_port(function_id: str, body: PortCreate) -> dict:
    fn = await _get_or_404(function_id)
    try:
        port = await repo.create_function_port({"function_id": function_id, **body.model_dump()})
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(fn["study_id"], "function_port_created", "function_port", port["id"], port)
    return port


@router.get("/functions/{function_id}/ports")
async def list_ports(function_id: str) -> list[dict]:
    await _get_or_404(function_id)
    return await repo.list_ports_by_function(function_id)


@router.patch("/function-ports/{port_id}")
async def update_port(port_id: str, body: PortUpdate) -> dict:
    updates = body.model_dump(exclude_unset=True)
    if updates.get("direction") not in (None, "in", "out"):
        raise HTTPException(400, "direction must be 'in' or 'out'")
    try:
        port = await repo.update_function_port(port_id, updates)
    except ValueError as exc:
        raise _map_error(exc)
    fn = await repo.get_function(port["function_id"])
    await broadcast_mutation(fn["study_id"] if fn else None, "function_port_updated", "function_port", port_id, port)
    return port


@router.delete("/function-ports/{port_id}")
async def delete_port(port_id: str) -> dict:
    ok = await repo.soft_delete_function_port(port_id)
    if not ok:
        raise HTTPException(404, f"Function port {port_id} not found")
    return {"id": port_id, "deleted": True}


# ─── Allocations ───

@router.post("/functions/{function_id}/allocate")
async def allocate_function(function_id: str, body: AllocateBody) -> dict:
    fn = await _get_or_404(function_id)
    _check_layer(body.layer)
    if not _element_exists(body.element_id):
        raise HTTPException(400, f"Element {body.element_id} not found")
    el_study = _study_of_element(body.element_id)
    if el_study and el_study != fn["study_id"]:
        raise HTTPException(400, "Element belongs to a different study")
    old = next((a for a in await repo.list_allocations_by_function(function_id)
                if a.get("layer") == body.layer and not a.get("secondary")), None)
    alloc = await repo.allocate_function(fn["study_id"], function_id, body.element_id, layer=body.layer)
    if old and old.get("element_id") != body.element_id and body.layer == "SA":
        # wave 3: the multi-element list follows the allocation row (first element replaced)
        await repo.remove_secondary_allocation(function_id, old["element_id"])
    alloc = _decorate_allocation(alloc)
    await broadcast_mutation(fn["study_id"], "function_allocated", "function", function_id, alloc)
    return alloc


@router.delete("/functions/{function_id}/allocate/{layer}")
async def unallocate_function(function_id: str, layer: str) -> dict:
    fn = await _get_or_404(function_id)
    _check_layer(layer)
    if layer == "SA":
        for a in await repo.list_allocations_by_function(function_id):
            if a.get("element_id"):
                await repo.remove_secondary_allocation(function_id, a["element_id"])
    ok = await repo.unallocate_function(function_id, layer=layer)
    if not ok:
        raise HTTPException(404, f"Function {function_id} has no allocation at layer {layer}")
    result = {"function_id": function_id, "layer": layer, "unallocated": True}
    await broadcast_mutation(fn["study_id"], "function_unallocated", "function", function_id, result)
    return result


@router.get("/functions/{function_id}/allocations")
async def list_function_allocations(function_id: str) -> list[dict]:
    await _get_or_404(function_id)
    return [_decorate_allocation(a) for a in await repo.list_allocations_by_function(function_id)]


@router.get("/elements/{element_id}/functions")
async def list_functions_for_element(element_id: str) -> list[dict]:
    """Functions allocated to an element (any layer)."""
    out = []
    for a in await repo.list_allocations_by_element(element_id):
        fn = await repo.get_function(a["function_id"])
        if fn:
            out.append({**fn, "allocation_layer": a.get("layer")})
    return out


# ─── Functional exchanges ───

@router.post("/functional-exchanges/")
async def create_functional_exchange(body: FunctionalExchangeCreate, study_id: str = Query(...)) -> dict:
    try:
        fx = await repo.create_functional_exchange({"study_id": study_id, **body.model_dump()})
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(study_id, "functional_exchange_created", "functional_exchange", fx["id"], fx)
    return fx


@router.get("/studies/{study_id}/functional-exchanges")
async def list_functional_exchanges(study_id: str) -> list[dict]:
    return await repo.list_functional_exchanges_by_study(study_id)


@router.get("/functional-exchanges/{exchange_id}")
async def get_functional_exchange(exchange_id: str) -> dict:
    from ..db._arcadia_common import get_row, get_session_factory, row_to_dict
    from ..db.models import FunctionalExchangeRow
    async with get_session_factory()() as session:
        row = await get_row(session, FunctionalExchangeRow, exchange_id)
    if row is None:
        raise HTTPException(404, f"Functional exchange {exchange_id} not found")
    return row_to_dict(row)


@router.patch("/functional-exchanges/{exchange_id}")
async def update_functional_exchange(exchange_id: str, body: FunctionalExchangeUpdate) -> dict:
    updates = body.model_dump(exclude_unset=True, exclude={"version"})
    try:
        fx = await repo.update_functional_exchange(exchange_id, updates, expected_version=body.version)
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(fx["study_id"], "functional_exchange_updated", "functional_exchange", exchange_id, fx)
    return fx


@router.delete("/functional-exchanges/{exchange_id}")
async def delete_functional_exchange(exchange_id: str) -> dict:
    ok = await repo.soft_delete_functional_exchange(exchange_id)
    if not ok:
        raise HTTPException(404, f"Functional exchange {exchange_id} not found")
    return {"id": exchange_id, "deleted": True}


# ─── Realizations ───

@router.post("/realizations/")
async def create_realization(body: RealizationCreate, study_id: str = Query(...)) -> dict:
    try:
        rz = await repo.create_realization({"study_id": study_id, **body.model_dump()})
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(study_id, "realization_created", "realization", rz["id"], rz)
    return rz


@router.get("/studies/{study_id}/realizations")
async def list_realizations(study_id: str) -> list[dict]:
    return await repo.list_realizations_by_study(study_id)


@router.get("/realizations/for/{kind}/{entity_id}")
async def list_realizations_for(kind: str, entity_id: str) -> list[dict]:
    if kind not in ("function", "element"):
        raise HTTPException(400, "kind must be 'function' or 'element'")
    return await repo.list_realizations_for(kind, entity_id)


@router.delete("/realizations/{realization_id}")
async def delete_realization(realization_id: str) -> dict:
    ok = await repo.soft_delete_realization(realization_id)
    if not ok:
        raise HTTPException(404, f"Realization {realization_id} not found")
    return {"id": realization_id, "deleted": True}


# ─── Wave 3 (3.R1): bulk import ───

class FunctionImportBody(BaseModel):
    document: Any                                  # functions.yaml (dict) or its text, or a list of functions
    element_map: dict[str, str] | None = None      # element code (PAY, SSEG …) -> element id
    link_requirements: bool = True                 # function_codes of the requirements -> satisfies


def _parse_function_document(doc: Any) -> dict:
    import yaml
    if isinstance(doc, (bytes, bytearray)):
        doc = doc.decode("utf-8-sig")
    if isinstance(doc, str):
        doc = yaml.safe_load(doc)
    if isinstance(doc, list):
        doc = {"functions": doc}
    if not isinstance(doc, dict) or not isinstance(doc.get("functions"), list):
        raise HTTPException(422, "the document has no 'functions' list")
    return doc


@router.post("/studies/{study_id}/functions/import")
async def import_functions(study_id: str, body: FunctionImportBody) -> dict:
    """One call for a whole functional architecture (3.R1): the function tree (``functions``:
    ``id``, ``name``, ``parent``, ``depth``, ``description``, ``leaf``, ``allocation`` element
    codes), the enabling processes (``enabling_processes``, kind ``process``) and the functional
    exchanges (``functional_interfaces``: ``from``, ``to``, ``item``). Functions are upserted by
    code, so a second import changes nothing. Element codes are resolved by ``element_map``, then
    by name (``services.requirement_queries.resolve_element_code``); the function keeps every
    element it is allocated to. The requirements' ``function_codes`` then become ``satisfies``
    relations."""
    import time
    from ..services import requirement_queries as rq
    from .elements import _elements
    from .studies import get_study_store

    t0 = time.perf_counter()
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    doc = _parse_function_document(body.document)
    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    seats = {str(e.get("id")): e.get("owner_seat") for e in doc.get("elements") or [] if isinstance(e, dict)}
    emap = dict(body.element_map or {})
    resolved: dict[str, str | None] = {}
    errors: list[str] = []

    def eid(code: str) -> str | None:
        if code not in resolved:
            resolved[code] = rq.resolve_element_code(code, elements, emap)
        return resolved[code]

    rows: list[dict] = []
    seen: set[str] = set()
    raw = [f for f in doc["functions"] if isinstance(f, dict)]
    for f in sorted(raw, key=lambda x: int(x.get("depth") or 1)):
        code = str(f.get("id") or f.get("code") or "").strip()
        if not code or not str(f.get("name") or "").strip():
            errors.append(f"function without id or name: {f!r:.80}")
            continue
        if code in seen:
            errors.append(f"duplicate function id {code}")
            continue
        seen.add(code)
        acodes = [str(c) for c in (f.get("allocation") or []) if c]
        leaf = bool(f.get("leaf", not f.get("children")))
        ids = [e for e in (eid(c) for c in acodes) if e] if leaf else []
        rows.append({"code": code, "name": str(f["name"]).strip(), "description": f.get("description") or "",
                     "parent_code": f.get("parent"), "level": int(f.get("depth") or 1), "is_leaf": leaf,
                     "function_type": "function",
                     "position_responsible": seats.get(acodes[0]) if acodes else None,
                     "element_ids": list(dict.fromkeys(ids)), "allocation_codes": acodes if leaf else [],
                     "extra": {"union_allocation_codes": acodes} if not leaf else {}})
    for p in doc.get("enabling_processes") or []:
        code = str(p.get("id") or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        rows.append({"code": code, "name": str(p.get("name") or code), "description": p.get("reference") or "",
                     "parent_code": None, "level": 1, "is_leaf": True, "function_type": "process",
                     "position_responsible": None, "element_ids": [], "allocation_codes": [],
                     "extra": {"reference": p.get("reference")}})
    for r in rows:
        if r["parent_code"] and r["parent_code"] not in seen:
            errors.append(f"{r['code']}: parent {r['parent_code']} is not in the document")
    if errors:
        raise HTTPException(422, {"errors": errors[:50]})
    exchanges = [{"from_code": str(x.get("from")), "to_code": str(x.get("to")), "item": x.get("item")}
                 for x in doc.get("functional_interfaces") or [] if isinstance(x, dict)]
    try:
        rep = await repo.bulk_import(study_id, rows, exchanges)
    except ValueError as exc:
        raise _map_error(exc)
    links = await rq.link_function_requirements(study_id) if body.link_requirements else None
    unresolved = sorted(c for c, v in resolved.items() if v is None)
    leaves = [r for r in rows if r["is_leaf"] and r["function_type"] == "function"]
    report = {
        "study_id": study_id, **{k: v for k, v in rep.items() if k != "id_map"},
        "functions": sum(1 for r in rows if r["function_type"] == "function"),
        "processes": sum(1 for r in rows if r["function_type"] == "process"),
        "by_depth": {str(d): sum(1 for r in rows if r["function_type"] == "function" and r["level"] == d)
                     for d in sorted({r["level"] for r in rows if r["function_type"] == "function"})},
        "leaves": len(leaves), "leaves_allocated": sum(1 for r in leaves if r["element_ids"]),
        "element_map": {c: v for c, v in resolved.items() if v}, "unresolved_elements": unresolved,
        "requirement_links": links, "id_map": rep["id_map"], "seconds": round(time.perf_counter() - t0, 3),
    }
    await broadcast_mutation(study_id, "functions_imported", "function", study_id,
                             {k: report[k] for k in ("created", "updated", "unchanged")})
    return report


class SecondaryAllocationBody(BaseModel):
    element_id: str


@router.post("/functions/{function_id}/allocate/also")
async def allocate_function_also(function_id: str, body: SecondaryAllocationBody) -> dict:
    """Allocate a function to one more element (wave 3: a function may sit on several)."""
    fn = await _get_or_404(function_id)
    if not _element_exists(body.element_id):
        raise HTTPException(400, f"Element {body.element_id} not found")
    if (_study_of_element(body.element_id) or fn["study_id"]) != fn["study_id"]:
        raise HTTPException(400, "Element belongs to a different study")
    if not await repo.list_allocations_by_function(function_id):
        alloc = await repo.allocate_function(fn["study_id"], function_id, body.element_id)
    updated = await repo.add_secondary_allocation(function_id, body.element_id)
    allocs = [_decorate_allocation(a) for a in await repo.list_allocations_by_function(function_id)]
    await broadcast_mutation(fn["study_id"], "function_allocated", "function", function_id, {"allocations": allocs})
    return {"function": updated, "allocations": allocs}


@router.delete("/functions/{function_id}/allocate/also/{element_id}")
async def unallocate_function_also(function_id: str, element_id: str) -> dict:
    fn = await _get_or_404(function_id)
    removed = await repo.remove_secondary_allocation(function_id, element_id)
    primary = [a for a in await repo.list_allocations_by_function(function_id) if not a.get("secondary")]
    if primary and primary[0].get("element_id") == element_id:
        rest = [e for e in ((await repo.get_function(function_id)) or {}).get("external_ids", {}).get("allocation") or []
                if e != element_id]
        if rest:
            await repo.allocate_function(fn["study_id"], function_id, rest[0])
        else:
            await repo.unallocate_function(function_id)
        removed = True
    if not removed:
        raise HTTPException(404, f"Function {function_id} is not allocated to {element_id}")
    allocs = [_decorate_allocation(a) for a in await repo.list_allocations_by_function(function_id)]
    await broadcast_mutation(fn["study_id"], "function_unallocated", "function", function_id, {"allocations": allocs})
    return {"function_id": function_id, "allocations": allocs}
