"""SpaceCDF Word document family: rmp. Risk Management Plan (RMP).

W1.09b: the register is the study's ``risk_register`` (via the export collector), every risk,
highest likelihood x consequence first, with category, owner, status, mitigation and source.
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


def _score(r: dict[str, Any]) -> int:
    try:
        return int(r.get("score") or (int(r.get("likelihood") or 0) * int(r.get("consequence") or 0)))
    except (TypeError, ValueError):
        return 0


def generate_rmp_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Generate Risk Management Plan (ECSS-M-ST-80C)."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    _add_cover_page(doc, "Risk Management Plan", "ECSS-M-ST-80C / NPR 8000.4", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    _add_section(doc, "1", "Introduction")
    _add_section(doc, "1.1", "Purpose", "This plan defines the risk management process for identification, assessment, mitigation, and monitoring of project risks.")

    _add_section(doc, "2", "Risk Management Process")
    _add_section(doc, "2.1", "Risk Identification", "Risks identified via brainstorming, checklists, heritage review, and technical analysis. "
                 "Each risk assigned unique ID and categorised (technical/programmatic/regulatory).")
    _add_section(doc, "2.2", "Risk Assessment", "Likelihood (1-5) x Consequence (1-5) = Risk Priority Number. "
                 "Green (<=4), Amber (5-9), Orange (10-15), Red (16-25).")
    _add_section(doc, "2.3", "Risk Mitigation", "For each risk: Accept / Mitigate / Transfer / Avoid. "
                 "Mitigation actions assigned to responsible position with deadline.")
    _add_section(doc, "2.4", "Risk Monitoring", "Risks reviewed at each design review (SRR, PDR, CDR). "
                 "Status tracked: Open / Mitigating / Closed / Accepted.")

    _add_section(doc, "3", "Risk Register")
    risks = sorted(data.get("risks", []) or [], key=lambda r: (-_score(r), str(r.get("id") or "")))
    if risks:
        doc.add_paragraph(f"{len(risks)} risks, highest likelihood x consequence first; "
                          f"{sum(1 for r in risks if (r.get('status') or 'open') != 'closed')} not closed.")
        _add_table(doc, ["ID", "Risk", "Category", "L", "C", "Score", "Owner", "Status", "Mitigation", "Source"],
                   [[r.get("id", ""), r.get("description") or r.get("title") or "", r.get("category") or "",
                     str(r.get("likelihood", "")), str(r.get("consequence", "")), str(_score(r)),
                     r.get("owner") or "", r.get("status") or "", r.get("mitigation") or "", r.get("source") or ""]
                    for r in risks])
    else:
        doc.add_paragraph("The study has no risk in its register yet.")

    _add_section(doc, "4", "Risk Acceptance Criteria")
    doc.add_paragraph("Risks scoring <= 9 may be accepted by the Project Manager. "
                      "Risks scoring 10-15 require Systems Engineer review. "
                      "Risks scoring >= 16 require Programme Board approval.")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
