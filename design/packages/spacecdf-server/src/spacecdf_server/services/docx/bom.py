"""SpaceCDF Word document family: bom. Bill of materials document.

Moved verbatim from services/docx_generator.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from docx import Document
from docx.shared import Pt

from ._common import (
    _add_cover_page,
    _add_footer,
    _add_toc_placeholder,
    _render_bullet,
    _render_formatted_table,
    _setup_margins,
    _setup_styles,
)


# ---------------------------------------------------------------------------
# BOM-specific DOCX renderer
# ---------------------------------------------------------------------------

def _render_bom_docx(bom_data: dict[str, Any]) -> bytes:
    """Render a Bill of Materials JSON as a styled Word document.

    Expected bom_data structure (from bom_generator):
      {
        title: str,
        generated: str,
        form_factor: str,
        groups: {subsystem_name: [line_items]},
        lines: [all_line_items],
        summary: {total_lines, total_mass_kg, total_power_w, total_cost_keur, ...},
        procurement_notes: [str],
        segment_totals: {segment: {mass_kg, power_w, cost_keur, items}},
      }
    """
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)

    title = bom_data.get("title", "Bill of Materials")
    study_name = title.replace("Bill of Materials \u2014 ", "").replace("SpaceCDF Bill of Materials \u2014 ", "")
    generated = bom_data.get("generated", "")
    date_str = generated[:10] if generated else datetime.now().strftime("%Y-%m-%d")

    # Cover page
    _add_cover_page(doc, "Bill of Materials", "SpaceCDF Procurement Package", study_name, date_str=date_str, status="DRAFT")
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    summary = bom_data.get("summary", {})
    groups = bom_data.get("groups", {})
    segment_totals = bom_data.get("segment_totals", {})
    procurement_notes = bom_data.get("procurement_notes", [])

    # --- Section 1: Summary ---
    doc.add_heading("1 Summary", level=1)

    summary_headers = ["Metric", "Value"]
    summary_rows = [
        ["Total line items", str(summary.get("total_lines", 0))],
        ["Total dry mass", f"{summary.get('total_mass_kg', 0):.3f} kg"],
        ["Total power", f"{summary.get('total_power_w', 0):.1f} W"],
        ["Total cost", f"{summary.get('total_cost_keur', 0):.1f} kEUR ({summary.get('total_cost_eur', 0):.0f} EUR)"],
        ["Mean TRL", str(summary.get("mean_trl", "N/A"))],
        ["BOM completeness", f"{summary.get('completeness_percent', 0):.0f}%"],
        ["Critical path", f"{summary.get('critical_path_weeks', 0)} weeks"],
        ["ITAR/EAR items", str(summary.get("itar_items", 0))],
        ["Low-TRL items (< 7)", str(summary.get("low_trl_items", 0))],
        ["Form factor", bom_data.get("form_factor", "N/A")],
    ]
    _render_formatted_table(doc, summary_headers, summary_rows)

    # --- Section 2: Segment Totals ---
    if segment_totals:
        doc.add_heading("2 Segment Totals", level=1)
        seg_headers = ["Segment", "Items", "Mass (kg)", "Power (W)", "Cost (kEUR)"]
        seg_rows = []
        for seg_name, seg_data in segment_totals.items():
            seg_rows.append([
                seg_name.title(),
                str(seg_data.get("items", 0)),
                f"{seg_data.get('mass_kg', 0):.3f}",
                f"{seg_data.get('power_w', 0):.1f}",
                f"{seg_data.get('cost_keur', 0):.1f}",
            ])
        _render_formatted_table(doc, seg_headers, seg_rows)

    # --- Section 3: Grouped BOM ---
    doc.add_heading("3 Bill of Materials by Subsystem", level=1)

    group_idx = 0
    for subsys_name, lines in groups.items():
        group_idx += 1
        doc.add_heading(f"3.{group_idx} {subsys_name}", level=2)

        bom_headers = [
            "Line", "Name", "Qty", "Mass (kg)",
            "Power (W)", "Cost (kEUR)", "TRL", "Model",
            "Procurement", "Lead (wk)",
        ]
        bom_rows = []
        for line in lines:
            bom_rows.append([
                str(line.get("line", "")),
                line.get("name", ""),
                str(line.get("quantity", 1)),
                f"{line.get('total_mass_kg', 0):.3f}",
                f"{line.get('total_power_w', 0):.1f}",
                f"{line.get('total_cost_keur', 0):.1f}",
                str(line.get("trl", "")),
                line.get("model_level", ""),
                line.get("procurement_status", ""),
                (f"{line['lead_time_min_weeks']}-{line['lead_time_weeks']}"
                 if line.get("lead_time_min_weeks") not in (None, line.get("lead_time_weeks"))
                 else str(line.get("lead_time_weeks", ""))),
            ])

        _render_formatted_table(doc, bom_headers, bom_rows)

        # Subsystem sub-totals
        sub_mass = sum(l.get("total_mass_kg", 0) for l in lines)
        sub_power = sum(l.get("total_power_w", 0) for l in lines)
        sub_cost = sum(l.get("total_cost_keur", 0) for l in lines)
        p = doc.add_paragraph()
        run = p.add_run(
            f"Subtotal: {len(lines)} items, "
            f"{sub_mass:.3f} kg, {sub_power:.1f} W, {sub_cost:.1f} kEUR"
        )
        run.font.size = Pt(9)
        run.font.italic = True
        run.font.name = 'Calibri'

    # --- Section 4: Procurement Notes ---
    doc.add_heading("4 Procurement Notes", level=1)
    if procurement_notes:
        for note in procurement_notes:
            _render_bullet(doc, f"- {note}")
    else:
        doc.add_paragraph("No procurement notes.")

    # --- Section 5: Export Control ---
    doc.add_heading("5 Export Control Summary", level=1)
    export_items = [l for l in bom_data.get("lines", []) if l.get("export_control") not in ("none", "", None)]
    if export_items:
        # W5.05: per-part ECCN, origin and permit (bom_generator.export_control_of)
        exp_headers = ["Line", "Name", "Manufacturer", "ECCN", "Origin", "Permit"]
        exp_rows = [
            [
                str(l.get("line", "")),
                l.get("name", ""),
                l.get("manufacturer", ""),
                l.get("eccn") or l.get("export_control", ""),
                l.get("origin", ""),
                l.get("permit", ""),
            ]
            for l in export_items
        ]
        _render_formatted_table(doc, exp_headers, exp_rows)
    else:
        doc.add_paragraph("No items with export control restrictions identified.")

    # Write to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
