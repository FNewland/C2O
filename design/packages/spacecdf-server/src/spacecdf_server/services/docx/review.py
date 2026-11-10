"""SpaceCDF Word document family: review. Review package stub (/docx/srr|pdr|cdr).

Moved verbatim from services/docx_generator.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import (
    _add_cover_page,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _setup_margins,
    _setup_styles,
)


def _generate_review_package_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate a design review data package (SRR/PDR/CDR)."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Design Review Data Package", "SpaceCDF Auto-Generated", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Review Objectives")
    doc.add_paragraph("This document compiles the design data package for review.")
    _add_section(doc, "2", "Mission Summary")
    mission_need = data.get("mission_need", {})
    doc.add_paragraph(mission_need.get("problem_statement", "To be defined"))
    _add_section(doc, "3", "Requirements Status")
    reqs = data.get("requirements", [])
    if reqs:
        _add_table(doc, ["ID", "Requirement", "Status"],
                   [[r.get("id", ""), r.get("text", "")[:60], r.get("status", "draft")] for r in reqs[:50]])
    _add_section(doc, "4", "Design Summary")
    doc.add_paragraph("Key design parameters and architecture decisions.")
    _add_section(doc, "5", "Budget Status")
    doc.add_paragraph("Mass, power, cost, link margin status vs allocation.")
    _add_section(doc, "6", "Risk Register")
    doc.add_paragraph("Current risk status and mitigations.")
    _add_section(doc, "7", "Open Actions")
    doc.add_paragraph("Actions from previous reviews and their status.")
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
