"""Requirements API — tree, derive, patch, soft-delete (SCDF-112).

Per SPINE_SPEC §6.3. Provides CRUD for the requirement hierarchy.
Requirements are linked to elements via `element_id` FK.

Persistence (SCDF-160 N0): write-through cache, same pattern as
``routers/elements.py``. ``_requirements`` is the primary read path and is
kept importable for consumers (relations, exporters, compliance); every
mutation is mirrored to the ``requirements`` table via ``db/requirement_repo``
and the cache is hydrated from the DB at start-up (``init_requirement_cache``
from the app lifespan) or lazily on first access in this process.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..db.requirement_repo import (
    db_create_requirement,
    db_soft_delete_requirement,
    db_update_requirement,
    load_all_requirements,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── In-memory store (write-through cache — DB is source of truth) ───
_requirements: dict[str, dict] = {}
_cache_loaded: bool = False


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
    global _cache_loaded
    _requirements.clear()
    _cache_loaded = False


async def ensure_requirements_loaded() -> None:
    """Lazy hydration for processes whose lifespan did not run (tests, TestClient).

    Consumers that read ``_requirements`` directly from an async context
    (relations/traceability, exporters) should await this first.
    """
    if not _cache_loaded:
        await init_requirement_cache()


_ensure_loaded = ensure_requirements_loaded


@router.get("/tree")
async def get_tree(study_id: str, element_id: str | None = None) -> list[dict]:
    """Return requirement tree for a study, optionally filtered by element_id."""
    await _ensure_loaded()
    results = []
    for r in _requirements.values():
        if r.get("study_id") != study_id:
            continue
        if r.get("status") == "retired":
            continue
        if element_id is not None and r.get("element_id") != element_id:
            continue
        results.append(r)
    return results


@router.get("/verify")
async def verify_requirements(study_id: str) -> dict:
    """Verify all requirements for a study: SMART check, orphan detection, threshold violations."""
    from ..services.requirement_engine import validate_smart

    await _ensure_loaded()
    reqs = [r for r in _requirements.values() if r.get("study_id") == study_id and r.get("status") != "retired"]

    issues = []
    orphans = 0
    smart_pass = 0
    smart_fail = 0

    for req in reqs:
        req_issues: list[str] = []
        if req.get("level") in ("system", "subsystem") and not req.get("derived_from_requirement_id") and not req.get("parent_id"):
            orphans += 1
            req_issues.append("Not derived from a parent requirement (orphan)")
        try:
            check = validate_smart(req)
            if check.is_smart:
                smart_pass += 1
            else:
                smart_fail += 1
                req_issues.extend(check.issues)
        except Exception:
            pass
        if req_issues:
            issues.append({"requirement_id": req["id"], "code": req.get("code", ""), "text": req.get("text", ""), "issues": req_issues})

    return {"study_id": study_id, "total": len(reqs), "smart_pass": smart_pass, "smart_fail": smart_fail, "orphans": orphans, "issues": issues}


@router.get("/{req_id}")
async def get_requirement(req_id: str) -> dict:
    """Get a single requirement."""
    await _ensure_loaded()
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")
    return req


@router.post("/")
async def create_requirement(body: dict[str, Any]) -> dict:
    """Create a new requirement."""
    await _ensure_loaded()
    req_id = body.get("id") or f"REQ-{uuid4().hex[:8]}"
    level = body.get("level", "system")
    parent_id = body.get("parent_id")

    # Validate parent reference if provided (derivation is optional, not mandatory)
    if parent_id and parent_id not in _requirements:
        raise HTTPException(400, f"Parent requirement {parent_id} not found")

    req = {
        "id": req_id,
        "study_id": body.get("study_id", ""),
        "parent_id": parent_id,
        "element_id": body.get("element_id"),
        "level": level,
        "code": body.get("code", req_id),
        "text": body.get("text", ""),
        "rationale": body.get("rationale"),
        "threshold_param_path": body.get("threshold_param_path"),
        "threshold_op": body.get("threshold_op"),
        "threshold_value": body.get("threshold_value"),
        "verification_method": body.get("verification_method"),
        "verification_phase": body.get("verification_phase"),
        "responsible_position": body.get("responsible_position"),
        "status": body.get("status", "draft"),
        "derived_from_requirement_id": body.get("derived_from_requirement_id"),
        # Objective trace (SCDF-160 traceability tree reads this; was silently dropped)
        "objective_id": body.get("objective_id"),
        # Identity in external tools (ReqIF / Capella) — persisted in RequirementRow.external_id
        "external_id": body.get("external_id"),
        # Interface requirement data (level "interface"): endpoints/type for IF-02, template info
        "ir_json": body.get("ir_json"),
    }
    _requirements[req_id] = req
    await db_create_requirement(req)
    if level == "interface":
        # IF-02: an interface requirement without an interface proposes it
        from ..services.interface_requirements import on_requirement_created
        await on_requirement_created(req)
    return req


@router.post("/{req_id}/derive")
async def derive_requirement(req_id: str, body: dict[str, Any]) -> dict:
    """Create a child requirement derived from parent."""
    await _ensure_loaded()
    parent = _requirements.get(req_id)
    if not parent:
        raise HTTPException(404, f"Parent requirement {req_id} not found")

    # Determine child level
    level_map = {"mission": "system", "system": "subsystem"}
    child_level = level_map.get(parent["level"])
    if not child_level:
        raise HTTPException(400, f"Cannot derive from {parent['level']} level")

    body["parent_id"] = req_id
    body["level"] = body.get("level", child_level)
    body["study_id"] = parent["study_id"]
    body.setdefault("derived_from_requirement_id", req_id)
    return await create_requirement(body)


@router.patch("/{req_id}")
async def update_requirement(req_id: str, body: dict[str, Any]) -> dict:
    """Update a requirement's fields."""
    await _ensure_loaded()
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")

    if req.get("level") == "interface":
        from ..services.interface_requirements import on_requirement_patched
        on_requirement_patched(req, body)
    for key in ("text", "rationale", "threshold_param_path", "threshold_op",
                "threshold_value", "verification_method", "verification_phase",
                "responsible_position", "status", "code", "element_id",
                "parent_id", "derived_from_requirement_id", "objective_id", "external_id"):
        if key in body:
            req[key] = body[key]

    await db_update_requirement(req_id, req)
    return req


@router.delete("/{req_id}")
async def delete_requirement(req_id: str) -> dict:
    """Soft-delete a requirement (set status=retired)."""
    await _ensure_loaded()
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")

    req["status"] = "retired"
    await db_soft_delete_requirement(req_id)
    return {"id": req_id, "status": "retired"}
