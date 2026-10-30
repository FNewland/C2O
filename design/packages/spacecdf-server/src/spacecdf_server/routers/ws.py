"""SpaceCDF — WebSocket Router for Real-Time Collaboration.

Engineers connect via WebSocket with their position_id. They can:
- Send parameter edits (scoped to their position's owned parameters)
- Send equipment selections
- Request re-convergence
- Receive real-time updates when ANY position changes a parameter

Protocol (JSON messages):

Client → Server:
  {"type": "parameter_edit", "parameter_id": "power.battery_capacity_wh",
   "new_value": 77.0, "rationale": "Selected NanoPower BPX",
   "equipment_id": "bat-gom-nanopow-bpx"}
  {"type": "request_convergence"}
  {"type": "ping"}

Server → Client:
  {"type": "parameter_update", "updates": {...}, "edited_by": "power_engineer"}
  {"type": "convergence_complete", "changed_params": [...], "time_ms": 4.5}
  {"type": "participant_joined", "position_id": "aocs_engineer", "name": "..."}
  {"type": "participant_left", "position_id": "aocs_engineer"}
  {"type": "conflict_update", "conflicts": [...]}
  {"type": "error", "message": "..."}
  {"type": "edit_rejected", "parameter_id": "...", "reason": "Not in your scope"}
  {"type": "pong"}
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from ..services.session_manager import get_session_manager
from ..db.write_queue import get_persistence_failures

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections: session_id -> {position_id: WebSocket}
_connections: dict[str, dict[str, WebSocket]] = {}


# ─── Edit Lock System for Level Workbench ───

@dataclass
class EditLock:
    element_id: str
    held_by: str  # display name
    study_id: str
    acquired_at: float
    last_heartbeat: float


# study_id → {element_id → EditLock}
_edit_locks: dict[str, dict[str, EditLock]] = {}
# study_id → [display_name] — all contributors who ever connected
_study_contributors: dict[str, list[str]] = {}
# study_id → {display_name → WebSocket}
_study_connections: dict[str, dict[str, Any]] = {}

# Background task handle
_heartbeat_task: asyncio.Task | None = None


async def _broadcast_study(study_id: str, message: dict, exclude: str | None = None) -> None:
    """Broadcast to all connected users in a study, optionally excluding one."""
    conns = _study_connections.get(study_id, {})
    logger.info("Broadcasting %s to study %s (%d connections, exclude=%s)",
                message.get("type"), study_id, len(conns), exclude)
    for name, ws in list(conns.items()):
        if name != exclude:
            try:
                await ws.send_json(message)
                logger.info("  → sent to %s", name)
            except Exception as exc:
                logger.warning("  → failed to send to %s: %s", name, exc)


async def _heartbeat_checker() -> None:
    """Background task: expire locks whose heartbeat is older than 30 seconds."""
    while True:
        await asyncio.sleep(10)
        now = time.time()
        for study_id, locks in list(_edit_locks.items()):
            for eid, lock in list(locks.items()):
                if now - lock.last_heartbeat > 30:
                    del locks[eid]
                    await _broadcast_study(study_id, {
                        "type": "lock_expired",
                        "element_id": eid,
                        "was_held_by": lock.held_by,
                    })


def start_heartbeat_checker() -> None:
    """Start the background heartbeat checker (call once at app startup)."""
    global _heartbeat_task
    if _heartbeat_task is None or _heartbeat_task.done():
        _heartbeat_task = asyncio.ensure_future(_heartbeat_checker())


async def _broadcast(session_id: str, message: dict, exclude_position: str | None = None) -> None:
    """Broadcast a message to all connected positions in a session."""
    connections = _connections.get(session_id, {})
    dead = []
    for pos_id, ws in connections.items():
        if pos_id == exclude_position:
            continue
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(pos_id)
    for pos_id in dead:
        connections.pop(pos_id, None)


async def _send(ws: WebSocket, message: dict) -> None:
    """Send a message to a single WebSocket."""
    try:
        await ws.send_json(message)
    except Exception:
        pass


@router.websocket("/ws/session/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
    position_id: str = Query(default=""),
    position_ids: str = Query(default=""),
    display_name: str = Query(default=""),
):
    """WebSocket endpoint for real-time concurrent design collaboration.

    Connect: ws://host/ws/session/{session_id}?position_id=power_engineer&display_name=Alice
    Multi-role: ws://host/ws/session/{session_id}?position_ids=systems_engineer,power_engineer&display_name=Alice
    """
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    # Parse position list: prefer position_ids (comma-separated), fallback to position_id
    if position_ids:
        positions = [p.strip() for p in position_ids.split(",") if p.strip()]
    elif position_id:
        positions = [position_id]
    else:
        await websocket.close(code=4003, reason="No position specified")
        return

    # Primary position for backward compatibility
    position_id = positions[0]

    await websocket.accept()

    # Register connection for each claimed position
    if session_id not in _connections:
        _connections[session_id] = {}
    for pid in positions:
        _connections[session_id][pid] = websocket

    # Join session for each position
    for pid in positions:
        participant = mgr.join_session(session_id, pid, display_name)
        if not participant:
            logger.warning("Could not join session %s as %s", session_id, pid)

    # Notify others
    await _broadcast(session_id, {
        "type": "participant_joined",
        "position_id": position_id,
        "positions": positions,
        "display_name": display_name or position_id,
        "active_positions": session.active_positions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, exclude_position=position_id)

    # Send initial state to the joining client
    state = mgr.get_session_state(session_id)
    if state:
        params_snapshot = {}
        for pid, p in state.parameters.items():
            params_snapshot[pid] = {
                "value": p.value, "unit": p.unit, "domain": p.domain,
                "source": p.source.value, "confidence": p.confidence,
                "equipment_id": p.equipment_id, "updated_by": p.updated_by,
            }
        await _send(websocket, {
            "type": "state_snapshot",
            "parameters": params_snapshot,
            "session_state": session.state.value,
            "active_positions": session.active_positions,
            "convergence_count": session.convergence_count,
        })

    # Message loop
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send(websocket, {"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            if msg_type == "ping":
                await _send(websocket, {"type": "pong"})

            elif msg_type == "parameter_edit":
                param_id = msg.get("parameter_id")
                new_value = msg.get("new_value")
                rationale = msg.get("rationale", "")
                equipment_id = msg.get("equipment_id")
                edit_type = msg.get("edit_type", "override")

                if not param_id or new_value is None:
                    await _send(websocket, {"type": "error", "message": "Missing parameter_id or new_value"})
                    continue

                # Check scope
                if not mgr.can_edit(position_id, param_id):
                    await _send(websocket, {
                        "type": "edit_rejected",
                        "parameter_id": param_id,
                        "reason": f"Parameter '{param_id}' is not in {position_id}'s scope",
                    })
                    continue

                # Apply edit — try each claimed position until one has scope
                edit = None
                for try_pos in positions:
                    edit = await mgr.apply_edit(
                        session_id, try_pos, param_id, new_value,
                        rationale=rationale, edit_type=edit_type, equipment_id=equipment_id,
                    )
                    if edit:
                        break

                if edit:
                    # Broadcast to all positions
                    await _broadcast(session_id, {
                        "type": "parameter_update",
                        "parameter_id": param_id,
                        "new_value": new_value,
                        "old_value": edit.old_value,
                        "edited_by": position_id,
                        "display_name": display_name or position_id,
                        "rationale": rationale,
                        "equipment_id": equipment_id,
                        "timestamp": edit.timestamp.isoformat(),
                    })

                    # Auto-trigger convergence after edit
                    convergence_result = await mgr.run_convergence(session_id)

                    # Broadcast convergence results
                    await _broadcast(session_id, {
                        "type": "convergence_complete",
                        "changed_params": convergence_result.get("changed_params", []),
                        "agents_executed": convergence_result.get("agents_executed", []),
                        "cascade_rounds": convergence_result.get("cascade_rounds", 0),
                        "time_ms": convergence_result.get("total_time_ms", 0),
                        "triggered_by": position_id,
                    })

                    # Send updated state to all
                    updated_state = mgr.get_session_state(session_id)
                    if updated_state:
                        # Only send changed parameters
                        updates = {}
                        for cid in convergence_result.get("changed_params", []):
                            p = updated_state.get_param(cid)
                            if p:
                                updates[cid] = {
                                    "value": p.value, "unit": p.unit, "domain": p.domain,
                                    "source": p.source.value, "confidence": p.confidence,
                                }
                        if updates:
                            await _broadcast(session_id, {
                                "type": "state_update",
                                "updates": updates,
                                "convergence_count": session.convergence_count,
                            })

                    # SCDF-035/105: Surface persistence failures if any
                    failures = get_persistence_failures()
                    if failures:
                        for failure in failures:
                            await _broadcast(session_id, failure)

            elif msg_type == "request_convergence":
                convergence_result = await mgr.run_convergence(session_id)
                await _broadcast(session_id, {
                    "type": "convergence_complete",
                    "changed_params": convergence_result.get("changed_params", []),
                    "agents_executed": convergence_result.get("agents_executed", []),
                    "cascade_rounds": convergence_result.get("cascade_rounds", 0),
                    "time_ms": convergence_result.get("total_time_ms", 0),
                    "triggered_by": position_id,
                })

            # ─── Model-centric element mutations (broadcast to all clients) ───
            elif msg_type == "element_create":
                from .elements import _elements
                from uuid import uuid4
                el_data = msg.get("element", {})
                el_id = uuid4().hex
                element = {"id": el_id, "study_id": msg.get("study_id", ""), **el_data, "version": 1, "deleted_at": None}
                _elements[el_id] = element
                await _broadcast(session_id, {
                    "type": "element_created", "element": element,
                    "actor": position_id, "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif msg_type == "element_update":
                from .elements import _elements
                el_id = msg.get("element_id")
                changes = msg.get("changes", {})
                version = msg.get("version", 0)
                el = _elements.get(el_id)
                if el and el["version"] == version:
                    old_values = {}
                    for k, v in changes.items():
                        old_values[k] = el.get(k)
                        el[k] = v
                    el["version"] += 1
                    await _broadcast(session_id, {
                        "type": "element_updated", "element_id": el_id,
                        "changes": {k: [old_values.get(k), v] for k, v in changes.items()},
                        "actor": position_id, "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                elif el:
                    await _send(websocket, {
                        "type": "conflict_rejected", "element_id": el_id,
                        "your_version": version, "current_version": el["version"],
                        "current_state": el,
                    })

            elif msg_type == "element_delete":
                from .elements import _elements
                el_id = msg.get("element_id")
                el = _elements.get(el_id)
                if el:
                    el["deleted_at"] = datetime.now(timezone.utc).isoformat()
                    await _broadcast(session_id, {
                        "type": "element_deleted", "element_id": el_id,
                        "actor": position_id, "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

            elif msg_type == "interface_create":
                from .elements import _interfaces
                from uuid import uuid4
                iface_data = msg.get("interface", {})
                iface_id = uuid4().hex
                iface = {"id": iface_id, "study_id": msg.get("study_id", ""), **iface_data, "version": 1, "deleted_at": None, "status": "defined", "criticality": "standard"}
                _interfaces[iface_id] = iface
                await _broadcast(session_id, {
                    "type": "interface_created", "interface": iface,
                    "actor": position_id, "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            else:
                await _send(websocket, {"type": "error", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("Position %s disconnected from session %s", position_id, session_id)
    except Exception as e:
        logger.error("WebSocket error for %s in %s: %s", position_id, session_id, e)
    finally:
        # Cleanup — remove all claimed positions for this connection
        conns = _connections.get(session_id, {})
        for pid in positions:
            conns.pop(pid, None)
            mgr.leave_session(session_id, pid)

        # Notify others
        await _broadcast(session_id, {
            "type": "participant_left",
            "position_id": position_id,
            "positions": positions,
            "active_positions": session.active_positions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# ─── Level Workbench: study-scoped WebSocket with edit locking ───

@router.websocket("/ws/study/{study_id}")
async def study_websocket(
    websocket: WebSocket,
    study_id: str,
    name: str = Query("Anonymous"),
) -> None:
    """WebSocket for the Level Workbench — collaborative editing with element locking.

    Connect: ws://host/ws/study/{study_id}?name=Alice

    Client → Server:
      {"type": "lock_request", "element_id": "..."}
      {"type": "lock_release", "element_id": "..."}
      {"type": "heartbeat"}
      {"type": "element_created/updated/deleted", ...}

    Server → Client:
      {"type": "users_update", "users": [...]}
      {"type": "locks_state", "locks": {...}}
      {"type": "element_locked", "element_id": "...", "held_by": "..."}
      {"type": "lock_denied", "element_id": "...", "held_by": "..."}
      {"type": "lock_released", "element_id": "...", "released_by": "..."}
      {"type": "lock_expired", "element_id": "...", "was_held_by": "..."}
    """
    await websocket.accept()

    # Ensure heartbeat checker is running
    start_heartbeat_checker()

    # Register connection
    if study_id not in _study_connections:
        _study_connections[study_id] = {}
    _study_connections[study_id][name] = websocket

    # Track contributor
    if study_id not in _study_contributors:
        _study_contributors[study_id] = []
    if name not in _study_contributors[study_id]:
        _study_contributors[study_id].append(name)

    # Broadcast updated user list
    users = [{"name": n} for n in _study_connections[study_id].keys()]
    logger.info("Study %s: user %s connected. Active users: %s", study_id, name, [u["name"] for u in users])
    await _broadcast_study(study_id, {
        "type": "users_update",
        "users": users,
    })

    # Send current lock state to the new connection (as array for frontend)
    locks_list = [
        {"element_id": lock.element_id, "held_by": lock.held_by}
        for lock in _edit_locks.get(study_id, {}).values()
    ]
    await _send(websocket, {"type": "locks_state", "locks": locks_list})

    # Message loop
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send(websocket, {"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            if msg_type == "lock_request":
                eid = msg.get("element_id")
                if not eid:
                    await _send(websocket, {"type": "error", "message": "Missing element_id"})
                    continue

                study_locks = _edit_locks.setdefault(study_id, {})
                existing = study_locks.get(eid)

                if existing and existing.held_by != name:
                    # Locked by someone else
                    await _send(websocket, {
                        "type": "lock_denied",
                        "element_id": eid,
                        "held_by": existing.held_by,
                    })
                else:
                    # Grant lock (or re-grant to same user)
                    now = time.time()
                    study_locks[eid] = EditLock(
                        element_id=eid,
                        held_by=name,
                        study_id=study_id,
                        acquired_at=now,
                        last_heartbeat=now,
                    )
                    await _broadcast_study(study_id, {
                        "type": "element_locked",
                        "element_id": eid,
                        "held_by": name,
                    })

            elif msg_type == "lock_release":
                eid = msg.get("element_id")
                if not eid:
                    continue
                study_locks = _edit_locks.get(study_id, {})
                existing = study_locks.get(eid)
                if existing and existing.held_by == name:
                    del study_locks[eid]
                    await _broadcast_study(study_id, {
                        "type": "lock_released",
                        "element_id": eid,
                        "released_by": name,
                    })

            elif msg_type == "heartbeat":
                # Update last_heartbeat on all locks held by this user
                for eid, lock in _edit_locks.get(study_id, {}).items():
                    if lock.held_by == name:
                        lock.last_heartbeat = time.time()

            elif msg_type in ("element_created", "element_updated", "element_deleted"):
                # Relay to all OTHER connections in this study
                await _broadcast_study(study_id, msg, exclude=name)

            else:
                await _send(websocket, {"type": "error", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("User %s disconnected from study %s", name, study_id)
    except Exception as e:
        logger.error("Study WebSocket error for %s in %s: %s", name, study_id, e)
    finally:
        # Release all locks held by this user
        study_locks = _edit_locks.get(study_id, {})
        released_eids = [eid for eid, lock in study_locks.items() if lock.held_by == name]
        for eid in released_eids:
            del study_locks[eid]
            await _broadcast_study(study_id, {
                "type": "lock_released",
                "element_id": eid,
                "released_by": name,
            })

        # Remove connection
        conns = _study_connections.get(study_id, {})
        conns.pop(name, None)

        # Broadcast updated user list
        users = [{"name": n} for n in _study_connections.get(study_id, {}).keys()]
        logger.info("Study %s: user %s disconnected. Remaining: %s", study_id, name, [u["name"] for u in users])
        await _broadcast_study(study_id, {
            "type": "users_update",
            "users": users,
        })


@router.get("/ws/study/{study_id}/contributors")
async def get_contributors(study_id: str) -> dict:
    """Return all users who have ever connected to this study's WebSocket."""
    return {
        "study_id": study_id,
        "contributors": _study_contributors.get(study_id, []),
    }
