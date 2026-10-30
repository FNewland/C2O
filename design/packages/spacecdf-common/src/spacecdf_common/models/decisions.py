"""SpaceCDF — Decision Engine.

The 46-decision lifecycle framework. Each design step is a decision
with question, alternatives, consequences, and rationale — not a form
field. Gate review evidence accumulates as decisions are made.

Decision maturity: open → explored → traded → decided → baselined → verified → validated
Decision type: a (pick-and-go) | b (trade study) | c (new design work)
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DecisionMaturity(str, Enum):
    OPEN = "open"                 # Not yet addressed
    EXPLORED = "explored"         # Alternatives identified, not evaluated
    TRADED = "traded"             # Trade study complete, recommendation made
    DECIDED = "decided"           # Selected by decision authority
    BASELINED = "baselined"       # Under configuration control
    VERIFIED = "verified"         # Implementation verified
    VALIDATED = "validated"       # Stakeholder confirms it met the need


class DecisionType(str, Enum):
    PICK_AND_GO = "a"             # Obvious choice from heritage/standards
    TRADE_STUDY = "b"             # Multiple viable options — need structured trade
    NEW_DESIGN = "c"              # No obvious solution — requires design work


class DecisionPhase(str, Enum):
    PRE_PHASE_A = "0"
    PHASE_A = "A"
    PHASE_B = "B"
    PHASE_C = "C"
    PHASE_D = "D"
    PHASE_E = "E"
    PHASE_F = "F"


class DecisionAlternative(BaseModel):
    """An alternative in a decision trade."""
    id: str = ""
    name: str = ""
    description: str = ""
    scores: dict[str, float] = Field(default_factory=dict)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    downstream_impacts: list[str] = Field(default_factory=list)
    heritage: str = ""
    trl: int = 9
    cost_impact_keur: float = 0.0
    mass_impact_kg: float = 0.0


class MissionDecision(BaseModel):
    """A single decision in the 46-decision lifecycle framework."""
    id: str = Field(description="e.g. '0.4' for orbit selection, 'B.3/EPS' for battery selection")
    title: str = ""
    question: str = Field(description="What question is being answered?")
    phase: DecisionPhase = DecisionPhase.PRE_PHASE_A
    decision_type: DecisionType = DecisionType.TRADE_STUDY
    category: str = Field(default="", description="mission / architecture / subsystem / component / verification")

    # What drives the answer
    driven_by: list[str] = Field(default_factory=list, description="Objective IDs, requirement IDs, or higher decision IDs")
    constraints: list[str] = Field(default_factory=list, description="Hard constraints on this decision")

    # Alternatives
    alternatives: list[DecisionAlternative] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)

    # Decision
    selected_alternative_id: str | None = None
    rationale: str = ""
    decided_by: str = ""
    decided_at: datetime | None = None

    # Maturity
    maturity: DecisionMaturity = DecisionMaturity.OPEN

    # Downstream
    downstream_decisions: list[str] = Field(default_factory=list, description="Decision IDs this constrains")
    affected_parameters: list[str] = Field(default_factory=list)
    gate_evidence: list[str] = Field(default_factory=list, description="Gate criterion IDs this provides evidence for")


# ---------------------------------------------------------------------------
# The 46-decision catalogue
# ---------------------------------------------------------------------------

def get_decision_catalogue() -> list[MissionDecision]:
    """Return the full 46-decision catalogue, pre-populated with questions
    and dependencies. Engineers fill in alternatives and decisions."""
    return [
        # === Phase 0 / Pre-Phase A ===
        MissionDecision(id="0.1", title="Mission justification", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.PICK_AND_GO,
            question="Why does this mission need to exist? What need does it serve?",
            category="mission", gate_evidence=["MCR-EC-01"],
            downstream_decisions=["0.2", "0.3", "0.4"]),
        MissionDecision(id="0.2", title="Stakeholder identification", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Who are the stakeholders, what do they need, and what are their constraints?",
            category="mission", driven_by=["0.1"], gate_evidence=["MCR-EC-02"],
            downstream_decisions=["0.3"]),
        MissionDecision(id="0.3", title="Objective prioritisation", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Which objectives are primary (must achieve) vs secondary (should achieve) vs constraints? What are needs vs wants?",
            category="mission", driven_by=["0.1", "0.2"], gate_evidence=["MCR-EC-03"],
            downstream_decisions=["0.4", "0.5", "0.6"]),
        MissionDecision(id="0.4", title="Solution modality (AoA)", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Is space the right answer? Have we considered drones, ground sensors, existing satellite data?",
            category="mission", driven_by=["0.3"], gate_evidence=["MCR-EC-04", "MCR-EC-05"],
            downstream_decisions=["0.5", "0.6"],
            evaluation_criteria=["Coverage", "Revisit", "Resolution", "Latency", "Cost", "Sustainability"]),
        MissionDecision(id="0.5", title="Mission concept(s)", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="What architecture concepts are feasible? Single sat, constellation, hosted payload?",
            category="architecture", driven_by=["0.3", "0.4"],
            downstream_decisions=["0.6", "0.7", "0.8"],
            evaluation_criteria=["Performance", "Cost", "Risk", "Schedule", "Heritage"]),
        MissionDecision(id="0.6", title="Orbit selection", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="What orbit class? LEO/MEO/GEO/Lunar? SSO/polar/equatorial? What altitude?",
            category="architecture", driven_by=["0.3", "0.5"],
            downstream_decisions=["0.7", "0.8", "A.5"],
            affected_parameters=["orbit.altitude_km", "orbit.inclination_deg", "orbit.period_s"],
            evaluation_criteria=["Coverage", "Revisit", "Launch cost", "Radiation", "Debris compliance", "Ground station access"]),
        MissionDecision(id="0.7", title="Ground segment concept", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Own stations, commercial network (KSAT, AWS), or DSN? How many stations? What latency?",
            category="architecture", driven_by=["0.6"],
            downstream_decisions=["B.9"],
            affected_parameters=["orbit.contact_time_per_day_s", "link.downlink_rate_bps", "cost.operations_keur"]),
        MissionDecision(id="0.8", title="ConOps definition", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="What are the mission modes? How do we operate? What level of autonomy?",
            category="mission", driven_by=["0.5", "0.6", "0.7"], gate_evidence=["MCR-EC-06"],
            downstream_decisions=["A.1"],
            affected_parameters=["power.total_sunlight_w", "power.total_eclipse_w"]),
        MissionDecision(id="0.9", title="Technology assessment", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="What's heritage (TRL 7-9)? What needs development (TRL 3-6)? What are the technology gaps?",
            category="mission", driven_by=["0.5"],
            downstream_decisions=["A.4"],
            gate_evidence=["MCR-EC-09"]),
        MissionDecision(id="0.10", title="Cost/schedule feasibility", phase=DecisionPhase.PRE_PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Can we afford this mission in the required timeline?",
            category="mission", driven_by=["0.5", "0.6", "0.7", "0.9"],
            gate_evidence=["MCR-EC-08"],
            affected_parameters=["cost.total_meur"]),

        # === Phase A ===
        MissionDecision(id="A.1", title="Level 1 requirements", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.NEW_DESIGN,
            question="What are the system-level 'shall' requirements with measures of performance?",
            category="architecture", driven_by=["0.3", "0.8"],
            downstream_decisions=["A.2", "A.3"],
            gate_evidence=["SRR-EC-01", "SRR-EC-02"]),
        MissionDecision(id="A.2", title="System architecture", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="How do we decompose the system? What is the product breakdown structure?",
            category="architecture", driven_by=["A.1"],
            downstream_decisions=["A.4", "A.5", "B.1"],
            evaluation_criteria=["Minimise interfaces", "Maximise internal synergy", "Heritage reuse", "Testability"]),
        MissionDecision(id="A.3", title="Functional decomposition", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.NEW_DESIGN,
            question="How do functions flow? What are the functional interfaces? How complex are the functional chains?",
            category="architecture", driven_by=["A.1", "0.8"],
            downstream_decisions=["B.2"]),
        MissionDecision(id="A.4", title="Payload selection", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Build, buy, or reuse the instrument? How well does it fit the need? What's the gap?",
            category="subsystem", driven_by=["A.1", "0.9"],
            downstream_decisions=["B.3/PL"],
            evaluation_criteria=["Performance fit", "Mass", "Power", "Cost", "TRL", "Heritage", "Lead time"]),
        MissionDecision(id="A.5", title="Bus selection", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Existing platform or new development? Which bus vendor/heritage?",
            category="architecture", driven_by=["A.2", "0.6"],
            downstream_decisions=["B.1"]),
        MissionDecision(id="A.6", title="Preliminary budgets", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Mass, power, data, ΔV allocations with margins? How much margin at this phase?",
            category="architecture", driven_by=["A.2", "A.4", "A.5"],
            gate_evidence=["SRR-EC-06"],
            affected_parameters=["systems.mass_margin_percent", "systems.power_margin_percent"]),
        MissionDecision(id="A.7", title="Acquisition strategy", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="Make/buy/reuse for each element? What's the procurement approach?",
            category="mission", driven_by=["A.2", "0.9"]),
        MissionDecision(id="A.8", title="Preliminary hazard identification", phase=DecisionPhase.PHASE_A, decision_type=DecisionType.TRADE_STUDY,
            question="What can go wrong? What are the single-point failures? Where is the risk?",
            category="mission", driven_by=["A.2"]),

        # === Phase B (subset — full set has 14) ===
        MissionDecision(id="B.1", title="Physical architecture (product tree)", phase=DecisionPhase.PHASE_B, decision_type=DecisionType.NEW_DESIGN,
            question="What are we physically building? Equipment list?",
            category="architecture", driven_by=["A.2", "A.5"]),
        MissionDecision(id="B.3", title="Component selection", phase=DecisionPhase.PHASE_B, decision_type=DecisionType.TRADE_STUDY,
            question="For each subsystem: which specific component? What's the fit vs the requirement? What are the gaps?",
            category="component", driven_by=["B.2"],
            evaluation_criteria=["Requirement fit", "Mass", "Power", "Cost", "TRL", "Heritage", "Interfaces", "Lead time", "Export control"]),
        MissionDecision(id="B.4", title="Margin allocation", phase=DecisionPhase.PHASE_B, decision_type=DecisionType.TRADE_STUDY,
            question="What margins at PDR? (ECSS: 5-20% depending on TRL and phase)",
            category="architecture", driven_by=["A.6"],
            gate_evidence=["PDR-EC-03"]),
        MissionDecision(id="B.5", title="Redundancy architecture", phase=DecisionPhase.PHASE_B, decision_type=DecisionType.TRADE_STUDY,
            question="Where to add redundancy? Which SPFs are unacceptable? (FMECA-driven)",
            category="architecture", driven_by=["A.8"],
            gate_evidence=["PDR-EC-05"],
            evaluation_criteria=["Reliability gain", "Mass cost", "Power cost", "Complexity", "Heritage"]),
        MissionDecision(id="B.6", title="Interface definition freeze", phase=DecisionPhase.PHASE_B, decision_type=DecisionType.NEW_DESIGN,
            question="Are all interfaces between subsystems defined and agreed? ICDs baselined?",
            category="architecture", driven_by=["B.1", "B.3"]),
        MissionDecision(id="B.7", title="AIT approach", phase=DecisionPhase.PHASE_B, decision_type=DecisionType.TRADE_STUDY,
            question="Protoflight, prototype, or digital twin? What test philosophy?",
            category="verification", driven_by=["B.1"]),
        MissionDecision(id="B.13", title="Verification approach", phase=DecisionPhase.PHASE_B, decision_type=DecisionType.TRADE_STUDY,
            question="For each requirement: test, analysis, inspection, or demonstration? What are the implications?",
            category="verification", driven_by=["A.1", "B.3"],
            gate_evidence=["SRR-EC-07"]),
    ]


class DecisionEngine(BaseModel):
    """Manages the lifecycle of all 46 design decisions.

    Tracks maturity, accumulates gate evidence, and identifies
    which decisions are active for the current phase.
    """
    decisions: list[MissionDecision] = Field(default_factory=get_decision_catalogue)
    current_phase: DecisionPhase = DecisionPhase.PRE_PHASE_A

    def get_decision(self, decision_id: str) -> MissionDecision | None:
        for d in self.decisions:
            if d.id == decision_id:
                return d
        return None

    def get_phase_decisions(self, phase: DecisionPhase | None = None) -> list[MissionDecision]:
        p = phase or self.current_phase
        return [d for d in self.decisions if d.phase == p]

    def get_active_decisions(self) -> list[MissionDecision]:
        """Decisions that should be addressed now (current phase, not yet decided)."""
        return [d for d in self.get_phase_decisions()
                if d.maturity.value in ("open", "explored", "traded")]

    def get_blocked_decisions(self) -> list[MissionDecision]:
        """Decisions whose prerequisites haven't been decided yet."""
        decided_ids = {d.id for d in self.decisions if d.maturity.value not in ("open", "explored")}
        blocked = []
        for d in self.get_active_decisions():
            for dep in d.driven_by:
                if dep not in decided_ids:
                    blocked.append(d)
                    break
        return blocked

    @property
    def maturity_summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in self.decisions:
            counts[d.maturity.value] = counts.get(d.maturity.value, 0) + 1
        return counts

    @property
    def phase_readiness(self) -> dict[str, Any]:
        """How ready is the current phase for its gate review?"""
        phase_decisions = self.get_phase_decisions()
        total = len(phase_decisions)
        decided = sum(1 for d in phase_decisions if d.maturity.value not in ("open", "explored"))
        return {
            "phase": self.current_phase.value,
            "total_decisions": total,
            "decided": decided,
            "remaining": total - decided,
            "readiness_percent": (decided / max(total, 1)) * 100,
        }

    def gate_evidence_coverage(self, gate_criteria: list[str]) -> dict[str, Any]:
        """How many gate criteria have supporting decisions?"""
        covered = set()
        for d in self.decisions:
            if d.maturity.value not in ("open", "explored"):
                covered.update(d.gate_evidence)
        total = len(gate_criteria)
        met = len(covered & set(gate_criteria))
        return {
            "total_criteria": total,
            "covered": met,
            "uncovered": total - met,
            "coverage_percent": (met / max(total, 1)) * 100,
            "uncovered_criteria": list(set(gate_criteria) - covered),
        }
