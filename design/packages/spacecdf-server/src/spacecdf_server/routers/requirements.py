"""Requirements API — tree, derive, patch, soft-delete (SCDF-112), plus the Nov 2026 baseline
fields (W2.01-W2.04).

Per SPINE_SPEC §6.3. Provides CRUD for the requirement hierarchy.
Requirements are linked to elements via `element_id` FK.

Persistence (SCDF-160 N0): write-through cache, same pattern as
``routers/elements.py``. ``_requirements`` is the primary read path and is
kept importable for consumers (relations, exporters, compliance); every
mutation is mirrored to the ``requirements`` table via ``db/requirement_repo``
and the cache is hydrated from the DB at start-up (``init_requirement_cache``
from the app lifespan) or lazily on first access in this process.

Nov 2026 (W2):

* **Levels** ``stakeholder``, ``mission``, ``segment``, ``system``, ``subsystem``, ``interface``;
  POST and PATCH answer 422 on any other level, operator, method, stage or priority.
* **Fields** ``priority``, ``category``, ``source_ref``, ``threshold_unit``, ``verification_level``,
  ``verification_methods`` (list; the first is ``verification_method``), ``open_item``. The stage
  is ``verification_phase`` (``verification_stage`` is accepted as its alias) and includes ``IOV``.
  Method ``D`` is stored as ``T`` (ECSS-E-ST-10-02C).
* **Codes** are unique among the live requirements of a study: a duplicate answers 409.
* **Several parents and objectives.** ``parent_id`` is the first parent; further parents are
  ``derives`` relations (source = this requirement, target = the parent). ``objective_id`` is the
  first objective; further objectives are ``traces`` relations to entity kind ``objective``. Every
  requirement served carries ``parent_ids`` and ``objective_ids`` (all of them, first first), and
  PATCH accepts both lists.
* Mutations are broadcast on the study socket (``requirement_created`` / ``_updated`` /
  ``_deleted`` / ``requirements_imported``), so the panel no longer polls.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from spacecdf_common.models.requirement import (
    LEVELS, PRIORITIES, THRESHOLD_OPS, VERIFICATION_LEVELS, VERIFICATION_METHODS, VERIFICATION_STAGES,
    normalise_method,
)

from ..db.requirement_repo import (
    DuplicateCodeError,
    RequirementStoreError,
    db_create_requirement,
    db_soft_delete_requirement,
    db_update_requirement,
    load_all_requirements,
    normalise_threshold_value,
)

logger = logging.getLogger(__name__)

router = APIRouter()

STATUSES = ("draft", "approved", "violated", "verified", "retired")

#: Fields a PATCH may change (``parent_ids`` / ``objective_ids`` are handled apart).
PATCH_FIELDS = ("text", "rationale", "req_type", "threshold_param_path", "threshold_op",
                "threshold_value", "threshold_unit", "verification_method", "verification_methods",
                "verification_phase", "verification_level", "responsible_position", "status", "code",
                "element_id", "parent_id", "derived_from_requirement_id", "objective_id", "external_id",
                "level", "priority", "category", "source_ref", "open_item", "ir_json")


# ─── In-memory store (write-through cache — DB is source of truth) ───
_requirements: dict[str, dict] = {}
_cache_loaded: bool = False

# Study index: study id -> requirement ids. A requirement never changes study and is never
# removed from ``_requirements`` (delete = retire), so the index stays valid while the store
# size is unchanged; other modules that add rows straight into the dict change the size.
_index: dict[str, list[str]] = {}
_index_size: int = -1


def study_ids(study_id: str) -> list[str]:
    """Ids of every requirement of ``study_id`` (retired included), from the study index."""
    global _index, _index_size
    if _index_size != len(_requirements):
        idx: dict[str, list[str]] = {}
        for rid, r in _requirements.items():
            idx.setdefault(r.get("study_id") or "", []).append(rid)
        _index, _index_size = idx, len(_requirements)
    return _index.get(study_id, [])


def study_requirements(study_id: str, live: bool = True) -> list[dict]:
    out = [_requirements[i] for i in study_ids(study_id) if i in _requirements]
    return [r for r in out if r.get("status") != "retired"] if live else out


async def init_requirement_cache() -> None:
    """Hydrate ``_requirements`` from the DB (idempotent; called from lifespan).

    In-memory entries win over DB rows (they are the freshest write-through
    state); rows only fill ids the process has not seen yet.
    """
    global _cache_loaded
    loaded = await load_all_requirements()
    for req_id, req in loaded.items():
        _requirements.setdefault(req_id, req)
    _cache_loaded = True
    logger.info("Requirement cache initialized: %d requirements", len(_requirements))


def reset_requirement_cache() -> None:
    """Drop the cache and force re-hydration on next access (tests: simulate restart)."""
    global _cache_loaded, _index_size
    _requirements.clear()
    _cache_loaded = False
    _index_size = -1


async def ensure_requirements_loaded() -> None:
    """Lazy hydration for processes whose lifespan did not run (tests, TestClient).

    Consumers that read ``_requirements`` directly from an async context
    (relations/traceability, exporters) should await this first.
    """
    if not _cache_loaded:
        await init_requirement_cache()


_ensure_loaded = ensure_requirements_loaded


# ─── Validation and normalisation ───

def normalise_fields(body: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise the requirement fields present in ``body`` (in place; returns it).

    Raises ``HTTPException(422)`` on an unknown level, status, operator, method, stage,
    verification level or priority."""
    def bad(field: str, value: Any, allowed: Any) -> HTTPException:
        return HTTPException(422, f"{field} {value!r} is not one of {list(allowed)}")

    if "verification_stage" in body:                      # alias of verification_phase
        body.setdefault("verification_phase", body.pop("verification_stage"))
    if "level" in body:
        if body["level"] not in LEVELS:
            raise bad("level", body["level"], LEVELS)
    if body.get("status") is not None and body["status"] not in STATUSES:
        raise bad("status", body["status"], STATUSES)
    if body.get("threshold_op") not in (None, ""):
        if body["threshold_op"] not in THRESHOLD_OPS:
            raise bad("threshold_op", body["threshold_op"], THRESHOLD_OPS)
    elif "threshold_op" in body:
        body["threshold_op"] = None
    if "verification_methods" in body:
        ms = body["verification_methods"]
        if isinstance(ms, str):
            ms = [m for m in ms.replace(";", ",").split(",")]
        ms = [normalise_method(m) for m in (ms or [])]
        ms = [m for i, m in enumerate(ms) if m and m not in ms[:i]]
        for m in ms:
            if m not in VERIFICATION_METHODS:
                raise bad("verification method", m, VERIFICATION_METHODS)
        body["verification_methods"] = ms or None
        if ms and "verification_method" not in body:
            body["verification_method"] = ms[0]
    if "verification_method" in body:
        m = normalise_method(body["verification_method"])
        if m is not None and m not in VERIFICATION_METHODS:
            raise bad("verification_method", body["verification_method"], VERIFICATION_METHODS)
        body["verification_method"] = m
    if "verification_phase" in body:
        # the known stages are VERIFICATION_STAGES (IOV = in-orbit); a project's own short stage
        # name (AIT, FRR …) is kept, upper-cased, within the 8-character column
        st = (str(body["verification_phase"]).strip().upper() or None) if body["verification_phase"] else None
        if st is not None and (len(st) > 8 or not st.replace("-", "").isalnum()):
            raise bad("verification stage", body["verification_phase"], VERIFICATION_STAGES)
        body["verification_phase"] = st
    if body.get("verification_level") not in (None, ""):
        if body["verification_level"] not in VERIFICATION_LEVELS:
            raise bad("verification_level", body["verification_level"], VERIFICATION_LEVELS)
    elif "verification_level" in body:
        body["verification_level"] = None
    if "priority" in body and body["priority"] not in (None, ""):
        try:
            p = int(body["priority"])
        except (TypeError, ValueError):
            raise bad("priority", body["priority"], PRIORITIES)
        if p not in PRIORITIES:
            raise bad("priority", body["priority"], PRIORITIES)
        body["priority"] = p
    elif "priority" in body:
        body["priority"] = None
    if "threshold_value" in body:
        body["threshold_value"] = normalise_threshold_value(body["threshold_value"])
    if "code" in body and body["code"] is not None:
        body["code"] = str(body["code"]).strip()
        if not body["code"] or len(body["code"]) > 32:
            raise HTTPException(422, "code must be 1 to 32 characters")
    return body


