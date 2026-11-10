"""SpaceCDF Word document family: regulatory. Shared regulatory stub (itu_api, iaru, rsssa, export, copuos, eol).

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
    _add_toc_placeholder,
    _setup_margins,
    _setup_styles,
)


def _generate_regulatory_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate a regulatory filing template document."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Regulatory Filing Template", "SpaceCDF Auto-Generated", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Mission Overview")
    mission_need = data.get("mission_need", {})
    doc.add_paragraph(mission_need.get("problem_statement", "To be defined"))
    _add_section(doc, "2", "Orbital Parameters")
    doc.add_paragraph(f"This section should be completed with the specific orbital parameters for the {study_name} mission.")
    _add_section(doc, "3", "Frequency Coordination")
    doc.add_paragraph("Frequency bands, bandwidths, EIRP, and coordination requirements to be specified per ITU Radio Regulations.")
    _add_section(doc, "4", "Spacecraft Characteristics")
    doc.add_paragraph("Mass, dimensions, power, and technical characteristics as required by the regulatory authority.")
    _add_section(doc, "5", "Compliance Statement")
    doc.add_paragraph("Statement of compliance with applicable regulations, standards, and guidelines.")
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
