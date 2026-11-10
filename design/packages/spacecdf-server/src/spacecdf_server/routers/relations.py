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
    POST   /studies/{id}/requirements/import      bulk import (YAML / JSON / CSV; W2.04)
    GET    /studies/{id}/requirements/coverage    objective coverage and orphans (W2.03)

Nov 2026 (W2.03): ``derives`` relations (requirement -> parent requirement) are further parents:
the tree shows a requirement under every parent, the trace walks all of them. ``traces``
relations to entity kind ``objective`` are further objectives.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
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

async def _study_requirements(study_id: str) -> dict[str, dict]:
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
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


def _extra_parents(relations: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for rel in relations:
        if rel.get("kind") == "derives" and rel.get("source_kind") == "requirement" \
                and rel.get("target_kind") == "requirement":
            out.setdefault(rel["source_id"], []).append(rel["target_id"])
    return out


def _parents_of(req: dict, extra: dict[str, list[str]]) -> list[str]:
    first = req.get("parent_id") or req.get("derived_from_requirement_id")
    return ([first] if first else []) + [p for p in extra.get(req["id"], []) if p != first]


def _req_summary(req: dict) -> dict:
    return {
        "id": req["id"], "code": req.get("code"), "text": req.get("text"),
        "level": req.get("level"), "status": req.get("status"),
        "parent_id": req.get("parent_id"), "element_id": req.get("element_id"),
        "objective_id": req.get("objective_id"), "category": req.get("category"),
        "priority": req.get("priority"), "responsible_position": req.get("responsible_position"),
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
                          functions_by_id: dict, seen: set[str], _path: frozenset = frozenset(),
                          _cache: dict | None = None) -> dict:
    """One requirement with its subtree. A requirement with several parents (W2.03) appears under
    each of them; ``_path`` only stops cycles. ``seen`` collects every id placed."""
    seen.add(req["id"])
    cache = _cache if _cache is not None else {}
    if req["id"] not in cache:
        cache[req["id"]] = await _linked_entities(req, relations, functions_by_id)
    elements, functions = cache[req["id"]]
    node = {**_req_summary(req), "elements": elements, "functions": functions, "children": []}
    path = _path | {req["id"]}
    for cid in children_of.get(req["id"], []):
        if cid in path or cid not in reqs:
            continue
        node["children"].append(await _build_req_node(reqs[cid], reqs, children_of, relations, functions_by_id,
                                                      seen, path, cache))
    return node


@router.get("/studies/{study_id}/traceability/tree")
async def get_traceability_tree(study_id: str) -> dict:
    """Objectives → requirements (by level, via parent chain) → linked
    elements/functions → verification."""
    from .studies import get_study_store

    study = get_study_store().get(study_id)
    reqs = await _study_requirements(study_id)
    relations = await repo.list_relations_by_study(study_id)
    functions_by_id = await function_repo.load_all_functions(study_id)

    children_of: dict[str | None, list[str]] = {}
    extra = _extra_parents(relations)
    for r in reqs.values():
        pids = [p for p in _parents_of(r, extra) if p in reqs]
        if not pids:
            children_of.setdefault(None, []).append(r["id"])
        for pid in pids:
            children_of.setdefault(pid, []).append(r["id"])
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
        if rel.get("kind") == "traces" and rel["source_kind"] == "requirement" and rel["target_id"] in obj_reqs \
                and rel.get("target_kind") in ("objective", "requirement"):
            if rel["source_id"] not in obj_reqs[rel["target_id"]]:
                obj_reqs[rel["target_id"]].append(rel["source_id"])

    seen: set[str] = set()
    traced: set[str] = set()
    placed: set[str] = set()
    cache: dict = {}
    for o in obj_list:
        nodes = []
        mine = {rid for rid in obj_reqs.get(o["id"], []) if rid in reqs}
        traced |= mine
        for rid in obj_reqs.get(o["id"], []):
            if rid not in reqs:
                continue
            # the top-most rows only: a row whose parent also traces this objective sits under it
            if any(p in mine for p in _parents_of(reqs[rid], extra)):
                continue
            nodes.append(await _build_req_node(reqs[rid], reqs, children_of, relations, functions_by_id, placed,
                                               _cache=cache))
        objectives.append({
            "id": o["id"], "text": o.get("text"), "priority": o.get("priority"),
            "type": o.get("type"), "measurable_criterion": o.get("measurable_criterion"),
            "status": o.get("status"), "requirements": nodes,
        })

    unlinked = []
    for rid in roots:
        if rid in traced:
            continue
        # rows already shown under an objective are not repeated here (stakeholder needs → objectives)
        unlinked.append(await _build_req_node(reqs[rid], reqs, children_of, relations, functions_by_id, seen,
                                              frozenset(placed), cache))

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
    from .requirements import _requirements, ensure_requirements_loaded
    from .studies import get_study_store

    await ensure_requirements_loaded()
    req = _requirements.get(requirement_id)
    if not req:
        raise HTTPException(404, f"Requirement {requirement_id} not found")
    study_id = req.get("study_id") or ""
    reqs = await _study_requirements(study_id)
    reqs.setdefault(requirement_id, req)
    relations = await repo.list_relations_by_study(study_id)
    functions_by_id = await function_repo.load_all_functions(study_id)

    # Up: every parent chain (``parent_id`` and ``derives`` relations), nearest first
    extra = _extra_parents(relations)
    up: list[dict] = []
    guard: set[str] = {requirement_id}
    frontier = [req]
    while frontier:
        nxt = []
        for cur in frontier:
            for pid in _parents_of(cur, extra):
                if pid in guard:
                    continue
                parent = reqs.get(pid) or _requirements.get(pid)
                if not parent:
                    continue
                guard.add(pid)
                up.append(_req_summary(parent))
                nxt.append(parent)
        frontier = nxt
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
        for pid in _parents_of(r, extra) or [None]:
            children_of.setdefault(pid, []).append(r["id"])
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


# ─── Bulk import and coverage (W2.03, W2.04) ───

class ImportBody(BaseModel):
    #: the document: a parsed YAML/JSON object (or list), or text in ``format``
    document: Any = None
    content: str | None = None
    format: str | None = None                  # yaml | json | csv (guessed when empty)
    dry_run: bool = False
    element_map: dict[str, str] | None = None  # file element name -> element id
    include_needs: bool = True
    include_objectives: bool = True
    study_id: str | None = None                # ignored (the path names the study); the seat guard reads it


@router.post("/studies/{study_id}/requirements/import")
async def import_requirements(study_id: str, body: ImportBody) -> dict:
    """Bulk import (W2.04). 422 with the error report when any row is invalid (nothing is
    written); ``dry_run`` answers 200 with the same report and the planned changes."""
    from ..services.requirement_import import ImportError_, import_requirements as run
    from .studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    doc = body.document if body.document is not None else body.content
    if doc is None:
        raise HTTPException(422, "send the requirements as 'document' (object) or 'content' (text)")
    try:
        report = await run(study_id, doc, fmt=body.format, dry_run=body.dry_run, element_map=body.element_map,
                           include_needs=body.include_needs, include_objectives=body.include_objectives)
    except ImportError_ as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:  # parse errors of YAML / JSON / CSV
        from ..db.requirement_repo import DuplicateCodeError, RequirementStoreError
        if isinstance(exc, DuplicateCodeError):
            raise HTTPException(409, str(exc))
        if isinstance(exc, RequirementStoreError):
            raise HTTPException(500, str(exc))
        if isinstance(exc, (ValueError, yaml_error())):
            raise HTTPException(422, f"cannot read the document: {exc}")
        raise
    if report["errors"] and not body.dry_run:
        raise HTTPException(422, report)
    return report


def yaml_error() -> type:
    import yaml
    return yaml.YAMLError


@router.get("/studies/{study_id}/requirements/coverage")
async def requirement_coverage(study_id: str) -> dict:
    """Per objective, the requirements that name it and those whose parent chain reaches it;
    orphans (below mission level, no parent) and requirements with several parents."""
    from ..services.requirement_import import coverage
    from .studies import get_study_store
    reqs = list((await _study_requirements(study_id)).values())
    relations = await repo.list_relations_by_study(study_id)
    extra = _extra_parents(relations)
    extra_obj: dict[str, list[str]] = {}
    for rel in relations:
        if rel.get("kind") == "traces" and rel.get("source_kind") == "requirement" \
                and rel.get("target_kind") == "objective":
            extra_obj.setdefault(rel["source_id"], []).append(rel["target_id"])
    study = get_study_store().get(study_id)
    mn = getattr(study, "mission_need", None) if study else None
    oids = [o.id for o in (getattr(mn, "objectives", None) or [])]
    for r in reqs:
        for o in [r.get("objective_id"), *extra_obj.get(r["id"], [])]:
            if o and o not in oids:
                oids.append(o)
    ids = {r["id"] for r in reqs}
    orphans = [r.get("code") for r in reqs
               if r.get("level") not in ("stakeholder", "mission", "interface")
               and not any(p in ids for p in _parents_of(r, extra))]
    multi = [r.get("code") for r in reqs if len([p for p in _parents_of(r, extra) if p in ids]) > 1]
    # wave 2: interface rows are not orphans (they trace to their interface), but the ones with
    # no parent requirement either are listed
    if_alone = [r.get("code") for r in reqs if r.get("level") == "interface"
                and not any(p in ids for p in _parents_of(r, extra))]
    return {"study_id": study_id, "requirements": len(reqs),
            "objectives": coverage(study_id, reqs, extra, extra_obj, oids),
            "orphans": sorted(c for c in orphans if c), "multi_parent": len(multi),
            "interface_without_parent": sorted(c for c in if_alone if c)}


@router.get("/studies/{study_id}/requirements/counts")
async def requirement_counts(study_id: str) -> dict:
    """Wave 2: live requirements by kind (stakeholder, objective, generated_interface, user), by
    level and by TS group, and the totals documents quote (docs/dev/REQUIREMENT_COUNTS.md)."""
    from ..services.requirement_queries import requirement_counts as counts
    return {"study_id": study_id, **(await counts(study_id))}


@router.get("/studies/{study_id}/requirements/ts-rows")
async def requirement_ts_rows(study_id: str, include_generated: bool = True) -> dict:
    """Wave 2 (for the TS, W4.06): the specification rows grouped by TS group, with unit,
    threshold, stage, parents, rationale and allocation."""
    from ..services.requirement_queries import TS_GROUP_LABELS, TS_GROUPS, ts_rows
    rows = await ts_rows(study_id, include_generated=include_generated)
    return {"study_id": study_id, "groups": [{"id": g, "label": TS_GROUP_LABELS[g],
                                              "count": sum(1 for r in rows if r["group"] == g)} for g in TS_GROUPS],
            "rows": rows}


@router.get("/studies/{study_id}/ird-dataset")
async def ird_dataset(study_id: str) -> dict:
    """Wave 2 (for the IRD/ICD, W4.07): interfaces, interface requirements, exchange items,
    power lines and bus nodes, from data."""
    from ..services.requirement_queries import ird_dataset as dataset
    return {"study_id": study_id, **(await dataset(study_id))}


# ─── Wave 3 (3.R1): function ↔ requirement coverage and the function picker ───

@router.get("/studies/{study_id}/requirements/function-coverage")
async def requirement_function_coverage(study_id: str) -> dict:
    """Leaves without a requirement, requirements without a function or process, and rows
    allocated where none of their functions is (warning). SRR-EC-12 and PRR-EC-03 read it."""
    from ..services.requirement_queries import function_coverage
    from .studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return await function_coverage(study_id)


@router.get("/studies/{study_id}/requirements/function-links")
async def requirement_function_links(study_id: str) -> dict:
    """Requirement id → the functions (and processes) that satisfy it, for the Requirements
    table's function column: ``{links: {req_id: [{id, code, name, kind}]}, functions: [...]}``."""
    from ..db import function_repo
    fns = {f["id"]: f for f in await function_repo.list_functions_by_study(study_id)}
    links: dict[str, list[dict]] = {}
    for rel in await repo.list_relations_by_study(study_id, kind="satisfies"):
        if rel.get("source_kind") == "function" and rel.get("target_kind") == "requirement":
            f, r = rel["source_id"], rel["target_id"]
        elif rel.get("source_kind") == "requirement" and rel.get("target_kind") == "function":
            f, r = rel["target_id"], rel["source_id"]
        else:
            continue
        fn = fns.get(f)
        if fn is None:
            continue
        lst = links.setdefault(r, [])
        if not any(x["id"] == f for x in lst):
            lst.append({"id": f, "code": fn.get("external_id"), "name": fn.get("name"),
                        "kind": "process" if fn.get("function_type") == "process" else "function"})
    for lst in links.values():
        lst.sort(key=lambda x: _code_key(x.get("code") or x.get("name") or ""))
    funcs = sorted(({"id": f["id"], "code": f.get("external_id"), "name": f.get("name"), "level": f.get("level"),
                     "kind": "process" if f.get("function_type") == "process" else "function",
                     "is_leaf": bool(f.get("is_leaf"))} for f in fns.values()),
                   key=lambda x: (x["kind"] == "process", _code_key(x.get("code") or x.get("name") or "")))
    return {"study_id": study_id, "links": links, "functions": funcs}


def _code_key(code: str) -> tuple:
    import re as _re
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in _re.split(r"[.\-]", str(code)))


