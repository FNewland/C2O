"""Typed requirement relations + traceability API (SCDF-160 §1.4, §3).

Relations (``satisfies|verifies|refines|derives|traces|allocates``) link any
two spine entities (requirement / element / function / interface / parameter
/ test). Rows are the truth (``db/relation_repo``).

Routes (mounted under ``/api``):
    POST   /relations/ ?study_id=                create (idempotent on kind+source+target)
    GET    /relations/{id}   /  DELETE /relations/{id}
    GET    /studies/{id}/relations               ?kind=
    GET    /relations/for/{entity_kind}/{entity_id}   ?kind= &direction=in|out|both
    GET    /studies/{id}/traceability/tree
    GET    /requirements/{id}/trace
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import function_repo
from ..db import relation_repo as repo
from ..db.relation_repo import ENTITY_KINDS, RELATION_KINDS
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)

router = APIRouter()

#: Relation kinds that bind a requirement to the design entity that meets it.
LINK_KINDS = ("satisfies", "allocates")


class RelationCreate(BaseModel):
    kind: str
    source_kind: str
    source_id: str
    target_kind: str
    target_id: str
    rationale: str | None = None
    external_id: str | None = None


def _map_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if "not found" in msg:
        return HTTPException(404, msg)
    return HTTPException(400, msg)


# ─── CRUD ───

@router.post("/relations/")
async def create_relation(body: RelationCreate, study_id: str = Query(...)) -> dict:
    if body.kind not in RELATION_KINDS:
        raise HTTPException(400, f"kind must be one of {RELATION_KINDS}")
    for k in (body.source_kind, body.target_kind):
        if k not in ENTITY_KINDS:
            raise HTTPException(400, f"entity kind must be one of {ENTITY_KINDS}")
    try:
        rel = await repo.create_relation({"study_id": study_id, **body.model_dump()})
    except ValueError as exc:
        raise _map_error(exc)
    await broadcast_mutation(study_id, "relation_created", "relation", rel["id"], rel)
    return rel


@router.get("/relations/for/{entity_kind}/{entity_id}")
async def list_relations_for(entity_kind: str, entity_id: str, kind: str | None = None,
                             direction: str = "both") -> list[dict]:
    if entity_kind not in ENTITY_KINDS:
        raise HTTPException(400, f"entity kind must be one of {ENTITY_KINDS}")
    if direction not in ("in", "out", "both"):
        raise HTTPException(400, "direction must be in|out|both")
    return await repo.list_relations_for(entity_kind, entity_id, kind=kind, direction=direction)


@router.get("/relations/{relation_id}")
async def get_relation(relation_id: str) -> dict:
    rel = await repo.get_relation(relation_id)
    if rel is None:
        raise HTTPException(404, f"Relation {relation_id} not found")
    return rel


@router.delete("/relations/{relation_id}")
async def delete_relation(relation_id: str) -> dict:
    rel = await repo.get_relation(relation_id)
    if rel is None:
        raise HTTPException(404, f"Relation {relation_id} not found")
    await repo.soft_delete_relation(relation_id)
    result = {"id": relation_id, "deleted": True}
    await broadcast_mutation(rel["study_id"], "relation_deleted", "relation", relation_id, result)
    return result


@router.get("/studies/{study_id}/relations")
async def list_relations(study_id: str, kind: str | None = None) -> list[dict]:
    if kind is not None and kind not in RELATION_KINDS:
        raise HTTPException(400, f"kind must be one of {RELATION_KINDS}")
    return await repo.list_relations_by_study(study_id, kind=kind)


# ─── Traceability ───

def _study_requirements(study_id: str) -> dict[str, dict]:
    from .requirements import _requirements
    return {
        r["id"]: r for r in _requirements.values()
        if r.get("study_id") == study_id and r.get("status") != "retired"
    }


def _element_ref(element_id: str) -> dict:
    from .elements import _elements
    el = _elements.get(element_id)
    return {
        "id": element_id,
        "name": el.get("name") if el else None,
        "element_type": el.get("element_type") if el else None,
        "subsystem_domain": el.get("subsystem_domain") if el else None,
    }


def _verification(req: dict) -> dict:
    return {
        "method": req.get("verification_method"),
        "phase": req.get("verification_phase"),
        "status": req.get("verification_status") or req.get("status"),
    }


def _req_summary(req: dict) -> dict:
    return {
        "id": req["id"], "code": req.get("code"), "text": req.get("text"),
        "level": req.get("level"), "status": req.get("status"),
        "parent_id": req.get("parent_id"), "element_id": req.get("element_id"),
        "verification": _verification(req),
    }


async def _linked_entities(req: dict, relations: list[dict], functions_by_id: dict[str, dict]) -> tuple[list, list]:
    """Elements / functions that satisfy or are allocated to ``req``.

    Relations are read in both directions (requirement→entity ``allocates``,
    entity→requirement ``satisfies``) plus ``RequirementRow.element_id``.
    """
    elements: dict[str, dict] = {}
    functions: dict[str, dict] = {}
    rid = req["id"]
    if req.get("element_id"):
        elements[req["element_id"]] = {**_element_ref(req["element_id"]), "relation": "element_id"}
    for rel in relations:
        if rel.get("kind") not in LINK_KINDS:
            continue
        if rel["source_kind"] == "requirement" and rel["source_id"] == rid:
            other_kind, other_id = rel["target_kind"], rel["target_id"]
        elif rel["target_kind"] == "requirement" and rel["target_id"] == rid:
            other_kind, other_id = rel["source_kind"], rel["source_id"]
        else:
            continue
        if other_kind == "element":
            elements.setdefault(other_id, {**_element_ref(other_id), "relation": rel["kind"]})
        elif other_kind == "function":
            fn = functions_by_id.get(other_id)
            if fn is None:
                fn = await function_repo.get_function(other_id) or {}
                functions_by_id[other_id] = fn
            functions.setdefault(other_id, {
                "id": other_id, "name": fn.get("name"), "layer": fn.get("layer"), "relation": rel["kind"],
            })
    return list(elements.values()), list(functions.values())


async def _build_req_node(req: dict, reqs: dict[str, dict], children_of: dict, relations: list[dict],
                          functions_by_id: dict, seen: set[str]) -> dict:
    seen.add(req["id"])
    elements, functions = await _linked_entities(req, relations, functions_by_id)
    node = {**_req_summary(req), "elements": elements, "functions": functions, "children": []}
    for cid in children_of.get(req["id"], []):
        if cid in seen:
            continue
        node["children"].append(await _build_req_node(reqs[cid], reqs, children_of, relations, functions_by_id, seen))
    return node


@router.get("/studies/{study_id}/traceability/tree")
async def get_traceability_tree(study_id: str) -> dict:
    """Objectives → requirements (by level, via parent chain) → linked
    elements/functions → verification."""
    from .studies import get_study_store

    study = get_study_store().get(study_id)
    reqs = _study_requirements(study_id)
    relations = await repo.list_relations_by_study(study_id)
    functions_by_id = await function_repo.load_all_functions(study_id)

    children_of: dict[str | None, list[str]] = {}
    for r in reqs.values():
        pid = r.get("parent_id")
        children_of.setdefault(pid if pid in reqs else None, []).append(r["id"])
    for lst in children_of.values():
        lst.sort(key=lambda i: (reqs[i].get("code") or "", i))
    roots = children_of.get(None, [])

    # Objective → requirement links: objective.traced_to_requirements and req.objective_id
    objectives: list[dict] = []
    mn = getattr(study, "mission_need", None) if study else None
    obj_list = [o.model_dump() for o in getattr(mn, "objectives", [])] if mn else []
    obj_reqs: dict[str, list[str]] = {o["id"]: list(o.get("traced_to_requirements") or []) for o in obj_list}
    for r in reqs.values():
        oid = r.get("objective_id")
        if oid and oid in obj_reqs and r["id"] not in obj_reqs[oid]:
            obj_reqs[oid].append(r["id"])
    # ``traces`` relations from requirement to an objective id are honoured too
    for rel in relations:
        if rel.get("kind") == "traces" and rel["source_kind"] == "requirement" and rel["target_id"] in obj_reqs:
            if rel["source_id"] not in obj_reqs[rel["target_id"]]:
                obj_reqs[rel["target_id"]].append(rel["source_id"])

    seen: set[str] = set()
    traced: set[str] = set()
    for o in obj_list:
        nodes = []
        for rid in obj_reqs.get(o["id"], []):
            if rid in reqs:
                traced.add(rid)
                nodes.append(await _build_req_node(reqs[rid], reqs, children_of, relations, functions_by_id, set()))
        objectives.append({
            "id": o["id"], "text": o.get("text"), "priority": o.get("priority"),
            "type": o.get("type"), "measurable_criterion": o.get("measurable_criterion"),
            "status": o.get("status"), "requirements": nodes,
        })

    unlinked = []
    for rid in roots:
        if rid in traced:
            continue
        unlinked.append(await _build_req_node(reqs[rid], reqs, children_of, relations, functions_by_id, seen))

    levels: dict[str, int] = {}
    for r in reqs.values():
        levels[r.get("level") or "unknown"] = levels.get(r.get("level") or "unknown", 0) + 1

    return {
        "study_id": study_id,
        "objectives": objectives,
        "unlinked_requirements": unlinked,
        "summary": {
            "objectives": len(obj_list),
            "requirements": len(reqs),
            "requirements_by_level": levels,
            "relations": len(relations),
            "requirements_traced_to_objectives": len(traced),
        },
    }


@router.get("/requirements/{requirement_id}/trace")
async def get_requirement_trace(requirement_id: str) -> dict:
    """Up (parents → objectives) and down (children → elements/functions → verification)."""
    from .requirements import _requirements
    from .studies import get_study_store

    req = _requirements.get(requirement_id)
    if not req:
        raise HTTPException(404, f"Requirement {requirement_id} not found")
    study_id = req.get("study_id") or ""
    reqs = _study_requirements(study_id)
    reqs.setdefault(requirement_id, req)
    relations = await repo.list_relations_by_study(study_id)
    functions_by_id = await function_repo.load_all_functions(study_id)

    # Up: parent chain
    up: list[dict] = []
    cur = req
    guard: set[str] = {requirement_id}
    while cur and cur.get("parent_id") and cur["parent_id"] not in guard:
        parent = reqs.get(cur["parent_id"]) or _requirements.get(cur["parent_id"])
        if not parent:
            break
        guard.add(parent["id"])
        up.append(_req_summary(parent))
        cur = parent
    derived_from = _requirements.get(req.get("derived_from_requirement_id") or "")

    # Objectives reached from the chain
    chain_ids = [requirement_id, *[p["id"] for p in up]]
    study = get_study_store().get(study_id)
    mn = getattr(study, "mission_need", None) if study else None
    objectives = []
    for o in (getattr(mn, "objectives", []) if mn else []):
        od = o.model_dump()
        linked = set(od.get("traced_to_requirements") or [])
        if any(cid in linked for cid in chain_ids) or any(
            (reqs.get(cid) or {}).get("objective_id") == od["id"] for cid in chain_ids
        ):
            objectives.append({"id": od["id"], "text": od.get("text"), "priority": od.get("priority")})

    # Down
    children_of: dict[str | None, list[str]] = {}
    for r in reqs.values():
        children_of.setdefault(r.get("parent_id"), []).append(r["id"])
    down = await _build_req_node(req, reqs, children_of, relations, functions_by_id, set())

    own_relations = [
        r for r in relations
        if (r["source_kind"] == "requirement" and r["source_id"] == requirement_id)
        or (r["target_kind"] == "requirement" and r["target_id"] == requirement_id)
    ]
    return {
        "requirement": _req_summary(req),
        "up": {"parents": up, "derived_from": _req_summary(derived_from) if derived_from else None,
               "objectives": objectives},
        "down": {"children": down["children"], "elements": down["elements"],
                 "functions": down["functions"], "verification": down["verification"]},
        "relations": own_relations,
    }
