#!/usr/bin/env python3
"""Compile SpaceCDF course materials into PDFs using fpdf2."""
import re, sys
from pathlib import Path
from datetime import datetime
from fpdf import FPDF

BASE = Path(__file__).resolve().parent.parent
COURSE_DIR = BASE / "docs" / "course"
PDF_DIR = BASE / "docs" / "pdf"
PDF_DIR.mkdir(exist_ok=True)

class CoursePDF(FPDF):
    def __init__(self, title="SpaceCDF"):
        super().__init__()
        self.doc_title = title
        self.set_auto_page_break(auto=True, margin=25)
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, self.doc_title, new_x="LMARGIN", new_y="NEXT")
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")
    def title_page(self, title, subtitle=""):
        self.add_page()
        self.ln(80)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(30, 58, 95)
        self.multi_cell(0, 10, title, align="C")
        if subtitle:
            self.ln(8)
            self.set_font("Helvetica", "", 12)
            self.set_text_color(107, 114, 128)
            self.multi_cell(0, 7, subtitle, align="C")
        self.ln(30)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(150, 150, 150)
        self.multi_cell(0, 7, f"Generated: {datetime.now().strftime('%Y-%m-%d')}", align="C")
    def _reset_x(self):
        self.set_x(self.l_margin)
    def add_md(self, text):
        self.add_page()
        in_code = False
        for line in text.split('\n'):
            s = line.strip()
            if s.startswith('```'):
                in_code = not in_code
                continue
            if in_code:
                self._reset_x()
                self.set_font("Courier", "", 7)
                self.set_text_color(100, 100, 100)
                self.multi_cell(0, 4, line[:100])
                continue
            clean = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
            clean = re.sub(r'\*(.+?)\*', r'\1', clean)
            clean = re.sub(r'`(.+?)`', r'\1', clean)
            clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean)
            if not clean:
                self.ln(2)
                continue
            self._reset_x()
            if s.startswith('# ') and not s.startswith('## '):
                self.set_font("Helvetica", "B", 15)
                self.set_text_color(30, 58, 95)
                self.multi_cell(0, 8, clean[2:])
                self.ln(2)
            elif s.startswith('## '):
                self.ln(3)
                self.set_font("Helvetica", "B", 12)
                self.set_text_color(30, 58, 95)
                self.multi_cell(0, 6, clean[3:])
                self.ln(1)
            elif s.startswith('### '):
                self.ln(2)
                self.set_font("Helvetica", "B", 10)
                self.set_text_color(55, 65, 81)
                self.multi_cell(0, 5, clean[4:])
            elif s.startswith('| '):
                if s.replace('|','').replace('-','').replace(' ','').replace(':','') == '':
                    continue
                self.set_font("Courier", "", 6)
                self.set_text_color(26, 26, 26)
                self.multi_cell(0, 3.5, clean[:130])
            elif s.startswith('- ') or s.startswith('* '):
                self.set_font("Helvetica", "", 9)
                self.set_text_color(26, 26, 26)
                self.multi_cell(0, 4.5, "  - " + clean[2:])
            elif s in ('---', '***'):
                self.ln(1)
            else:
                self.set_font("Helvetica", "", 9)
                self.set_text_color(26, 26, 26)
                self.multi_cell(0, 4.5, clean)

def compile_book(title, files, out_name, subtitle=""):
    print(f"\nCompiling: {title} ({len(files)} files)")
    pdf = CoursePDF(title)
    pdf.title_page(title, subtitle)
    for f in files:
        if f.exists():
            try:
                pdf.add_md(f.read_text(encoding='utf-8'))
                print(f"  + {f.name}")
            except Exception as e:
                print(f"  ! {f.name}: {e}")
    out = PDF_DIR / out_name
    pdf.output(str(out))
    print(f"  => {out.name} ({out.stat().st_size//1024} KB)")

def compile_single(title, path, out_name):
    print(f"\nCompiling: {title}")
    if not path.exists(): print(f"  MISSING"); return
    pdf = CoursePDF(title)
    pdf.title_page(title)
    try:
        pdf.add_md(path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"  ! Error: {e}")
    out = PDF_DIR / out_name
    pdf.output(str(out))
    print(f"  => {out.name} ({out.stat().st_size//1024} KB)")

if __name__ == "__main__":
    print("=" * 50)
    print("  SpaceCDF PDF Compilation")
    print("=" * 50)
    fac = sorted((COURSE_DIR / "facilitator").glob("*.md"))
    ver = sorted((COURSE_DIR / "verification").glob("*.md"))
    compile_book("Facilitator's Book", fac + ver, "SpaceCDF_Facilitator_Book.pdf", "40-Hour Mission Design Programme")
    ws = sorted((COURSE_DIR / "learner").glob("*.md"))
    compile_book("Learner's Workbook", ws, "SpaceCDF_Learner_Workbook.pdf", "Worksheets and Exercises")
    compile_single("3-Week Syllabus", COURSE_DIR / "3_WEEK_SYLLABUS.md", "SpaceCDF_3Week_Syllabus.pdf")
    compile_single("Course Plan", COURSE_DIR / "COURSE_PLAN.md", "SpaceCDF_Course_Plan.pdf")
    compile_single("User Guide", BASE / "docs" / "USER_GUIDE.md", "SpaceCDF_User_Guide.pdf")
    compile_single("API Documentation", BASE / "docs" / "API_DOCUMENTATION.md", "SpaceCDF_API_Documentation.pdf")
    print(f"\n{'='*50}")
    for p in sorted(PDF_DIR.glob("*.pdf")):
        print(f"  {p.name} ({p.stat().st_size//1024} KB)")
    print(f"{'='*50}")