class FunctionLinksBody(BaseModel):
    function_ids: list[str]


@router.put("/requirements/{requirement_id}/functions")
async def put_requirement_functions(requirement_id: str, body: FunctionLinksBody) -> dict:
    """The function picker: the functions (or processes) that satisfy this requirement become
    exactly ``function_ids``; the row's ``function_codes`` follows."""
    from ..db.requirement_repo import db_update_requirement
    from ..services.requirement_queries import set_requirement_functions
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    req = _requirements.get(requirement_id)
    if req is None or req.get("status") == "retired":
        raise HTTPException(404, f"Requirement {requirement_id} not found")
    try:
        res = await set_requirement_functions(req["study_id"], req, list(dict.fromkeys(body.function_ids)))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    req["function_codes"] = res["function_codes"] or None
    await db_update_requirement(requirement_id, req)
    from ._arcadia_events import broadcast_mutation
    await broadcast_mutation(req["study_id"], "requirement_updated", "requirement", requirement_id, req)
    return {"requirement_id": requirement_id, **res}


# ─── Wave 3 (3.R2): threshold ↔ computed value binding ───

@router.get("/studies/{study_id}/requirements/bindings")
async def requirement_bindings(study_id: str) -> dict:
    """The "checked against" column: per row with a numeric threshold, its binding, the proposal
    (from ``budget_ref``, unit and keywords) and the compliance verdict; the catalogue of figures
    a threshold can be bound to, with their current value."""
    from ..services.threshold_binding import binding_rows
    from .studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return await binding_rows(study_id)


