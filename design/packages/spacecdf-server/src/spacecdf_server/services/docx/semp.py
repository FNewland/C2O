"""SpaceCDF Word document family: semp. Systems Engineering Management Plan (SEMP).

Moved verbatim from services/docx_generator.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import (
    _add_cover_page,
    _add_diagrams,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _setup_margins,
    _setup_styles,
)


def generate_semp_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate Systems Engineering Management Plan (NASA SEH Appendix J)."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Systems Engineering Management Plan", "NASA SEH Appendix J / ECSS-M-ST-10C", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", "This SEMP defines the systems engineering approach, processes, and management controls.")
    _add_section(doc, "1.2", "Mission Overview")
    mission_need = data.get("mission_need", {})
    doc.add_paragraph(mission_need.get("problem_statement", "To be defined"))

    _add_section(doc, "2", "SE Organisation and Responsibilities")
    doc.add_paragraph("The SE team follows the CDF concurrent engineering model with 16 specialist positions.")
    _add_table(doc, ["Role", "Responsibility"],
               [["Systems Engineer", "Technical baseline, budgets, trade studies"],
                ["Mission Analyst", "Orbit, coverage, delta-V analysis"],
                ["Payload Lead", "Instrument performance, data products"],
                ["Power Engineer", "EPS sizing, energy balance"],
                ["AOCS Engineer", "Pointing, orbit maintenance"],
                ["Comms Engineer", "Link budget, TTC design"],
                ["Thermal Engineer", "Thermal control, analysis"],
                ["Structures Engineer", "Configuration, mass budget, AIT"]])

    _add_section(doc, "3", "Technical Processes")
    _add_section(doc, "3.1", "Requirements Engineering", "Suggest-then-approve pattern with SMART validation. Requirements linked to functions and traced to objectives.")
    _add_section(doc, "3.2", "Architecture Design", "Trade studies per subsystem with derived requirements. Options evaluated on mass, power, cost, TRL.")
    _add_section(doc, "3.3", "Interface Management", "Interfaces captured at segment and subsystem level. Managed via interface matrix.")
    _add_section(doc, "3.4", "Verification & Validation", "V&V matrix per ECSS-E-ST-10-02C. Methods: Analysis, Test, Inspection, Demonstration.")

    _add_section(doc, "4", "Technical Management Processes")
    _add_section(doc, "4.1", "Configuration Management", "Design baselines at SRR, PDR, CDR. Change control via board.")
    _add_section(doc, "4.2", "Risk Management", "5x5 risk matrix per ECSS-M-ST-80C. Continuous monitoring.")
    _add_section(doc, "4.3", "Technical Budgets", "Mass, power, link, pointing, delta-V, data, cost. Margins per ECSS design phase.")

    _add_section(doc, "5", "Reviews and Decision Gates")
    _add_table(doc, ["Review", "Phase Entry", "Key Deliverables"],
               [["MDR", "0 \u2192 A", "Mission Need Statement, ConOps outline"],
                ["PRR", "A \u2192 B", "Preliminary requirements, product and function trees, budgets with margins"],
                ["SRR", "B", "Requirements baseline, functional architecture"],
                ["PDR", "B \u2192 C", "Preliminary design, budgets with margin"],
                ["CDR", "C \u2192 D", "Detailed design, manufacturing drawings, test plan"],
                ["TRR", "D (test)", "Qualified hardware, test procedures"],
                ["FRR", "D (launch)", "Flight-ready spacecraft, ops procedures"]])

    _add_diagrams(doc, "6", "System Diagrams", data,
                  "Operations concept, architecture, interfaces, requirements and risk figures drawn from the design "
                  "model (the same figures as the SpaceCDF Diagrams view). The gate and maturity each figure is "
                  "expected at follow its caption (D draft, B baselined, U updated).")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
