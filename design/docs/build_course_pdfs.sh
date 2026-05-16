#!/bin/bash
# SpaceCDF — Course PDF builder (uOttawa garnet style)
#
# Rebuilds the textbook (formerly "Facilitator Book") and the course
# workbook from per-session / per-worksheet markdown files using
# weasyprint, applying the uOttawa Horizon palette so the volumes match
# the rest of the SpaceCDF course materials.
#
# Run from the docs/ directory:
#   cd docs && bash build_course_pdfs.sh

set -e
OUTDIR="pdf"
mkdir -p "$OUTDIR"

# ---- uOttawa Horizon CSS ----------------------------------------------------
CSS=$(cat <<'CSSEOF'
@page {
    size: A4;
    margin: 22mm 22mm 25mm 22mm;
    @top-left {
        content: string(running-title);
        font-family: 'Calibri', 'Helvetica Neue', Arial, sans-serif;
        font-size: 9pt; font-weight: bold; color: #2d2d2c;
        border-bottom: 1.2pt solid #8f001a;
        padding-bottom: 3pt;
    }
    @top-right {
        content: string(running-code);
        font-family: 'Calibri', 'Helvetica Neue', Arial, sans-serif;
        font-size: 9pt; color: #80746c;
        border-bottom: 1.2pt solid #8f001a;
        padding-bottom: 3pt;
    }
    @bottom-left {
        content: "SpaceCDF · " string(running-title);
        font-size: 8pt; color: #2d2d2c;
    }
    @bottom-center {
        content: "Page " counter(page) " of / de " counter(pages);
        font-size: 8pt; color: #80746c;
    }
    @bottom-right {
        content: "uOttawa SEDTI";
        font-size: 8pt; font-weight: bold; color: #8f001a;
    }
}
@page cover {
    size: A4;
    margin: 0;
    @top-left { content: none; }
    @top-right { content: none; }
    @bottom-left { content: none; }
    @bottom-center { content: none; }
    @bottom-right { content: none; }
}
html { string-set: running-title attr(data-title), running-code attr(data-code); }
body {
    font-family: 'Calibri', 'Helvetica Neue', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.4;
    color: #2d2d2c;
}
.cover {
    page: cover;
    height: 297mm;
    background: white;
    margin: 0;
    padding: 0;
    page-break-after: always;
    display: block;
    position: relative;
}
.cover .banner {
    background: #8f001a;
    color: white;
    padding: 22mm 22mm 12mm 22mm;
    height: 42mm;
}
.cover .banner .uo {
    font-family: 'Calibri', Helvetica, Arial, sans-serif;
    font-size: 32pt; font-weight: 700; letter-spacing: -0.5pt;
    line-height: 1.1;
}
.cover .banner .uo .light { font-weight: 300; }
.cover .banner .label {
    font-size: 8.5pt; font-weight: 700; letter-spacing: 0.5pt;
    margin-top: 4pt;
}
.cover .body { padding: 20mm 22mm 0 22mm; }
.cover h1 {
    font-size: 34pt;
    line-height: 1.05;
    font-weight: 800;
    color: #8f001a;
    margin: 0 0 6pt 0;
    border: none;
    border-bottom: 1.4pt solid #8f001a;
    padding-bottom: 10pt;
    page-break-before: avoid;
}
.cover .subtitle {
    font-family: 'Cambria', 'Georgia', serif;
    font-style: italic;
    font-size: 14pt;
    color: #2d2d2c;
    margin: 8pt 0 20pt 0;
}
.cover .cohort { font-weight: 700; font-size: 11pt; margin: 0; }
.cover .year { font-size: 11pt; margin: 0; }
.cover .footerblock {
    position: absolute;
    left: 22mm;
    right: 22mm;
    bottom: 18mm;
    border-top: 1.4pt solid #8f001a;
    padding-top: 8pt;
}
.cover .publisher {
    font-weight: 700; color: #8f001a; font-size: 10.5pt; margin: 0;
}
.cover .meta { font-size: 9.5pt; margin: 2pt 0 0 0; }
.cover .classification {
    font-style: italic; color: #80746c; font-size: 9pt; margin: 4pt 0 0 0;
}
h1 {
    color: #8f001a;
    font-size: 20pt;
    font-weight: 700;
    margin: 18pt 0 6pt 0;
    page-break-before: always;
    page-break-after: avoid;
}
h2 {
    color: #8f001a;
    font-size: 14pt;
    font-weight: 700;
    margin: 14pt 0 4pt 0;
    page-break-after: avoid;
}
h3 {
    color: #2d2d2c;
    font-size: 12pt;
    font-weight: 700;
    margin: 10pt 0 2pt 0;
    page-break-after: avoid;
}
h4 { color: #3a3a37; font-size: 11pt; font-weight: 700; margin: 8pt 0 2pt 0; }
p { margin: 0 0 6pt 0; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9.5pt; }
th {
    background: #8f001a; color: white; padding: 5pt 8pt;
    text-align: left; font-weight: 700;
}
td {
    border: 0.5pt solid #d6d4d2; padding: 4pt 8pt;
    vertical-align: top;
}
tr:nth-child(even) td { background: #f2f2f2; }
code {
    background: #f2f2f2; padding: 1pt 3pt; border-radius: 2pt;
    font-family: 'Consolas', 'Menlo', monospace; font-size: 9.5pt;
}
pre {
    background: #f2f2f2; color: #2d2d2c; padding: 8pt 10pt;
    border-left: 3pt solid #8f001a;
    font-family: 'Consolas', 'Menlo', monospace; font-size: 9pt;
    overflow-x: hidden;
}
pre code { background: transparent; padding: 0; }
blockquote {
    border-left: 3pt solid #8f001a;
    background: #f8f4f4;
    padding: 6pt 10pt;
    margin: 6pt 0;
    color: #2d2d2c;
}
img, svg { max-width: 100%; height: auto; }
.figure-caption {
    text-align: center; font-style: italic; font-size: 9pt;
    color: #80746c; margin: 2pt 0 12pt 0;
}
hr {
    border: none; border-top: 0.5pt solid #d6d4d2; margin: 14pt 0;
}
a { color: #8f001a; text-decoration: none; }
.inline-svg {
    display: block;
    text-align: center;
    margin: 10pt 0;
    page-break-inside: avoid;
}
.inline-svg svg {
    max-width: 100%;
    height: auto;
}
/* Math: SVGs carry their own intrinsic size so we only need to cap the
   maximum width for very wide display equations.  No forced height — that
   would crush expressions with fractions/sqrt. */
img.math-display {
    display: block;
    margin: 8pt auto;
    max-width: 80%;
    height: auto;
}
img.math-inline {
    display: inline;
    vertical-align: middle;
    max-width: 100%;
    height: auto;            /* SVG natural size — picks up matplotlib's
                                point dimensions so simple variables stay
                                small and stacked fractions get the
                                vertical room they need */
}
CSSEOF
)

# ---- build helper ----------------------------------------------------------
build_pdf() {
    local md="$1"   # markdown source path
    local title="$2"
    local subtitle="$3"
    local code="$4"
    local outname="$5"

    if [ ! -f "$md" ]; then
        echo "  SKIP: $md not found"
        return
    fi
    echo "  Building $outname …"

    # Render math to PNGs and produce a pre-processed markdown alongside.
    local prepped="${md%.md}.math.md"
    python3 "$(dirname "$0")/_render_math.py" "$md" "$prepped" 2>&1 | tail -2

    python3 - "$prepped" "$title" "$subtitle" "$code" "$OUTDIR/$outname" "$(dirname "$0")" <<'PYEOF'
import sys, re, markdown, html, datetime, pathlib

src, title, subtitle, code, out, docs_root = sys.argv[1:7]
md_text = pathlib.Path(src).read_text()
# Strip leading YAML front-matter (--- ... ---) which pandoc-style headers leave behind
md_text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', md_text, count=1, flags=re.S)

# Extract inline <svg> blocks and replace with placeholders so the markdown
# parser does NOT treat their <text> elements as paragraphs.  We splice them
# back into the rendered HTML afterwards.
_svg_blocks: list[str] = []
def _stash_svg(m):
    _svg_blocks.append(m.group(0))
    return f"\n\nSVG_PLACEHOLDER_{len(_svg_blocks)-1}\n\n"
md_text = re.sub(r"<svg[\s\S]*?</svg>", _stash_svg, md_text, flags=re.I)

body_html = markdown.markdown(
    md_text,
    extensions=['tables', 'fenced_code', 'toc', 'attr_list', 'sane_lists'],
)

# Splice SVG blocks back, centred in a wrapper for proper page layout
for i, svg in enumerate(_svg_blocks):
    body_html = body_html.replace(
        f"<p>SVG_PLACEHOLDER_{i}</p>",
        f'<div class="inline-svg">{svg}</div>',
    )

css_path = "/tmp/_spacecdf_css.css"
cover_html = f"""
<div class="cover">
  <div class="banner">
    <div class="uo"><span class="light">u</span>Ottawa</div>
    <div class="label">UNIVERSITÉ D'OTTAWA · UNIVERSITY OF OTTAWA</div>
  </div>
  <div class="body">
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">{html.escape(subtitle)}</p>
    <p class="cohort">SpaceCDF</p>
    <p class="year">2026</p>
    <div class="footerblock">
      <p class="publisher">Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)</p>
      <p class="meta">{html.escape(code)} · SpaceCDF · Issue 1.0 · {datetime.date.today().isoformat()}</p>
      <p class="classification">Classification: Internal</p>
    </div>
  </div>
</div>
"""

doc = f"""<!doctype html>
<html data-title="{html.escape(title)}" data-code="{html.escape(code)}">
<head><meta charset="utf-8">
<style>__CSS__</style>
</head>
<body>
{cover_html}
{body_html}
</body></html>
"""

with open(css_path, 'r') as f:
    css = f.read()
doc = doc.replace("__CSS__", css)

from weasyprint import HTML
# Resolve relative image paths against docs/course/ — same convention the
# Markdown sources use ("../assets/figures/fig_*.png" or
# "../assets/figures/_math/m_*.png" → docs/assets/figures/...).
base = pathlib.Path(docs_root).resolve() / "course"
HTML(string=doc, base_url=str(base) + "/").write_pdf(out)
print(f"    -> {out}", flush=True)
PYEOF
    # Tidy up the intermediate math-rendered markdown
    rm -f "$prepped"
}

# Write CSS to a temp file the inner Python can read
echo "$CSS" > /tmp/_spacecdf_css.css

# Concatenate the per-session textbook source
COMBINED="/tmp/spacecdf_textbook_combined.md"
{
    cat "$(dirname "$0")/course/facilitator_book_expanded.md"
} > "$COMBINED"

WORKBOOK="/tmp/spacecdf_workbook_combined.md"
{
    cat "$(dirname "$0")/course/learner_workbook_expanded.md"
} > "$WORKBOOK"

echo "Building course volumes:"
build_pdf "$COMBINED" \
    "SpaceCDF — A Course Textbook" \
    "Companion textbook for the SpaceCDF 40-hour Concurrent Design Facility programme" \
    "SCDF-TEXT-001" \
    "SpaceCDF_Textbook.pdf"

build_pdf "$WORKBOOK" \
    "SpaceCDF — Course Workbook" \
    "Self-paced worksheets, exercises and reflections to accompany the SpaceCDF textbook" \
    "SCDF-WORK-001" \
    "SpaceCDF_Workbook.pdf"

# Installation guide
build_pdf "$(dirname "$0")/INSTALLATION_GUIDE.md" \
    "SpaceCDF — Installation Guide" \
    "From GitHub to your first design in 30 minutes" \
    "SCDF-INSTALL-001" \
    "SpaceCDF_Installation_Guide.pdf"

echo ""
echo "Done. PDFs in $(dirname "$0")/$OUTDIR/"
ls -la "$(dirname "$0")/$OUTDIR"/*.pdf | grep -E "Textbook|Workbook|Installation"