def _keep_methods_in_step(req: dict) -> None:
    """``verification_method`` is the first of ``verification_methods``."""
    ms = list(req.get("verification_methods") or [])
    m = req.get("verification_method")
    if m and (not ms or ms[0] != m):
        ms = [m] + [x for x in ms if x != m]
        req["verification_methods"] = ms
    elif not m and ms:
        req["verification_methods"] = None


def code_taken(study_id: str, code: str, except_id: str | None = None) -> dict | None:
    for r in study_requirements(study_id):
        if r.get("code") == code and r["id"] != except_id:
            return r
    return None


# ─── Several parents and objectives (relations) ───

async def _relation_maps(study_id: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """(extra parents, extra objectives) per requirement id, from ``derives`` / ``traces``."""
    from ..db.relation_repo import list_relations_by_study
    parents: dict[str, list[str]] = {}
    objectives: dict[str, list[str]] = {}
    try:
        rels = await list_relations_by_study(study_id)
    except Exception:
        logger.exception("relations unavailable for study %s", study_id)
        return parents, objectives
    for rel in sorted(rels, key=lambda r: (str(r.get("created_at") or ""), r.get("id") or "")):
        if rel.get("source_kind") != "requirement":
            continue
        if rel.get("kind") == "derives" and rel.get("target_kind") == "requirement":
            parents.setdefault(rel["source_id"], []).append(rel["target_id"])
        elif rel.get("kind") == "traces" and rel.get("target_kind") == "objective":
            objectives.setdefault(rel["source_id"], []).append(rel["target_id"])
    return parents, objectives


def _with_lists(req: dict, parents: dict[str, list[str]], objectives: dict[str, list[str]]) -> dict:
    first = req.get("parent_id") or req.get("derived_from_requirement_id")
    pids = ([first] if first else []) + [p for p in parents.get(req["id"], []) if p != first]
    oid = req.get("objective_id")
    oids = ([oid] if oid else []) + [o for o in objectives.get(req["id"], []) if o != oid]
    return {**req, "parent_ids": pids, "objective_ids": oids}


async def with_lists(study_id: str, reqs: list[dict]) -> list[dict]:
    parents, objectives = await _relation_maps(study_id)
    return [_with_lists(r, parents, objectives) for r in reqs]


def all_parent_ids(req: dict, extra: dict[str, list[str]]) -> list[str]:
    first = req.get("parent_id") or req.get("derived_from_requirement_id")
    return ([first] if first else []) + [p for p in extra.get(req["id"], []) if p != first]


async def set_extra_links(study_id: str, req_id: str, kind: str, target_kind: str,
                          wanted: list[str]) -> tuple[int, int]:
    """Make the ``kind`` relations from ``req_id`` to ``target_kind`` exactly ``wanted``.
    Returns (created, removed)."""
    from ..db.relation_repo import create_relation, list_relations_for, soft_delete_relation
    have = [r for r in await list_relations_for("requirement", req_id, kind=kind, direction="out")
            if r.get("target_kind") == target_kind]
    have_ids = {r["target_id"]: r for r in have}
    created = removed = 0
    for t in wanted:
        if t not in have_ids:
            await create_relation({"study_id": study_id, "kind": kind, "source_kind": "requirement",
                                   "source_id": req_id, "target_kind": target_kind, "target_id": t})
            created += 1
    for t, r in have_ids.items():
        if t not in wanted:
            await soft_delete_relation(r["id"])
            removed += 1
    return created, removed


async def _broadcast(study_id: str | None, event: str, req_id: str, payload: Any = None) -> None:
    from ._arcadia_events import broadcast_mutation
    await broadcast_mutation(study_id, event, "requirement", req_id, payload)


# ─── Routes ───

@router.get("/tree")
async def get_tree(study_id: str, element_id: str | None = None) -> list[dict]:
    """Return the live requirements of a study (optionally of one element), each with
    ``parent_ids`` and ``objective_ids``."""
    await _ensure_loaded()
    results = [r for r in study_requirements(study_id)
               if element_id is None or r.get("element_id") == element_id]
    return await with_lists(study_id, results)


@router.get("/verify")
async def verify_requirements(study_id: str) -> dict:
    """Verify all requirements for a study: SMART check, orphan detection, threshold violations."""
    from ..services.requirement_engine import validate_smart

    await _ensure_loaded()
    reqs = study_requirements(study_id)
    extra, _ = await _relation_maps(study_id)
    live = {r["id"] for r in reqs}

    issues = []
    orphans = 0
    smart_pass = 0
    smart_fail = 0

    for req in reqs:
        req_issues: list[str] = []
        req_codes: list[str] = []
        # Anything below mission level, other than an interface requirement, needs a parent;
        # a ``derives`` relation counts as a parent (W2.03).
        has_parent = any(p in live for p in all_parent_ids(req, extra))
        if req.get("level") not in ("stakeholder", "mission", "interface") and not has_parent:
            orphans += 1
            req_issues.append("Not derived from a parent requirement (orphan)")
            req_codes.append("orphan")
        try:
            check = validate_smart({**req, "has_parent": has_parent or bool(req.get("parent_id"))})
            if check.is_smart:
                smart_pass += 1
            else:
                smart_fail += 1
                req_issues.extend(check.issues)
                req_codes.extend(check.codes)
        except Exception:
            logger.debug("SMART check failed for %s", req.get("id"), exc_info=True)
        if req_issues:
            issues.append({"requirement_id": req["id"], "code": req.get("code", ""), "text": req.get("text", ""),
                           "issues": req_issues, "codes": req_codes})

    return {"study_id": study_id, "total": len(reqs), "smart_pass": smart_pass, "smart_fail": smart_fail,
            "orphans": orphans, "issues": issues}


@router.patch("/bulk")
async def bulk_update(body: dict[str, Any]) -> dict:
    """Bulk edit (W2.08): ``{"study_id", "ids": [...], "changes": {field: value}}``.

    The same changes go to every listed requirement; ``code`` cannot be bulk-edited."""
    await _ensure_loaded()
    sid = body.get("study_id")
    ids = list(body.get("ids") or [])
    changes = dict(body.get("changes") or {})
    if not sid or not ids or not changes:
        raise HTTPException(422, "study_id, ids and changes are required")
    if "code" in changes:
        raise HTTPException(422, "code cannot be changed in bulk")
    unknown = [k for k in changes if k not in PATCH_FIELDS]
    if unknown:
        raise HTTPException(422, f"unknown field(s): {unknown}")
    normalise_fields(changes)
    out = []
    for rid in ids:
        r = _requirements.get(rid)
        if not r or r.get("study_id") != sid:
            raise HTTPException(404, f"Requirement {rid} not found in study {sid}")
    for rid in ids:
        out.append(await update_requirement(rid, dict(changes), broadcast=False))
    await _broadcast(sid, "requirement_updated", ids[0], {"ids": ids, "fields": sorted(changes)})
    return {"updated": len(out), "ids": ids}


@router.get("/{req_id}")
async def get_requirement(req_id: str) -> dict:
    """Get a single requirement."""
    await _ensure_loaded()
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")
    return (await with_lists(req.get("study_id") or "", [req]))[0]


@router.post("/")
async def create_requirement(body: dict[str, Any]) -> dict:
    """Create a new requirement (409 when the study already has a live requirement with the code)."""
    await _ensure_loaded()
    body = normalise_fields(dict(body))
    sid = body.get("study_id", "")
    req_id = body.get("id") or f"REQ-{uuid4().hex[:8]}"
    if req_id in _requirements:
        raise HTTPException(409, f"Requirement id {req_id} already exists")
    level = body.get("level", "system")
    parent_ids = [p for p in (body.get("parent_ids") or []) if p]
    parent_id = body.get("parent_id") or (parent_ids[0] if parent_ids else None)
    objective_ids = [o for o in (body.get("objective_ids") or []) if o]
    objective_id = body.get("objective_id") or (objective_ids[0] if objective_ids else None)

    # Validate parent reference if provided (derivation is optional, not mandatory)
    for p in [parent_id, *parent_ids]:
        if p and p not in _requirements:
            raise HTTPException(400, f"Parent requirement {p} not found")
    code = body.get("code") or req_id
    if sid and code_taken(sid, code):
        raise HTTPException(409, f"Code {code} is already used in this study")

    req = {
        "id": req_id,
        "study_id": sid,
        "parent_id": parent_id,
        "element_id": body.get("element_id"),
        "level": level,
        "code": code,
        "text": body.get("text", ""),
        "rationale": body.get("rationale"),
        "req_type": body.get("req_type"),
        "threshold_param_path": body.get("threshold_param_path"),
        "threshold_op": body.get("threshold_op"),
        "threshold_value": body.get("threshold_value"),
        "threshold_unit": body.get("threshold_unit"),
        "verification_method": body.get("verification_method"),
        "verification_methods": body.get("verification_methods"),
        "verification_phase": body.get("verification_phase"),
        "verification_level": body.get("verification_level"),
        "responsible_position": body.get("responsible_position"),
        "status": body.get("status", "draft"),
        "derived_from_requirement_id": body.get("derived_from_requirement_id"),
        # Objective trace (SCDF-160 traceability tree reads this; was silently dropped)
        "objective_id": objective_id,
        # Identity in external tools (ReqIF / Capella) — persisted in RequirementRow.external_id
        "external_id": body.get("external_id"),
        # Interface requirement data (level "interface"): endpoints/type for IF-02, template info
        "ir_json": body.get("ir_json"),
        "priority": body.get("priority"),
        "category": body.get("category"),
        "source_ref": body.get("source_ref"),
        "open_item": body.get("open_item"),
    }
    from ..db.requirement_repo import REQ_TYPES
    if not req["req_type"] and req["rationale"] in REQ_TYPES:   # older clients sent the type here
        req["req_type"], req["rationale"] = req["rationale"], None
    _keep_methods_in_step(req)
    try:
        await db_create_requirement(req)
    except DuplicateCodeError as exc:
        raise HTTPException(409, str(exc))
    except RequirementStoreError as exc:
        raise HTTPException(500, str(exc))
    _requirements[req_id] = req
    if sid and len(parent_ids) > 1:
        await set_extra_links(sid, req_id, "derives", "requirement", [p for p in parent_ids if p != parent_id])
    if sid and len(objective_ids) > 1:
        await set_extra_links(sid, req_id, "traces", "objective", [o for o in objective_ids if o != objective_id])
    if level == "interface":
        # IF-02: an interface requirement without an interface proposes it
        from ..services.interface_requirements import on_requirement_created
        await on_requirement_created(req)
    await _broadcast(sid, "requirement_created", req_id)
    return (await with_lists(sid, [req]))[0] if sid else req


@router.post("/{req_id}/derive")
async def derive_requirement(req_id: str, body: dict[str, Any]) -> dict:
    """Create a child requirement derived from parent."""
    await _ensure_loaded()
    parent = _requirements.get(req_id)
    if not parent:
        raise HTTPException(404, f"Parent requirement {req_id} not found")

    # Determine child level
    # a mission requirement flows down to the system by default (send "level": "segment" for a
    # segment requirement); a stakeholder need to a mission requirement
    level_map = {"stakeholder": "mission", "mission": "system", "segment": "system", "system": "subsystem"}
    child_level = level_map.get(parent["level"])
    if not child_level:
        raise HTTPException(400, f"Cannot derive from {parent['level']} level")

    body["parent_id"] = req_id
    body["level"] = body.get("level", child_level)
    body["study_id"] = parent["study_id"]
    body.setdefault("derived_from_requirement_id", req_id)
    return await create_requirement(body)


@router.patch("/{req_id}")
async def update_requirement(req_id: str, body: dict[str, Any], broadcast: bool = True) -> dict:
    """Update a requirement's fields. ``parent_ids`` / ``objective_ids`` replace every parent /
    objective (the first is stored in ``parent_id`` / ``objective_id``, the rest as relations)."""
    await _ensure_loaded()
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")
    body = normalise_fields(dict(body))
    sid = req.get("study_id") or ""
    if body.get("code") and body["code"] != req.get("code") and code_taken(sid, body["code"], req_id):
        raise HTTPException(409, f"Code {body['code']} is already used in this study")
    parent_ids = body.pop("parent_ids", None)
    objective_ids = body.pop("objective_ids", None)
    iface_id = body.pop("interface_id", None) if "interface_id" in body else ...
    xitem_ids = body.pop("exchange_item_ids", None)
    if iface_id is not ... or xitem_ids is not None:
        # W2.07: the IR form picks the interface and the ICD row (exchange item)
        ir = dict(body.get("ir_json") or req.get("ir_json") or {})
        if iface_id is not ...:
            ir["interface_id"] = iface_id
            ir["interface_ids"] = [iface_id] if iface_id else []
            ir.setdefault("origin", "user")
        if xitem_ids is not None:
            ir["exchange_item_ids"] = [x for x in xitem_ids if x]
        body["ir_json"] = ir
    if parent_ids is not None:
        parent_ids = [p for p in parent_ids if p]
        for p in parent_ids:
            if p not in _requirements or p == req_id:
                raise HTTPException(400, f"Parent requirement {p} not found")
        body["parent_id"] = parent_ids[0] if parent_ids else None
        body["derived_from_requirement_id"] = body["parent_id"]
    if objective_ids is not None:
        objective_ids = [o for o in objective_ids if o]
        body["objective_id"] = objective_ids[0] if objective_ids else None

    if req.get("level") == "interface":
        from ..services.interface_requirements import on_requirement_patched
        on_requirement_patched(req, body)
    before = dict(req)
    for key in PATCH_FIELDS:
        if key in body:
            req[key] = body[key]
    if "verification_method" in body or "verification_methods" in body:
        _keep_methods_in_step(req)

    try:
        await db_update_requirement(req_id, req)
    except DuplicateCodeError as exc:
        req.clear()
        req.update(before)
        raise HTTPException(409, str(exc))
    except RequirementStoreError as exc:
        req.clear()
        req.update(before)
        raise HTTPException(500, str(exc))
    if sid and parent_ids is not None:
        await set_extra_links(sid, req_id, "derives", "requirement", parent_ids[1:])
    if sid and objective_ids is not None:
        await set_extra_links(sid, req_id, "traces", "objective", objective_ids[1:])
    if sid and iface_id is not ...:
        await set_extra_links(sid, req_id, "allocates", "interface", [iface_id] if iface_id else [])
    if sid and xitem_ids is not None:
        await set_extra_links(sid, req_id, "allocates", "exchange_item", (req.get("ir_json") or {}).get("exchange_item_ids") or [])
    if broadcast:
        await _broadcast(sid, "requirement_updated", req_id)
    return (await with_lists(sid, [req]))[0] if sid else req


@router.delete("/{req_id}")
async def delete_requirement(req_id: str) -> dict:
    """Soft-delete a requirement (set status=retired)."""
    await _ensure_loaded()
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")

    req["status"] = "retired"
    await db_soft_delete_requirement(req_id)
    await _broadcast(req.get("study_id"), "requirement_deleted", req_id)
    return {"id": req_id, "status": "retired"}
