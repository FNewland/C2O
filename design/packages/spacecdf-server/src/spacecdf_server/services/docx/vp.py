"""SpaceCDF Word document family: vp. Verification Plan (VP).

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


def generate_vp_docx(
    study_name: str = "",
    requirements: list[dict[str, Any]] | None = None,
) -> bytes:
    """Generate Verification Plan as .docx bytes."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    reqs = requirements or []

    _add_cover_page(doc, "Verification Plan", "ECSS-E-ST-10-02C Rev.1", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

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
