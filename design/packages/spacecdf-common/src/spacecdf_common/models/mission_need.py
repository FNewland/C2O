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

from pydantic import BaseModel, Field, model_validator


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
    AFFECTED = "affected"         # affected party with no role in the mission (wave 3, 3.S3)


class StakeholderCategory(str, Enum):
    """Why the stakeholder matters to the design (wave 3, 3.S3). The categories are kept apart on
    purpose: a body that decides is not consulted like a beneficiary, and a rights-holder is not
    an affected party. One stakeholder may sit in two categories (``categories``)."""
    DECISION_AUTHORITY = "decision_authority"   # decides go / no-go, grants a licence, accepts for flight
    BENEFICIARY = "beneficiary"                 # uses what the mission delivers
    AFFECTED_PARTY = "affected_party"           # bears an effect without using the mission
    RIGHTS_HOLDER = "rights_holder"             # holds rights over the lands, data or knowledge concerned
    NON_HUMAN = "non_human"                     # the orbital environment, ecosystems, future users


#: words of a free-text category (the v2 baseline writes "decision authority / rights-holder")
_CATEGORY_WORDS = (("decision", "decision_authority"), ("beneficiar", "beneficiary"), ("affected", "affected_party"),
                   ("rights", "rights_holder"), ("non-human", "non_human"), ("non human", "non_human"),
                   ("environment", "non_human"))


def parse_categories(raw: Any) -> list[str]:
    """Category ids from an id, a list or the baseline's free text, in the order given."""
    items = raw if isinstance(raw, (list, tuple)) else str(raw or "").replace(",", "/").split("/")
    valid = {c.value for c in StakeholderCategory}
    out: list[str] = []
    for it in items:
        s = str(getattr(it, "value", it) or "").strip().lower()
        if not s:
            continue
        cid = s.replace(" ", "_").replace("-", "_") if s.replace(" ", "_").replace("-", "_") in valid else None
        if cid is None:
            cid = next((c for w, c in _CATEGORY_WORDS if w in s), None)
        if cid and cid not in out:
            out.append(cid)
    return out


class Stakeholder(BaseModel):
    """A person, group, or organisation with a stake in the mission."""
    id: str = ""
    name: str = Field(description="e.g. 'ESA Earth Observation Programme', 'Farmers in Sub-Saharan Africa'")
    role: StakeholderRole = StakeholderRole.USER
    needs: list[str] = Field(default_factory=list, description="What this stakeholder needs from the mission")
    constraints: list[str] = Field(default_factory=list, description="Constraints this stakeholder imposes")
    priority: str = Field(default="primary", description="primary / secondary / advisory")
    # wave 3 (3.S3): the register of the systems-engineering V
    category: str = Field(default="", description="primary StakeholderCategory id ('' = not yet classified)")
    categories: list[str] = Field(default_factory=list, description="every StakeholderCategory id that applies")
    authority: str = Field(default="", description="what this stakeholder decides or controls")
    engagement: str = Field(default="", description="how the team engages it: inform, consult, involve, collaborate, co-decide …")
    need_ids: list[str] = Field(default_factory=list, description="stakeholder needs (SN-…) this stakeholder holds")
    note: str = ""
    consent_status: str = Field(default="", description="for a decision authority over lands or data: where consent stands")

    @model_validator(mode="before")
    @classmethod
    def _tolerant(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        role = d.get("role")
        if role is not None and str(getattr(role, "value", role)) not in {r.value for r in StakeholderRole}:
            d["role"] = "user"
        cats = parse_categories(d.get("categories") or d.get("category"))
        d["categories"] = cats
        d["category"] = cats[0] if cats else ""
        return d


class StakeholderNeed(BaseModel):
    """One stakeholder need (SN-…), the top row of the requirement tree (wave 3, 3.S3)."""
    id: str
    text: str = ""
    stakeholder_ids: list[str] = Field(default_factory=list)
    stakeholder: str = Field(default="", description="the holder as named in the source")
    role: str = ""
    traces_to: list[str] = Field(default_factory=list, description="requirement codes that answer it")


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
    AERIAL_AIRCRAFT = "aerial_aircraft"       # Crewed aircraft
    GROUND_SENSOR = "ground_sensor"           # In-situ ground sensors
    GROUND_NETWORK = "ground_network"         # Network of ground stations
    HYBRID = "hybrid"                         # Combination of modalities
    OTHER = "other"


class AlternativeDecision(str, Enum):
    UNDER_REVIEW = "under_review"
    SELECTED = "selected"
    REJECTED = "rejected"
    DEFERRED = "deferred"


# Mission-trade categories (services/mission_trade.py) → AlternativeType. The wizard sends
# the trade's own category; unknown values fall back to OTHER instead of rejecting the
# whole Mission Need (walkthrough finding: alternatives were lost on save).
_TRADE_CATEGORY_TYPES = {
    "existing_satellite": "space_existing", "commercial_tasking": "space_existing",
    "aerial": "aerial_aircraft", "drone": "aerial_drone", "uav": "aerial_drone",
    "ground": "ground_network", "ground_sensor": "ground_sensor", "ground_network": "ground_network",
    "new_satellite": "space_dedicated", "constellation": "space_constellation",
    "hosted": "space_hosted", "hybrid": "hybrid",
}


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

    @model_validator(mode="before")
    @classmethod
    def _accept_trade_category(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        raw = d.get("type") or d.get("category")
        d.pop("category", None)
        if raw is not None:
            v = str(getattr(raw, "value", raw)).strip().lower()
            valid = {t.value for t in AlternativeType}
            d["type"] = v if v in valid else _TRADE_CATEGORY_TYPES.get(v, "other")
        dec = d.get("decision")
        if dec is not None and str(getattr(dec, "value", dec)) not in {x.value for x in AlternativeDecision}:
            d["decision"] = "under_review"
        if not d.get("id") and d.get("name"):
            d["id"] = str(d["name"])
        return d


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
    stakeholder_needs: list[StakeholderNeed] = Field(default_factory=list,
                                                     description="needs by SN id (wave 3, 3.S3)")
    governance_notes: dict[str, str] = Field(default_factory=dict,
                                             description="decision authority, data governance, legal status, limits")

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

    @model_validator(mode="before")
    @classmethod
    def _accept_alternatives_alias(cls, data: Any) -> Any:
        """The frontend store calls the list ``alternatives``; the model ``alternatives_considered``.

        Before Nov 2026 the wizard sent ``alternatives`` and pydantic dropped it silently
        (walkthrough top problem 3). Both spellings are now accepted.
        """
        if isinstance(data, dict) and data.get("alternatives") and not data.get("alternatives_considered"):
            data = {**data, "alternatives_considered": data["alternatives"]}
        if isinstance(data, dict) and "alternatives" in data:
            data = {k: v for k, v in data.items() if k != "alternatives"}
        return data

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
