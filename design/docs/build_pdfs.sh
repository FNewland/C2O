#!/bin/bash
# SpaceCDF PDF Builder
# Converts markdown docs to PDF using Python markdown + weasyprint
# Usage: cd docs && bash build_pdfs.sh
#
# Prerequisites: pip install markdown weasyprint

set -e

OUTDIR="pdf"
mkdir -p "$OUTDIR"

# CSS for PDF styling
CSS=$(cat <<'CSSEOF'
@page { size: A4; margin: 2cm; @bottom-center { content: counter(page) " / " counter(pages); font-size: 9pt; color: #666; } }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #1a1a2e; }
h1 { color: #1e3a5f; border-bottom: 2px solid #3b82f6; padding-bottom: 0.3em; page-break-after: avoid; }
h2 { color: #2563eb; margin-top: 1.5em; page-break-after: avoid; }
h3 { color: #374151; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 10pt; }
th { background: #1e3a5f; color: white; padding: 6px 10px; text-align: left; }
td { border: 1px solid #d1d5db; padding: 5px 10px; }
tr:nth-child(even) { background: #f9fafb; }
code { background: #f3f4f6; padding: 2px 4px; border-radius: 3px; font-size: 10pt; }
pre { background: #1f2937; color: #e5e7eb; padding: 1em; border-radius: 6px; overflow-x: auto; font-size: 9pt; }
blockquote { border-left: 3px solid #3b82f6; padding-left: 1em; color: #6b7280; }
.cover { text-align: center; padding-top: 30%; }
.cover h1 { font-size: 28pt; border: none; }
.cover .subtitle { font-size: 14pt; color: #6b7280; }
.cover .meta { font-size: 10pt; color: #9ca3af; margin-top: 3em; }
CSSEOF
)

build_pdf() {
    local src="$1"
    local title="$2"
    local outname="$3"

    if [ ! -f "$src" ]; then
        echo "SKIP: $src not found"
        return
    fi

    echo "Building $outname from $src..."

    python3 -c "
import markdown, sys
with open('$src', 'r') as f:
    md = f.read()
html = markdown.markdown(md, extensions=['tables', 'fenced_code', 'toc'])
cover = '''<div class=\"cover\">
<h1>$title</h1>
<p class=\"subtitle\">SpaceCDF — AI-Assisted Concurrent Design Facility</p>
<p class=\"meta\">University of Ottawa · SEDTI<br/>Generated: $(date +%Y-%m-%d)</p>
</div><hr/>'''
print(f'<html><head><meta charset=\"utf-8\"/><style>{css}</style></head><body>{cover}{html}</body></html>',
      file=open('/tmp/spacecdf_tmp.html', 'w'))
" 2>/dev/null

    weasyprint /tmp/spacecdf_tmp.html "$OUTDIR/$outname" 2>/dev/null && echo "  -> $OUTDIR/$outname" || echo "  FAILED: $outname"
}

# Build all key documents
build_pdf "USER_GUIDE.md" "User Guide" "SpaceCDF_User_Guide.pdf"
build_pdf "API_DOCUMENTATION.md" "API Documentation" "SpaceCDF_API_Documentation.pdf"
build_pdf "course/COURSE_PLAN.md" "Course Plan (40 Hours)" "SpaceCDF_Course_Plan.pdf"
build_pdf "course/3_WEEK_SYLLABUS.md" "3-Week Intensive Syllabus" "SpaceCDF_3Week_Syllabus.pdf"

# Concatenate facilitator sessions
echo "Building Facilitator Book (combined sessions)..."
COMBINED="/tmp/spacecdf_facilitator_combined.md"
echo "# SpaceCDF Facilitator Book" > "$COMBINED"
echo "" >> "$COMBINED"
for session in course/facilitator/session_*.md; do
    [ -f "$session" ] && cat "$session" >> "$COMBINED" && echo -e "\n---\n" >> "$COMBINED"
done
# Append position appendices
[ -f "course/facilitator/appendix_positions.md" ] && cat "course/facilitator/appendix_positions.md" >> "$COMBINED"
build_pdf "$COMBINED" "Facilitator Book" "SpaceCDF_Facilitator_Book.pdf"

# Concatenate learner worksheets
echo "Building Learner Workbook (combined worksheets)..."
LEARNER="/tmp/spacecdf_learner_combined.md"
echo "# SpaceCDF Learner Workbook" > "$LEARNER"
echo "" >> "$LEARNER"
for ws in course/learner/worksheet_*.md; do
    [ -f "$ws" ] && cat "$ws" >> "$LEARNER" && echo -e "\n---\n" >> "$LEARNER"
done
build_pdf "$LEARNER" "Learner Workbook" "SpaceCDF_Learner_Workbook.pdf"

echo ""
echo "Done. PDFs in $OUTDIR/"
ls -la "$OUTDIR/"*.pdf 2>/dev/null
