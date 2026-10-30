#!/usr/bin/env python3
"""
Build the open-textbook PDF from docs/oer/chapters/*.md.

    cd docs/oer && python3 build_oer.py            # -> ../pdf/Concurrent_Spacecraft_Design_OER.pdf
    python3 build_oer.py --html out.html           # also keep the intermediate HTML
    python3 build_oer.py --lang fr                 # French edition from fr/chapters/
                                                   # -> ../pdf/Concurrent_Spacecraft_Design_OER_FR.pdf

French edition: book chrome (cover, contents, running heads, "Page N sur M")
is French, <html lang="fr"> with hyphens:auto, and every heading id is taken
positionally from the ENGLISH book, so anchors keep their English slugs
(headings are 1:1 between the editions; the build refuses on a count mismatch).

Pipeline: concatenate chapters in numeric order -> render $…$ / $$…$$ math to
SVG with docs/_render_math.py (matplotlib mathtext) -> Python-Markdown -> inline
SVG blocks spliced back -> WeasyPrint with a neutral, licence-bearing cover.
No institutional branding. Requires: markdown, weasyprint, matplotlib.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent          # docs/oer
DOCS = HERE.parent                                      # docs
CHAPTERS = HERE / "chapters"
OUT_PDF = DOCS / "pdf" / "Concurrent_Spacecraft_Design_OER.pdf"

TITLE = "Concurrent Spacecraft Design"
SUBTITLE = "An Open Textbook on Mission Design and Concurrent Engineering"
AUTHORS = "Franz Newland and contributors"
EDITION = "Open Educational Resource edition 1.0"
LICENCE = "Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)"

# French edition (--lang fr). English values above are untouched.
FR = {
    "chapters": HERE / "fr" / "chapters",
    "out_pdf": DOCS / "pdf" / "Concurrent_Spacecraft_Design_OER_FR.pdf",
    "combined": HERE / "book.fr.md",
    "title": "Conception concourante d\u2019engins spatiaux",
    "subtitle": "Un manuel ouvert sur la conception de missions et l\u2019ing\u00e9nierie concourante",
    "authors": "Franz Newland et collaborateurs",
    "edition": "\u00c9dition REL 1.0 (ressource \u00e9ducative libre)",
    "licence": "Sous licence Creative Commons Attribution 4.0 International (CC BY 4.0)",
    "licence_body": "Vous \u00eates libre de partager et d\u2019adapter cette \u0153uvre \u00e0 toutes fins, y compris "
                    "commerciales, \u00e0 condition d\u2019en cr\u00e9diter l\u2019origine de mani\u00e8re appropri\u00e9e. "
                    "Texte int\u00e9gral de la licence\u202f: https://creativecommons.org/licenses/by/4.0/deed.fr",
    "series": "Manuel ouvert \u00b7 Ing\u00e9nierie des syst\u00e8mes spatiaux",
    "contents": "Table des mati\u00e8res",
    "part_re": r"^# (Partie [IVX]+ \u2014 .*)$",
}
LANG = "en"

CSS = r"""
* { font-family: 'Carlito', 'DejaVu Sans', sans-serif; }
code, pre, code * { font-family: 'DejaVu Sans Mono', monospace; }
@page {
    size: A4;
    margin: 22mm 20mm 24mm 20mm;
    @top-left   { content: string(running-title); font-size: 8pt; color: #555; width: 26%;
                  vertical-align: bottom;
                  border-bottom: 0.6pt solid #1f4e79; padding-bottom: 3pt; }
    @top-right  { content: string(running-chapter); font-size: 8pt; color: #555; width: 72%;
                  vertical-align: bottom; text-align: right;
                  border-bottom: 0.6pt solid #1f4e79; padding-bottom: 3pt; }
    @bottom-left   { content: "CC BY 4.0"; font-size: 8pt; color: #777; }
    @bottom-center { content: counter(page); font-size: 9pt; color: #333; }
    @bottom-right  { content: "Concurrent Spacecraft Design"; font-size: 8pt; color: #777; }
}
@page cover { margin: 0; @top-left{content:none} @top-right{content:none}
              @bottom-left{content:none} @bottom-center{content:none} @bottom-right{content:none} }
@page toc   { @top-left{content:none} @top-right{content:none} }
html { string-set: running-title attr(data-title); }
body { font-family: 'Carlito', 'DejaVu Sans', sans-serif; font-size: 10.2pt;
       line-height: 1.42; color: #222; }
h1 { string-set: running-chapter content(); }

/* cover */
.cover { page: cover; height: 297mm; position: relative; background: #ffffff; page-break-after: always; }
.cover .band { background: #1f4e79; height: 70mm; padding: 26mm 22mm 0 22mm; color: #fff; }
.cover .band .series { font-size: 9pt; letter-spacing: 1.5pt; text-transform: uppercase; opacity: .85; }
.cover .body { padding: 18mm 22mm 0 22mm; }
.cover h1 { font-size: 34pt; line-height: 1.08; font-weight: 800; color: #1f4e79; margin: 0 0 8pt 0;
            border: none; border-bottom: 1.6pt solid #1f4e79; padding-bottom: 10pt;
            page-break-before: avoid; page-break-after: avoid; string-set: none; }
.cover .subtitle { font-size: 14pt; font-style: italic; color: #333; margin: 6pt 0 26pt 0; text-align: left; }
.cover p { text-align: left; }
.cover .authors { font-size: 12.5pt; font-weight: 600; margin: 0 0 4pt 0; }
.cover .edition { font-size: 10.5pt; color: #444; }
.cover .foot { position: absolute; left: 22mm; right: 22mm; bottom: 20mm; border-top: 1.2pt solid #1f4e79;
               padding-top: 8pt; font-size: 9.5pt; color: #333; }
.cover .foot .lic { font-weight: 600; color: #1f4e79; }

/* TOC */
.toc { page: toc; page-break-after: always; }
.toc h1 { border: none; }
.toc ul { list-style: none; padding-left: 0; }
.toc li { margin: 2pt 0; }
.toc li.l2 { padding-left: 14pt; font-size: 9.4pt; color: #444; }
.toc a { text-decoration: none; color: inherit; }
.toc a::after { content: leader('.') target-counter(attr(href), page); }

/* headings */
h1 { font-size: 22pt; color: #1f4e79; border-bottom: 1.2pt solid #1f4e79; padding-bottom: 5pt;
     margin: 0 0 14pt 0; page-break-after: avoid; }
body > h1 { page-break-before: always; }
.toc h1, .cover h1 { page-break-before: avoid; }
h1.part { font-size: 28pt; border: none; margin-top: 90mm; text-align: center; page-break-after: always; }
h2 { font-size: 14.5pt; color: #1f4e79; margin: 18pt 0 6pt 0; page-break-after: avoid; }
h3 { font-size: 11.8pt; color: #333; margin: 12pt 0 4pt 0; page-break-after: avoid; }
h4 { font-size: 10.5pt; color: #333; margin: 10pt 0 3pt 0; }

p { margin: 0 0 7pt 0; text-align: justify; orphans: 3; widows: 3; }
blockquote { margin: 8pt 0; padding: 6pt 12pt; border-left: 3pt solid #1f4e79; background: #f3f6fa; }
blockquote p { margin: 0 0 4pt 0; text-align: left; }  /* worked examples: inline math + justify = ugly gaps */
table { border-collapse: collapse; width: 100%; margin: 8pt 0 12pt 0; font-size: 8.6pt; page-break-inside: auto; }
th, td { border: 0.5pt solid #bbb; padding: 3pt 3.5pt; vertical-align: top; }
td { overflow-wrap: break-word; }
/* tables with >= 8 columns cannot fit at body size: shrink and allow in-word breaks rather than run off the page */
table.wide { font-size: 7.9pt; }
table.wide th, table.wide td { padding: 2.5pt 3pt; }
table.wide td { overflow-wrap: break-word; }
table.xwide { font-size: 7.6pt; }
table.xwide td { overflow-wrap: anywhere; }
th { background: #e8eef5; text-align: left; font-weight: 700; }
tr { page-break-inside: avoid; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.6pt; background: #f4f4f4; padding: 0 2pt; }
pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.2pt; background: #f4f4f4;
      padding: 7pt 9pt; border-left: 3pt solid #bbb; white-space: pre-wrap; page-break-inside: avoid; }
img { max-width: 100%; height: auto; display: block; margin: 10pt auto 4pt auto; page-break-inside: avoid;
      page-break-after: avoid; }   /* keep the "**Figure N.k**" caption on the same page */
img.math-display { margin: 6pt auto; page-break-after: auto; }
img.math-inline { display: inline; vertical-align: middle; margin: 0 1pt; }
.inline-svg { text-align: center; margin: 10pt 0; page-break-inside: avoid; page-break-after: avoid; }
.inline-svg svg { max-width: 100%; height: auto; }
p.caption, p:has(> strong:first-child) { }
em { color: #333; }
hr { border: none; border-top: 0.6pt solid #ccc; margin: 14pt 0; }
ol, ul { margin: 0 0 7pt 0; }
li { margin: 1.5pt 0; }
"""


def check_fonts() -> None:
    """Refuse to build unless the two families named in CSS resolve via fontconfig.
    (A fallback to a random system font — e.g. a macOS .dfont seen through a
    mounted volume — produced an unreadable PDF once.)"""
    import shutil, subprocess
    if not shutil.which("fc-match"):
        print("warning: fontconfig (fc-match) not found; cannot verify fonts", file=sys.stderr)
        return
    for fam in ("Carlito", "DejaVu Sans", "DejaVu Sans Mono"):
        got = subprocess.run(["fc-match", "-f", "%{family}", fam], capture_output=True, text=True).stdout
        if fam.split()[0] not in got:
            sys.exit(f"font '{fam}' not installed (fc-match gave '{got}'). "
                     "Install fonts-crosextra-carlito and fonts-dejavu-core (see Makefile 'deps').")


def chapter_files(lang: str | None = None) -> list[pathlib.Path]:
    d = FR["chapters"] if (lang or LANG) == "fr" else CHAPTERS
    return sorted(p for p in d.glob("*.md") if p.name[:2].isdigit())


_LIST_RE = re.compile(r"^(>\s*)?([-*]|\d+\.)\s+\S")
_CODE_FENCE_RE = re.compile(r"^>\s*```")


def _normalise_lists(txt: str) -> str:
    """Python-Markdown needs a blank line before a list that follows a
    paragraph (otherwise the items run on as prose), and it does not parse
    fenced code inside a blockquote. Insert the blank line, and turn
    "> ```" fences into blockquote-indented code blocks."""
    out: list[str] = []
    in_bq_fence = False
    for line in txt.split("\n"):
        if _CODE_FENCE_RE.match(line):
            in_bq_fence = not in_bq_fence
            if in_bq_fence:
                out.append(">")
            continue
        if in_bq_fence:
            content = line[2:] if line.startswith("> ") else line[1:] if line.startswith(">") else line
            out.append(">     " + content)
            continue
        # nested items indented 2-3 spaces are lazy continuations to Python-Markdown; it needs 4
        line = re.sub(r"^(>?) {2,3}(?=([-*]|\d+\.)\s)", r"\1    ", line)
        m = _LIST_RE.match(line)
        if m and out:
            prev = out[-1]
            prev_body = prev[1:].strip() if prev.startswith(">") else prev.strip()
            prev_is_item = bool(_LIST_RE.match(prev)) or prev.startswith(("  ", "\t", ">  "))
            if prev_body and not prev_is_item and not prev.lstrip().startswith("|"):
                out.append(">" if (prev.startswith(">") and m.group(1)) else "")
        out.append(line)
    return "\n".join(out)


def concatenate(lang: str | None = None) -> str:
    parts = []
    for p in chapter_files(lang):
        txt = p.read_text(encoding="utf-8")
        txt = re.sub(r"^---\s*\n.*?\n---\s*\n", "", txt, count=1, flags=re.S)  # strip YAML
        parts.append(_normalise_lists(txt).rstrip() + "\n")
    return "\n\n".join(parts)


def build_toc(md_text: str) -> str:
    items = []
    for line in md_text.splitlines():
        m = re.match(r"^(#{1,2})\s+(.*)$", line)
        if not m:
            continue
        level, text = len(m.group(1)), m.group(2).strip()
        if level == 2 and not re.match(r"^\d+\.\d+ ", text):
            continue  # only numbered sections at level 2
        # use Python-Markdown's own slugify so TOC hrefs hit the ids the toc
        # extension generates ("1.1 What…" -> "11-what", not "1-1-what")
        from markdown.extensions.toc import slugify
        slug = slugify(text, "-")
        items.append((level, text, slug))
    lis = "".join(
        f'<li class="l{lvl}"><a href="#{slug}">{html.escape(text)}</a></li>'
        for lvl, text, slug in items
    )
    return f'<div class="toc"><h1>Contents</h1><ul>{lis}</ul></div>'


def md_to_body(md_text: str, part_re: str = r"^# (Part [IVX]+ — .*)$") -> str:
    import markdown

    # 2. stash inline SVG blocks
    svgs: list[str] = []
    def _stash(m):
        svgs.append(m.group(0))
        return f"\n\nSVG_PLACEHOLDER_{len(svgs)-1}\n\n"
    md_text = re.sub(r"<svg[\s\S]*?</svg>", _stash, md_text, flags=re.I)

    # Part headings get a class so they render as part-title pages
    md_text = re.sub(part_re, r"# \1 {: .part }", md_text, flags=re.M)

    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists", "md_in_html"],
        extension_configs={"toc": {"anchorlink": False, "toc_depth": "1-3"}},
    )
    for i, svg in enumerate(svgs):
        body = body.replace(f"<p>SVG_PLACEHOLDER_{i}</p>", f'<div class="inline-svg">{svg}</div>')

    # tag tables with many columns so the CSS can shrink them to the page width
    def _tag_wide(m):
        ncols = len(re.findall(r"<th\b", m.group(0).split("</tr>")[0]))
        cls = "wide xwide" if ncols >= 10 else "wide" if ncols >= 8 else None
        return m.group(0).replace("<table>", f'<table class="{cls}">', 1) if cls else m.group(0)
    body = re.sub(r"<table>[\s\S]*?</table>", _tag_wide, body)
    return body


def render(md_path: pathlib.Path, html_out: pathlib.Path | None) -> pathlib.Path:
    if LANG == "fr":
        return render_fr(md_path, html_out)
    from weasyprint import HTML

    # 1. math -> SVG via the existing renderer (writes <stem>.math.md)
    prepped = md_path.with_suffix(".math.md")
    subprocess.run([sys.executable, str(DOCS / "_render_math.py"), str(md_path), str(prepped)],
                   check=True)
    md_text = prepped.read_text(encoding="utf-8")
    body = md_to_body(md_text)

    toc = build_toc(prepped.read_text(encoding="utf-8"))
    today = _dt.date.today().isoformat()
    cover = f"""
<div class="cover">
  <div class="band"><div class="series">Open textbook · Space systems engineering</div></div>
  <div class="body">
    <h1>{html.escape(TITLE)}</h1>
    <p class="subtitle">{html.escape(SUBTITLE)}</p>
    <p class="authors">{html.escape(AUTHORS)}</p>
    <p class="edition">{html.escape(EDITION)} · {today}</p>
  </div>
  <div class="foot">
    <p class="lic">{html.escape(LICENCE)}</p>
    <p>You are free to share and adapt this work for any purpose, including commercially, provided you give
       appropriate credit. Full licence text: https://creativecommons.org/licenses/by/4.0/</p>
  </div>
</div>"""
    doc = f"""<!doctype html><html data-title="{html.escape(TITLE)}"><head><meta charset="utf-8">
<style>{CSS}</style></head><body>{cover}{toc}{body}</body></html>"""
    if html_out:
        html_out.write_text(doc, encoding="utf-8")

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=doc, base_url=str(HERE) + "/").write_pdf(OUT_PDF)
    try:
        prepped.unlink(missing_ok=True)
    except OSError:
        pass  # intermediate file; harmless if it cannot be removed
    return OUT_PDF


FR_CSS_EXTRA = r"""
@page { @top-left { width: 34%; } @top-right { width: 64%; } @bottom-center { content: "Page " counter(page) " sur " counter(pages); font-size: 9pt; color: #333; }
        @bottom-right  { content: "Conception concourante d’engins spatiaux"; font-size: 8pt; color: #777; } }
p, li, td, blockquote { hyphens: auto; }
h1, h2, h3, h4, th, code, pre, .cover * { hyphens: manual; }
"""


def _toc_from_html(body: str, title: str) -> str:
    """Contents list built from the rendered headings (French text, English ids)."""
    items = []
    for m in re.finditer(r'<h([12])\b[^>]*\sid="([^"]*)"[^>]*>([\s\S]*?)</h\1>', body):
        lvl, hid, inner = int(m.group(1)), m.group(2), m.group(3)
        inner = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*>', r"\1", inner)
        text = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        if lvl == 2 and not re.match(r"^\d+\.\d+ ", text):
            continue
        items.append(f'<li class="l{lvl}"><a href="#{hid}">{html.escape(text)}</a></li>')
    return f'<div class="toc"><h1>{html.escape(title)}</h1><ul>{"".join(items)}</ul></div>'


def _prefer_fr_figures(body: str) -> str:
    """Point every <img src="…/fig_x.png|svg"> at fig_x_fr.png|svg when that French
    figure exists (built by docs/assets/figures/make_all.py); otherwise keep the English."""
    swapped, kept = [], []

    def _swap(m):
        src = m.group(2)
        p = pathlib.Path(src)
        if p.stem.endswith("_fr") or p.suffix.lower() not in (".png", ".svg"):
            return m.group(0)
        fr = p.with_name(f"{p.stem}_fr{p.suffix}")
        if (HERE / fr).is_file():
            swapped.append(p.name)
            return f"{m.group(1)}{fr.as_posix()}{m.group(3)}"
        if p.name.startswith("fig_"):
            kept.append(p.name)
        return m.group(0)

    body = re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")', _swap, body)
    print(f"  figures: {len(swapped)} French, {len(kept)} English fallback"
          + (f" ({', '.join(sorted(set(kept)))})" if kept else ""))
    return body


def render_fr(md_path: pathlib.Path, html_out: pathlib.Path | None) -> pathlib.Path:
    from weasyprint import HTML
    sys.path.insert(0, str(DOCS))
    from _render_math import transform
    from _i18n_build import heading_ids, remap_heading_ids, broken_links

    # English heading ids, rendered through the identical pipeline
    en_body = md_to_body(transform(concatenate("en"))[0])
    fr_body = md_to_body(transform(md_path.read_text(encoding="utf-8"))[0], part_re=FR["part_re"])
    fr_body = remap_heading_ids(fr_body, heading_ids(en_body), "OER FR")
    fr_body = _prefer_fr_figures(fr_body)
    toc = _toc_from_html(fr_body, FR["contents"])
    today = _dt.date.today().isoformat()
    cover = f"""
<div class="cover">
  <div class="band"><div class="series">{html.escape(FR["series"])}</div></div>
  <div class="body">
    <h1>{html.escape(FR["title"])}</h1>
    <p class="subtitle">{html.escape(FR["subtitle"])}</p>
    <p class="authors">{html.escape(FR["authors"])}</p>
    <p class="edition">{html.escape(FR["edition"])} · {today}</p>
  </div>
  <div class="foot">
    <p class="lic">{html.escape(FR["licence"])}</p>
    <p>{html.escape(FR["licence_body"])}</p>
  </div>
</div>"""
    doc = f"""<!doctype html><html lang="fr" data-title="{html.escape(FR["title"])}"><head><meta charset="utf-8">
<style>{CSS}{FR_CSS_EXTRA}</style></head><body>{cover}{toc}{fr_body}</body></html>"""
    bad = broken_links(doc)
    n_links = len(re.findall(r'href="#', doc))
    print(f"  internal links: {n_links}, unresolved: {len(bad)}"
          + (f" e.g. {bad[:5]}" if bad else ""))
    if html_out:
        html_out.write_text(doc, encoding="utf-8")
    out = FR["out_pdf"]
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=doc, base_url=str(HERE) + "/").write_pdf(out)
    md_path.unlink(missing_ok=True)   # intermediate only; the English book.md stays as before
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", type=pathlib.Path, help="also write the intermediate HTML here")
    ap.add_argument("--lang", choices=("en", "fr"), default="en", help="edition to build (default en)")
    args = ap.parse_args()
    global LANG
    LANG = args.lang
    check_fonts()
    combined = FR["combined"] if LANG == "fr" else HERE / "book.md"
    combined.write_text(concatenate(), encoding="utf-8")
    out = render(combined, args.html)
    print(f"-> {out} ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
