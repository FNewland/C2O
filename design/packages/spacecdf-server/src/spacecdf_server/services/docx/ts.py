"""SpaceCDF Word document family: ts. Technical Specification (TS).

W1.09a: every requirement the team entered (no row cap), by level then code, with code, type,
threshold (``threshold_op`` + ``threshold_value`` [+ unit]), verification method, parent,
allocation and rationale. Interface requirements generated from links (``IR-*``) are in the IRD.
The type grouping and the environment section are W4.06.
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


def threshold_text(r: dict[str, Any]) -> str:
    """``>= 10`` / ``<= 30 s``: the stored threshold of a requirement ("" when none)."""
    val = r.get("threshold_value")
    if val is None or val == "":
        return ""
    if isinstance(val, float) and val == int(val):
        val = int(val)
    parts = [str(r.get("threshold_op") or ""), str(val), str(r.get("unit") or r.get("threshold_unit") or "")]
    return " ".join(p for p in parts if p).strip()


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
    reqs = [r for r in data.get("requirements", []) if not str(r.get("code") or "").startswith("IR-")]
    if reqs:
        levels: list[str] = []
        for r in reqs:
            if (r.get("level") or "") not in levels:
                levels.append(r.get("level") or "")
        doc.add_paragraph(f"{len(reqs)} requirements, by level ({', '.join(l for l in levels if l)}) then code.")
        for i, lvl in enumerate(levels, start=1):
            rows = [r for r in reqs if (r.get("level") or "") == lvl]
            _add_section(doc, f"4.{i}", f"{(lvl or 'Unspecified').capitalize()} requirements ({len(rows)})")
            _add_table(doc, ["Code", "Type", "Requirement", "Threshold", "Method", "Parent", "Allocated to", "Rationale"],
                       [[r.get("code") or r.get("id", ""), r.get("req_type") or "", r.get("text") or "",
                         threshold_text(r), r.get("verification_method") or "", r.get("parent_code") or "",
                         r.get("allocated_to") or "", r.get("rationale") or ""] for r in rows])
    else:
        doc.add_paragraph("No requirements have been entered for this study.")

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
