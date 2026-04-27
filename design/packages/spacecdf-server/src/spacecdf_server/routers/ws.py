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

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from ..services.session_manager import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections: session_id -> {position_id: WebSocket}
_connections: dict[str, dict[str, WebSocket]] = {}


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
