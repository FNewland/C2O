"""SpaceCDF Word document family: ts. Technical Specification (TS).

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


def generate_ts_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate Technical Specification (ECSS-E-ST-10C Annex B)."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Technical Specification", "ECSS-E-ST-10C Annex B", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", "This document defines the technical requirements for the system and its elements.")
    _add_section(doc, "1.2", "Scope", f"Applicable to the {study_name} system at all levels of decomposition.")

    _add_section(doc, "2", "Applicable and Reference Documents")
    doc.add_paragraph("ECSS-E-ST-10C -- Space engineering -- System engineering general requirements")
    doc.add_paragraph("ECSS-Q-ST-40C -- Space product assurance -- Safety")

    _add_section(doc, "3", "System Description")
    mission_need = data.get("mission_need", {})
    doc.add_paragraph(mission_need.get("problem_statement", "To be defined"))

    _add_section(doc, "4", "Technical Requirements")
    reqs = data.get("requirements", [])
    if reqs:
        _add_table(doc, ["ID", "Type", "Requirement", "Threshold", "V-Method"],
                   [[r.get("id", ""), r.get("req_type", ""), r.get("text", "")[:80],
                     f"{r.get('operator', '')} {r.get('threshold', '')} {r.get('unit', '')}",
                     r.get("verification_method", "A")] for r in reqs[:80]])

    _add_section(doc, "5", "Interface Requirements")
    doc.add_paragraph("Interface requirements are defined in the IRD (separate document).")

    _add_section(doc, "6", "Design and Construction Standards")
    doc.add_paragraph("Per ECSS-Q-ST-70C for materials and processes. Workmanship per ECSS-Q-ST-70-08C.")

    _add_section(doc, "7", "Verification Requirements")
    doc.add_paragraph("Verification approach defined in the Verification Plan (VP). "
                      "All requirements shall be verified by at least one method: Analysis, Test, Inspection, or Demonstration.")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
