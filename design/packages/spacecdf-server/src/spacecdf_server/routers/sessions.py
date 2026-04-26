"""SpaceCDF — Session Management REST API.

Create, list, and manage concurrent design sessions.
Sessions are created from studies and provide the real-time
collaboration context for WebSocket connections.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .studies import get_study_store
from ..services.session_manager import get_session_manager
from ..db import repo as db_repo

router = APIRouter()


class CreateSessionRequest(BaseModel):
    study_id: str
    name: str = ""


class JoinSessionRequest(BaseModel):
    position_id: str
    display_name: str = ""


@router.get("/")
async def list_sessions() -> list[dict]:
    """List design sessions — merges in-memory active sessions with persisted ones.

    In-memory sessions take precedence when IDs collide (they have richer state).
    """
    mgr = get_session_manager()
    in_memory = mgr.list_sessions()

    results: dict[str, dict] = {}
    for s in in_memory:
        results[s.id] = {
            "id": s.id,
            "study_id": s.study_id,
            "name": s.name,
            "state": s.state.value,
            "participants": [
                {"position_id": p.position_id, "display_name": p.display_name, "is_active": p.is_active}
                for p in s.participants
            ],
            "active_positions": s.active_positions,
            "convergence_count": s.convergence_count,
            "edit_count": len(s.edits),
            "created": s.created.isoformat(),
            "persisted": False,
            "in_memory": True,
        }

    try:
        persisted = await db_repo.list_sessions()
    except Exception:
        persisted = []

    for row in persisted:
        if row["id"] in results:
            results[row["id"]]["persisted"] = True
            continue
        results[row["id"]] = {
            "id": row["id"],
            "study_id": row["study_id"],
            "name": row["name"],
            "state": row["state"],
            "participants": [],
            "active_positions": [],
            "convergence_count": 0,
            "edit_count": 0,
            "created": row.get("created_at"),
            "persisted": True,
            "in_memory": False,
        }

    return list(results.values())


@router.post("/")
async def create_session(req: CreateSessionRequest) -> dict:
    """Create a new design session from a study.

    Runs the initial full convergence to seed the session's design state.
    """
    studies = get_study_store()
    study = studies.get(req.study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {req.study_id} not found")

    mgr = get_session_manager()
    session = mgr.create_session(req.study_id, req.name)

    # Run initial convergence
    await mgr.initialise_session_state(session.id, study.requirements)

    return {
        "id": session.id,
        "study_id": session.study_id,
        "name": session.name,
        "state": session.state.value,
        "message": "Session created. Connect via WebSocket at /ws/session/{id}?position_id=YOUR_POSITION",
    }


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict:
    """Get session details including participants and edit history.

    Falls back to the persistence layer if the session is not in memory.
    """
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        # Try to resume from persistence
        session = await mgr.resume_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "id": session.id,
        "study_id": session.study_id,
        "name": session.name,
        "state": session.state.value,
        "participants": [
            {"position_id": p.position_id, "display_name": p.display_name, "is_active": p.is_active}
            for p in session.participants
        ],
        "active_positions": session.active_positions,
        "convergence_count": session.convergence_count,
        "edit_count": len(session.edits),
        "recent_edits": [
            {
                "id": e.id,
                "parameter_id": e.parameter_id,
                "old_value": e.old_value,
                "new_value": e.new_value,
                "edited_by": e.edited_by,
                "display_name": e.display_name,
                "timestamp": e.timestamp.isoformat(),
                "rationale": e.rationale,
                "edit_type": e.edit_type,
            }
            for e in session.edits[-20:]  # Last 20 edits
        ],
        "created": session.created.isoformat(),
    }


@router.get("/{session_id}/history")
async def get_session_history(session_id: str) -> dict:
    """Return the full persisted edit history for a session."""
    edits = await db_repo.list_edits(session_id)
    return {"session_id": session_id, "edits": edits, "count": len(edits)}


@router.post("/{session_id}/resume")
async def resume_session(session_id: str) -> dict:
    """Rehydrate a persisted session into memory."""
    mgr = get_session_manager()
    session = await mgr.resume_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found in memory or persistence",
        )
    return {
        "id": session.id,
        "study_id": session.study_id,
        "name": session.name,
        "state": session.state.value,
        "resumed": True,
    }


@router.get("/{session_id}/state")
async def get_session_state(session_id: str) -> dict:
    """Get the current design state for a session (all parameter values)."""
    mgr = get_session_manager()
    state = mgr.get_session_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found or not initialised")

    params = {}
    for pid, p in state.parameters.items():
        params[pid] = {
            "value": p.value,
            "unit": p.unit,
            "domain": p.domain,
            "source": p.source.value,
            "confidence": p.confidence,
            "margin_percent": p.margin_percent,
            "equipment_id": p.equipment_id,
            "equipment_name": p.equipment_name,
            "override_by": p.override_by,
            "updated_by": p.updated_by,
        }

    return {"session_id": session_id, "parameters": params}
