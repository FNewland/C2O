#!/usr/bin/env python3
"""SpaceCDF PDF Builder — uses fpdf2 (pure Python, no native deps).

Converts markdown course documents to formatted A4 PDFs with:
- Cover page with title, subtitle, date
- Table of contents
- Proper headings, tables, code blocks, bullet lists
- Page numbers in footer
- Blue accent colour scheme matching SpaceCDF brand

Usage: cd docs && python3 build_pdfs_fpdf.py
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path

from fpdf import FPDF


class SpaceCDFPDF(FPDF):
    """Custom PDF with SpaceCDF branding."""

    def __init__(self, title: str = "", subtitle: str = ""):
        super().__init__()
        self.doc_title = title
        self.doc_subtitle = subtitle
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)
        self.toc_entries: list[tuple[int, str, int]] = []

    def header(self):
        if self.page_no() <= 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, f"SpaceCDF -- {self.doc_title}", align="L")
        self.ln(10)

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def cover_page(self):
        self.add_page()
        self.ln(60)
        w = self.w - 40  # page width minus margins
        # Title
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(30, 58, 95)
        self.set_x(20)
        self.multi_cell(w, 14, _clean_md(self.doc_title), align="C")
        self.ln(8)
        # Subtitle
        self.set_font("Helvetica", "", 14)
        self.set_text_color(107, 114, 128)
        self.set_x(20)
        self.multi_cell(w, 8, _clean_md(self.doc_subtitle), align="C")
        self.ln(20)
        # Meta
        self.set_font("Helvetica", "", 10)
        self.set_text_color(156, 163, 175)
        self.set_x(20)
        self.multi_cell(w, 6, "SpaceCDF -- AI-Assisted Concurrent Design Facility", align="C")
        self.set_x(20)
        self.multi_cell(w, 6, "University of Ottawa - SEDTI", align="C")
        self.set_x(20)
        self.multi_cell(w, 6, f"Generated: {date.today().isoformat()}", align="C")
        self.ln(30)
        # Draft watermark
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(239, 68, 68)
        self.set_x(20)
        self.cell(w, 8, "DRAFT", align="C")


def parse_markdown_to_pdf(pdf: SpaceCDFPDF, md_text: str):
    """Parse markdown and render to PDF using fpdf2."""
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    in_table = False
    table_rows: list[list[str]] = []

    # Strip YAML frontmatter
    if lines and lines[0].strip() == "---":
        end = 1
        while end < len(lines) and lines[end].strip() != "---":
            end += 1
        lines = lines[end + 1 :]

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code block toggle
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                pdf.ln(3)
                i += 1
                continue
            else:
                in_code_block = True
                i += 1
                continue

        if in_code_block:
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(229, 231, 235)
            pdf.set_fill_color(31, 41, 55)
            text = _clean_md(line[:120])
            pdf.cell(0, 4.5, f"  {text}", fill=True, new_x="LMARGIN", new_y="NEXT")
            i += 1
            continue

        # Table detection
        if "|" in stripped and stripped.startswith("|"):
            # Check if separator row
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                i += 1
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            # Check if next line continues table
            if i + 1 < len(lines) and "|" in lines[i + 1].strip():
                i += 1
                continue
            else:
                # Render table
                _render_table(pdf, table_rows)
                in_table = False
                table_rows = []
                i += 1
                continue

        # SVG blocks — render a bordered placeholder box with the diagram title
        if "<svg" in stripped:
            # Try to extract a title from the SVG or surrounding context
            svg_title = "Diagram"
            svg_content = stripped
            while i < len(lines) and "</svg>" not in lines[i]:
                svg_content += lines[i]
                i += 1
            i += 1
            # Extract title from <text> elements or nearby heading
            import re as _re
            title_match = _re.search(r'<text[^>]*>([^<]+)</text>', svg_content)
            if title_match:
                svg_title = _clean_md(title_match.group(1))
            # Draw a placeholder box
            pdf.ln(3)
            box_y = pdf.get_y()
            box_h = 40
            if pdf.get_y() + box_h > pdf.h - 25:
                pdf.add_page()
                box_y = pdf.get_y()
            pdf.set_draw_color(59, 130, 246)
            pdf.set_line_width(0.5)
            pdf.rect(25, box_y, 160, box_h)
            pdf.set_line_width(0.2)
            # Diagonal lines to indicate diagram area
            pdf.set_draw_color(220, 220, 230)
            pdf.line(25, box_y, 185, box_y + box_h)
            pdf.line(185, box_y, 25, box_y + box_h)
            # Label
            pdf.set_font("Helvetica", "BI", 10)
            pdf.set_text_color(59, 130, 246)
            pdf.set_xy(25, box_y + box_h / 2 - 5)
            pdf.cell(160, 5, f"Figure: {svg_title}", align="C")
            pdf.set_xy(25, box_y + box_h / 2 + 2)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(156, 163, 175)
            pdf.cell(160, 4, "(See digital/markdown version for interactive diagram)", align="C")
            pdf.set_xy(20, box_y + box_h + 3)
            pdf.ln(3)
            continue

        # HTML comments (SVG descriptions) — skip
        if stripped.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        # Headings
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped.lstrip("#").strip()
            _render_heading(pdf, text, level)
            i += 1
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            pdf.ln(3)
            y = pdf.get_y()
            pdf.set_draw_color(209, 213, 219)
            pdf.line(20, y, 190, y)
            pdf.ln(5)
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            text = _clean_md(stripped.lstrip("> ").strip())
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(107, 114, 128)
            pdf.set_draw_color(59, 130, 246)
            pdf.line(22, pdf.get_y(), 22, pdf.get_y() + 5)
            pdf.set_x(26)
            pdf.multi_cell(155, 5, text)
            pdf.ln(2)
            i += 1
            continue

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(26, 26, 46)
            pdf.set_x(25)
            pdf.cell(5, 5, "-")
            pdf.multi_cell(155, 5, _clean_md(text))
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\.\s", stripped):
            num, text = stripped.split(".", 1)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(26, 26, 46)
            pdf.set_x(25)
            pdf.cell(8, 5, f"{num}.")
            pdf.multi_cell(152, 5, _clean_md(text.strip()))
            i += 1
            continue

        # Empty line
        if not stripped:
            pdf.ln(3)
            i += 1
            continue

        # Blank response lines (underscores) — render as full-width ruled lines
        if re.match(r"^_{5,}$", stripped):
            pdf.set_draw_color(180, 180, 190)
            y = pdf.get_y() + 4
            pdf.line(20, y, 190, y)  # Full page width
            pdf.ln(6)
            i += 1
            continue

        # Lines with label + underscores (e.g., "Name: ___________")
        if "___" in stripped:
            parts = stripped.split("___", 1)
            label = _clean_md(parts[0].strip())
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(26, 26, 46)
            if label:
                label_w = pdf.get_string_width(label) + 4
                pdf.cell(label_w, 6, label)
            # Draw line for the rest of the width
            pdf.set_draw_color(180, 180, 190)
            x = pdf.get_x()
            y = pdf.get_y() + 5
            pdf.line(x, y, 190, y)  # Extend to right margin
            pdf.ln(7)
            i += 1
            continue

        # Regular paragraph
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(26, 26, 46)
        pdf.multi_cell(0, 5, _clean_md(stripped))
        pdf.ln(1)
        i += 1


def _render_heading(pdf: SpaceCDFPDF, text: str, level: int):
    text = _clean_md(text)
    if level == 1:
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(30, 58, 95)
        pdf.multi_cell(0, 9, text)
        # Underline
        y = pdf.get_y()
        pdf.set_draw_color(59, 130, 246)
        pdf.set_line_width(0.5)
        pdf.line(20, y + 1, 190, y + 1)
        pdf.set_line_width(0.2)
        pdf.ln(5)
        pdf.toc_entries.append((1, text, pdf.page_no()))
    elif level == 2:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(37, 99, 235)
        pdf.multi_cell(0, 7, text)
        pdf.ln(3)
        pdf.toc_entries.append((2, text, pdf.page_no()))
    elif level == 3:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(55, 65, 81)
        pdf.multi_cell(0, 6, text)
        pdf.ln(2)
    else:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(75, 85, 99)
        pdf.multi_cell(0, 5, text)
        pdf.ln(2)


def _render_table(pdf: SpaceCDFPDF, rows: list[list[str]]):
    if not rows:
        return
    pdf.ln(3)
    n_cols = max(len(r) for r in rows)
    avail_w = 170
    line_h = 4  # Height per line of text in a cell

    # Calculate column widths proportional to max content length
    max_lens = [0] * n_cols
    for row in rows:
        for j, cell in enumerate(row[:n_cols]):
            max_lens[j] = max(max_lens[j], len(_clean_md(cell)))
    total_len = max(sum(max_lens), 1)
    col_widths = [max(avail_w * l / total_len, 15) for l in max_lens]
    # Normalize to fit available width
    scale = avail_w / sum(col_widths)
    col_widths = [w * scale for w in col_widths]

    for row_idx, row in enumerate(rows):
        while len(row) < n_cols:
            row.append("")

        is_header = row_idx == 0
        if is_header:
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_fill_color(30, 58, 95)
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(26, 26, 46)
            if row_idx % 2 == 0:
                pdf.set_fill_color(249, 250, 251)
            else:
                pdf.set_fill_color(255, 255, 255)

        # Calculate row height based on tallest cell
        cell_texts = [_clean_md(cell) for cell in row[:n_cols]]
        row_height = line_h  # minimum 1 line
        for j, text in enumerate(cell_texts):
            # Estimate number of lines needed for wrapping
            char_width = pdf.get_string_width("x")
            chars_per_line = max(int(col_widths[j] / char_width) - 1, 5)
            n_lines = max(1, -(-len(text) // chars_per_line))  # ceil division
            row_height = max(row_height, n_lines * line_h)
        row_height = min(row_height, 30)  # cap at ~7 lines

        # Check if we need a page break
        if pdf.get_y() + row_height > pdf.h - 20:
            pdf.add_page()

        # Draw cells using multi_cell in a row
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for j, text in enumerate(cell_texts):
            x = x_start + sum(col_widths[:j])
            pdf.set_xy(x, y_start)
            # Draw cell background and border
            pdf.rect(x, y_start, col_widths[j], row_height, style="DF")
            # Draw text with padding
            pdf.set_xy(x + 1, y_start + 0.5)
            pdf.multi_cell(col_widths[j] - 2, line_h, text)

        # Move to next row
        pdf.set_xy(x_start, y_start + row_height)

    pdf.set_text_color(26, 26, 46)
    pdf.ln(3)


def _latex_to_text(latex: str) -> str:
    """Convert LaTeX math notation to readable plain text."""
    t = latex
    # Step 1: Handle subscripts/superscripts FIRST (removes inner braces so \frac can match)
    for _ in range(3):
        t = re.sub(r"_\{([^{}]+)\}", r"_\1", t)
        t = re.sub(r"\^\{([^{}]+)\}", r"^\1", t)
    # Step 2: Now handle fractions (inner braces already removed)
    for _ in range(3):
        t = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", t)
    # Fallback: bare \frac without braces
    t = re.sub(r"\\frac([A-Za-z0-9_]+)([A-Za-z0-9_]+)", r"(\1)/(\2)", t)
    # Step 3: Common commands — order matters (longer commands first)
    cmd_replacements = [
        (r"\times", " x "), (r"\cdot", " * "), (r"\pm", " +/- "),
        (r"\approx", " ~= "), (r"\geq", " >= "), (r"\leq", " <= "),
        (r"\neq", " != "), (r"\infty", "inf"),
        (r"\sqrt", "sqrt"), (r"\sum", "Sum"), (r"\prod", "Prod"),
        (r"\pi", "pi"), (r"\mu", "u"), (r"\sigma", "sigma"),
        (r"\alpha", "alpha"), (r"\beta", "beta"), (r"\gamma", "gamma"),
        (r"\delta", "delta"), (r"\Delta", "D"), (r"\theta", "theta"),
        (r"\lambda", "lambda"), (r"\omega", "omega"), (r"\epsilon", "eps"),
        (r"\eta", "eta"), (r"\rho", "rho"), (r"\phi", "phi"),
        (r"\cos", "cos"), (r"\sin", "sin"), (r"\tan", "tan"),
        (r"\log", "log"), (r"\ln", "ln"), (r"\exp", "exp"),
        (r"\text", ""), (r"\mathrm", ""), (r"\mathbf", ""),
        (r"\left", ""), (r"\right", ""), (r"\quad", " "), (r"\,", " "),
        (r"\%", "%"), (r"\_", "_"),
    ]
    for cmd, repl in cmd_replacements:
        t = t.replace(cmd, repl)
    # Clean remaining braces
    t = t.replace("{", "").replace("}", "")
    # Clean up multiple spaces
    t = re.sub(r"  +", " ", t).strip()
    return t


def _clean_md(text: str) -> str:
    """Strip markdown formatting and make latin-1 safe for fpdf."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)  # Italic
    text = re.sub(r"`(.+?)`", r"\1", text)  # Code
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # Links (keep text)
    # LaTeX — convert common notation to readable form
    text = re.sub(r"\$(.+?)\$", lambda m: _latex_to_text(m.group(1)), text)
    # Replace Unicode characters with latin-1 safe equivalents
    replacements = {
        "\u2014": "--", "\u2013": "-", "\u2192": "->", "\u2194": "<->",
        "\u2190": "<-", "\u0394": "D", "\u03bc": "u", "\u03c0": "pi",
        "\u00b2": "2", "\u00b3": "3", "\u2264": "<=", "\u2265": ">=",
        "\u2260": "!=", "\u221a": "sqrt", "\u2248": "~=", "\u221e": "inf",
        "\u03b1": "alpha", "\u03b2": "beta", "\u03b3": "gamma",
        "\u03b4": "delta", "\u03b5": "epsilon", "\u03b8": "theta",
        "\u03bb": "lambda", "\u03c3": "sigma", "\u03c9": "omega",
        "\u2022": "*", "\u25cf": "*", "\u25cb": "o",
        "\u2713": "[x]", "\u2717": "[ ]",
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u00d7": "x", "\u00f7": "/",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Final safety: encode to latin-1, replace anything remaining
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


def build_pdf(src_path: str, title: str, subtitle: str, out_path: str):
    """Build a single PDF from a markdown file."""
    if not os.path.exists(src_path):
        print(f"  SKIP: {src_path} not found")
        return

    print(f"  Building {out_path}...")
    with open(src_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    pdf = SpaceCDFPDF(title=title, subtitle=subtitle)
    pdf.cover_page()
    pdf.add_page()
    parse_markdown_to_pdf(pdf, md_text)
    pdf.output(out_path)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"  -> {out_path} ({size_kb:.0f} KB, {pdf.page_no()} pages)")


def main():
    os.makedirs("pdf", exist_ok=True)

    docs = [
        ("USER_GUIDE.md", "User Guide", "Reference guide for SpaceCDF tool features", "pdf/SpaceCDF_User_Guide.pdf"),
        ("API_DOCUMENTATION.md", "API Documentation", "REST API reference for SpaceCDF backend", "pdf/SpaceCDF_API_Documentation.pdf"),
        ("course/3_WEEK_SYLLABUS.md", "3-Week Intensive Syllabus", "Programme structure and assessment", "pdf/SpaceCDF_3Week_Syllabus.pdf"),
        ("course/facilitator_book_expanded.md", "Facilitator's Book", "Teaching reference for the 40-hour CDF intensive", "pdf/SpaceCDF_Facilitator_Book.pdf"),
        ("course/learner_workbook_expanded.md", "Learner's Workbook", "Worksheets and exercises for the 40-hour CDF intensive", "pdf/SpaceCDF_Learner_Workbook.pdf"),
    ]

    if os.path.exists("course/COURSE_PLAN.md"):
        docs.append(("course/COURSE_PLAN.md", "Course Plan", "40-hour programme schedule", "pdf/SpaceCDF_Course_Plan.pdf"))

    print(f"SpaceCDF PDF Builder — {len(docs)} documents\n")
    for src, title, subtitle, out in docs:
        build_pdf(src, title, subtitle, out)

    print(f"\nDone. {len(docs)} PDFs in pdf/")


if __name__ == "__main__":
    main()
