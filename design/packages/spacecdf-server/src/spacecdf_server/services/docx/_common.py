"""Shared Word helpers for every document family in services/docx (W0.1).

Styles, margins, cover page, footer, ToC placeholder, Markdown-ish rich content, pipe
tables, numbered sections and the diagram figure block. Moved verbatim from
services/docx_generator.py (whose original module docstring follows).

Generates editable .docx files for all ECSS documents using python-docx.
Each document is populated from the live design state.

Two rendering paths:
  1. Legacy per-type generators (generate_mrd_docx, etc.) — hardcoded sections.
  2. Universal DID renderer (generate_did_docx) — takes any DID JSON with
     {sections: [{number, title, subsections: [{number, title, content}]}]}
     and renders rich content (tables, bullets, mixed text).

Supports: MRD, TS, VP, ConOps, SEMP, RMP, IRD, Test Plan, BOM.

Visual style: uOttawa SpaceCDF Facilitator's Book.  All cover pages,
headers, footers, ToCs and tables route through
``spacecdf_agents.exporters.docs.theme`` so every document shares the
garnet course identity.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from docx import Document

from ..branding import BRANDING as _BRAND
from docx.shared import Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

# uOttawa SpaceCDF course-style theme (shared with the design-review generator).
from spacecdf_agents.exporters.docs import theme as _theme


# ---------------------------------------------------------------------------
# Colour palette — uOttawa Horizon (kept as RGBColor tuples for the legacy
# helpers; identical to the theme module's constants).
# ---------------------------------------------------------------------------

_CLR_HEADER_BG = RGBColor(0x8f, 0x00, 0x1a)   # uOttawa garnet — table headers
_CLR_ALT_ROW = RGBColor(0xf2, 0xf2, 0xf2)     # polar grey — alternate rows
_CLR_WHITE = RGBColor(255, 255, 255)
_CLR_TITLE = RGBColor(0x8f, 0x00, 0x1a)       # garnet — headings & titles
_CLR_SUBTITLE = RGBColor(0x80, 0x74, 0x6c)    # warm grey — captions & metadata
_CLR_BODY = RGBColor(0x2d, 0x2d, 0x2c)        # charcoal — body text
_CLR_ACCENT = RGBColor(0x67, 0x79, 0x6c)      # uOttawa green — accent


# ---------------------------------------------------------------------------
# Document setup helpers
# ---------------------------------------------------------------------------

def _setup_styles(doc: Document):
    """Apply the uOttawa SpaceCDF Facilitator's Book styles to the document."""
    _theme.apply_styles(doc)


def _setup_margins(doc: Document):
    """Set the SpaceCDF page geometry on every section."""
    _theme._set_page_geometry(doc)


def _add_footer(doc: Document, study_name: str, document_code: str = ""):
    """Bilingual EN/FR running header + footer matching the course style."""
    _theme.add_page_furniture(
        doc,
        running_title=f"SpaceCDF \u2014 {study_name}",
        document_code=document_code,
        footer_left=f"SpaceCDF \u00b7 {study_name}",
        footer_right=_BRAND.footer_brand,
    )


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def _add_cover_page(
    doc: Document,
    title: str,
    standard: str,
    study_name: str,
    date_str: str | None = None,
    status: str = "DRAFT",
):
    """uOttawa SpaceCDF-style cover page (delegates to the shared theme)."""
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    _theme.add_cover_page(
        doc,
        title=title,
        subtitle=standard,
        document_code=standard,
        study_name=study_name,
        issue="1.0",
        date=date_str,
        classification=status if status != "DRAFT" else "Internal · DRAFT",
        cohort="SpaceCDF",
        publisher=_BRAND.publisher,
    )


# ---------------------------------------------------------------------------
# Table of Contents placeholder
# ---------------------------------------------------------------------------

def _add_toc_placeholder(doc: Document):
    """Insert a Word-native ToC field (delegates to the shared theme)."""
    _theme.add_toc(doc)


# ---------------------------------------------------------------------------
# Content detection & rendering
# ---------------------------------------------------------------------------

_PIPE_TABLE_RE = re.compile(r'^\|(.+)\|$')
_SEPARATOR_RE = re.compile(r'^\|\s*[-:]+[\s|:-]*\|$')


def _is_pipe_table_line(line: str) -> bool:
    """Check if a line is a pipe-delimited table row."""
    return bool(_PIPE_TABLE_RE.match(line.strip()))


def _is_separator_line(line: str) -> bool:
    """Check if a line is a markdown table separator (|---|---|)."""
    return bool(_SEPARATOR_RE.match(line.strip()))


def _is_bullet_line(line: str) -> bool:
    """Check if a line starts with - or * (bullet list)."""
    stripped = line.strip()
    return stripped.startswith("- ") or stripped.startswith("* ")


def _parse_pipe_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """Parse pipe-delimited table lines into headers and rows.

    Returns (headers, rows) where each row is a list of cell strings.
    Skips separator lines.
    """
    headers: list[str] = []
    rows: list[list[str]] = []
    header_done = False

    for line in lines:
        stripped = line.strip()
        if _is_separator_line(stripped):
            header_done = True
            continue
        match = _PIPE_TABLE_RE.match(stripped)
        if not match:
            continue
        cells = [c.strip() for c in match.group(1).split('|')]
        if not header_done:
            headers = cells
            header_done = True
        else:
            rows.append(cells)

    return headers, rows


