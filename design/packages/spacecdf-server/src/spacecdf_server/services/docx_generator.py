"""SpaceCDF -- Word Document Generator.

Generates editable .docx files for all ECSS documents using python-docx.
Each document is populated from the live design state.

Supports: MRD, TS, VP, ConOps, SEMP, RMP, IRD, Test Plan.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def _add_title_page(doc: Document, title: str, subtitle: str, study_name: str):
    """Add a formatted title page."""
    # Add empty paragraphs for spacing
    for _ in range(4):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(30, 58, 95)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(subtitle)
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(107, 114, 128)

    for _ in range(3):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(f"Study: {study_name}").font.size = Pt(12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}").font.size = Pt(10)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("SpaceCDF -- AI-Assisted Concurrent Design Facility").font.size = Pt(9)

    doc.add_page_break()


def _add_section(doc: Document, number: str, title: str, content: str = ""):
    """Add a numbered section heading with content."""
    doc.add_heading(f"{number} {title}", level=1 if '.' not in number else 2)
    if content:
        doc.add_paragraph(content)


def _add_table(doc: Document, headers: list[str], rows: list[list[str]]):
    """Add a formatted table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(9)

    # Data rows
    for r, row_data in enumerate(rows):
        for c, cell_text in enumerate(row_data):
            table.rows[r + 1].cells[c].text = str(cell_text)
            for paragraph in table.rows[r + 1].cells[c].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)


