"""ChangeEvent — typed envelope for every design mutation.

Per SPINE_SPEC §2. Unifies persistence, broadcast, undo, and audit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChangeKind(str, Enum):
    PARAMETER_OVERRIDE = "parameter_override"
    EQUIPMENT_SELECTION = "equipment_selection"
    REQUIREMENT_EDIT = "requirement_edit"
    REQUIREMENT_DELETE = "requirement_delete"
    CONOPS_EDIT = "conops_edit"
    QA_ANSWER = "qa_answer"
    MARGIN_PHASE_CHANGE = "margin_phase_change"
    PARAMETRIC_FRACTION_EDIT = "parametric_fraction_edit"
    LAUNCH_VEHICLE_SELECTION = "launch_vehicle_selection"
    SPECTRUM_BAND_SELECTION = "spectrum_band_selection"
    GATE_CRITERION_TOGGLE = "gate_criterion_toggle"


class ChangeEvent(BaseModel):
    """A single mutation to the design state."""
    id: UUID = Field(default_factory=uuid4)
    kind: ChangeKind
    session_id: str
    actor_id: str                       # position_id or "system"
    actor_label: str = ""
    target_id: str                      # param path, requirement id, equipment id...
    target_kind: str                    # "parameter" | "requirement" | "equipment" | "conops_mode" | ...
    old_value: Any = None
    new_value: Any = None
    rationale: str = ""
    correlation_id: UUID | None = None  # group multiple edits as one transaction
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