class AcceptBindingsBody(BaseModel):
    requirement_ids: list[str] | None = None     # None: every proposed row


@router.post("/studies/{study_id}/requirements/bindings/accept")
async def accept_requirement_bindings(study_id: str, body: AcceptBindingsBody, request: Request) -> dict:
    from ..services.threshold_binding import accept
    from .studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return await accept(study_id, body.requirement_ids, by=await _person(request, study_id))


class BindingBody(BaseModel):
    path: str | None = None                      # None clears the binding


@router.put("/requirements/{requirement_id}/binding")
async def put_requirement_binding(requirement_id: str, body: BindingBody, request: Request) -> dict:
    """Bind a row by hand to a catalogue figure (or an ``el:`` element parameter), or clear it."""
    from ..services.threshold_binding import CATALOGUE, bind
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    req = _requirements.get(requirement_id)
    if req is None or req.get("status") == "retired":
        raise HTTPException(404, f"Requirement {requirement_id} not found")
    path = (body.path or "").strip() or None
    if path and path not in CATALOGUE and not path.startswith("el:") and "." not in path:
        raise HTTPException(422, f"unknown figure {path!r}")
    await bind(req, path, source="manual", by=await _person(request, req["study_id"]))
    from ._arcadia_events import broadcast_mutation
    await broadcast_mutation(req["study_id"], "requirement_updated", "requirement", requirement_id, req)
    return req


