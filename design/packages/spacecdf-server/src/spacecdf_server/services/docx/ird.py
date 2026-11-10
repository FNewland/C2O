"""SpaceCDF Word document family: ird. Interface Requirements Document (IRD).

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


def generate_ird_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate Interface Requirements Document (NASA SEH Appendix L)."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Interface Requirements Document", "NASA SEH Appendix L / ECSS-E-ST-10-24C", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", "This document defines the interfaces between mission segments and between subsystems.")
    _add_section(doc, "1.2", "Scope", "Covers mechanical, electrical, data, and RF interfaces.")

    _add_section(doc, "2", "Mission Segment Interfaces")
    _add_table(doc, ["Interface", "Segment A", "Segment B", "Type", "Description"],
               [["IF-001", "Space", "Ground", "RF", "S/X-band TM/TC link"],
                ["IF-002", "Space", "Ground", "RF", "Payload data downlink"],
                ["IF-003", "Ground", "User", "Data", "Data products via API/FTP"],
                ["IF-004", "Launch", "Space", "Mechanical", "Separation interface per PUG"],
                ["IF-005", "External", "Space", "RF", "GNSS signals for orbit determination"]])

    _add_section(doc, "3", "Subsystem Interfaces")
    _add_table(doc, ["Interface", "From", "To", "Type", "Protocol/Standard"],
               [["IF-101", "OBC", "EPS", "Electrical", "I2C power telemetry"],
                ["IF-102", "OBC", "TTC", "Data", "CCSDS TM/TC packets"],
                ["IF-103", "OBC", "Payload", "Data", "SpaceWire/LVDS"],
                ["IF-104", "EPS", "All", "Electrical", "28V regulated bus"],
                ["IF-105", "AOCS", "Payload", "Data", "Attitude quaternion @ 10Hz"]])

    _add_section(doc, "4", "Physical Interface Definitions")
    doc.add_paragraph("Connector definitions, pinouts, and harness routing to be defined during Phase C.")

    _add_diagrams(doc, "5", "Interface Diagrams", data,
                  "Drawn from the design model (the same figures as the SpaceCDF Diagrams view); "
                  "each figure lists what the model still lacks for it.")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
