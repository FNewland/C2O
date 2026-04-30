"""SpaceCDF — Mission Need, Objectives, and Alternatives models.

Implements the top of the System-V: stakeholder needs → objectives →
concept exploration → mission definition. This layer sits ABOVE
MissionRequirements and drives the entire design rationale.

Aligned with:
  - NASA SEH Process 1: Stakeholder Expectations Definition
  - NASA Pre-Phase A: "Capture and baseline expectations as NGOs"
  - ECSS-M-ST-10C Rev.1: Mission Definition (Phase 0)
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Stakeholder model
# ---------------------------------------------------------------------------

class StakeholderRole(str, Enum):
    SPONSOR = "sponsor"           # Funding agency / customer
    USER = "user"                 # End user of mission data/service
    OPERATOR = "operator"         # Mission operations team
    REGULATOR = "regulator"       # Licensing, spectrum, debris compliance
    SCIENCE_PI = "science_pi"     # Principal Investigator
    PUBLIC = "public"             # General public / society
    PARTNER = "partner"           # International or commercial partner
    LAUNCH_PROVIDER = "launch_provider"


class Stakeholder(BaseModel):
    """A person, group, or organisation with a stake in the mission."""
    id: str = ""
    name: str = Field(description="e.g. 'ESA Earth Observation Programme', 'Farmers in Sub-Saharan Africa'")
    role: StakeholderRole = StakeholderRole.USER
    needs: list[str] = Field(default_factory=list, description="What this stakeholder needs from the mission")
    constraints: list[str] = Field(default_factory=list, description="Constraints this stakeholder imposes")
    priority: str = Field(default="primary", description="primary / secondary / advisory")


# ---------------------------------------------------------------------------
# Objective model
# ---------------------------------------------------------------------------

class ObjectivePriority(str, Enum):
    PRIMARY = "primary"           # Must achieve — mission fails without this
    SECONDARY = "secondary"       # Should achieve — enhances mission value
    TERTIARY = "tertiary"         # Nice to have — opportunistic
    CONSTRAINT = "constraint"     # Hard boundary that cannot be violated


class ObjectiveType(str, Enum):
    PERFORMANCE = "performance"   # Measurable capability (e.g. "10m GSD")
    COVERAGE = "coverage"         # Geographic/temporal coverage
    TIMELINESS = "timeliness"     # Data latency requirements
    COST = "cost"                 # Cost ceiling
    SCHEDULE = "schedule"         # Timeline constraint
    SUSTAINABILITY = "sustainability"  # Debris, environment
    CAPACITY_BUILDING = "capacity_building"  # Educational, national capability


class Objective(BaseModel):
    """A mission objective derived from stakeholder needs."""
    id: str = ""
    text: str = Field(description="Clear, measurable objective statement")
    priority: ObjectivePriority = ObjectivePriority.PRIMARY
    type: ObjectiveType = ObjectiveType.PERFORMANCE
    measurable_criterion: str = Field(default="", description="How do we measure success? e.g. 'GSD <= 10m at nadir'")
    stakeholder_ids: list[str] = Field(default_factory=list, description="Which stakeholders this serves")
    traced_to_requirements: list[str] = Field(default_factory=list, description="Requirement IDs that implement this")
    status: str = Field(default="proposed", description="proposed / accepted / deferred / rejected")


# ---------------------------------------------------------------------------
# Alternative / concept model
# ---------------------------------------------------------------------------

class AlternativeType(str, Enum):
    SPACE_DEDICATED = "space_dedicated"       # New dedicated satellite
    SPACE_HOSTED = "space_hosted"             # Hosted payload on existing platform
    SPACE_EXISTING = "space_existing"         # Use existing satellite data (Copernicus, Landsat, commercial)
    SPACE_CONSTELLATION = "space_constellation"
    AERIAL_DRONE = "aerial_drone"             # UAV / drone
    AERIAL_AIRCRAFT = "aerial_aircraft"       # Manned aircraft
    GROUND_SENSOR = "ground_sensor"           # In-situ ground sensors
    GROUND_NETWORK = "ground_network"         # Network of ground stations
    HYBRID = "hybrid"                         # Combination of modalities
    OTHER = "other"


class AlternativeDecision(str, Enum):
    UNDER_REVIEW = "under_review"
    SELECTED = "selected"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class Alternative(BaseModel):
    """A candidate solution to the mission need — may or may not involve space."""
    id: str = ""
    name: str = Field(description="e.g. 'Dedicated 6U CubeSat', 'Use Copernicus Sentinel-2 data'")
    type: AlternativeType = AlternativeType.SPACE_DEDICATED
    description: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    feasibility_score: float = Field(default=0.0, description="0-1 feasibility assessment")
    cost_estimate_meur: float | None = None
    schedule_estimate_months: int | None = None
    objectives_met: list[str] = Field(default_factory=list, description="Which objective IDs this can satisfy")
    decision: AlternativeDecision = AlternativeDecision.UNDER_REVIEW
    decision_rationale: str = ""


# ---------------------------------------------------------------------------
# Mission Need — the top of the V
# ---------------------------------------------------------------------------

class MissionNeed(BaseModel):
    """The top of the System-V: why does this mission exist?

    This model captures everything that should be established BEFORE
    specifying an orbit altitude or payload mass. It answers:
    - What problem are we solving?
    - For whom?
    - What does success look like?
    - Is space the right answer?
    - What are the alternatives?
    """
    # Problem definition
    problem_statement: str = Field(default="", description="What problem are we trying to solve? In plain language.")
    operational_context: str = Field(default="", description="When, where, and how will the solution be used?")

    # Stakeholders
    stakeholders: list[Stakeholder] = Field(default_factory=list)

    # Objectives (derived from stakeholder needs)
    objectives: list[Objective] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list, description="Top-level: how do we know the mission succeeded?")

    # Concept exploration
    alternatives_considered: list[Alternative] = Field(default_factory=list)
    selected_alternative_id: str | None = Field(default=None, description="ID of the selected alternative")
    selection_rationale: str = Field(default="", description="Why was this alternative chosen over others?")

    # Concept of Operations (summary — detailed ConOps is a separate document)
    conops_summary: str = Field(default="", description="How will the system be operated? Key operational modes, ground segment concept, data flow.")

    # Metadata
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phase: str = Field(default="pre_phase_a", description="Current study phase")

    @property
    def has_non_space_alternative(self) -> bool:
        """Check if at least one non-space alternative has been considered."""
        non_space_types = {AlternativeType.AERIAL_DRONE, AlternativeType.AERIAL_AIRCRAFT,
                          AlternativeType.GROUND_SENSOR, AlternativeType.GROUND_NETWORK,
                          AlternativeType.SPACE_EXISTING}
        return any(a.type in non_space_types for a in self.alternatives_considered)

    @property
    def selected_alternative(self) -> Alternative | None:
        if not self.selected_alternative_id:
            return None
        for a in self.alternatives_considered:
            if a.id == self.selected_alternative_id:
                return a
        return None

    @property
    def is_space_mission(self) -> bool:
        """Whether the selected concept is a space-based solution."""
        sel = self.selected_alternative
        if sel is None:
            return True  # Default assumption if nothing selected
        return sel.type in {AlternativeType.SPACE_DEDICATED, AlternativeType.SPACE_HOSTED,
                            AlternativeType.SPACE_CONSTELLATION, AlternativeType.HYBRID}


# ---------------------------------------------------------------------------
# Position answer model (for key_questions in positions.yaml)
# ---------------------------------------------------------------------------

class PositionAnswer(BaseModel):
    """An engineer's response to a key question for their position."""
    question_id: str = Field(description="Matches the question ID in positions.yaml")
    position_id: str = Field(description="Which position is answering")
    answer_text: str = Field(default="", description="The engineer's answer")
    confidence: str = Field(default="medium", description="high / medium / low")
    evidence: list[str] = Field(default_factory=list, description="Parameter IDs or references supporting the answer")
    impacts: list[str] = Field(default_factory=list, description="Impacts on other positions / parameters")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    display_name: str = ""
