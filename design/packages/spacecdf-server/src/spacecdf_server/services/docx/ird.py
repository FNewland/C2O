"""SpaceCDF Word document family: ird. Interface Requirements Document (IRD).

W1.09a: the interface tables come from the study (interfaces between segments, interfaces inside
the space segment, and the interface requirements, including the ``IR-*`` rows generated from the
links); nothing is hard-coded. Exchange items, electrical lines and bus nodes are W4.07.
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

    els = {e.get("id"): e for e in data.get("elements") or [] if e.get("id")}

    def seg(eid):
        cur, n = els.get(eid) or {}, 0
        while cur and not cur.get("segment") and cur.get("parent_id") in els and n < 50:
            cur, n = els[cur["parent_id"]], n + 1
        return (cur or {}).get("segment") or ""

    def row(i):
        a, b = i.get("source_element_id") or i.get("from_element_id"), i.get("target_element_id") or i.get("to_element_id")
        props = i.get("properties") if isinstance(i.get("properties"), dict) else {}
        detail = "; ".join(f"{k}: {v}" for k, v in props.items() if not isinstance(v, (dict, list)))
        return a, b, [i.get("name") or "", (els.get(a) or {}).get("name") or a or "", (els.get(b) or {}).get("name") or b or "",
                      str(i.get("interface_type") or i.get("type") or ""), i.get("status") or "", detail]

    ifs = sorted(data.get("interfaces") or [], key=lambda i: (str(i.get("interface_type") or ""), str(i.get("name") or "")))
    seg_rows, sub_rows = [], []
    for i in ifs:
        a, b, r = row(i)
        (seg_rows if seg(a) != seg(b) else sub_rows).append(r)
    headers = ["Interface", "From", "To", "Type", "Status", "Properties"]
    _add_section(doc, "2", "Mission Segment Interfaces")
    if seg_rows:
        _add_table(doc, headers, seg_rows)
    else:
        doc.add_paragraph("No interface between segments is recorded in the study yet.")
    _add_section(doc, "3", "Subsystem Interfaces")
    if sub_rows:
        _add_table(doc, headers, sub_rows)
    else:
        doc.add_paragraph("No interface inside a segment is recorded in the study yet.")
    irs = data.get("interface_requirements") or []
    _add_section(doc, "3.1", f"Interface Requirements ({len(irs)})")
    if irs:
        from .ts import threshold_text
        _add_table(doc, ["Code", "Requirement", "Threshold", "Method", "Parent", "Allocated to"],
                   [[r.get("code") or r.get("id", ""), r.get("text") or "", threshold_text(r),
                     r.get("verification_method") or "", r.get("parent_code") or "", r.get("allocated_to") or ""]
                    for r in irs])
    else:
        doc.add_paragraph("No interface requirement is recorded in the study yet.")

    _add_section(doc, "4", "Physical Interface Definitions")
    doc.add_paragraph("Connector definitions, pinouts, and harness routing to be defined during Phase C.")

    _add_diagrams(doc, "5", "Interface Diagrams", data,
                  "Drawn from the design model (the same figures as the SpaceCDF Diagrams view); "
                  "each figure lists what the model still lacks for it.")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
