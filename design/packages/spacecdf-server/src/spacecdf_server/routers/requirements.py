"""Requirements API — tree, derive, patch, soft-delete (SCDF-112).

Per SPINE_SPEC §6.3. Provides CRUD for the requirement hierarchy.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

router = APIRouter()


# In-memory store (Phase A — will migrate to DB repo in Phase B)
_requirements: dict[str, dict] = {}


@router.get("/tree")
async def get_tree(study_id: str) -> list[dict]:
    """Return full requirement tree for a study."""
    return [r for r in _requirements.values() if r.get("study_id") == study_id and r.get("status") != "retired"]


@router.get("/{req_id}")
async def get_requirement(req_id: str) -> dict:
    """Get a single requirement."""
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")
    return req


@router.post("/")
async def create_requirement(body: dict[str, Any]) -> dict:
    """Create a new requirement."""
    req_id = body.get("id") or f"REQ-{uuid4().hex[:8]}"
    level = body.get("level", "system")
    parent_id = body.get("parent_id")

    # Validate hierarchy
    if level in ("system", "subsystem") and not parent_id:
        raise HTTPException(400, f"{level} requirements must have a parent_id")
    if parent_id and parent_id not in _requirements:
        raise HTTPException(400, f"Parent requirement {parent_id} not found")

    req = {
        "id": req_id,
        "study_id": body.get("study_id", ""),
        "parent_id": parent_id,
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
    }
    _requirements[req_id] = req
    return req


@router.post("/{req_id}/derive")
async def derive_requirement(req_id: str, body: dict[str, Any]) -> dict:
    """Create a child requirement derived from parent."""
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
    return await create_requirement(body)


@router.patch("/{req_id}")
async def update_requirement(req_id: str, body: dict[str, Any]) -> dict:
    """Update a requirement's fields."""
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")

    for key in ("text", "rationale", "threshold_param_path", "threshold_op",
                "threshold_value", "verification_method", "verification_phase",
                "responsible_position", "status", "code"):
        if key in body:
            req[key] = body[key]

    return req


@router.delete("/{req_id}")
async def delete_requirement(req_id: str) -> dict:
    """Soft-delete a requirement (set status=retired)."""
    req = _requirements.get(req_id)
    if not req:
        raise HTTPException(404, f"Requirement {req_id} not found")

    req["status"] = "retired"
    return {"id": req_id, "status": "retired"}
