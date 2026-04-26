"""SpaceCDF — Cross-domain conflict data models.

Represents clashes between engineering domains where one subsystem's
needs conflict with another's constraints. Each conflict identifies
the two positions involved and suggests resolutions.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

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