async def _person(request: Request, study_id: str) -> str:
    try:
        from ..seats.service import seat_ctx
        ctx = await seat_ctx(request, study_id)
        return ctx.person.name if ctx and ctx.person else ""
    except Exception:  # noqa: BLE001 — no seats: anonymous
        return ""


# ─── Wave 3 (3.R3): allocation requirements in step with the ledger (AR-01) ───

@router.get("/studies/{study_id}/requirements/allocation-sync")
async def allocation_sync_status(study_id: str) -> dict:
    """Per allocation-ledger line, the requirement that covers it and its state (covered,
    uncovered, stale, nil), and the rows whose line was deleted."""
    from ..services.allocation_requirements import status
    from .studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return await status(study_id)


@router.post("/studies/{study_id}/requirements/allocation-sync")
async def allocation_sync_run(study_id: str) -> dict:
    """Apply AR-01: propose ``AR-*`` rows for uncovered lines, mark covering rows stale or
    retired (A's ledger routes call the same service after each change)."""
    from ..services.allocation_requirements import sync
    from .studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return await sync(study_id)


class AllocationFlagBody(BaseModel):
    action: str                                   # accept | dismiss


@router.post("/requirements/{requirement_id}/allocation-sync")
async def allocation_flag_resolve(requirement_id: str, body: AllocationFlagBody) -> dict:
    from ..services.allocation_requirements import resolve
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    req = _requirements.get(requirement_id)
    if req is None:
        raise HTTPException(404, f"Requirement {requirement_id} not found")
    try:
        req = await resolve(req, body.action)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    from ._arcadia_events import broadcast_mutation
    await broadcast_mutation(req["study_id"], "requirement_updated", "requirement", requirement_id, req)
    return req


# ─── Wave 3 (3.R4): the evidence the wave-3 gate criteria read ───

@router.get("/studies/{study_id}/gate-evidence")
async def gate_evidence(study_id: str) -> dict:
    """Collect (and keep for the gate evaluation) the wave-3 evidence of the study: function
    coverage, threshold-binding values, ICD issue control, allocation ledger and its covering
    requirements, SE deliverables, validation coverage, logbook decisions. Returns a summary."""
    from ..services.gate_evaluator import collect_evidence
    from .studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    ev = await collect_evidence(study_id)
    cov = ev.get("function_coverage") or {}
    return {"study_id": study_id,
            "function_coverage": {k: cov.get(k) for k in ("functions", "leaves", "leaves_allocated", "requirements",
                                                         "requirements_with_function")} if cov else None,
            "binding_values": len(ev.get("binding_values") or {}),
            "icds": (ev.get("icds") or {}).get("counts"),
            "ledger_lines": len(ev.get("ledger") or []) if ev.get("ledger") is not None else None,
            "allocation_requirements": (ev.get("allocation_requirements") or {}).get("counts"),
            "panel_decisions": ev.get("panel_decisions"),
            "se_deliverables": ev.get("se_deliverables") is not None,
            "validation": ev.get("validation") is not None}
