"""SpaceCDF Word document family: review. Review package stub (/docx/srr|pdr|cdr).

W1.09a: requirements by level then code, no row cap, with code and threshold; the risk
register too. The full gate-specific packs are ``POST /api/exports/docs/{id}?review=`` (W4.02);
this stub is retired in W4.14.
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
    reqs = [r for r in reqs if not str(r.get("code") or "").startswith("IR-")]
    if reqs:
        from .ts import threshold_text
        _add_table(doc, ["Code", "Level", "Requirement", "Threshold", "Method", "Status"],
                   [[r.get("code") or r.get("id", ""), r.get("level") or "", r.get("text") or "", threshold_text(r),
                     r.get("verification_method") or "", r.get("status", "draft")] for r in reqs])
    _add_section(doc, "4", "Design Summary")
    doc.add_paragraph("The design, budgets and analyses of the study are in the gate-specific review data pack "
                      "(Export drawer, Design Reviews).")
    _add_section(doc, "5", "Budget Status")
    doc.add_paragraph("The budgets of the study (roll-up of the selected equipment) are in the review data pack "
                      "and its master budget workbook.")
    _add_section(doc, "6", "Risk Register")
    risks = data.get("risks") or []
    if risks:
        _add_table(doc, ["ID", "Risk", "L x C", "Status", "Mitigation"],
                   [[r.get("id", ""), r.get("description") or r.get("title") or "",
                     str(r.get("score") or ""), r.get("status") or "", r.get("mitigation") or ""] for r in risks])
    else:
        doc.add_paragraph("The study has no risk in its register yet.")
    _add_section(doc, "7", "Open Actions")
    doc.add_paragraph("Actions from previous reviews and their status.")
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
