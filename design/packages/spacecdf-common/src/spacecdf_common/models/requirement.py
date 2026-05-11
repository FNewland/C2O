"""Requirement model for the reactive spine (SPINE_SPEC SS6.2).

This is the Pydantic model mirroring RequirementRow in db/models.py.
It is the single source of truth for requirement validation and serialization.

NOTE: This module is separate from `requirements.py` which contains
the auto-generation and verification logic for the legacy compliance matrix.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class RequirementLevel(str, Enum):
    MISSION = "mission"
    SYSTEM = "system"
    SUBSYSTEM = "subsystem"


class RequirementStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    VIOLATED = "violated"
    VERIFIED = "verified"
    RETIRED = "retired"


class Requirement(BaseModel):
    """A formal requirement in the spine hierarchy.

    Hierarchy rules:
    - MISSION requirements have no parent (parent_id is None).
    - SYSTEM requirements MUST have a parent (validated here; parent level
      checked in the repository for DB-backed enforcement).
    - SUBSYSTEM requirements MUST have a parent (validated here; parent level
      checked in the repository for DB-backed enforcement).
    """

    id: str
    study_id: str
    parent_id: str | None = None
    level: RequirementLevel
    code: str = Field(description="Human-readable code, e.g. 'MR-001', 'SR-PWR-002'")
    text: str
    rationale: str | None = None
    threshold_param_path: str | None = Field(
        default=None,
        description="Design parameter path for auto-evaluation, e.g. 'power.battery_capacity_wh'",
    )
    threshold_op: str | None = Field(
        default=None,
        description="Comparison operator: '<=', '>=', '==', 'in_range', 'exists'",
    )
    threshold_value: str | None = Field(
        default=None,
        description="JSON-encoded threshold value, e.g. '100' or '{\"min\": 100, \"max\": 200}'",
    )
    verification_method: str | None = Field(
        default=None, description="A (analysis), T (test), I (inspection), R (review), D (demonstration)"
    )
    verification_phase: str | None = Field(
        default=None, description="PDR, CDR, QR, AR"
    )
    verification_evidence: str | None = None
    responsible_position: str | None = None
    status: RequirementStatus = RequirementStatus.DRAFT
    element_id: str | None = Field(
        default=None,
        description="FK to design_elements.id — the element this requirement governs",
    )
    derived_from_requirement_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_hierarchy(self) -> "Requirement":
        """Subsystem and system requirements must have a parent_id."""
        if self.level == RequirementLevel.SUBSYSTEM and not self.parent_id:
            raise ValueError("Subsystem requirements must have a system parent (parent_id required)")
        if self.level == RequirementLevel.SYSTEM and not self.parent_id:
            raise ValueError("System requirements must have a mission parent (parent_id required)")
        return self

    def is_evaluable(self) -> bool:
        """True if this requirement can be auto-evaluated against a design state."""
        return self.threshold_param_path is not None and self.threshold_op is not None

    class Config:
        use_enum_values = False  # Keep enums as enum objects