def _set_cell_shading(cell, color: RGBColor):
    """Set background shading on a table cell."""
    hex_color = f"{color[0]:02X}{color[1]:02X}{color[2]:02X}"
    shading = parse_xml(
        f'<w:shd {nsdecls("w")} w:fill="{hex_color}" w:val="clear"/>'
    )
    cell._tc.get_or_add_tcPr().append(shading)


def _render_formatted_table(doc: Document, headers: list[str], rows: list[list[str]]):
    """Render a table with styled header and alternating row colours."""
    if not headers:
        return

    num_cols = len(headers)
    table = doc.add_table(rows=1 + len(rows), cols=num_cols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(header)
        run.bold = True
        run.font.size = Pt(10)
        run.font.name = 'Calibri'
        run.font.color.rgb = _CLR_WHITE
        _set_cell_shading(cell, _CLR_HEADER_BG)

    # Data rows
    for r_idx, row_data in enumerate(rows):
        for c_idx in range(num_cols):
            cell_text = row_data[c_idx] if c_idx < len(row_data) else ""
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(cell_text)
            run.font.size = Pt(10)
            run.font.name = 'Calibri'
            # Alternating row colour
            if r_idx % 2 == 1:
                _set_cell_shading(cell, _CLR_ALT_ROW)

    doc.add_paragraph()  # spacing after table


def _render_bullet(doc: Document, text: str):
    """Add a bullet-point paragraph."""
    # Strip leading "- " or "* "
    clean = text.strip()
    if clean.startswith("- "):
        clean = clean[2:]
    elif clean.startswith("* "):
        clean = clean[2:]

    p = doc.add_paragraph(style='List Bullet')
    # Handle bold segments with **text** markers
    _add_formatted_run(p, clean)


def _add_formatted_run(paragraph, text: str):
    """Add text to a paragraph, handling **bold** markdown markers."""
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
            run.font.size = Pt(10)
            run.font.name = 'Calibri'
        else:
            run = paragraph.add_run(part)
            run.font.size = Pt(10)
            run.font.name = 'Calibri'


def _render_rich_content(doc: Document, content: str):
    """Parse and render mixed content: text, pipe tables, and bullet lists.

    Handles content that contains a mix of plain paragraphs, pipe-delimited
    tables, and bullet lines, rendering each block with the appropriate style.
    """
    if not content or not content.strip():
        return

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Accumulate consecutive pipe-table lines
        if _is_pipe_table_line(line):
            table_lines: list[str] = []
            while i < len(lines) and (_is_pipe_table_line(lines[i]) or _is_separator_line(lines[i])):
                table_lines.append(lines[i])
                i += 1
            headers, rows = _parse_pipe_table(table_lines)
            if headers:
                _render_formatted_table(doc, headers, rows)
            continue

        # Skip standalone separator lines (edge case)
        if _is_separator_line(line):
            i += 1
            continue

        # Bullet list items
        if _is_bullet_line(line):
            _render_bullet(doc, line)
            i += 1
            continue

        # Plain text paragraph (skip empty lines)
        stripped = line.strip()
        if stripped:
            p = doc.add_paragraph()
            _add_formatted_run(p, stripped)
        i += 1


# ---------------------------------------------------------------------------
# Heading level helper
# ---------------------------------------------------------------------------

def _heading_level(number: str) -> int:
    """Determine heading level from section number (1 -> 1, 1.1 -> 2, 1.1.1 -> 3)."""
    dots = number.count('.')
    if dots == 0:
        return 1
    elif dots == 1:
        return 2
    else:
        return 3


# ---------------------------------------------------------------------------
# Legacy helpers (preserved for backward compatibility)
# ---------------------------------------------------------------------------

def _add_title_page(doc: Document, title: str, subtitle: str, study_name: str):
    """Add a formatted title page (legacy — now wraps _add_cover_page)."""
    _add_cover_page(doc, title, subtitle, study_name)


def _add_section(doc: Document, number: str, title: str, content: str = ""):
    """Add a numbered section heading with content (legacy)."""
    level = _heading_level(number)
    doc.add_heading(f"{number} {title}", level=level)
    if content:
        _render_rich_content(doc, content)


def _add_table(doc: Document, headers: list[str], rows: list[list[str]]):
    """Add a formatted table (legacy — now wraps _render_formatted_table)."""
    _render_formatted_table(doc, headers, rows)




def _add_diagrams(doc: Document, number: str, title: str, data: dict[str, Any], intro: str) -> None:
    """Embed the study's diagram models (``data["diagrams"]``, built by the export route)."""
    models = data.get("diagrams") or []
    if not models:
        return
    from ..diagrams.render import add_diagram
    _add_section(doc, number, title, intro)
    for k, m in enumerate(models, 1):
        add_diagram(doc, m, heading_level=None, gaps=True, table=False)
