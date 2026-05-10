"""SpaceCDF — Design Session data models.

A DesignSession represents a concurrent design session where multiple
engineers join by position, edit parameters within their scope, and
see real-time updates from other positions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SessionState(str, Enum):
    LOBBY = "lobby"          # Waiting for engineers to join
    ACTIVE = "active"        # Engineers working, edits allowed
    CONVERGING = "converging"  # Re-convergence in progress
    REVIEW = "review"        # Design frozen for review
    CLOSED = "closed"        # Session complete


class Participant(BaseModel):
    """An engineer connected to a design session."""
    position_id: str
    display_name: str = ""
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ParameterEdit(BaseModel):
    """Record of a single parameter edit by a position engineer."""
    id: str = ""
    parameter_id: str
    old_value: float | str | bool | None = None
    new_value: float | str | bool
    edited_by: str = Field(description="Position ID of the editor")
    display_name: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rationale: str = ""
    edit_type: Literal["override", "equipment_selection", "constraint", "resolution"] = "override"
    equipment_id: str | None = None


class DesignSession(BaseModel):
    """A concurrent design session with multiple engineers."""
    id: str
    study_id: str
    name: str = "Design Session"
    state: SessionState = SessionState.LOBBY
    participants: list[Participant] = Field(default_factory=list)
    edits: list[ParameterEdit] = Field(default_factory=list)
    convergence_count: int = 0
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_convergence: datetime | None = None
    dirty_params: set[str] = Field(default_factory=set)  # SCDF-040: replaces recent_edits heuristic

    def get_participant(self, position_id: str) -> Participant | None:
        for p in self.participants:
            if p.position_id == position_id:
                return p
        return None

    def add_participant(self, position_id: str, display_name: str = "") -> Participant:
        existing = self.get_participant(position_id)
        if existing:
            existing.is_active = True
            existing.last_activity = datetime.now(timezone.utc)
            return existing
        p = Participant(position_id=position_id, display_name=display_name or position_id)
        self.participants.append(p)
        return p

    def remove_participant(self, position_id: str) -> None:
        p = self.get_participant(position_id)
        if p:
            p.is_active = False

    @property
    def active_participants(self) -> list[Participant]:
        return [p for p in self.participants if p.is_active]

    @property
    def active_positions(self) -> list[str]:
        return [p.position_id for p in self.active_participants]
