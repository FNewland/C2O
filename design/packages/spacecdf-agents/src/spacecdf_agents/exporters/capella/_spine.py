"""Gateway between the Capella adapter and the SpaceCDF spine.

All ``spacecdf_server`` imports are lazy (same convention as
``exporters/docs/generator.py``) so ``mapping.py`` stays importable without
the server package.

Where the Capella UUID is stored (``external_ids['capella']``):

* functions, exchange items, requirements (in-memory store) -> ``external_ids``
* functional exchanges, relations -> ``external_id = "capella:<uuid>"``
  (those rows only have the scalar column)
* elements -> ``performance['external_ids']['capella']``
* interfaces -> ``properties['external_ids']['capella']``

The last two are a stop-gap: ``DesignElementRow`` / ``ElementInterfaceRow``
have no ``external_ids_json`` column yet (``db/models.py`` is owned by another
work-stream).  ``mapping._recorded_uuid`` reads ``external_ids`` so once the
columns exist only :func:`_element_external_ids` / :func:`_interface_external_ids`
need to change.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from .mapping import SpineSnapshot

logger = logging.getLogger(__name__)


# ── external-id accessors ───────────────────────────────────────────────

def _element_external_ids(el: dict) -> dict:
    perf = el.get("performance")
    if isinstance(perf, dict) and isinstance(perf.get("external_ids"), dict):
        return perf["external_ids"]
    return {}


def _interface_external_ids(iface: dict) -> dict:
    props = iface.get("properties")
    if isinstance(props, dict) and isinstance(props.get("external_ids"), dict):
        return props["external_ids"]
    return {}


def _with_external_ids(d: dict) -> dict:
    """Return a copy of the dict with an API-level ``external_ids`` key."""
    out = dict(d)
    if "external_ids" not in out or not isinstance(out.get("external_ids"), dict):
        ext = out.get("external_ids_json")
        out["external_ids"] = dict(ext) if isinstance(ext, dict) else {}
    return out


# ── loading ─────────────────────────────────────────────────────────────

def _effective_value(p: dict) -> float | None:
    sw = p.get("value_switch") or "computed"
    order = {"manual": ("manual_value", "computed_value", "reference_value"),
             "reference": ("reference_value", "computed_value", "manual_value")}.get(
        sw, ("computed_value", "manual_value", "reference_value"))
    for k in order:
        if p.get(k) is not None:
            return p[k]
    return None


async def load_snapshot(study_id: str) -> SpineSnapshot:
    from spacecdf_server.db.element_repo import load_all_elements
    from spacecdf_server.db.exchange_item_repo import load_all_exchange_items
    from spacecdf_server.db.function_repo import (
        load_all_function_allocations, load_all_function_ports, load_all_functional_exchanges,
        load_all_functions,
    )
    from spacecdf_server.db.parameter_repo import (
        load_all_element_parameters, load_all_parameter_definitions,
    )
    from spacecdf_server.db.relation_repo import load_all_relations
    from spacecdf_server.routers.requirements import _requirements

    elements_all, interfaces_all = await load_all_elements()
    elements = []
    for e in elements_all.values():
        if e.get("study_id") != study_id:
            continue
        e = dict(e)
        e["external_ids"] = _element_external_ids(e)
        elements.append(e)
    interfaces = []
    for i in interfaces_all.values():
        if i.get("study_id") != study_id:
            continue
        i = dict(i)
        i["external_ids"] = _interface_external_ids(i)
        i["exchange_item_ids"] = list(i.get("exchange_item_ids_json") or i.get("exchange_item_ids") or [])
        interfaces.append(i)

    functions = [_with_external_ids(f) for f in (await load_all_functions(study_id)).values()]
    ports = list((await load_all_function_ports(study_id)).values())
    allocations = list((await load_all_function_allocations(study_id)).values())
    fxs = list((await load_all_functional_exchanges(study_id)).values())
    items = [_with_external_ids(x) for x in (await load_all_exchange_items(study_id)).values()]
    relations = list((await load_all_relations(study_id)).values())
    requirements = [dict(r) for r in _requirements.values()
                    if r.get("study_id") == study_id and r.get("status") != "retired"]

    defs = await load_all_parameter_definitions()
    params = []
    for p in (await load_all_element_parameters(study_id)).values():
        d = defs.get(p.get("definition_id") or "")
        if not d:
            continue
        params.append({"element_id": p["element_id"], "name": d["name"],
                       "unit": d.get("unit") or "", "value": _effective_value(p)})

    study_name = study_id
    try:
        from spacecdf_server.routers.studies import get_study_store
        s = get_study_store().get(study_id)
        if s is not None:
            study_name = getattr(s, "name", None) or study_id
    except Exception:
        pass

    return SpineSnapshot(
        study_id=study_id, study_name=study_name, elements=elements, interfaces=interfaces,
        functions=functions, function_ports=ports, allocations=allocations,
        functional_exchanges=fxs, exchange_items=items, requirements=requirements,
        relations=relations, parameters=params,
    )


# ── write-back of Capella UUIDs ─────────────────────────────────────────

async def record_capella_ids(snap: SpineSnapshot, id_map: dict[tuple[str, str], str]) -> int:
    """Store ``external_ids['capella']`` for every exported entity. Returns count."""
    from spacecdf_server.db.element_repo import db_update_element, db_update_interface
    from spacecdf_server.db.exchange_item_repo import update_exchange_item
    from spacecdf_server.db.function_repo import update_function, update_functional_exchange
    from spacecdf_server.db.relation_repo import create_relation
    from spacecdf_server.routers import elements as elements_router
    from spacecdf_server.routers.requirements import _requirements

    n = 0
    by_kind: dict[str, dict[str, str]] = {}
    for (kind, sid), u in id_map.items():
        by_kind.setdefault(kind, {})[sid] = u

    for e in snap.elements:
        u = by_kind.get("element", {}).get(e["id"])
        if not u or _element_external_ids(e).get("capella") == u:
            continue
        perf = dict(e.get("performance") or {})
        perf["external_ids"] = {**(perf.get("external_ids") or {}), "capella": u}
        full = {k: v for k, v in e.items() if k != "external_ids"}
        full["performance"] = perf
        await db_update_element(e["id"], full)
        cached = elements_router._elements.get(e["id"])
        if cached is not None:
            cached["performance"] = perf
        n += 1

    for i in snap.interfaces:
        u = by_kind.get("interface", {}).get(i["id"])
        if not u or _interface_external_ids(i).get("capella") == u:
            continue
        props = dict(i.get("properties") or {})
        props["external_ids"] = {**(props.get("external_ids") or {}), "capella": u}
        full = {k: v for k, v in i.items() if k not in ("external_ids", "exchange_item_ids")}
        full["properties"] = props
        await db_update_interface(i["id"], full)
        cached = elements_router._interfaces.get(i["id"])
        if cached is not None:
            cached["properties"] = props
        n += 1

    for f in snap.functions:
        u = by_kind.get("function", {}).get(f["id"])
        if u and f.get("external_ids", {}).get("capella") != u:
            await update_function(f["id"], {"external_ids": {**f.get("external_ids", {}), "capella": u}})
            n += 1
    for x in snap.exchange_items:
        u = by_kind.get("exchange_item", {}).get(x["id"])
        if u and x.get("external_ids", {}).get("capella") != u:
            await update_exchange_item(x["id"], {"external_ids": {**x.get("external_ids", {}), "capella": u}})
            n += 1
    for fx in snap.functional_exchanges:
        u = by_kind.get("functional_exchange", {}).get(fx["id"])
        if u and fx.get("external_id") != f"capella:{u}":
            await update_functional_exchange(fx["id"], {"external_id": f"capella:{u}"})
            n += 1
    for r in snap.requirements:
        u = by_kind.get("requirement", {}).get(r["id"])
        live = _requirements.get(r["id"])
        if u and live is not None and (live.get("external_ids") or {}).get("capella") != u:
            live["external_ids"] = {**(live.get("external_ids") or {}), "capella": u}
            n += 1
    for rel in snap.relations:
        u = by_kind.get("relation", {}).get(rel["id"])
        if u and rel.get("external_id") != f"capella:{u}":
            await create_relation({**rel, "external_id": f"capella:{u}"})
            n += 1
    return n


# ── importer upserts ────────────────────────────────────────────────────

async def upsert_element(study_id: str, existing: dict | None, data: dict, capella_uuid: str) -> dict:
    """Create or update a design element (write-through cache + DB)."""
    from spacecdf_server.db.element_repo import db_create_element, db_update_element
    from spacecdf_server.routers import elements as elements_router

    perf = dict((existing or {}).get("performance") or {})
    perf["external_ids"] = {**(perf.get("external_ids") or {}), "capella": capella_uuid}
    if existing is None:
        el = {
            "id": uuid4().hex, "study_id": study_id, "session_id": None, "parent_id": None,
            "name": "", "element_type": "component", "subsystem_domain": None, "description": "",
            "segment": "space", "layer": "PA", "quantity": 1, "margin_percent": 20.0,
            "in_scope": True, "frozen": False, "diagram_collapsed": False,
            "version": 1, "deleted_at": None,
        }
        el.update(data)
        el["performance"] = perf
        await db_create_element(el)
        elements_router._elements[el["id"]] = el
        return el
    el = dict(existing)
    el.update({k: v for k, v in data.items() if v is not None})
    el["performance"] = perf
    el["version"] = int(el.get("version") or 1) + 1
    el.pop("external_ids", None)
    await db_update_element(el["id"], el)
    cached = elements_router._elements.get(el["id"])
    if cached is not None:
        cached.update(el)
    return el


async def upsert_interface(study_id: str, existing: dict | None, data: dict, capella_uuid: str) -> dict:
    from spacecdf_server.db.element_repo import db_create_interface, db_update_interface
    from spacecdf_server.routers import elements as elements_router

    props = dict((existing or {}).get("properties") or {})
    props["external_ids"] = {**(props.get("external_ids") or {}), "capella": capella_uuid}
    if existing is None:
        iface = {
            "id": uuid4().hex, "study_id": study_id, "name": "", "interface_type": "data",
            "direction": "bidirectional", "status": "defined", "criticality": "standard",
            "diagram_label": "", "version": 1, "deleted_at": None,
        }
        iface.update(data)
        iface["properties"] = props
        iface["exchange_item_ids_json"] = list(data.get("exchange_item_ids") or [])
        iface["exchange_item_ids"] = list(iface["exchange_item_ids_json"])
        await db_create_interface(iface)
        elements_router._interfaces[iface["id"]] = iface
        return iface
    iface = dict(existing)
    iface.update({k: v for k, v in data.items() if v is not None})
    iface["properties"] = props
    if "exchange_item_ids" in data:
        iface["exchange_item_ids_json"] = list(data["exchange_item_ids"] or [])
        iface["exchange_item_ids"] = list(iface["exchange_item_ids_json"])
    iface["version"] = int(iface.get("version") or 1) + 1
    iface.pop("external_ids", None)
    await db_update_interface(iface["id"], iface)
    cached = elements_router._interfaces.get(iface["id"])
    if cached is not None:
        cached.update(iface)
    return iface


async def upsert_function(study_id: str, existing: dict | None, data: dict, capella_uuid: str) -> dict:
    from spacecdf_server.db.function_repo import create_function, update_function
    ext = {**((existing or {}).get("external_ids") or {}), "capella": capella_uuid}
    if existing is None:
        return await create_function({**data, "study_id": study_id, "external_ids": ext})
    return await update_function(existing["id"], {**data, "external_ids": ext})


async def upsert_function_port(existing: dict | None, data: dict) -> dict:
    from spacecdf_server.db.function_repo import create_function_port, update_function_port
    if existing is None:
        return await create_function_port(data)
    return await update_function_port(existing["id"], {k: v for k, v in data.items() if k != "function_id"})


async def upsert_functional_exchange(study_id: str, existing: dict | None, data: dict, capella_uuid: str) -> dict:
    from spacecdf_server.db.function_repo import create_functional_exchange, update_functional_exchange
    ext = f"capella:{capella_uuid}"
    if existing is None:
        return await create_functional_exchange({**data, "study_id": study_id, "external_id": ext})
    return await update_functional_exchange(existing["id"], {**data, "external_id": ext})


async def upsert_exchange_item(study_id: str, existing: dict | None, data: dict, capella_uuid: str) -> dict:
    from spacecdf_server.db.exchange_item_repo import create_exchange_item, update_exchange_item
    ext = {**((existing or {}).get("external_ids") or {}), "capella": capella_uuid}
    if existing is None:
        return await create_exchange_item({**data, "study_id": study_id, "external_ids": ext})
    return await update_exchange_item(existing["id"], {**data, "external_ids": ext})


async def set_allocation(study_id: str, function_id: str, element_id: str, layer: str) -> dict:
    from spacecdf_server.db.function_repo import allocate_function
    return await allocate_function(study_id, function_id, element_id, layer)


def upsert_requirement(study_id: str, existing: dict | None, data: dict, capella_uuid: str) -> dict:
    """Requirements live in ``routers.requirements._requirements`` (what the API serves)."""
    from spacecdf_server.routers.requirements import _requirements
    if existing is None:
        req_id = data.get("id")
        if not req_id or req_id in _requirements:  # store is global across studies
            req_id = f"REQ-{uuid4().hex[:8]}"
        req = {
            "id": req_id, "study_id": study_id, "parent_id": None, "element_id": None,
            "level": "system", "code": req_id, "text": "", "rationale": None,
            "threshold_param_path": None, "threshold_op": None, "threshold_value": None,
            "verification_method": None, "verification_phase": None, "responsible_position": None,
            "status": "draft", "derived_from_requirement_id": None,
        }
        req.update({k: v for k, v in data.items() if k != "id"})
        req["external_ids"] = {"capella": capella_uuid}
        _requirements[req_id] = req
        return req
    req = _requirements.get(existing["id"], existing)
    req.update({k: v for k, v in data.items() if k != "id" and v is not None})
    req["external_ids"] = {**(req.get("external_ids") or {}), "capella": capella_uuid}
    _requirements[req["id"]] = req
    return req


async def upsert_relation(study_id: str, data: dict, capella_uuid: str) -> dict:
    from spacecdf_server.db.relation_repo import create_relation
    return await create_relation({**data, "study_id": study_id, "external_id": f"capella:{capella_uuid}"})


async def upsert_parameter(study_id: str, element_id: str, name: str, value: float) -> dict:
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    return await upsert_element_parameter({
        "study_id": study_id, "element_id": element_id, "definition_name": name,
        "manual_value": value, "value_switch": "manual",
    })
