"""SpaceCDF — Systems Engineering Management Plan (SEMP) Generator.

Generates a structured SEMP document from live design-session data and
user-supplied answers to a SEMP questionnaire.  The output mirrors the
standard section layout of ECSS-M-ST-10C Rev.1 and is compatible with
NASA SEH Appendix J.

References:
  - ECSS-M-ST-10C Rev.1 — Space project management — Project planning and implementation
  - ECSS-E-ST-10C Rev.1 — Space engineering — System engineering general requirements
  - ECSS-E-HB-10-02A — Verification guidelines
  - NASA/SP-2016-6105 Rev 2 — NASA Systems Engineering Handbook, Appendix J
"""
from __future__ import annotations

import logging
import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type aliases for readability
# ---------------------------------------------------------------------------
SempSection = dict[str, Any]
SempSubsection = dict[str, Any]

# ---------------------------------------------------------------------------
# ECSS margin policy by phase — used for Section 5
# ---------------------------------------------------------------------------
ECSS_MARGIN_POLICY: dict[str, dict[str, str]] = {
    "Phase 0/A": {
        "Mass": ">=20 % at equipment level, >=20 % system margin",
        "Power": ">=20 % at equipment level, >=20 % system margin",
        "Link": ">=6 dB",
        "Delta-V": ">=25 %",
        "Data": ">=50 % storage, >=30 % downlink",
    },
    "Phase B": {
        "Mass": ">=10 % at equipment level, >=20 % system margin",
        "Power": ">=10 % at equipment level, >=20 % system margin",
        "Link": ">=4 dB",
        "Delta-V": ">=15 %",
        "Data": ">=30 % storage, >=20 % downlink",
    },
    "Phase C/D": {
        "Mass": ">=5 % at equipment level, >=10 % system margin",
        "Power": ">=5 % at equipment level, >=10 % system margin",
        "Link": ">=3 dB",
        "Delta-V": ">=5 %",
        "Data": ">=10 % storage, >=10 % downlink",
    },
}

# Review entry / exit criteria templates
_REVIEW_CRITERIA: dict[str, dict[str, str]] = {
    "MDR": {
        "entry": "Mission need statement approved; preliminary ConOps drafted",
        "exit": "Mission need confirmed; feasibility demonstrated; Phase A authorised",
        "deliverables": "Mission Need Statement, preliminary ConOps, stakeholder register",
    },
    "PRR": {
        "entry": "Phase A study complete; system requirements baselined",
        "exit": "System concept feasible; critical technologies identified; Phase B authorised",
        "deliverables": "System Requirements Document, Technology Development Plan, preliminary SEMP",
    },
    "SRR": {
        "entry": "System requirements complete and traceable to mission objectives",
        "exit": "Requirements baseline approved; no TBDs above threshold",
        "deliverables": "SRD, ICD drafts, V&V plan draft, updated risk register",
    },
    "PDR": {
        "entry": "Preliminary design complete; all subsystems addressed",
        "exit": "Design meets requirements; development risks acceptable; Phase C authorised",
        "deliverables": "Design Description Document, updated ICDs, mass/power budgets, test plan",
    },
    "CDR": {
        "entry": "Detailed design complete; all analyses done",
        "exit": "Design ready for manufacturing; all TBDs resolved",
        "deliverables": "Detailed DDD, final ICDs, AS-built predictions, manufacturing plan",
    },
    "QR": {
        "entry": "Qualification testing complete",
        "exit": "Design qualified for flight; deviations dispositioned",
        "deliverables": "Qualification test reports, NCR status, flight readiness certificate",
    },
    "AR": {
        "entry": "Flight model acceptance testing complete",
        "exit": "FM accepted for launch campaign",
        "deliverables": "Acceptance test reports, final mass/power properties, flight ops procedures",
    },
    "FRR": {
        "entry": "Launch campaign activities complete; spacecraft on launcher",
        "exit": "Go for launch",
        "deliverables": "Flight Readiness Certificate, launch sequence, contingency plans",
    },
    "LRR": {
        "entry": "All ground systems verified; countdown rehearsal complete",
        "exit": "Launch authorised",
        "deliverables": "Launch Readiness Certificate, ground segment acceptance",
    },
    "ELR": {
        "entry": "Commissioning phase complete",
        "exit": "Mission declared operational",
        "deliverables": "Commissioning report, performance verification, ops handover",
    },
    "EOM": {
        "entry": "Nominal mission lifetime complete or consumables depleted",
        "exit": "Disposal / passivation initiated",
        "deliverables": "End-of-mission report, disposal plan execution log",
    },
}

