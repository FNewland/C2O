"""SpaceCDF Word document family: mrd. Mission Requirements Document (MRD).

Moved verbatim from services/docx_generator.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document
from docx.shared import Pt

from ._common import (
    _add_cover_page,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _render_rich_content,
    _setup_margins,
    _setup_styles,
)


# ---------------------------------------------------------------------------
# Legacy per-type generators (preserved for backward compat)
# ---------------------------------------------------------------------------

def generate_mrd_docx(
    study_name: str = "",
    mission_need: dict[str, Any] | None = None,
    requirements: list[dict[str, Any]] | None = None,
    orbit: dict[str, Any] | None = None,
    elements: list[dict[str, Any]] | None = None,
) -> bytes:
    """Generate Mission Requirements Document as .docx bytes."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    mn = mission_need or {}
    reqs = requirements or []
    orb = orbit or {}
    elems = elements or []

    _add_cover_page(doc, "Mission Requirements Document", "ECSS-E-ST-10C Annex A", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    # ── Section 1: Executive Summary ──
    _add_section(doc, "1", "Executive Summary")
    problem = mn.get("problem_statement", "")
    sel_rationale = mn.get("selection_rationale", "")
    if problem:
        summary_text = problem
        if sel_rationale:
            summary_text += f"\n\n{sel_rationale}"
        _render_rich_content(doc, summary_text)
    else:
        doc.add_paragraph(
            f"This Mission Requirements Document (MRD) defines the mission-level and "
            f"system-level requirements for the {study_name} mission. It captures "
            f"stakeholder needs, mission objectives, the alternatives analysis, and "
            f"the traceable requirements baseline."
        )

    # ── Section 2: Mission Need ──
    _add_section(doc, "2", "Mission Need")
    _add_section(doc, "2.1", "Problem Statement",
                 mn.get("problem_statement", "[To be defined]"))
    _add_section(doc, "2.2", "Operational Context",
                 mn.get("operational_context", "[To be defined]"))

    # ── Section 3: Stakeholder Register ──
    _add_section(doc, "3", "Stakeholder Register")
    stakeholders = mn.get("stakeholders", [])
    if stakeholders:
        _add_table(doc,
                   ["Name", "Role", "Key Needs", "Priority"],
                   [
                       [
                           s.get("name", ""),
                           s.get("role", ""),
                           ", ".join(s.get("needs", [])) if isinstance(s.get("needs"), list) else str(s.get("needs", "")),
                           s.get("priority", ""),
                       ]
                       for s in stakeholders
                   ])
    else:
        doc.add_paragraph("[Stakeholder register to be populated]")

    # ── Section 4: Mission Objectives ──
    _add_section(doc, "4", "Mission Objectives")
    objectives = mn.get("objectives", [])
    if objectives:
        _add_table(doc,
                   ["ID", "Objective", "Priority", "Measurable Criterion", "Status"],
                   [
                       [
                           o.get("id", ""),
                           o.get("text", ""),
                           o.get("priority", ""),
                           o.get("measurable_criterion", ""),
                           o.get("status", "proposed"),
                       ]
                       for o in objectives
                   ])
    else:
        doc.add_paragraph("[Objectives to be defined]")

    # ── Section 5: Alternatives Analysis ──
    _add_section(doc, "5", "Alternatives Analysis")
    alternatives = mn.get("alternatives", [])
    if alternatives:
        _add_table(doc,
                   ["Name", "Type", "Pros", "Cons", "Feasibility", "Decision"],
                   [
                       [
                           a.get("name", ""),
                           a.get("type", ""),
                           "; ".join(a.get("pros", [])) if isinstance(a.get("pros"), list) else str(a.get("pros", "")),
                           "; ".join(a.get("cons", [])) if isinstance(a.get("cons"), list) else str(a.get("cons", "")),
                           f"{a.get('feasibility_score', 0):.1f}" if a.get("feasibility_score") else "",
                           a.get("decision", ""),
                       ]
                       for a in alternatives
                   ])
    else:
        doc.add_paragraph("[Alternatives analysis to be performed]")

    # ── Section 6: Selected Concept ──
    _add_section(doc, "6", "Selected Concept")
    sel_alt_id = mn.get("selected_alternative_id")
    selected_alt = None
    if sel_alt_id and alternatives:
        selected_alt = next((a for a in alternatives if a.get("id") == sel_alt_id), None)
    if selected_alt:
        p = doc.add_paragraph()
        run = p.add_run(f"Selected concept: {selected_alt.get('name', '')}")
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(10)
        if selected_alt.get("description"):
            doc.add_paragraph(selected_alt["description"])
    _add_section(doc, "6.1", "Selection Rationale",
                 mn.get("selection_rationale", "[To be documented]"))

    # ── Section 7: Mission Requirements ──
    _add_section(doc, "7", "Mission Requirements")
    mission_reqs = [r for r in reqs if r.get("level", "").lower() == "mission"]
    if mission_reqs:
        _add_table(doc,
                   ["ID", "Code", "Type", "Requirement Text", "Verification"],
                   [
                       [
                           r.get("id", "")[:12],
                           r.get("code", ""),
                           r.get("type", r.get("req_type", "")),
                           r.get("text", ""),
                           r.get("verification_method", ""),
                       ]
                       for r in mission_reqs[:80]
                   ])
    elif reqs:
        doc.add_paragraph(
            f"No requirements are tagged with level='mission'. "
            f"Showing all {len(reqs)} requirements below in Section 8."
        )
    else:
        doc.add_paragraph("[Requirements to be generated from objectives]")

    # ── Section 8: System Requirements ──
    _add_section(doc, "8", "System Requirements")
    system_reqs = [r for r in reqs if r.get("level", "").lower() == "system"]
    if system_reqs:
        _add_table(doc,
                   ["ID", "Code", "Type", "Requirement Text", "Verification"],
                   [
                       [
                           r.get("id", "")[:12],
                           r.get("code", ""),
                           r.get("type", r.get("req_type", "")),
                           r.get("text", ""),
                           r.get("verification_method", ""),
                       ]
                       for r in system_reqs[:80]
                   ])
    elif not mission_reqs and reqs:
        # No level-tagged reqs -- show all
        _add_table(doc,
                   ["ID", "Code", "Level", "Type", "Requirement Text", "Verification"],
                   [
                       [
                           r.get("id", "")[:12],
                           r.get("code", ""),
                           r.get("level", ""),
                           r.get("type", r.get("req_type", "")),
                           r.get("text", ""),
                           r.get("verification_method", ""),
                       ]
                       for r in reqs[:80]
                   ])
    else:
        doc.add_paragraph("[System requirements to be derived from mission requirements]")

    # ── Section 9: Orbit & Payload Summary ──
    _add_section(doc, "9", "Orbit & Payload Summary")
    if orb:
        orbit_rows = [
            ["Orbit Type", str(orb.get("orbit_type", "TBD"))],
            ["Altitude", f"{orb.get('altitude_km', 'TBD')} km"],
            ["Inclination", f"{orb.get('inclination_deg', 'TBD')} deg"],
            ["Eccentricity", str(orb.get("eccentricity", "TBD"))],
            ["Design Lifetime", f"{orb.get('design_lifetime_years', 'TBD')} years"],
        ]
        if orb.get("period_min"):
            orbit_rows.append(["Orbital Period", f"{orb['period_min']} min"])
        if orb.get("eclipse_fraction"):
            orbit_rows.append(["Eclipse Fraction", f"{orb['eclipse_fraction']}"])
        _add_table(doc, ["Parameter", "Value"], orbit_rows)
    else:
        doc.add_paragraph("[Orbit parameters to be defined]")

    # Payload elements
    payload_elems = [e for e in elems if e.get("subsystem_domain") == "payload"]
    if payload_elems:
        _add_section(doc, "9.1", "Payloads")
        _add_table(doc,
                   ["Name", "Mass (kg)", "Power (W)", "Data Rate"],
                   [
                       [
                           e.get("name", ""),
                           str(e.get("mass_kg", "")),
                           str(e.get("power_avg_w", "")),
                           str((e.get("performance") or {}).get("data_rate_mbps", "")),
                       ]
                       for e in payload_elems
                   ])

    # ── Section 10: Constraints ──
    _add_section(doc, "10", "Constraints")
    _add_section(doc, "10.1", "Programmatic Constraints",
                 "[Budget, schedule, launch date constraints]")
    _add_section(doc, "10.2", "Technical Constraints",
                 "[Orbit, mass, interfaces, regulatory]")
    _add_section(doc, "10.3", "Regulatory Constraints",
                 "Space debris mitigation per ECSS-U-AS-10C Rev.2. ITU frequency coordination required.")

    # Return as bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
