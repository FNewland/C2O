"""SpaceCDF — Named snapshot + diff API (Phase 5B).

Endpoints:
    POST   /api/snapshots/sessions/{session_id}        -- create named snapshot
    GET    /api/snapshots/sessions/{session_id}        -- list snapshots
    GET    /api/snapshots/{snapshot_id}                -- single snapshot + state
    GET    /api/snapshots/diff?a={id}&b={id}           -- structured diff
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.snapshots import (
    create_named_snapshot,
    diff_snapshots,
    get_snapshot,
    list_snapshots,
)

router = APIRouter()


class CreateSnapshotBody(BaseModel):
    name: str
    label: str = "manual"
    tags: list[str] = []
    parent_snapshot_id: int | None = None


@router.post("/sessions/{session_id}")
async def create_snapshot(session_id: str, body: CreateSnapshotBody) -> dict:
    try:
        info = await create_named_snapshot(
            session_id=session_id,
            name=body.name,
            label=body.label,
            tags=body.tags,
            parent_snapshot_id=body.parent_snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return info.__dict__


@router.get("/sessions/{session_id}")
async def list_session_snapshots(session_id: str) -> list[dict]:
    rows = await list_snapshots(session_id)
    return [r.__dict__ for r in rows]


@router.get("/diff")
async def snapshot_diff(
    a: int = Query(..., description="Snapshot A id (the baseline)"),
    b: int = Query(..., description="Snapshot B id (the comparison)"),
) -> dict:
    try:
        return await diff_snapshots(a, b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{snapshot_id}")
async def get_single_snapshot(snapshot_id: int) -> dict:
    result = await get_snapshot(snapshot_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")
    info, state = result
    return {"info": info.__dict__, "state": state}
