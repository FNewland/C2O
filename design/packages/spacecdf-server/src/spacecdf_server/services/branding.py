"""SpaceCDF — Document branding for University of Ottawa / SEDTI.

Provides shared branding configuration and DOCX helper functions
for consistent headers, footers, and colour schemes across all exports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BrandingConfig:
    """Branding configuration applied to all exported documents."""
    university: str = "University of Ottawa"
    department: str = "SEDTI — Space Exploration & Design Technology Initiative"
    tool_name: str = "SpaceCDF"
    tool_version: str = "2.0"

    # Colours (UOttawa garnet + dark grey)
    primary_color: str = "#8B0000"    # UOttawa garnet
    secondary_color: str = "#2D2D2D"  # Dark grey
    accent_color: str = "#C8102E"     # Bright red accent
    header_bg: str = "#8B0000"
    header_text: str = "#FFFFFF"

    # Footer text
    footer_left: str = "University of Ottawa — SEDTI"
    footer_right: str = "SpaceCDF v2.0 — Concurrent Design Facility"

    # Classification
    classification: str = "UNCLASSIFIED — FOR ACADEMIC USE"

    # Logo paths (relative to project root)
    logo_path: str | None = None  # Set if logo file exists


# Singleton instance
BRANDING = BrandingConfig()


def get_branding() -> BrandingConfig:
    """Return the current branding configuration."""
    return BRANDING


def apply_docx_branding(doc: Any) -> None:
    """Apply UOttawa/SEDTI branding to a python-docx Document.

    Sets:
    - Default font (Calibri)
    - Header with university name, department, tool name
    - Footer with page number and classification
    - Title page colour scheme
    """
    try:
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        return  # python-docx not installed — skip branding

    b = BRANDING
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x2D, 0x2D, 0x2D)

    # Header
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        if not header.paragraphs:
            header.add_paragraph()
        hp = header.paragraphs[0]
        hp.text = f"{b.university}  |  {b.department}  |  {b.tool_name}"
        hp.style.font.size = Pt(8)
        hp.style.font.color.rgb = RGBColor(0x8B, 0x00, 0x00)
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Footer
        footer = section.footer
        footer.is_linked_to_previous = False
        if not footer.paragraphs:
            footer.add_paragraph()
        fp = footer.paragraphs[0]
        fp.text = f"{b.footer_left}  |  {b.classification}  |  {b.footer_right}"
        fp.style.font.size = Pt(7)
        fp.style.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER


def create_branded_docx(title: str, subtitle: str = "") -> Any:
    """Create a new DOCX document with UOttawa/SEDTI branding pre-applied.

    Returns a python-docx Document ready for content.
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        return None

    doc = Document()
    apply_docx_branding(doc)

    b = BRANDING

    # Title page
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_before = Pt(72)
    run = p.add_run(b.university)
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0x8B, 0x00, 0x00)
    run.bold = True

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = p2.add_run(b.department)
    run2.font.size = Pt(12)
    run2.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.space_before = Pt(36)
    run3 = p3.add_run(title)
    run3.font.size = Pt(24)
    run3.bold = True

    if subtitle:
        p4 = doc.add_paragraph()
        p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run4 = p4.add_run(subtitle)
        run4.font.size = Pt(14)
        run4.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # Classification
    pc = doc.add_paragraph()
    pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pc.space_before = Pt(24)
    rc = pc.add_run(b.classification)
    rc.font.size = Pt(10)
    rc.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

    doc.add_page_break()
    return doc


def create_branded_xlsx(title: str) -> Any:
    """Create a new XLSX workbook with UOttawa/SEDTI branding.

    Returns an openpyxl Workbook with a branded title sheet.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = "Cover"

    b = BRANDING
    garnet_fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
    white_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")

    ws.merge_cells("A1:F1")
    ws["A1"].value = b.university
    ws["A1"].font = white_font
    ws["A1"].fill = garnet_fill
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:F2")
    ws["A2"].value = b.department
    ws["A2"].font = Font(name="Calibri", size=10, color="666666")
    ws["A2"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A4:F4")
    ws["A4"].value = title
    ws["A4"].font = Font(name="Calibri", size=18, bold=True)
    ws["A4"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A6:F6")
    ws["A6"].value = b.classification
    ws["A6"].font = Font(name="Calibri", size=9, color="CC0000")
    ws["A6"].alignment = Alignment(horizontal="center")

    return wb
