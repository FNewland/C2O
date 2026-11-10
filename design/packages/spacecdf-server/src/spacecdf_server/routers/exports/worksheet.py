"""SpaceCDF export family: worksheet.

Branded blank DOCX worksheets for the course.
Routes (prefix /api/exports): POST /worksheet/{template_id}

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse


router = APIRouter()

# ─── Branded DOCX Worksheets ───

WORKSHEET_TEMPLATES = {
    "mission_need": {
        "title": "Mission Need Statement Worksheet",
        "sections": [
            ("1. Problem Statement", "What problem does this mission solve? Who is affected?"),
            ("2. Operational Context", "When, where, and how will mission products be used?"),
            ("3. Stakeholder Register", "Name / Role / Key Needs / Priority"),
            ("4. Mission Objectives", "ID / Objective / Priority / Measurable Criterion"),
            ("5. Success Criteria", "What constitutes mission success?"),
        ],
    },
    "trade_study": {
        "title": "Trade Study Worksheet",
        "sections": [
            ("1. Trade Context", "What decision is being made? What are the constraints?"),
            ("2. Evaluation Criteria", "Criterion / Weight / Direction / Threshold"),
            ("3. Options Under Consideration", "Option / Description / Pros / Cons"),
            ("4. Scoring Matrix", "Use Pugh Matrix or Weighted Scoring in Decide tab."),
            ("5. Decision and Rationale", "Selected option / Rationale / Dissenting opinions"),
        ],
    },
    "requirements": {
        "title": "Requirements Derivation Worksheet",
        "sections": [
            ("1. Parent Requirement", "Code / Text / Level"),
            ("2. Derived Requirements", "Code / Level / Text / Verification Method / Element"),
            ("3. Traceability Check", "All derived trace to parent? All parent covered?"),
            ("4. SMART Validation", "Specific? Measurable? Achievable? Relevant? Traceable?"),
        ],
    },
    "subsystem_design": {
        "title": "Subsystem Design Worksheet",
        "sections": [
            ("1. Subsystem Identification", "Name / Domain / Parent system / Driving requirement"),
            ("2. Architecture Options", "Option / Mass / Power / Cost / TRL / Notes"),
            ("3. Selected Architecture", "Selection / Rationale"),
            ("4. Budget Allocation", "Mass / Power / Cost allocations"),
            ("5. Interfaces", "Interface / Type / To-From / Direction / Properties"),
        ],
    },
    "equipment_selection": {
        "title": "Equipment Selection Worksheet",
        "sections": [
            ("1. Subsystem and Budget", "Subsystem / Mass budget / Power budget / Cost budget"),
            ("2. Candidate Components", "Component / Manufacturer / Mass / Power / Cost / TRL"),
            ("3. Selection and Rationale", "Selected / Rationale / Margin remaining"),
            ("4. Verification", "Inspection / Analysis / Test / Demonstration"),
        ],
    },
}


@router.post("/worksheet/{template_id}")
async def generate_worksheet(template_id: str) -> StreamingResponse:
    """Generate a branded DOCX worksheet template."""
    if template_id not in WORKSHEET_TEMPLATES:
        raise HTTPException(400, f"Unknown worksheet: {template_id}. Available: {list(WORKSHEET_TEMPLATES.keys())}")

    from ...services.branding import create_branded_docx
    from docx.shared import Pt

    tmpl = WORKSHEET_TEMPLATES[template_id]
    doc = create_branded_docx(tmpl["title"], "Worksheet Template")
    if doc is None:
        raise HTTPException(500, "python-docx not available")

    for heading, content in tmpl["sections"]:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(content)
        # Add blank lines for writing
        for _ in range(3):
            p = doc.add_paragraph("")
            p.style.font.size = Pt(11)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="SpaceCDF_Worksheet_{template_id}.docx"'},
    )
