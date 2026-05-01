"""SpaceCDF — Session Manager Service.

Manages the lifecycle of concurrent design sessions: create, join,
edit parameters, request convergence, leave, close.

Validates parameter edits against position ownership using fnmatch
patterns from the positions YAML.
"""
from __future__ import annotations

import asyncio
import fnmatch
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from spacecdf_common.agents.base import DesignState
from spacecdf_common.config.loader import load_yaml
from spacecdf_common.models.parameter import ParameterSource, ParameterValue
from spacecdf_common.models.session import (
    DesignSession,
    Participant,
    ParameterEdit,
    SessionState,
)
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator

from ..db import repo as db_repo
from ..db.write_queue import (
    enqueue_edit,
    enqueue_session,
    enqueue_snapshot,
    enqueue_study,
)

logger = logging.getLogger(__name__)

SNAPSHOT_EVERY_N_EDITS = 10


class SessionManager:
    """Manages concurrent design sessions with position-scoped editing."""

    def __init__(self):
        self._sessions: dict[str, DesignSession] = {}
        self._session_states: dict[str, DesignState] = {}
        self._position_patterns: dict[str, list[dict]] = {}  # position_id -> [{param_pattern, role}]
        self._edit_counters: dict[str, int] = {}  # session_id -> edit count for snapshot cadence
        self._locks: dict[str, asyncio.Lock] = {}  # per-session lock for concurrent edit safety
        self._load_position_ownership()

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        """Get or create a per-session asyncio.Lock.

        Serialises state mutations (apply_edit + run_convergence) within a
        session to prevent race conditions when multiple positions edit
        simultaneously. Different sessions remain fully concurrent.
        """
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]

    def _load_position_ownership(self) -> None:
        """Load position parameter ownership patterns for edit scoping."""
        # Search for positions.yaml
        positions_path = None
        search_root = Path(__file__).resolve()
        while search_root != search_root.parent:
            candidate = search_root / "packages" / "spacecdf-kb" / "src" / "spacecdf_kb" / "data" / "positions" / "positions.yaml"
            if candidate.exists():
                positions_path = candidate
                break
            search_root = search_root.parent

        if not positions_path:
            logger.warning("Could not find positions.yaml — edit scoping disabled")
            return

        try:
            data = load_yaml(positions_path)
            for pos in data.get("positions", []):
                pos_id = pos["id"]
                self._position_patterns[pos_id] = pos.get("parameters", [])
        except Exception as e:
            logger.warning("Failed to load position ownership: %s", e)

    def can_edit(self, position_id: str, parameter_id: str) -> bool:
        """Check if a position is allowed to edit a parameter.

        Uses fnmatch patterns from the position's 'owns' parameter list.
        """
        patterns = self._position_patterns.get(position_id, [])
        for p in patterns:
            if p.get("role") == "owns":
                if fnmatch.fnmatch(parameter_id, p.get("param_pattern", "")):
                    return True
        # Systems engineer can edit anything (fallback for arbitration)
        if position_id == "systems_engineer":
            return True
        return False

    def create_session(self, study_id: str, name: str = "") -> DesignSession:
        """Create a new design session for a study."""
        session_id = str(uuid.uuid4())[:8]
        session = DesignSession(
            id=session_id,
            study_id=study_id,
            name=name or f"Session {session_id}",
            state=SessionState.LOBBY,
        )
        self._sessions[session_id] = session
        logger.info("Created session %s for study %s", session_id, study_id)

        # Fire-and-forget persistence (non-blocking). The write queue
        # will flush these to the DB in a background worker.
        try:
            asyncio.create_task(
                enqueue_study({"id": study_id, "name": name or f"Study {study_id}"})
            )
            asyncio.create_task(
                enqueue_session(
                    {
                        "id": session_id,
                        "study_id": study_id,
                        "name": session.name,
                        "state": session.state.value,
                    }
                )
            )
        except RuntimeError:
            # No running event loop — ignore (e.g. unit-test construction)
            pass
        except Exception as e:
            logger.warning("Failed to enqueue session persistence: %s", e)
        return session

    def get_session(self, session_id: str) -> DesignSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[DesignSession]:
        return list(self._sessions.values())

    def join_session(self, session_id: str, position_id: str, display_name: str = "") -> Participant | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        # Check position not already taken by someone active
        existing = session.get_participant(position_id)
        if existing and existing.is_active:
            existing.display_name = display_name or existing.display_name
            return existing
        participant = session.add_participant(position_id, display_name)
        if session.state == SessionState.LOBBY and len(session.active_participants) >= 1:
            session.state = SessionState.ACTIVE
        logger.info("Position %s joined session %s (%s)", position_id, session_id, display_name)
        return participant

    def leave_session(self, session_id: str, position_id: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.remove_participant(position_id)
            if not session.active_participants:
                session.state = SessionState.LOBBY
            logger.info("Position %s left session %s", position_id, session_id)

    async def apply_edit(
        self,
        session_id: str,
        position_id: str,
        parameter_id: str,
        new_value: float | str | bool,
        rationale: str = "",
        edit_type: str = "override",
        equipment_id: str | None = None,
    ) -> ParameterEdit | None:
        """Apply a parameter edit from a position engineer.

        Validates ownership, records the edit, updates the design state,
        and returns the edit record for WebSocket broadcast.

        Thread-safe via per-session asyncio.Lock — serialises concurrent
        edits from multiple positions within the same session.
        """
        async with self._get_lock(session_id):
            return await self._apply_edit_inner(
                session_id, position_id, parameter_id, new_value,
                rationale, edit_type, equipment_id,
            )

    async def _apply_edit_inner(
        self,
        session_id: str,
        position_id: str,
        parameter_id: str,
        new_value: float | str | bool,
        rationale: str = "",
        edit_type: str = "override",
        equipment_id: str | None = None,
    ) -> ParameterEdit | None:
        """Inner implementation of apply_edit (called under lock)."""
        session = self._sessions.get(session_id)
        if not session or session.state not in (SessionState.ACTIVE, SessionState.LOBBY):
            return None

        # Validate ownership
        if not self.can_edit(position_id, parameter_id):
            logger.warning(
                "Position %s attempted to edit %s — not in scope",
                position_id, parameter_id,
            )
            return None

        # Get current design state
        state = self._session_states.get(session_id)
        if not state:
            return None

        # Record old value
        old_param = state.get_param(parameter_id)
        old_value = old_param.value if old_param else None

        # Create edit record
        edit = ParameterEdit(
            id=str(uuid.uuid4())[:8],
            parameter_id=parameter_id,
            old_value=old_value,
            new_value=new_value,
            edited_by=position_id,
            display_name=position_id.replace("_", " ").title(),
            rationale=rationale,
            edit_type=edit_type,
            equipment_id=equipment_id,
        )
        session.edits.append(edit)

        # Apply to design state with sticky source
        source = ParameterSource.KB_COMPONENT if equipment_id else ParameterSource.POSITION_OVERRIDE
        state._parameters[parameter_id] = ParameterValue(
            id=parameter_id,
            name=old_param.name if old_param else parameter_id,
            value=new_value,
            unit=old_param.unit if old_param else "",
            domain=old_param.domain if old_param else parameter_id.split(".")[0],
            source=source,
            confidence=0.95 if equipment_id else 0.90,
            margin_percent=5.0 if equipment_id else 10.0,
            equipment_id=equipment_id,
            override_by=position_id,
            updated_by=f"position:{position_id}",
            rationale=rationale,
        )

        logger.info(
            "Edit applied: %s.%s = %s (by %s)",
            session_id, parameter_id, new_value, position_id,
        )

        # Fire-and-forget persistence (non-blocking hot path).
        try:
            await enqueue_edit(
                {
                    "id": edit.id,
                    "session_id": session_id,
                    "position_id": position_id,
                    "param_path": parameter_id,
                    "old_value": old_value,
                    "new_value": new_value,
                    "source": source.value if hasattr(source, "value") else str(source),
                    "actor_label": edit.display_name,
                    "edit_type": edit_type,
                    "equipment_id": equipment_id,
                    "rationale": rationale,
                }
            )
            # Snapshot every N edits
            count = self._edit_counters.get(session_id, 0) + 1
            self._edit_counters[session_id] = count
            if count % SNAPSHOT_EVERY_N_EDITS == 0:
                state_dict = self._serialise_state(state)
                await enqueue_snapshot(session_id, state_dict)
        except Exception as e:
            logger.warning("Edit persistence enqueue failed: %s", e)

        return edit

    def _serialise_state(self, state: DesignState) -> dict:
        """Serialise a DesignState to a JSON-safe dict for snapshotting."""
        out: dict[str, Any] = {"_version": getattr(state, "version", 0), "parameters": {}}
        for pid, p in state.parameters.items():
            out["parameters"][pid] = {
                "id": p.id,
                "name": p.name,
                "value": p.value,
                "unit": p.unit,
                "domain": p.domain,
                "source": p.source.value if hasattr(p.source, "value") else str(p.source),
                "confidence": p.confidence,
                "margin_percent": p.margin_percent,
                "equipment_id": p.equipment_id,
                "equipment_name": getattr(p, "equipment_name", None),
                "override_by": p.override_by,
                "updated_by": p.updated_by,
                "rationale": getattr(p, "rationale", ""),
            }
        return out

    async def resume_session(self, session_id: str) -> DesignSession | None:
        """Load a persisted session into memory if not already active.

        Returns None if session not found in memory or DB.
        """
        if session_id in self._sessions:
            return self._sessions[session_id]

        try:
            row = await db_repo.load_session(session_id)
        except Exception as e:
            logger.warning("resume_session DB load failed: %s", e)
            row = None

        if not row:
            return None

        try:
            state_value = row.state
            try:
                resumed_state = SessionState(state_value)
            except Exception:
                resumed_state = SessionState.LOBBY

            session = DesignSession(
                id=row.id,
                study_id=row.study_id,
                name=row.name or f"Session {row.id}",
                state=resumed_state,
            )
            self._sessions[session_id] = session
            logger.info("Resumed session %s from persistence", session_id)
            return session
        except Exception as e:
            logger.warning("resume_session reconstruction failed: %s", e)
            return None

    async def run_convergence(self, session_id: str) -> dict:
        """Run selective re-convergence for the session's design state.

        Called after edits to propagate changes through the agent network.
        Serialised via per-session lock to prevent overlapping convergence runs.
        """
        async with self._get_lock(session_id):
            return await self._run_convergence_inner(session_id)

    async def _run_convergence_inner(self, session_id: str) -> dict:
        """Inner convergence implementation (called under lock)."""
        session = self._sessions.get(session_id)
        state = self._session_states.get(session_id)
        if not session or not state:
            return {"error": "Session not found"}

        session.state = SessionState.CONVERGING

        # Use selective re-convergence
        from .reconvergence import SelectiveReconvergence
        reconverger = SelectiveReconvergence()
        reconverger.initialise()

        # Find recently edited parameters
        recent_edits = session.edits[-20:]  # Last 20 edits
        changed_ids = {e.parameter_id for e in recent_edits}

        result = await reconverger.reconverge(state, changed_ids)

        session.state = SessionState.ACTIVE
        session.convergence_count += 1
        session.last_convergence = datetime.now(timezone.utc)

        return {
            "changed_params": list(result.changed_params),
            "agents_executed": result.agents_executed,
            "cascade_rounds": result.cascade_rounds,
            "total_time_ms": round(result.total_time_ms, 2),
            "warnings": result.warnings[:10],
        }

    async def initialise_session_state(
        self,
        session_id: str,
        requirements: MissionRequirements,
        conops: object | None = None,
    ) -> None:
        """Run initial full convergence to seed the session design state.

        When conops is provided, passes it to the orchestrator so agents
        use operational mode profiles for multi-mode sizing.
        """
        orchestrator = DesignLoopOrchestrator()
        orchestrator.initialise_agents()
        loop_result = await orchestrator.run(requirements, conops=conops)
        if loop_result.final_state:
            self._session_states[session_id] = loop_result.final_state

    def get_session_state(self, session_id: str) -> DesignState | None:
        return self._session_states.get(session_id)


# Singleton instance
_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