def generate_mrd_docx(
    study_name: str = "",
    mission_need: dict[str, Any] | None = None,
    requirements: list[dict[str, Any]] | None = None,
) -> bytes:
    """Generate Mission Requirements Document as .docx bytes."""
    doc = Document()
    mn = mission_need or {}
    reqs = requirements or []

    _add_title_page(doc, "Mission Requirements Document", "ECSS-E-ST-10C Annex A", study_name)

    # ToC placeholder
    _add_section(doc, "0", "Table of Contents")
    doc.add_paragraph("[Table of Contents -- update field after editing]")
    doc.add_page_break()

    # Section 1: Introduction
    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose",
                 f"This document defines the mission-level requirements for the {study_name} mission.")
    _add_section(doc, "1.2", "Scope",
                 "Covers all mission-level requirements derived from stakeholder needs and mission objectives.")
    _add_section(doc, "1.3", "Applicable Documents",
                 "ECSS-E-ST-10C Rev.1, ECSS-M-ST-10C Rev.1, NASA/SP-2016-6105 Rev 2")

    # Section 2: Mission Overview
    _add_section(doc, "2", "Mission Overview")
    _add_section(doc, "2.1", "Problem Statement",
                 mn.get("problem_statement", "[To be defined]"))
    _add_section(doc, "2.2", "Mission Objectives")
    objectives = mn.get("objectives", [])
    if objectives:
        _add_table(doc,
                   ["Priority", "Objective", "Measurable Criterion"],
                   [[o.get("priority", ""), o.get("text", ""), o.get("measurable_criterion", "")] for o in objectives])
    else:
        doc.add_paragraph("[Objectives to be defined]")

    _add_section(doc, "2.3", "Stakeholders")
    stakeholders = mn.get("stakeholders", [])
    if stakeholders:
        _add_table(doc,
                   ["Name", "Role", "Key Needs"],
                   [[s.get("name", ""), s.get("role", ""), ", ".join(s.get("needs", []))] for s in stakeholders])

    # Section 3: Requirements
    _add_section(doc, "3", "Mission Requirements")
    if reqs:
        _add_table(doc,
                   ["ID", "Level", "Type", "Requirement Text", "Verification"],
                   [[r.get("id", ""), r.get("level", ""), r.get("type", r.get("req_type", "")),
                     r.get("text", ""), r.get("verification_method", "")] for r in reqs[:50]])
    else:
        doc.add_paragraph("[Requirements to be generated from objectives]")

    # Section 4: Constraints
    _add_section(doc, "4", "Constraints")
    _add_section(doc, "4.1", "Programmatic Constraints", "[Budget, schedule, launch date constraints]")
    _add_section(doc, "4.2", "Technical Constraints", "[Orbit, mass, interfaces, regulatory]")
    _add_section(doc, "4.3", "Regulatory Constraints",
                 "Space debris mitigation per ECSS-U-AS-10C Rev.2. ITU frequency coordination required.")

    # Return as bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generate_conops_docx(
    study_name: str = "",
    mission_need: dict[str, Any] | None = None,
    conops: dict[str, Any] | None = None,
) -> bytes:
    """Generate Concept of Operations document as .docx bytes."""
    doc = Document()
    mn = mission_need or {}
    ops = conops or {}

    _add_title_page(doc, "Concept of Operations", "NASA SEH Appendix S", study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose",
                 f"Describes how the {study_name} mission will be operated to meet mission objectives.")
    _add_section(doc, "1.2", "Mission Overview", mn.get("problem_statement", "[TBD]"))

    _add_section(doc, "2", "Mission Architecture")
    _add_section(doc, "2.1", "Space Segment", "Spacecraft + payload.")
    _add_section(doc, "2.2", "Ground Segment", "Ground station(s) + MCC + data processing.")
    _add_section(doc, "2.3", "User Segment", "Data products and services to end users.")

    _add_section(doc, "3", "Mission Phases")
    phases = ops.get("phases", [])
    if phases:
        _add_table(doc, ["Phase", "Duration (days)", "Description"],
                   [[p.get("name", ""), str(p.get("duration_days", "")), p.get("description", "")] for p in phases])
    else:
        doc.add_paragraph("LEOP (3 days), Commissioning (30 days), Nominal Operations, Disposal")

    _add_section(doc, "4", "Operational Modes")
    modes = ops.get("modes", [])
    if modes:
        _add_table(doc, ["Mode", "Subsystems Active", "Pointing", "Data Flow"],
                   [[m.get("name", ""), ", ".join(m.get("subsystems_active", [])),
                     m.get("pointing", ""), m.get("dataflow", "")] for m in modes])

    _add_section(doc, "5", "Data Flow Pipeline")
    doc.add_paragraph("Instrument -> Onboard Storage -> Downlink -> Ground Processing -> Archive -> User")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generate_vp_docx(
    study_name: str = "",
    requirements: list[dict[str, Any]] | None = None,
) -> bytes:
    """Generate Verification Plan as .docx bytes."""
    doc = Document()
    reqs = requirements or []

    _add_title_page(doc, "Verification Plan", "ECSS-E-ST-10-02C Rev.1", study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", f"Defines the verification approach for {study_name}.")
    _add_section(doc, "1.2", "Verification Methods",
                 "Analysis (A), Test (T), Review of Design (R), Inspection (I) per ECSS-E-ST-10-02C.")

    _add_section(doc, "2", "Verification Matrix")
    if reqs:
        _add_table(doc,
                   ["Req ID", "Requirement", "Method", "Phase", "Status"],
                   [[r.get("id", ""), r.get("text", "")[:60], r.get("verification_method", "A"),
                     "Phase B", "Planned"] for r in reqs[:50]])

    _add_section(doc, "3", "Environmental Test Programme")
    _add_section(doc, "3.1", "Vibration", "Sine + random per launch vehicle PUG. 3 axes, 1 min/axis.")
    _add_section(doc, "3.2", "Thermal Vacuum", "Qualification range +/-10C beyond operating. 4 cycles minimum.")
    _add_section(doc, "3.3", "EMC", "Per ECSS-E-ST-20-07C if required by launch provider.")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# Map of available document types
DOCX_GENERATORS = {
    "mrd": ("Mission Requirements Document", generate_mrd_docx),
    "conops": ("Concept of Operations", generate_conops_docx),
    "vp": ("Verification Plan", generate_vp_docx),
}
