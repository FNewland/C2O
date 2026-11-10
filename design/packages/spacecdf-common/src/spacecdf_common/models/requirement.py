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
    """Requirement levels, top down (W2.01).

    ``stakeholder`` holds stakeholder needs (SN-xx), ``segment`` the space, ground, launch and
    user segment rows (and operations), ``interface`` the interface requirements (IRD rows,
    parents at any level).
    """
    STAKEHOLDER = "stakeholder"
    MISSION = "mission"
    SEGMENT = "segment"
    SYSTEM = "system"
    SUBSYSTEM = "subsystem"
    INTERFACE = "interface"


#: Level values, top down (the order the table groups by and the flow-down counts).
LEVELS: tuple[str, ...] = tuple(lv.value for lv in RequirementLevel)

#: Rank of each level (lower = higher in the tree). ``interface`` sits beside the tree.
LEVEL_RANK: dict[str, int] = {"stakeholder": 0, "mission": 1, "segment": 2, "system": 3, "subsystem": 4,
                              "interface": 5}

#: Verification methods (ECSS-E-ST-10-02C: test, analysis, review of design, inspection).
#: Demonstration is part of test there, so ``D`` is stored as ``T``.
VERIFICATION_METHODS: tuple[str, ...] = ("T", "A", "R", "I")

#: Verification stages: the review that closes the requirement, or in-orbit verification.
VERIFICATION_STAGES: tuple[str, ...] = ("PDR", "CDR", "QR", "AR", "IOV")

#: Verification levels: the product level the requirement is verified at.
VERIFICATION_LEVELS: tuple[str, ...] = ("mission", "segment", "system", "subsystem", "unit")

#: Threshold operators. ``in_range`` takes ``{"min", "max"}``; ``before``/``after`` take an ISO date.
THRESHOLD_OPS: tuple[str, ...] = ("<=", ">=", "<", ">", "==", "in_range", "before", "after", "exists")

#: Priorities: 1 mandatory (mission or licence fails without it), 2 full performance, 3 goal.
PRIORITIES: tuple[int, ...] = (1, 2, 3)


def normalise_method(method: str | None) -> str | None:
    """``D`` (demonstration) is a test in ECSS-E-ST-10-02C; blank is None."""
    if method is None:
        return None
    m = str(method).strip()
    if not m:
        return None
    words = {"test": "T", "testing": "T", "demonstration": "T", "analysis": "A", "similarity": "A",
             "review": "R", "review of design": "R", "inspection": "I"}
    m = words.get(m.lower(), m.upper())
    return "T" if m == "D" else m


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
        description="Comparison operator: '<=', '>=', '<', '>', '==', 'in_range', 'before', 'after', 'exists'",
    )
    threshold_value: str | None = Field(
        default=None,
        description="JSON-encoded threshold value, e.g. '100' or '{\"min\": 100, \"max\": 200}'",
    )
    verification_method: str | None = Field(
        default=None, description="A (analysis), T (test), I (inspection), R (review), D (demonstration)"
    )
    verification_phase: str | None = Field(
        default=None, description="Verification stage: PDR, CDR, QR, AR or IOV (in-orbit)"
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
