"""SpaceCDF Word document family: did. Universal DID renderer (any {sections:[...]} JSON, e.g. the VCD).

Moved verbatim from services/docx_generator.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any


from ._common import _BRAND, _theme
from ._common import (
    _heading_level,
    _render_rich_content,
)


# ---------------------------------------------------------------------------
# Universal DID-to-DOCX renderer
# ---------------------------------------------------------------------------

def generate_did_docx(did_json: dict[str, Any]) -> bytes:
    """Convert a DID JSON response into a styled .docx file.

    Works for ALL document types (MRD, TS, IRD, ConOps, SEMP, RMP, Test Plan,
    etc.) since they all share the structure:
      {
        document: str,
        standard: str,
        study_name: str,
        document_code: str            (optional — defaults to standard)
        issue: str                    (optional — defaults to "1.0")
        classification: str           (optional — defaults to "Internal")
        acronyms: dict[str,str]       (optional — adds an acronym table)
        applicable_documents: list    (optional — list of {id,ref,title})
        reference_documents: list     (optional — list of {id,ref,title})
        change_record: list           (optional — list of {issue,date,by,summary})
        sections: [
          {number, title, content, subsections: [...]}
        ]
      }

    Content strings may contain:
      - Pipe-delimited tables
      - Bullet lists (lines starting with "- " or "* ")
      - Bold markers (**text**)
      - Plain text paragraphs
      - Any mix of the above
    """
    doc = _theme.new_document()
    _theme.reset_counters()

    title = did_json.get("document", "SpaceCDF Document")
    standard = did_json.get("standard", "")
    study_name = did_json.get("study_name", "Unnamed Mission")
    generated = did_json.get("generated", "")
    date_str = generated[:10] if generated else datetime.now().strftime("%Y-%m-%d")
    document_code = did_json.get("document_code") or standard or "SCDF-DOC"
    issue = did_json.get("issue", "1.0")
    classification = did_json.get("classification", "Internal · DRAFT")

    # Cover page
    _theme.add_cover_page(
        doc,
        title=title,
        subtitle=standard,
        document_code=document_code,
        study_name=study_name,
        issue=issue,
        date=date_str,
        classification=classification,
        cohort="SpaceCDF",
        publisher=_BRAND.publisher,
    )

    # Page furniture (header rule + bilingual footer with Page X of / de Y)
    _theme.add_page_furniture(
        doc,
        running_title=f"SpaceCDF — {title}",
        document_code=document_code,
        footer_left=f"{document_code} · {study_name}",
        footer_right=_BRAND.footer_brand,
    )

    # Document information & change record
    _theme.add_doc_info_table(
        doc, document_code=document_code, title=title,
        study_name=study_name, issue=issue, date=date_str,
        classification=classification, applies_to=study_name,
    )
    if did_json.get("change_record"):
        _theme.add_change_record(doc, did_json["change_record"])
    else:
        _theme.add_change_record(doc, [
            {"issue": issue, "date": date_str, "by": "SpaceCDF",
             "summary": f"Initial issue of {title}."}
        ])

    # AIG (Peters 2023) acknowledgement — applies to every exported document
    _theme.add_aig_acknowledgement(doc)

    # Acronyms & references (optional)
    if did_json.get("acronyms"):
        _theme.add_acronyms_table(doc, did_json["acronyms"])
    if did_json.get("applicable_documents"):
        _theme.add_reference_list(doc, did_json["applicable_documents"],
                                  heading="Applicable Documents")
    if did_json.get("reference_documents"):
        _theme.add_reference_list(doc, did_json["reference_documents"],
                                  heading="Reference Documents")

    # Table of contents
    _theme.add_toc(doc)

    # Render sections
    sections = did_json.get("sections", [])
    for section in sections:
        sec_number = section.get("number", "")
        sec_title = section.get("title", "")
        sec_level = _heading_level(sec_number)

        doc.add_heading(f"{sec_number} {sec_title}", level=sec_level)

        # Some sections may have direct content (top-level)
        sec_content = section.get("content", "")
        if sec_content:
            _render_rich_content(doc, sec_content)

        # Subsections
        subsections = section.get("subsections", [])
        for sub in subsections:
            sub_number = sub.get("number", "")
            sub_title = sub.get("title", "")
            sub_level = _heading_level(sub_number)
            sub_content = sub.get("content", "")

            doc.add_heading(f"{sub_number} {sub_title}", level=sub_level)
            if sub_content:
                _render_rich_content(doc, sub_content)

            # Nested subsections (if any)
            nested = sub.get("subsections", [])
            for nested_sub in nested:
                n_number = nested_sub.get("number", "")
                n_title = nested_sub.get("title", "")
                n_content = nested_sub.get("content", "")
                n_level = _heading_level(n_number)

                doc.add_heading(f"{n_number} {n_title}", level=n_level)
                if n_content:
                    _render_rich_content(doc, n_content)

    # Write to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
