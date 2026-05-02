"""SpaceCDF — Session Guidance System.

Tells the user WHEN to start a session, WHAT TYPE, WHO should attend,
and WHAT to decide. Based on current study maturity and ESA CDF methodology.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionTemplate:
    """A template for a CDF session type."""
    session_type: str           # architecture / sizing / trade / review
    name: str
    duration_hours: float
    objective: str
    decisions_to_address: list[str]
    recommended_positions: list[str]
    agenda: list[str]
    pre_reads: list[str]
    outputs: list[str]


# ESA CDF-aligned session templates
SESSION_TEMPLATES: list[SessionTemplate] = [
    SessionTemplate(
        session_type="kickoff",
        name="Mission Definition Kickoff",
        duration_hours=2.0,
        objective="Establish mission need, stakeholders, objectives, and initial concepts",
        decisions_to_address=["0.1", "0.2", "0.3", "0.4"],
        recommended_positions=["systems_engineer", "mission_analyst", "payload_lead", "cost_engineer"],
        agenda=[
            "1. Problem statement presentation (15 min)",
            "2. Stakeholder identification and needs capture (20 min)",
            "3. Mission objectives definition and prioritisation (30 min)",
            "4. Alternatives brainstorming — including non-space options (20 min)",
            "5. Initial feasibility assessment (15 min)",
            "6. Action items and next session planning (10 min)",
        ],
        pre_reads=["Stakeholder needs document (if available)", "Similar mission survey"],
        outputs=["Baselined mission need", "Stakeholder register", "Objectives hierarchy", "Alternatives list"],
    ),
    SessionTemplate(
        session_type="architecture",
        name="Architecture Exploration",
        duration_hours=3.0,
        objective="Select orbit, mission concept, and ground segment architecture",
        decisions_to_address=["0.5", "0.6", "0.7", "0.8"],
        recommended_positions=["systems_engineer", "mission_analyst", "payload_lead", "power_engineer",
                               "comms_engineer", "propulsion_engineer", "cost_engineer"],
        agenda=[
            "1. Review orbit trade study results (20 min)",
            "2. Present mission class advisor recommendation (10 min)",
            "3. Orbit selection decision (20 min)",
            "4. Ground segment architecture trade (20 min)",
            "5. ConOps discussion — mission modes, data flow, operations (30 min)",
            "6. Preliminary budget allocations (20 min)",
            "7. Technology assessment and risk identification (15 min)",
            "8. Decision capture and action items (15 min)",
        ],
        pre_reads=["Orbit trade study report", "Ground segment trade study", "Mission class advisor output"],
        outputs=["Selected orbit", "Ground segment concept", "ConOps (4 modes minimum)", "Preliminary budgets"],
    ),
    SessionTemplate(
        session_type="sizing",
        name="Subsystem Sizing",
        duration_hours=2.0,
        objective="Run design convergence, review budgets, identify conflicts",
        decisions_to_address=["A.4", "A.5", "A.6"],
        recommended_positions=["systems_engineer", "power_engineer", "aocs_engineer", "thermal_engineer",
                               "comms_engineer", "propulsion_engineer", "structures_engineer"],
        agenda=[
            "1. Run design convergence loop (5 min — tool does this)",
            "2. Review mass budget — each subsystem presents allocation vs actual (20 min)",
            "3. Review power budget per ConOps mode (15 min)",
            "4. Review link budget and data throughput (10 min)",
            "5. Review pointing budget (10 min)",
            "6. Identify cross-domain conflicts (15 min)",
            "7. Each position answers key questions (20 min)",
            "8. Action items for conflict resolution (15 min)",
        ],
        pre_reads=["Current design dashboard", "Budget status"],
        outputs=["Converged design", "Budget closure status", "Conflict list", "Position Q&A responses"],
    ),
    SessionTemplate(
        session_type="component_selection",
        name="Component Selection",
        duration_hours=2.0,
        objective="Select COTS components for each subsystem with fit-gap analysis",
        decisions_to_address=["B.3"],
        recommended_positions=["systems_engineer", "power_engineer", "aocs_engineer",
                               "comms_engineer", "cost_engineer"],
        agenda=[
            "1. Review derived requirements per subsystem (10 min)",
            "2. EPS component selection: battery + EPS board + solar panels (20 min)",
            "3. AOCS component selection: star tracker + wheels + magnetorquers (20 min)",
            "4. Comms component selection: transceiver + antenna (15 min)",
            "5. OBC selection (10 min)",
            "6. Structure and deployer selection (10 min)",
            "7. Review BOM — total mass, cost, lead times, export control (15 min)",
            "8. Fit-gap review: any make-or-buy decisions needed? (10 min)",
        ],
        pre_reads=["Derived requirements per subsystem", "Component fit-gap analysis"],
        outputs=["Selected component list", "Bill of Materials", "Fit-gap report", "Make-or-buy decisions"],
    ),
    SessionTemplate(
        session_type="trade_study",
        name="Trade Study",
        duration_hours=1.0,
        objective="Resolve a specific design conflict or trade-off",
        decisions_to_address=[],  # Filled per study
        recommended_positions=["systems_engineer"],  # + affected domains
        agenda=[
            "1. Present the decision: what question are we answering? (5 min)",
            "2. Present alternatives with pros/cons (10 min)",
            "3. Evaluate against criteria (15 min)",
            "4. Discuss and deliberate (15 min)",
            "5. Decision and rationale capture (10 min)",
            "6. Impact assessment — what changes downstream? (5 min)",
        ],
        pre_reads=["Trade study briefing"],
        outputs=["Decision record with rationale"],
    ),
    SessionTemplate(
        session_type="gate_review",
        name="Gate Review Preparation",
        duration_hours=1.5,
        objective="Check readiness for the next lifecycle gate (MCR/SRR/PDR)",
        decisions_to_address=["gate"],
        recommended_positions=["systems_engineer", "mission_analyst", "cost_engineer"],
        agenda=[
            "1. Review gate exit criteria checklist (20 min)",
            "2. For each RED/AMBER criterion: what's missing? who's responsible? (30 min)",
            "3. Review engineering budgets — any mission requirements at risk? (15 min)",
            "4. Review open decisions — any blocking the gate? (10 min)",
            "5. Generate gate review package (document export) (10 min)",
            "6. Go/no-go assessment (10 min)",
        ],
        pre_reads=["Gate exit criteria checklist", "Engineering budgets dashboard"],
        outputs=["Gate readiness assessment", "Action list for RED items", "Review package"],
    ),
]


def recommend_next_session(
    study_state: dict[str, Any],
) -> dict[str, Any]:
    """Based on current study maturity, recommend what session to run next.

    Examines: mission need completeness, orbit selection status, design
    convergence status, component selection status, gate readiness.
    """
    mn = study_state.get("mission_need", {})
    has_need = bool(mn.get("problem_statement", ""))
    has_stakeholders = len(mn.get("stakeholders", [])) > 0
    has_objectives = len(mn.get("objectives", [])) > 0
    has_alternatives = len(mn.get("alternatives", [])) >= 2
    has_selected_concept = bool(mn.get("selected_alternative_id"))
    has_design_result = study_state.get("has_design_result", False)
    has_components = study_state.get("components_selected", 0) > 0
    has_orbit = study_state.get("orbit_decided", False)

    if not has_need or not has_stakeholders or not has_objectives:
        template = SESSION_TEMPLATES[0]  # Kickoff
        reason = "Mission need, stakeholders, or objectives are not yet defined."
    elif not has_alternatives or not has_selected_concept or not has_orbit:
        template = SESSION_TEMPLATES[1]  # Architecture
        reason = "Architecture decisions (orbit, ground segment, ConOps) are outstanding."
    elif not has_design_result:
        template = SESSION_TEMPLATES[2]  # Sizing
        reason = "Design has not been converged yet. Run subsystem sizing."
    elif not has_components:
        template = SESSION_TEMPLATES[3]  # Component selection
        reason = "Components have not been selected. Run component selection session."
    else:
        template = SESSION_TEMPLATES[5]  # Gate review
        reason = "Design is converged with components selected. Prepare for gate review."

    return {
        "recommended_session": {
            "type": template.session_type,
            "name": template.name,
            "duration_hours": template.duration_hours,
            "objective": template.objective,
            "decisions": template.decisions_to_address,
            "positions": template.recommended_positions,
            "agenda": template.agenda,
            "pre_reads": template.pre_reads,
            "outputs": template.outputs,
        },
        "reason": reason,
        "study_maturity": {
            "has_mission_need": has_need,
            "has_stakeholders": has_stakeholders,
            "has_objectives": has_objectives,
            "has_alternatives": has_alternatives,
            "has_selected_concept": has_selected_concept,
            "has_orbit_decision": has_orbit,
            "has_design_result": has_design_result,
            "has_components": has_components,
        },
        "all_session_types": [
            {"type": t.session_type, "name": t.name, "duration_hours": t.duration_hours, "objective": t.objective}
            for t in SESSION_TEMPLATES
        ],
    }
