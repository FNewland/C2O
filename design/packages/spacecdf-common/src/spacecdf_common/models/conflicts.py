"""SpaceCDF — Multi-level conflict detection, decision records, and change impact.

Level 1: Stakeholder conflicts (funder vs PI vs operator)
Level 2: Objective conflicts (coverage vs GSD vs cost)
Level 3: Requirement conflicts (pointing vs mass, DoD vs mass)
Level 4: Design conflicts (parametric margin violations) — original model
Level 5: Interface conflicts (spatial/thermal/electrical)

Also provides:
  - Structured decision records (NASA SEH Process 17: Decision Analysis)
  - Change impact propagation (objective change → requirement cascade)
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConflictSeverity(str, Enum):
    CRITICAL = "critical"  # Design cannot proceed without resolution
    MAJOR = "major"        # Requires trade-off decision from team
    MINOR = "minor"        # Flag for awareness, may resolve with iteration


class ConflictResolution(BaseModel):
    """A suggested way to resolve a cross-domain conflict."""

    description: str
    position_responsible: str = Field(description="Position ID that should act")
    parameter_to_change: str = Field(description="Parameter ID to adjust")
    suggested_direction: Literal["increase", "decrease", "replace", "relax", "accept"]
    estimated_impact: str = Field(default="", description="What changes if this resolution is adopted")


class CrossDomainConflict(BaseModel):
    """A detected conflict between two engineering domains."""

    id: str = Field(description="Unique conflict identifier, e.g. 'CONF-DATA-001'")
    severity: ConflictSeverity
    title: str = Field(description="Short title, e.g. 'Data Rate vs Downlink Capacity'")
    description: str = Field(description="Detailed explanation of the conflict")
    domain_a: str = Field(description="First engineering domain involved")
    domain_b: str = Field(description="Second engineering domain involved")
    position_a: str = Field(description="Position ID for domain A, e.g. 'payload_lead'")
    position_b: str = Field(description="Position ID for domain B, e.g. 'comms_engineer'")
    param_a: str = Field(description="Parameter ID from domain A")
    param_b: str = Field(description="Parameter ID from domain B")
    value_a_str: str = Field(default="", description="Human-readable value from A")
    value_b_str: str = Field(default="", description="Human-readable value from B")
    resolutions: list[ConflictResolution] = Field(default_factory=list)


class ConflictReport(BaseModel):
    """Summary of all detected conflicts for a design iteration."""

    conflicts: list[CrossDomainConflict] = Field(default_factory=list)

    @property
    def total_critical(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == ConflictSeverity.CRITICAL)

    @property
    def total_major(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == ConflictSeverity.MAJOR)

    @property
    def total_minor(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == ConflictSeverity.MINOR)

    @property
    def has_blockers(self) -> bool:
        return self.total_critical > 0


# ---------------------------------------------------------------------------
# Multi-level conflict model (extends the original Level 4 model above)
# ---------------------------------------------------------------------------

class ConflictLevel(str, Enum):
    STAKEHOLDER = "stakeholder"       # Level 1: competing stakeholder needs
    OBJECTIVE = "objective"           # Level 2: competing objectives
    REQUIREMENT = "requirement"       # Level 3: conflicting requirements
    DESIGN = "design"                 # Level 4: parametric margin violations
    INTERFACE = "interface"           # Level 5: subsystem interface conflicts


class ConflictStatus(str, Enum):
    OPEN = "open"
    UNDER_DISCUSSION = "under_discussion"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"


class MultiLevelConflict(BaseModel):
    """A conflict at any V-model level — generalises CrossDomainConflict."""
    id: str = ""
    level: ConflictLevel = ConflictLevel.DESIGN
    severity: ConflictSeverity = ConflictSeverity.MAJOR
    status: ConflictStatus = ConflictStatus.OPEN
    title: str = ""
    description: str = ""
    element_a: str = ""
    element_a_type: str = ""
    element_a_position: str = ""
    element_b: str = ""
    element_b_type: str = ""
    element_b_position: str = ""
    resolution_options: list[str] = Field(default_factory=list)
    selected_resolution: str = ""
    resolution_rationale: str = ""
    affected_parameters: list[str] = Field(default_factory=list)
    affected_subsystems: list[str] = Field(default_factory=list)
    detected_by: str = Field(default="auto")
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Decision Record (NASA SEH Process 17)
# ---------------------------------------------------------------------------

class DecisionCriterion(BaseModel):
    name: str = ""
    weight: float = 1.0
    unit: str = ""


class DecisionAlternative(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    scores: dict[str, float] = Field(default_factory=dict)
    weighted_total: float = 0.0
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class DecisionRecord(BaseModel):
    """Structured record of a design decision — captures WHY a choice was made."""
    id: str = ""
    title: str = ""
    decision_statement: str = ""
    level: str = Field(default="architecture")
    criteria: list[DecisionCriterion] = Field(default_factory=list)
    alternatives: list[DecisionAlternative] = Field(default_factory=list)
    selected_alternative_id: str | None = None
    rationale: str = ""
    decision_authority: str = ""
    related_objective_ids: list[str] = Field(default_factory=list)
    related_requirement_ids: list[str] = Field(default_factory=list)
    affected_parameters: list[str] = Field(default_factory=list)
    status: str = Field(default="open")
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Change Impact Propagation
# ---------------------------------------------------------------------------

class ChangeImpact(BaseModel):
    """Cascading impact of changing a higher-level V-model element."""
    source_type: str = ""
    source_id: str = ""
    change_description: str = ""
    affected_requirements: list[str] = Field(default_factory=list)
    affected_parameters: list[str] = Field(default_factory=list)
    affected_subsystems: list[str] = Field(default_factory=list)
    affected_functions: list[str] = Field(default_factory=list)
    cascade_depth: int = 0
    invalidates_baseline: bool = False
    requires_reconvergence: bool = True
    effort_estimate: str = ""


def assess_change_impact(
    source_type: str,
    source_id: str,
    change_description: str,
    requirements: list[dict] | None = None,
    functions: list[dict] | None = None,
    objectives: list[dict] | None = None,
) -> ChangeImpact:
    """Trace the cascading impact of a change to a higher-level element."""
    impact = ChangeImpact(
        source_type=source_type,
        source_id=source_id,
        change_description=change_description,
    )

    requirements = requirements or []
    functions = functions or []

    if source_type == "objective":
        for req in requirements:
            obj_ids = req.get("objective_ids", []) or req.get("traced_from_objectives", []) or []
            if source_id in obj_ids:
                impact.affected_requirements.append(req.get("id", ""))
                for pid in req.get("parameter_ids", []):
                    impact.affected_parameters.append(pid)
                    domain = pid.split(".")[0] if "." in pid else ""
                    if domain and domain not in impact.affected_subsystems:
                        impact.affected_subsystems.append(domain)

        for func in functions:
            if source_id in (func.get("objective_ids", []) or []):
                impact.affected_functions.append(func.get("id", ""))

    elif source_type == "requirement":
        for req in requirements:
            if req.get("id") == source_id:
                for pid in req.get("parameter_ids", []):
                    impact.affected_parameters.append(pid)
                    domain = pid.split(".")[0] if "." in pid else ""
                    if domain and domain not in impact.affected_subsystems:
                        impact.affected_subsystems.append(domain)

    impact.cascade_depth = (
        (1 if impact.affected_requirements else 0) +
        (1 if impact.affected_parameters else 0) +
        (1 if impact.affected_subsystems else 0)
    )
    impact.invalidates_baseline = impact.cascade_depth >= 2
    impact.effort_estimate = (
        "redesign" if impact.cascade_depth >= 3 else
        "high" if len(impact.affected_subsystems) >= 3 else
        "medium" if len(impact.affected_parameters) >= 2 else "low"
    )
    return impact
