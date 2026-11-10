"""SpaceCDF Word document family: testplan. Test plan (/docx/testplan stub).

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


def generate_testplan_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate Test Plan (ECSS-E-ST-10-03C)."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Test Plan", "ECSS-E-ST-10-03C / ECSS-E-ST-10-02C", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", "This plan defines the test programme for qualification and acceptance of the spacecraft.")

    _add_section(doc, "2", "Test Philosophy")
    doc.add_paragraph("Protoflight approach: single model subjected to qualification levels with acceptance durations. "
                      "Per ECSS-E-ST-10-03C for CubeSat/small satellite class.")

    _add_section(doc, "3", "Test Programme")
    _add_table(doc, ["Test", "Level", "Standard", "Facility", "Duration"],
               [["Vibration (Sine)", "Qualification", "Launch vehicle PUG", "Shaker table", "3 axes, 2 min/axis"],
                ["Vibration (Random)", "Qualification", "Launch vehicle PUG", "Shaker table", "3 axes, 1 min/axis"],
                ["Thermal Vacuum", "Qualification", "+/-10 deg C beyond op range", "TVAC chamber", "4 cycles, 2h dwell"],
                ["Thermal Cycling", "Acceptance", "Operating range", "Chamber", "8 cycles, 1h dwell"],
                ["EMC/EMI", "Qualification", "ECSS-E-ST-20-07C", "Anechoic chamber", "1 day"],
                ["Functional", "Acceptance", "N/A", "Clean room", "Continuous"],
                ["Mass Properties", "Acceptance", "N/A", "Balance fixture", "1 day"],
                ["Deployment", "Qualification", "N/A", "0g simulator", "100+ actuations"]])

    _add_section(doc, "4", "Test Sequence")
    doc.add_paragraph("1. Incoming inspection -> 2. Functional test (baseline) -> 3. Vibration -> "
                      "4. Functional test -> 5. TVAC -> 6. Functional test -> 7. EMC -> "
                      "8. Final functional test -> 9. Mass properties -> 10. Delivery/integration.")

    _add_section(doc, "5", "Pass/Fail Criteria")
    doc.add_paragraph("All functional tests must pass with identical results pre- and post-environmental. "
                      "Any degradation triggers NCR (Non-Conformance Report) and MRB (Material Review Board).")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