# Default review-gate sequence
_DEFAULT_GATE_SEQUENCE = ["MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR", "LRR", "ELR", "EOM"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_semp(
    study_data: dict[str, Any],
    semp_answers: dict[str, Any],
) -> dict[str, Any]:
    """Generate a complete SEMP document structure.

    Parameters
    ----------
    study_data:
        Live design-session data containing requirements definition,
        mission need, phases, modes, architecture selections, generated
        requirements, parameters, and budget allocations.
    semp_answers:
        User-provided answers from the SEMP questionnaire covering model
        philosophy, risk matrix, baseline dates, CCB, review dates,
        team size, SE responsible, and disposal approach.

    Returns
    -------
    dict with ``sections`` list — each section has number, title, content,
    subsections, and an ``auto_generated`` flag.
    """
    reqs_def = study_data.get("requirements", {}) or {}
    mission_need = study_data.get("mission_need", {}) or {}
    mission_phases = study_data.get("mission_phases", []) or []
    operational_modes = study_data.get("operational_modes", []) or []
    arch_selections = study_data.get("architecture_selections", {}) or {}
    gen_reqs = study_data.get("generated_requirements", []) or []
    parameters = study_data.get("parameters", {}) or {}
    budgets = study_data.get("budget_allocations", {}) or {}

    study_name = reqs_def.get("name", "Unnamed Mission")
    mission_type = reqs_def.get("mission_type", "")
    sc_class = reqs_def.get("spacecraft_class", "")
    orbit = reqs_def.get("orbit", {}) or {}
    payloads = reqs_def.get("payloads", []) or []
    design_life = reqs_def.get("design_lifetime_years", 0)

    model_phil = semp_answers.get("model_philosophy", {}) or {}
    risk_matrix_size = semp_answers.get("risk_matrix_size", "5x5")
    risk_tolerance = semp_answers.get("risk_tolerance", "Medium")
    baseline_dates = semp_answers.get("baseline_dates", {}) or {}
    ccb_membership = semp_answers.get("ccb_membership", "")
    review_dates = semp_answers.get("review_dates", {}) or {}
    team_size = semp_answers.get("team_size", 0)
    se_responsible = semp_answers.get("se_responsible", "")
    disposal_approach = semp_answers.get("disposal_approach", "")

    sections: list[SempSection] = [
        _section_1_introduction(study_name, mission_type, sc_class, orbit, payloads, design_life, mission_need),
        _section_2_model_philosophy(model_phil, arch_selections),
        _section_3_milestones(mission_phases, review_dates),
        _section_4_requirements_management(gen_reqs),
        _section_5_budgets_margins(parameters, budgets),
        _section_6_trade_studies(arch_selections),
        _section_7_risk_management(risk_matrix_size, risk_tolerance, arch_selections, parameters),
        _section_8_configuration_management(baseline_dates, ccb_membership),
        _section_9_interface_management(arch_selections, gen_reqs),
        _section_10_vv_approach(gen_reqs),
        _section_11_architecture_conops(mission_need, operational_modes, study_name),
        _section_12_schedule(review_dates, mission_phases),
        _section_13_organisation(team_size, se_responsible),
        _section_14_sustainability_disposal(disposal_approach, orbit, design_life),
    ]

    return {
        "document": "Systems Engineering Management Plan (SEMP)",
        "standard": "ECSS-M-ST-10C / NASA SEH Appendix J",
        "study_name": study_name,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# SVG timeline generator
# ---------------------------------------------------------------------------

def generate_semp_svg_timeline(
    mission_phases: list[dict[str, Any]],
    review_dates: dict[str, str],
) -> str:
    """Return an SVG string showing a Gantt-style timeline of mission phases
    and review gates.

    Parameters
    ----------
    mission_phases:
        List of ``{id, name, duration_days}`` dicts.
    review_dates:
        Mapping of review gate name to ISO-8601 date string.

    Returns
    -------
    SVG markup as a string.
    """
    if not mission_phases:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="100"><text x="20" y="50" font-size="14">No mission phases defined.</text></svg>'

    # Layout constants
    left_margin = 180
    right_margin = 40
    top_margin = 60
    row_height = 36
    bar_height = 22
    canvas_width = 900
    bar_area_width = canvas_width - left_margin - right_margin

    total_days = sum(p.get("duration_days", 0) for p in mission_phases)
    if total_days == 0:
        total_days = 1  # avoid division by zero

    num_phases = len(mission_phases)
    canvas_height = top_margin + num_phases * row_height + 80  # extra for legend

    # Colour palette
    phase_colours = [
        "#4A90D9", "#50B86C", "#E6A23C", "#E25C5C",
        "#9B59B6", "#1ABC9C", "#3498DB", "#F39C12",
        "#E74C3C", "#2ECC71", "#8E44AD", "#16A085",
    ]

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" '
                 f'viewBox="0 0 {canvas_width} {canvas_height}" style="font-family:Arial,Helvetica,sans-serif">')
    # Background
    lines.append(f'<rect width="{canvas_width}" height="{canvas_height}" fill="#FAFAFA" rx="8"/>')

    # Title
    lines.append(f'<text x="{canvas_width // 2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#333">Mission Timeline</text>')

    # Header line
    header_y = top_margin - 10
    lines.append(f'<line x1="{left_margin}" y1="{header_y}" x2="{left_margin + bar_area_width}" y2="{header_y}" stroke="#CCC" stroke-width="1"/>')

    # Phase bars
    cumulative_days = 0
    for i, phase in enumerate(mission_phases):
        phase_name = phase.get("name", phase.get("id", f"Phase {i + 1}"))
        duration = phase.get("duration_days", 0)

        y = top_margin + i * row_height
        x_start = left_margin + int(cumulative_days / total_days * bar_area_width)
        bar_w = max(int(duration / total_days * bar_area_width), 4)
        colour = phase_colours[i % len(phase_colours)]

        # Label
        lines.append(f'<text x="{left_margin - 10}" y="{y + bar_height // 2 + 5}" text-anchor="end" '
                     f'font-size="12" fill="#444">{_svg_escape(phase_name)}</text>')
        # Bar
        lines.append(f'<rect x="{x_start}" y="{y}" width="{bar_w}" height="{bar_height}" '
                     f'rx="4" fill="{colour}" opacity="0.85"/>')
        # Duration label inside bar
        dur_label = f"{duration}d"
        if bar_w > 40:
            lines.append(f'<text x="{x_start + bar_w // 2}" y="{y + bar_height // 2 + 4}" '
                         f'text-anchor="middle" font-size="10" fill="#FFF">{dur_label}</text>')

        cumulative_days += duration

    # Review gate diamonds
    if review_dates:
        gate_y_base = top_margin + num_phases * row_height + 10
        lines.append(f'<text x="{left_margin - 10}" y="{gate_y_base + 12}" text-anchor="end" '
                     f'font-size="11" fill="#666" font-style="italic">Reviews</text>')

        # Parse dates and place proportionally if we can match to phase timeline
        sorted_gates = sorted(review_dates.items(), key=lambda kv: kv[1])
        gate_spacing = bar_area_width / max(len(sorted_gates), 1)

        for gi, (gate_name, _date_str) in enumerate(sorted_gates):
            gx = left_margin + int(gi * gate_spacing) + int(gate_spacing / 2)
            gy = gate_y_base + 6
            diamond_size = 8
            points = (f"{gx},{gy - diamond_size} {gx + diamond_size},{gy} "
                      f"{gx},{gy + diamond_size} {gx - diamond_size},{gy}")
            lines.append(f'<polygon points="{points}" fill="#E25C5C"/>')
            lines.append(f'<text x="{gx}" y="{gy + diamond_size + 14}" text-anchor="middle" '
                         f'font-size="9" fill="#555">{_svg_escape(gate_name)}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def _svg_escape(text: str) -> str:
    """Escape XML special characters for SVG text content."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_1_introduction(
    study_name: str,
    mission_type: str,
    sc_class: str,
    orbit: dict[str, Any],
    payloads: list[Any],
    design_life: float,
    mission_need: dict[str, Any],
) -> SempSection:
    objectives = mission_need.get("objectives", [])
    problem = mission_need.get("problem_statement", "")
    orbit_desc = _describe_orbit(orbit)
    payload_names = ", ".join(
        p.get("name", p) if isinstance(p, dict) else str(p) for p in payloads
    ) or "None specified"

    obj_text = "\n".join(f"  - {o}" for o in objectives) if objectives else "  - To be defined"

    return _make_section(
        number="1",
        title="Introduction",
        content=(
            f"This Systems Engineering Management Plan (SEMP) defines the systems engineering "
            f"approach, processes, and management controls for the {study_name} mission.  "
            f"It is a living document maintained under configuration control and updated "
            f"at each major project review."
        ),
        subsections=[
            _sub("1.1", "Purpose",
                 f"The purpose of this SEMP is to describe how systems engineering will be "
                 f"planned, organised, and executed throughout the {study_name} project "
                 f"lifecycle.  It establishes responsibilities, processes, and the technical "
                 f"management approach in accordance with ECSS-M-ST-10C and is compatible "
                 f"with the NASA SE Handbook (NASA/SP-2016-6105 Rev 2, Appendix J)."),
            _sub("1.2", "Scope",
                 f"This SEMP covers the full lifecycle of the {study_name} mission from "
                 f"Phase 0 concept exploration through Phase F disposal.  The mission is "
                 f"classified as a {mission_type or 'general'} mission using a "
                 f"{sc_class or 'standard'}-class spacecraft.  "
                 f"The target orbit is {orbit_desc}.  "
                 f"Primary payloads: {payload_names}.  "
                 f"Design lifetime: {design_life} years."),
            _sub("1.3", "Mission Objectives",
                 f"The mission addresses the following need:\n\n{problem or 'Not yet defined.'}\n\n"
                 f"Objectives:\n{obj_text}"),
            _sub("1.4", "Applicable Documents",
                 "The following standards and documents are applicable:\n"
                 "  - ECSS-M-ST-10C Rev.1 — Space project management: Project planning and implementation\n"
                 "  - ECSS-E-ST-10C Rev.1 — Space engineering: System engineering general requirements\n"
                 "  - ECSS-E-HB-10-02A — Verification guidelines\n"
                 "  - ECSS-Q-ST-10C — Space product assurance: Product assurance management\n"
                 "  - ECSS-M-ST-40C — Configuration and information management\n"
                 "  - ECSS-M-ST-80C — Risk management\n"
                 "  - NASA/SP-2016-6105 Rev 2 — NASA Systems Engineering Handbook"),
            _sub("1.5", "Reference Documents",
                 "  - Mission Requirements Document (MRD)\n"
                 "  - System Requirements Document (SRD)\n"
                 "  - Design Description Document (DDD)\n"
                 "  - Verification & Validation Plan (VVP)\n"
                 "  - Risk Management Plan (RMP)\n"
                 "  - Configuration Management Plan (CMP)"),
        ],
        auto_generated=True,
    )


def _section_2_model_philosophy(
    model_phil: dict[str, str],
    arch_selections: dict[str, Any],
) -> SempSection:
    # Build table rows: subsystem | model approach | rationale
    rows: list[str] = []
    all_subsystems = sorted(set(list(model_phil.keys()) + list(arch_selections.keys())))

    if not all_subsystems:
        all_subsystems = [
            "Structure", "Thermal", "Power", "AOCS", "Propulsion",
            "Communications", "Data Handling", "Payload",
        ]

    for ss in all_subsystems:
        level = model_phil.get(ss, _default_model_level(ss, arch_selections))
        rationale = _model_rationale(level)
        rows.append(f"  | {ss:<20s} | {level:<12s} | {rationale}")

    table_header = "  | Subsystem            | Model Level  | Rationale"
    table_sep = "  |" + "-" * 22 + "|" + "-" * 14 + "|" + "-" * 50
    table = "\n".join([table_header, table_sep] + rows)

    return _make_section(
        number="2",
        title="Model Philosophy",
        content=(
            "The model philosophy defines the number and purpose of hardware models "
            "built during the development programme.  The choice between a protoflight "
            "approach (PFM) and a full qualification approach (QM + FM) depends on the "
            "heritage, criticality, and cost/schedule constraints of each subsystem.\n\n"
            "In a protoflight approach, the flight unit undergoes qualification-level "
            "testing at reduced duration.  This reduces cost and schedule but accepts "
            "higher risk from potential over-testing of the flight hardware.  A full "
            "qualification approach builds a dedicated Qualification Model (QM) that is "
            "tested to qualification levels and durations, preserving the flight unit "
            "from excessive stress.  Engineering Models (EM) are used for early "
            "functional verification and interface testing regardless of the chosen "
            "approach."
        ),
        subsections=[
            _sub("2.1", "Model Allocation Table", table),
            _sub("2.2", "Protoflight vs Full Qualification",
                 "The protoflight approach (PFM) is selected when:\n"
                 "  - The subsystem has high heritage (TRL >= 7)\n"
                 "  - Schedule and cost constraints preclude a dedicated QM\n"
                 "  - Failure consequences are bounded and recoverable\n\n"
                 "The full qualification approach (QM + FM) is selected when:\n"
                 "  - Technology readiness is low (TRL < 6) and qualification data is absent\n"
                 "  - The subsystem is mission-critical with no redundancy\n"
                 "  - Failure would be catastrophic or result in total mission loss\n\n"
                 "Engineering Models (EM) are built for all subsystems to support "
                 "early integration testing, interface verification, and software "
                 "validation on a flatsat configuration."),
        ],
        auto_generated=True,
    )


def _section_3_milestones(
    mission_phases: list[dict[str, Any]],
    review_dates: dict[str, str],
) -> SempSection:
    # Build review/milestone table
    rows: list[str] = []
    gates = list(review_dates.keys()) if review_dates else _DEFAULT_GATE_SEQUENCE[:6]

    for gate in gates:
        date_str = review_dates.get(gate, "TBD")
        criteria = _REVIEW_CRITERIA.get(gate, _REVIEW_CRITERIA.get("PDR", {}))
        entry = criteria.get("entry", "As per project plan")
        exit_ = criteria.get("exit", "All actions closed or assigned")
        deliverables = criteria.get("deliverables", "Review data package")
        rows.append(
            f"  | {gate:<6s} | {date_str:<12s} | {entry[:50]:<50s} | {exit_[:45]:<45s} | {deliverables[:40]}"
        )

    table_header = "  | Gate   | Date         | Entry Criteria                                     | Exit Criteria                                  | Key Deliverables"
    table_sep = "  |" + "-" * 8 + "|" + "-" * 14 + "|" + "-" * 52 + "|" + "-" * 48 + "|" + "-" * 42
    table = "\n".join([table_header, table_sep] + rows)

    # Phase summary
    phase_lines = []
    cumulative = 0
    for p in mission_phases:
        dur = p.get("duration_days", 0)
        phase_lines.append(
            f"  - {p.get('name', p.get('id', '?'))}: {dur} days "
            f"(day {cumulative} to day {cumulative + dur})"
        )
        cumulative += dur

    phase_summary = "\n".join(phase_lines) if phase_lines else "  No mission phases defined."

    return _make_section(
        number="3",
        title="Milestones & Reviews",
        content=(
            "The project follows the ECSS lifecycle model with key decision points "
            "(KDPs) between each phase.  Reviews are conducted to assess technical "
            "maturity and authorise transition to the next phase.  The table below "
            "summarises the planned reviews, their dates, and associated entry/exit "
            "criteria."
        ),
        subsections=[
            _sub("3.1", "Review Schedule", table),
            _sub("3.2", "Mission Phase Durations",
                 f"The mission timeline spans {cumulative} days total:\n\n{phase_summary}"),
        ],
        auto_generated=True,
    )


def _section_4_requirements_management(
    gen_reqs: list[dict[str, Any]],
) -> SempSection:
    total = len(gen_reqs)
    by_level: Counter[str] = Counter()
    by_domain: Counter[str] = Counter()
    by_vmethod: Counter[str] = Counter()
    for r in gen_reqs:
        by_level[r.get("level", "system")] += 1
        by_domain[r.get("domain", "systems")] += 1
        by_vmethod[r.get("verification_method", "Analysis")] += 1

    level_summary = "\n".join(
        f"  - {level.capitalize()}: {count}" for level, count in sorted(by_level.items())
    ) or "  No requirements generated."

    domain_summary = "\n".join(
        f"  - {domain.capitalize()}: {count}" for domain, count in sorted(by_domain.items())
    ) or "  No domain breakdown available."

    return _make_section(
        number="4",
        title="Requirements Management",
        content=(
            f"The project manages a total of {total} requirements across multiple levels "
            f"and engineering domains.  Requirements traceability is maintained "
            f"bidirectionally: upward from derived requirements to parent requirements "
            f"and mission objectives, and downward from mission requirements to "
            f"subsystem specifications and verification activities.\n\n"
            f"The requirements baseline is established at SRR and placed under "
            f"configuration control.  Changes are processed through the Change Control "
            f"Board (CCB).  Each requirement is assigned a unique identifier, an owning "
            f"domain, a level (mission/system/subsystem/equipment), and a verification "
            f"method (Inspection, Analysis, Demonstration, or Test)."
        ),
        subsections=[
            _sub("4.1", "Requirement Counts by Level", level_summary),
            _sub("4.2", "Requirement Counts by Domain", domain_summary),
            _sub("4.3", "Traceability Approach",
                 "Requirements traceability is maintained in the SpaceCDF design database "
                 "with automatic link generation between levels.  The traceability matrix "
                 "is exported at each review gate.  Orphan detection alerts the team to "
                 "requirements without parent linkage or verification assignments."),
        ],
        auto_generated=True,
    )


def _section_5_budgets_margins(
    parameters: dict[str, Any],
    budgets: dict[str, Any],
) -> SempSection:
    # Build budget summary from parameters and allocations
    budget_rows: list[str] = []
    for btype, bdata in sorted(budgets.items()):
        if isinstance(bdata, dict):
            allocated = bdata.get("allocated", "N/A")
            current = bdata.get("current", "N/A")
            margin = bdata.get("margin_pct", "N/A")
            budget_rows.append(f"  | {btype:<18s} | {str(allocated):<14s} | {str(current):<14s} | {str(margin):<10s} |")
        else:
            budget_rows.append(f"  | {btype:<18s} | {str(bdata):<14s} | {'—':<14s} | {'—':<10s} |")

    if budget_rows:
        table_header = "  | Budget Type        | Allocated      | Current        | Margin (%) |"
        table_sep = "  |" + "-" * 20 + "|" + "-" * 16 + "|" + "-" * 16 + "|" + "-" * 12 + "|"
        budget_table = "\n".join([table_header, table_sep] + budget_rows)
    else:
        budget_table = "  No budget allocations defined yet."

    # ECSS margin policy table
    policy_rows: list[str] = []
    for phase_label, domains in ECSS_MARGIN_POLICY.items():
        for domain, rule in domains.items():
            policy_rows.append(f"  | {phase_label:<12s} | {domain:<10s} | {rule}")
    policy_header = "  | Phase        | Domain     | Required Margin"
    policy_sep = "  |" + "-" * 14 + "|" + "-" * 12 + "|" + "-" * 50
    policy_table = "\n".join([policy_header, policy_sep] + policy_rows)

    # Key parameters summary
    key_params = ["total_mass_kg", "dry_mass_kg", "total_power_w", "delta_v_m_s",
                  "data_rate_kbps", "link_margin_db"]
    param_lines = []
    for kp in key_params:
        val = parameters.get(kp)
        if val is not None:
            param_lines.append(f"  - {kp.replace('_', ' ').title()}: {val}")
    param_summary = "\n".join(param_lines) if param_lines else "  No key parameters extracted."

    return _make_section(
        number="5",
        title="Budgets & Margins",
        content=(
            "Design budgets are maintained for mass, power, link, delta-V, data, and "
            "pointing.  Margins are applied per ECSS-E-HB-10-02A at equipment level "
            "and system level, with minimum values that decrease as design maturity "
            "increases through the project phases.  Margin compliance is automatically "
            "monitored by the SpaceCDF constraint engine and violations are flagged."
        ),
        subsections=[
            _sub("5.1", "Current Budget Allocations", budget_table),
            _sub("5.2", "Key Design Parameters", param_summary),
            _sub("5.3", "ECSS Margin Policy by Phase", policy_table),
        ],
        auto_generated=True,
    )


def _section_6_trade_studies(
    arch_selections: dict[str, Any],
) -> SempSection:
    if not arch_selections:
        trade_summary = "  No architecture trade selections recorded yet."
    else:
        rows: list[str] = []
        for subsystem, sel in sorted(arch_selections.items()):
            if isinstance(sel, dict):
                option = sel.get("option_name", "N/A")
                mass = sel.get("mass_kg", "—")
                power = sel.get("power_w", "—")
                cost = sel.get("cost_keur", "—")
                rows.append(
                    f"  | {subsystem:<18s} | {option:<22s} | {str(mass):<10s} | "
                    f"{str(power):<10s} | {str(cost):<10s} |"
                )
            else:
                rows.append(f"  | {subsystem:<18s} | {str(sel):<22s} | {'—':<10s} | {'—':<10s} | {'—':<10s} |")

        table_header = "  | Subsystem          | Selected Option        | Mass (kg)  | Power (W)  | Cost (kEUR)|"
        table_sep = "  |" + "-" * 20 + "|" + "-" * 24 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 12 + "|"
        trade_summary = "\n".join([table_header, table_sep] + rows)

    return _make_section(
        number="6",
        title="Trade Studies",
        content=(
            "Trade studies are conducted to evaluate alternative design solutions "
            "against weighted evaluation criteria.  Each subsystem trade considers "
            "mass, power, cost, heritage/TRL, complexity, and programmatic risk.  "
            "The selected options form the design baseline and are placed under "
            "configuration control after PDR.\n\n"
            "The table below summarises the current architecture selections:"
        ),
        subsections=[
            _sub("6.1", "Architecture Selections", trade_summary),
            _sub("6.2", "Trade Study Process",
                 "Trade studies follow a structured process:\n"
                 "  1. Define the trade space and candidate options\n"
                 "  2. Establish evaluation criteria and weightings\n"
                 "  3. Score each option against criteria (1-5 scale)\n"
                 "  4. Compute weighted scores and identify the preferred option\n"
                 "  5. Document rationale and sensitivity to weighting changes\n"
                 "  6. Present recommendation at the relevant review gate"),
        ],
        auto_generated=True,
    )


def _section_7_risk_management(
    risk_matrix_size: str,
    risk_tolerance: str,
    arch_selections: dict[str, Any],
    parameters: dict[str, Any],
) -> SempSection:
    dims = risk_matrix_size.split("x")
    n = int(dims[0]) if len(dims) >= 1 and dims[0].isdigit() else 5

    # Auto-detect potential risks from architecture and parameters
    auto_risks: list[str] = []

    for ss, sel in arch_selections.items():
        if isinstance(sel, dict):
            option_name = sel.get("option_name", "").lower()
            # Flag novel / low-TRL selections
            if any(kw in option_name for kw in ["novel", "experimental", "custom", "new"]):
                auto_risks.append(
                    f"Technology maturity risk: {ss} uses '{sel.get('option_name', '')}' "
                    f"which may require additional development and qualification."
                )

    # Check margin risks from parameters
    total_mass = parameters.get("total_mass_kg")
    max_mass = parameters.get("max_mass_kg") or parameters.get("launcher_capacity_kg")
    if total_mass and max_mass:
        try:
            margin_pct = (float(max_mass) - float(total_mass)) / float(max_mass) * 100
            if margin_pct < 10:
                auto_risks.append(
                    f"Mass margin risk: Current margin is {margin_pct:.1f}%, below the "
                    f"recommended 20% for early phases.  Mass growth could exceed launcher capacity."
                )
        except (ValueError, ZeroDivisionError):
            pass

    total_power = parameters.get("total_power_w")
    available_power = parameters.get("available_power_w") or parameters.get("solar_array_power_w")
    if total_power and available_power:
        try:
            p_margin = (float(available_power) - float(total_power)) / float(available_power) * 100
            if p_margin < 15:
                auto_risks.append(
                    f"Power margin risk: Current power margin is {p_margin:.1f}%, "
                    f"approaching the minimum ECSS threshold."
                )
        except (ValueError, ZeroDivisionError):
            pass

    if not auto_risks:
        auto_risks.append("No automatically detected risks at this time.  Manual risk identification is required.")

    risk_list = "\n".join(f"  {i+1}. {r}" for i, r in enumerate(auto_risks))

    return _make_section(
        number="7",
        title="Risk Management",
        content=(
            f"Risk management follows ECSS-M-ST-80C.  Risks are assessed using a "
            f"{risk_matrix_size} probability-severity matrix with a project risk "
            f"tolerance of \"{risk_tolerance}\".  Risks above the tolerance line require "
            f"mitigation actions with assigned owners and target closure dates.\n\n"
            f"The risk register is maintained throughout the project lifecycle and "
            f"reviewed at each major review gate.  New risks are identified through "
            f"regular risk workshops, design reviews, and automated analysis of "
            f"design margin trends."
        ),
        subsections=[
            _sub("7.1", "Risk Matrix",
                 f"The project uses a {risk_matrix_size} risk matrix per ECSS-M-ST-80C.\n\n"
                 f"  Probability levels: {n} (from rare/very low to almost certain/very high)\n"
                 f"  Severity levels:    {n} (from negligible to catastrophic)\n\n"
                 f"Risk tolerance: {risk_tolerance}.  Risks classified as \"{risk_tolerance}\" "
                 f"or higher require documented mitigation plans.  Risks classified as "
                 f"\"High\" or \"Very High\" are escalated to the Project Manager and "
                 f"reported at each review gate."),
            _sub("7.2", "Auto-Detected Risks",
                 f"The following risks have been automatically identified from the "
                 f"current design state:\n\n{risk_list}"),
            _sub("7.3", "Risk Response Strategy",
                 "Risk responses are categorised as:\n"
                 "  - Avoid: Eliminate the risk by changing the design approach\n"
                 "  - Mitigate: Reduce probability or severity through specific actions\n"
                 "  - Transfer: Shift the risk to another party (insurance, subcontractor)\n"
                 "  - Accept: Acknowledge the risk with contingency reserves allocated"),
        ],
        auto_generated=False,
    )


def _section_8_configuration_management(
    baseline_dates: dict[str, str],
    ccb_membership: str,
) -> SempSection:
    if baseline_dates:
        baseline_rows = "\n".join(
            f"  - {gate}: {date}" for gate, date in sorted(baseline_dates.items())
        )
    else:
        baseline_rows = "  No baseline dates defined yet."

    return _make_section(
        number="8",
        title="Configuration Management",
        content=(
            "Configuration management follows ECSS-M-ST-40C.  The configuration "
            "baseline is established progressively: the Functional Baseline at SRR, "
            "the Design-To Baseline at PDR, and the As-Built Baseline at CDR/AR.  "
            "All changes to baselined items are processed through the Configuration "
            "Control Board (CCB)."
        ),
        subsections=[
            _sub("8.1", "Configuration Baselines",
                 f"Planned baseline establishment dates:\n\n{baseline_rows}"),
            _sub("8.2", "Change Control Board (CCB)",
                 f"The CCB is responsible for reviewing and dispositioning all change "
                 f"requests to baselined configuration items.\n\n"
                 f"CCB Membership: {ccb_membership or 'To be defined.'}\n\n"
                 f"Change request categories:\n"
                 f"  - Class 1 (Major): Changes affecting form, fit, function, or interface — require full CCB review\n"
                 f"  - Class 2 (Minor): Changes that do not affect external interfaces — delegated approval"),
            _sub("8.3", "Configuration Items",
                 "The following are designated as Configuration Items (CIs):\n"
                 "  - System Requirements Document (SRD)\n"
                 "  - Interface Control Documents (ICDs)\n"
                 "  - Design Description Documents (DDDs)\n"
                 "  - Flight software binaries and source code\n"
                 "  - Test procedures and test reports\n"
                 "  - Mass, power, and link budgets\n"
                 "  - Hardware drawings and parts lists"),
        ],
        auto_generated=False,
    )


def _section_9_interface_management(
    arch_selections: dict[str, Any],
    gen_reqs: list[dict[str, Any]],
) -> SempSection:
    num_subsystems = len(arch_selections)
    # Estimate interface count: each pair of subsystems may have interfaces
    estimated_interfaces = num_subsystems * (num_subsystems - 1) // 2 if num_subsystems > 1 else 0

    # Count interface-related requirements
    iface_reqs = [r for r in gen_reqs if "interface" in r.get("text", "").lower()
                  or r.get("domain", "").lower() == "interfaces"]
    num_iface_reqs = len(iface_reqs)

    return _make_section(
        number="9",
        title="Interface Management",
        content=(
            f"Interface management ensures that all physical, functional, and "
            f"informational interfaces between subsystems, the spacecraft and its "
            f"environment, and the space and ground segments are identified, "
            f"documented, and controlled.\n\n"
            f"The current architecture has {num_subsystems} subsystem domains with "
            f"an estimated {estimated_interfaces} potential bilateral interfaces.  "
            f"There are {num_iface_reqs} interface-related requirements in the "
            f"requirements database."
        ),
        subsections=[
            _sub("9.1", "ICD Development Approach",
                 "Interface Control Documents (ICDs) are developed bilaterally between "
                 "interfacing subsystem teams.  Each ICD covers:\n"
                 "  - Mechanical interfaces (mounting, envelope, alignment)\n"
                 "  - Electrical interfaces (connectors, grounding, power)\n"
                 "  - Data interfaces (protocols, data rates, message formats)\n"
                 "  - Thermal interfaces (heat dissipation paths, thermal coupling)\n\n"
                 "ICDs are baselined at PDR and placed under CCB control."),
            _sub("9.2", "Interface Verification",
                 "Interfaces are verified through:\n"
                 "  - Interface compatibility analyses during Phase B\n"
                 "  - Electrical interface tests on the flatsat/EM configuration\n"
                 "  - Mechanical fit-checks during AIT\n"
                 "  - End-to-end data flow tests during system validation"),
        ],
        auto_generated=True,
    )


def _section_10_vv_approach(
    gen_reqs: list[dict[str, Any]],
) -> SempSection:
    # Count verification methods (IADT)
    method_counts: Counter[str] = Counter()
    for r in gen_reqs:
        vm = r.get("verification_method", "Analysis")
        # Normalise
        vm_upper = vm[0].upper() if vm else "A"
        method_map = {"I": "Inspection", "A": "Analysis", "D": "Demonstration", "T": "Test",
                      "R": "Review of Design"}
        method_name = method_map.get(vm_upper, vm)
        method_counts[method_name] += 1

    total = len(gen_reqs)
    if total > 0:
        breakdown_lines = []
        for method in ["Inspection", "Analysis", "Demonstration", "Test", "Review of Design"]:
            count = method_counts.get(method, 0)
            pct = count / total * 100
            bar = "#" * int(pct / 2)
            breakdown_lines.append(f"  {method:<20s}: {count:4d} ({pct:5.1f}%)  {bar}")
        breakdown = "\n".join(breakdown_lines)
    else:
        breakdown = "  No requirements with verification methods defined."

    return _make_section(
        number="10",
        title="Verification & Validation Approach",
        content=(
            f"The V&V approach follows the ECSS verification methodology "
            f"(ECSS-E-ST-10-02C).  Each requirement is assigned one or more "
            f"verification methods from the standard IADT taxonomy: Inspection, "
            f"Analysis, Demonstration, or Test (with Review of Design as a "
            f"supplementary method for early phases).\n\n"
            f"Of {total} generated requirements, the verification method breakdown is:"
        ),
        subsections=[
            _sub("10.1", "Verification Method Distribution", breakdown),
            _sub("10.2", "Verification Levels",
                 "Verification is performed at multiple integration levels:\n"
                 "  - Equipment level: Individual units tested against their specifications\n"
                 "  - Subsystem level: Integrated subsystem performance verification\n"
                 "  - System level: Full spacecraft functional and environmental testing\n"
                 "  - In-orbit: Commissioning verification of on-orbit performance"),
            _sub("10.3", "Verification Control",
                 "A Verification Control Document (VCD) tracks the status of each "
                 "requirement verification.  The VCD is maintained in the SpaceCDF "
                 "database and exported at each review gate.  Verification closure "
                 "requires objective evidence (test reports, analysis results, or "
                 "inspection records) linked to the specific requirement."),
        ],
        auto_generated=True,
    )


def _section_11_architecture_conops(
    mission_need: dict[str, Any],
    operational_modes: list[dict[str, Any]],
    study_name: str,
) -> SempSection:
    problem = mission_need.get("problem_statement", "Not yet defined.")
    objectives = mission_need.get("objectives", [])

    obj_text = "\n".join(f"  {i+1}. {o}" for i, o in enumerate(objectives)) if objectives else "  To be defined."

    # Operational modes table
    if operational_modes:
        mode_rows: list[str] = []
        for mode in operational_modes:
            mode_name = mode.get("name", mode.get("id", "Unknown"))
            active = mode.get("subsystems_active", [])
            active_str = ", ".join(active) if isinstance(active, list) else str(active)
            mode_rows.append(f"  | {mode_name:<20s} | {active_str}")

        mode_header = "  | Mode                 | Active Subsystems"
        mode_sep = "  |" + "-" * 22 + "|" + "-" * 60
        mode_table = "\n".join([mode_header, mode_sep] + mode_rows)
    else:
        mode_table = "  No operational modes defined."

    return _make_section(
        number="11",
        title="Architecture & Concept of Operations",
        content=(
            f"This section describes the system architecture and the concept of "
            f"operations (ConOps) for the {study_name} mission."
        ),
        subsections=[
            _sub("11.1", "Mission Need",
                 f"{problem}\n\nMission Objectives:\n{obj_text}"),
            _sub("11.2", "Operational Modes",
                 f"The spacecraft operates in the following modes:\n\n{mode_table}\n\n"
                 f"Each mode defines which subsystems are active, the power consumption "
                 f"profile, and the data generation rate.  Mode transitions are governed "
                 f"by the on-board autonomy and ground command rules."),
            _sub("11.3", "System Architecture",
                 "The system architecture decomposes the mission into space segment, "
                 "ground segment, and launch segment.  The space segment functional "
                 "decomposition follows ECSS-E-ST-10C and maps functions to physical "
                 "subsystems through the functional-physical allocation matrix."),
        ],
        auto_generated=True,
    )


def _section_12_schedule(
    review_dates: dict[str, str],
    mission_phases: list[dict[str, Any]],
) -> SempSection:
    # Build schedule summary
    if review_dates:
        review_lines = "\n".join(
            f"  - {gate}: {date}" for gate, date in sorted(review_dates.items())
        )
    else:
        review_lines = "  No review dates defined."

    total_days = sum(p.get("duration_days", 0) for p in mission_phases)
    total_months = total_days / 30.44 if total_days > 0 else 0
    total_years = total_days / 365.25 if total_days > 0 else 0

    return _make_section(
        number="12",
        title="Schedule",
        content=(
            f"The project schedule spans approximately {total_days} days "
            f"({total_months:.1f} months / {total_years:.1f} years) across all "
            f"mission phases.  The schedule is structured around the ECSS lifecycle "
            f"phases with Key Decision Points (KDPs) at each phase transition."
        ),
        subsections=[
            _sub("12.1", "Key Review Dates", review_lines),
            _sub("12.2", "Schedule Risk",
                 "Schedule margins are maintained by:\n"
                 "  - Including contingency in each phase duration\n"
                 "  - Identifying long-lead items early in Phase B\n"
                 "  - Tracking schedule performance against the baseline\n"
                 "  - Escalating schedule deviations at monthly progress meetings"),
            _sub("12.3", "Critical Path",
                 "The critical path is determined by the longest sequence of "
                 "dependent activities from PDR to launch.  Typically, this passes "
                 "through the primary structure manufacturing, AIT campaign, and "
                 "environmental test programme.  The critical path is monitored "
                 "using earned value management (EVM) metrics."),
        ],
        auto_generated=True,
    )


def _section_13_organisation(
    team_size: int | float,
    se_responsible: str,
) -> SempSection:
    return _make_section(
        number="13",
        title="Organisation",
        content=(
            f"The project team comprises approximately {int(team_size) if team_size else 'TBD'} "
            f"members.  The Systems Engineering function is led by "
            f"{se_responsible or 'the appointed Systems Engineer (TBD)'}."
        ),
        subsections=[
            _sub("13.1", "SE Responsibilities",
                 f"The Systems Engineer ({se_responsible or 'TBD'}) is responsible for:\n"
                 "  - Maintaining the SEMP and ensuring its implementation\n"
                 "  - Chairing the technical review process\n"
                 "  - Managing requirements traceability and verification\n"
                 "  - Coordinating subsystem interfaces\n"
                 "  - Maintaining design budgets and margins\n"
                 "  - Conducting trade studies and design optimisation\n"
                 "  - Reporting technical status to the Project Manager"),
            _sub("13.2", "Team Structure",
                 "The project is organised by engineering domain with each subsystem "
                 "lead reporting to the Systems Engineer.  The team structure follows "
                 "a concurrent engineering approach where all domains work in parallel "
                 "with frequent design iterations and cross-domain consistency checks."),
            _sub("13.3", "Competence & Training",
                 "Team members are selected based on domain expertise and experience "
                 "with similar missions.  Training on ECSS processes, tools, and the "
                 "SpaceCDF concurrent design environment is provided at project start."),
        ],
        auto_generated=False,
    )


def _section_14_sustainability_disposal(
    disposal_approach: str,
    orbit: dict[str, Any],
    design_life: float,
) -> SempSection:
    orbit_type = orbit.get("type", "").upper() if orbit else ""
    altitude = orbit.get("altitude_km", orbit.get("altitude", ""))
    orbit_desc = _describe_orbit(orbit)

    # Determine applicable debris mitigation guidelines
    if orbit_type in ("LEO", "SSO") or (altitude and _safe_float(altitude) < 2000):
        debris_guidance = (
            "For LEO missions, the spacecraft shall comply with the IADC Space Debris "
            "Mitigation Guidelines and the 25-year post-mission orbital lifetime rule "
            "(or the updated IADC 5-year recommendation).  A deorbit strategy must "
            "be defined that ensures atmospheric re-entry within the required timeframe."
        )
    elif orbit_type == "GEO":
        debris_guidance = (
            "For GEO missions, the spacecraft shall be re-orbited to a graveyard orbit "
            "at least 300 km above the GEO protected region at end of mission.  "
            "Sufficient propellant must be reserved for the re-orbit manoeuvre."
        )
    else:
        debris_guidance = (
            "Debris mitigation measures shall comply with the IADC Space Debris "
            "Mitigation Guidelines and applicable national regulations.  The specific "
            "disposal strategy depends on the final orbit selection."
        )

    return _make_section(
        number="14",
        title="Sustainability & Disposal",
        content=(
            f"The project addresses space sustainability through compliance with "
            f"international debris mitigation guidelines and responsible end-of-life "
            f"disposal planning.  The design lifetime is {design_life} years in "
            f"{orbit_desc}."
        ),
        subsections=[
            _sub("14.1", "Disposal Approach",
                 f"{disposal_approach or 'The disposal approach is to be defined during Phase B.'}\n\n"
                 f"{debris_guidance}"),
            _sub("14.2", "Passivation",
                 "At end of mission, the spacecraft will be passivated by:\n"
                 "  - Depleting or venting residual propellant\n"
                 "  - Disconnecting batteries from the bus\n"
                 "  - Disabling transmitters\n"
                 "  - Discharging any pressure vessels\n\n"
                 "Passivation procedures will be developed during Phase C and validated "
                 "during the system-level V&V campaign."),
            _sub("14.3", "Sustainability Considerations",
                 "The project considers the following sustainability aspects:\n"
                 "  - Minimising mission-related debris (no planned release of objects)\n"
                 "  - Collision avoidance capability during operations\n"
                 "  - Trackability by ground-based surveillance networks\n"
                 "  - Demisability assessment for re-entering components\n"
                 "  - Compliance with ESA Zero Debris Charter targets (where applicable)"),
        ],
        auto_generated=False,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_section(
    *,
    number: str,
    title: str,
    content: str,
    subsections: list[SempSubsection],
    auto_generated: bool,
) -> SempSection:
    return {
        "number": number,
        "title": title,
        "content": content,
        "subsections": subsections,
        "auto_generated": auto_generated,
    }


def _sub(number: str, title: str, content: str) -> SempSubsection:
    return {"number": number, "title": title, "content": content}


def _describe_orbit(orbit: dict[str, Any]) -> str:
    if not orbit:
        return "to be determined"
    parts: list[str] = []
    otype = orbit.get("type", "")
    alt = orbit.get("altitude_km", orbit.get("altitude", ""))
    inc = orbit.get("inclination_deg", orbit.get("inclination", ""))
    if otype:
        parts.append(otype.upper())
    if alt:
        parts.append(f"{alt} km altitude")
    if inc:
        parts.append(f"{inc} deg inclination")
    return ", ".join(parts) if parts else "to be determined"


def _default_model_level(subsystem: str, arch_selections: dict[str, Any]) -> str:
    """Infer a default model level based on subsystem type."""
    sel = arch_selections.get(subsystem, {})
    option_name = ""
    if isinstance(sel, dict):
        option_name = sel.get("option_name", "").lower()

    # Conservative defaults based on typical space engineering practice
    ss_lower = subsystem.lower()
    if any(kw in ss_lower for kw in ["payload", "instrument"]):
        return "EM + QM + FM"
    if any(kw in ss_lower for kw in ["structure", "thermal"]):
        return "STM + PFM"
    if any(kw in option_name for kw in ["cots", "heritage", "proven", "off-the-shelf"]):
        return "PFM"
    if any(kw in option_name for kw in ["novel", "new", "custom", "experimental"]):
        return "EM + QM + FM"
    return "EM + PFM"


def _model_rationale(level: str) -> str:
    """Return a brief rationale string for the given model level."""
    level_upper = level.upper()
    if "QM" in level_upper and "FM" in level_upper:
        return "Full qualification — low TRL or mission-critical item"
    if "PFM" in level_upper and "STM" in level_upper:
        return "Structural model + protoflight — structural verification needed"
    if "PFM" in level_upper:
        return "Protoflight approach — high heritage, acceptable risk"
    if "EM" in level_upper:
        return "Engineering model for early functional/interface testing"
    return "Standard model approach"


def _safe_float(val: Any) -> float:
    """Convert a value to float, returning 0.0 on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0
