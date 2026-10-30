#!/usr/bin/env python3
"""Build the single-file course books (Drive docs/course/*.md) and the
ORBIT NORTH Week 3 pack to PDF, in English or French.

    python3 build_course_books.py --lang fr --src "$FR_COURSE_DIR" --en-src "$EN_COURSE_DIR"
    python3 build_course_books.py --lang en --src "$EN_COURSE_DIR"

Books (each skipped if its sources are absent):
    textbook   facilitator_book_expanded.md + orbit_north_week3.md (Part 2) + back_cover.md
    workbook   learner_workbook_expanded.md + orbit_north_week3_workbook.md (Part 5)
    instructor instructor_book.md
    week3      docs/orbit_north/week3/<name>.md (EN) or .../week3/fr/<name>.md (FR), one PDF each

Styling is the uOttawa Horizon CSS of build_course_pdfs.sh (read from that
script, so the two stay in step) plus running heads per part, an index with
page numbers, and "Page N sur M" in French. French: <html lang="fr">,
hyphens:auto, and every heading id is taken positionally from the English
source so the index and any #anchor that targets an English slug resolves.
Output: docs/pdf/fr/*_FR.pdf (FR) or docs/pdf/en/*.pdf (EN).

Figures: every image whose path contains assets/figures/ (the books use
../assets/figures/ from docs/course and ../../assets/figures/ from
docs/orbit_north/week3) is taken from one figures folder, FIG_DIR (env or
--fig-dir).  Default: the Drive layout, i.e. <EN course dir>/../assets/figures
(= ../../assets/figures from the French docs/course/fr), falling back to the
paths as written.  The French build uses fig_<name>_fr.<ext> when that file
exists in FIG_DIR, else the English figure.
French index: the <section class="index"> of a French book is re-sorted into
French alphabetical order at build time (accents folded: É under E, œ = oe;
symbols first under « Symboles »); the Markdown keeps the English order so the
EN/FR structure stays parallel.  Index links are #anchors and are unaffected.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import os
import pathlib
import re
import sys

DOCS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(DOCS))
from _render_math import transform            # noqa: E402
from _i18n_build import heading_ids, remap_heading_ids, broken_links   # noqa: E402

WEEK3 = ["training_day1", "training_day2", "sim_leop_instructor", "sim_commissioning_instructor",
         "student_tool_reference", "student_procedure_quickref", "peer_review_worksheets",
         "breakpoint_spec"]

L = {
    "en": dict(
        textbook=("SpaceCDF Course Textbook", "SCDF-TEXT-001", "SpaceCDF_Textbook"),
        workbook=("SpaceCDF Course Workbook", "SCDF-WORK-001", "SpaceCDF_Workbook"),
        instructor=("SpaceCDF Instructor Book", "SCDF-INST-001", "SpaceCDF_Instructor_Book"),
        week3_running="ORBIT NORTH · Week 3",
        page='"Page " counter(page) " of " counter(pages)',
        footer_right="uOttawa SEDTI",
        publisher="Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)",
        issue="Issue 1.0", classification="Classification: Internal",
        instructor_sub="Supplement to the SpaceCDF Course Textbook",
        suffix="", outdir="en",
    ),
    "fr": dict(
        textbook=("Manuel du cours SpaceCDF", "SCDF-TEXT-001", "SpaceCDF_Textbook_FR"),
        workbook=("Cahier d’exercices", "SCDF-WORK-001", "SpaceCDF_Workbook_FR"),
        instructor=("Guide de l’enseignant SpaceCDF", "SCDF-INST-001", "SpaceCDF_Instructor_Book_FR"),
        week3_running="ORBIT NORTH · Semaine 3",
        page='"Page " counter(page) " sur " counter(pages)',
        footer_right="uOttawa ECIPG",
        publisher="Faculté de génie · École de conception et d’innovation pédagogique en génie (ECIPG)",
        issue="Édition 1.0", classification="Classification : usage interne",
        instructor_sub="Complément au manuel du cours SpaceCDF",
        suffix="_FR", outdir="fr",
    ),
}

EXTRA_CSS = """
@page {
    @top-left { width: 45%; vertical-align: bottom; }
    @top-right { content: string(running-part); width: 53%; vertical-align: bottom; text-align: right; }
    @bottom-left { content: string(running-title); font-family: 'Carlito', sans-serif; }
    @bottom-center { content: __PAGE__; font-family: 'Carlito', sans-serif; font-size: 8pt; color: #80746c; }
    @bottom-right { content: "__FOOTRIGHT__"; font-family: 'Carlito', sans-serif; font-size: 8pt;
                    font-weight: bold; color: #8f001a; }
}
@page backcover { @top-left{content:none} @top-right{content:none} @bottom-left{content:none}
                  @bottom-center{content:none} @bottom-right{content:none} }
html { string-set: running-title attr(data-title); }
/* the root's string-set is re-applied on every page, so the part head starts from the cover */
.cover { string-set: running-part attr(data-code); }
body { font-family: 'Carlito', 'Calibri', 'DejaVu Sans', sans-serif; }
code, pre { font-family: 'DejaVu Sans Mono', 'Consolas', monospace; }
.cover .subtitle { font-family: 'Caladea', 'Cambria', 'DejaVu Serif', serif; }
h1.part-divider { font-size: 30pt; text-align: center; margin-top: 85mm; border: none;
                  page-break-after: always; string-set: running-part content(); }
.cover h1 { page-break-before: avoid; string-set: none; }
td, th { overflow-wrap: break-word; }
.index ul { list-style: none; padding-left: 0; column-count: 2; column-gap: 10mm; font-size: 9pt; }
.index li { margin: 1pt 0; break-inside: avoid; }
.index .idx-letter { font-weight: 700; color: #8f001a; margin: 8pt 0 2pt 0; }
a.idx-page::after { content: target-counter(attr(href), page); }
.back-cover { page: backcover; page-break-before: always; }
.back-cover h1 { page-break-before: avoid; }
"""
FR_CSS = """
p, li, td, blockquote { hyphens: auto; }
h1, h2, h3, h4, th, code, pre, .cover * { hyphens: manual; }
"""


def base_css() -> str:
    sh = (DOCS / "build_course_pdfs.sh").read_text(encoding="utf-8")
    m = re.search(r"<<'CSSEOF'\n([\s\S]*?)\nCSSEOF", sh)
    if not m:
        sys.exit("could not read the CSS block from build_course_pdfs.sh")
    return m.group(1)


def split_yaml(txt: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, flags=re.S)
    if not m:
        return {}, txt
    meta = {}
    for line in m.group(1).splitlines():
        km = re.match(r'^([\w-]+):\s*"?(.*?)"?\s*$', line)
        if km:
            meta[km.group(1)] = km.group(2)
    return meta, txt[m.end():]


def md_to_html(md_text: str) -> str:
    import markdown
    md_text = transform(md_text)[0]
    svgs: list[str] = []

    def _stash(m):
        svgs.append(m.group(0))
        return f"\n\nSVG_PLACEHOLDER_{len(svgs)-1}\n\n"
    md_text = re.sub(r"<svg[\s\S]*?</svg>", _stash, md_text, flags=re.I)
    # slugify_unicode: the hand-built index targets ids such as "c8-ebn₀-vs-ber"
    from markdown.extensions.toc import TocExtension, slugify_unicode
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "attr_list", "sane_lists",
                                                  TocExtension(slugify=slugify_unicode)])
    for i, svg in enumerate(svgs):
        body = body.replace(f"<p>SVG_PLACEHOLDER_{i}</p>", f'<div class="inline-svg">{svg}</div>')
    return body


def assemble(src: pathlib.Path, names: list[str]) -> tuple[dict, str, str] | None:
    """Concatenate the book parts; the last part named 'back_cover' becomes the back page."""
    if not all((src / f"{n}.md").exists() for n in names if n != "back_cover"):
        return None
    meta, parts, back = {}, [], ""
    for n in names:
        p = src / f"{n}.md"
        if not p.exists():
            continue
        m, body = split_yaml(p.read_text(encoding="utf-8"))
        meta = meta or m
        if n == "back_cover":
            back = body
        else:
            parts.append(body.rstrip() + "\n")
    return meta, "\n\n".join(parts), back


def cover_html(lang: str, title: str, subtitle: str, code: str, cohort: str, year: str, publisher: str) -> str:
    s = L[lang]
    return f"""
<div class="cover" data-code="{html.escape(code)}">
  <div class="banner">
    <div class="uo"><span class="light">u</span>Ottawa</div>
    <div class="label">UNIVERSITÉ D'OTTAWA · UNIVERSITY OF OTTAWA</div>
  </div>
  <div class="body">
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">{html.escape(subtitle)}</p>
    <p class="cohort">{html.escape(cohort)}</p>
    <p class="year">{html.escape(year)}</p>
    <div class="footerblock">
      <p class="publisher">{html.escape(publisher)}</p>
      <p class="meta">{html.escape(code)} · {html.escape(cohort)} · {s['issue']} · {_dt.date.today().isoformat()}</p>
      <p class="classification">{html.escape(s['classification'])}</p>
    </div>
  </div>
</div>"""


_IMG_RE = re.compile(r'(<img\b[^>]*?\ssrc=")([^"]*?assets/figures/)([^"/]+)(")')


def localise_images(body_html: str, fig_dir: pathlib.Path | None, lang: str) -> tuple[str, list[str], list[str]]:
    """Point assets/figures/ images at fig_dir; in French prefer <name>_fr.<ext>.
    Returns (html, french figures used, figures missing from fig_dir)."""
    used_fr: list[str] = []
    missing: list[str] = []
    if fig_dir is None:
        return body_html, used_fr, missing

    def sub(m):
        name = m.group(3)
        target = fig_dir / name
        if lang == "fr":
            stem, ext = os.path.splitext(name)
            fr = fig_dir / f"{stem}_fr{ext}"
            if fr.exists():
                target = fr
                used_fr.append(fr.name)
        if not target.exists():
            missing.append(name)
            return m.group(0)
        return m.group(1) + target.resolve().as_uri() + m.group(4)

    return _IMG_RE.sub(sub, body_html), used_fr, missing


def _fold(text: str) -> str:
    """French collation key: accents folded, ligatures expanded, case-insensitive, punctuation ignored."""
    import unicodedata
    t = text.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("Æ", "AE")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).casefold()
    return re.sub(r"[^\w\s]", "", t).strip()


def sort_index_fr(md_text: str) -> str:
    """Re-sort the French <section class="index"> alphabetically with recomputed letter groups."""
    m = re.search(r'(<section class="index">.*?)(\n<div class="idx-letter">.*?)(\n</section>)', md_text, re.S)
    if not m:
        return md_text
    items = re.findall(r"^<li>.*</li>$", m.group(2), re.M)
    if not items:
        return md_text

    def label(li: str) -> str:
        return html.unescape(re.sub(r"<[^>]+>", "", li[4:-5]))

    groups: dict[str, list[tuple[tuple[str, str], str]]] = {}
    for li in items:
        lab = label(li)
        k = _fold(lab)
        first = k[:1].upper()
        g = first if "A" <= first <= "Z" else "Symboles"
        groups.setdefault(g, []).append(((k, lab.casefold()), li))
    order = (["Symboles"] if "Symboles" in groups else []) + sorted(g for g in groups if g != "Symboles")
    out = []
    for g in order:
        out.append(f'\n<div class="idx-letter">{g}</div>\n<ul>\n'
                   + "\n".join(li for _, li in sorted(groups[g], key=lambda t: t[0])) + "\n</ul>\n")
    return md_text[:m.start(2)] + "".join(out) + md_text[m.start(3):]


def build(lang: str, label: str, running: str, code: str, out: pathlib.Path,
          meta: dict, body_md: str, back_md: str, en_body_md: str | None,
          title: str, subtitle: str, cohort: str, year: str, fig_dir: pathlib.Path | None = None) -> None:
    from weasyprint import HTML
    s = L[lang]
    if lang == "fr":
        body_md = sort_index_fr(body_md)
    body = md_to_html(body_md)
    back = md_to_html(back_md) if back_md else ""
    body, used_fr, missing = localise_images(body, fig_dir, lang)
    n_img = len(re.findall(r"<img\b", body))
    if lang == "fr":
        if en_body_md is None:
            sys.exit(f"{label}: English source needed for anchor mapping (set EN_COURSE_DIR / --en-src)")
        en_html = md_to_html(en_body_md)
        body = remap_heading_ids(body, heading_ids(en_html), label)
    css = (base_css() + EXTRA_CSS.replace("__PAGE__", s["page"]).replace("__FOOTRIGHT__", s["footer_right"])
           + (FR_CSS if lang == "fr" else ""))
    publisher = meta.get("publisher") or s["publisher"]
    doc = (f'<!doctype html><html lang="{lang}" data-title="{html.escape(running)}" data-code="{html.escape(code)}">'
           f'<head><meta charset="utf-8"><style>{css}</style></head><body>'
           + cover_html(lang, title, subtitle, code, cohort, year, publisher) + body
           + (f'<div class="back-cover">{back}</div>' if back else "") + "</body></html>")
    bad = broken_links(doc)
    n_links = len(re.findall(r'href="#', doc))
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=doc, base_url=str(DOCS / "course") + "/").write_pdf(out)
    print(f"  {out.name}: internal links {n_links}, unresolved {len(bad)}"
          + (f" e.g. {bad[:5]}" if bad else "")
          + f"; images {n_img}" + (f", French figures {len(used_fr)}" if lang == "fr" else "")
          + (f", MISSING figures {sorted(set(missing))}" if missing else ""), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("en", "fr"), default="fr")
    ap.add_argument("--src", type=pathlib.Path, help="directory with the single-file books "
                    "(default: $FR_COURSE_DIR or docs/course/fr for fr; $EN_COURSE_DIR or docs/course for en)")
    ap.add_argument("--en-src", type=pathlib.Path, help="English books, for French anchor mapping "
                    "(default: $EN_COURSE_DIR or docs/course)")
    ap.add_argument("--only", nargs="*", choices=("textbook", "workbook", "instructor", "week3"))
    ap.add_argument("--fig-dir", type=pathlib.Path, help="figures folder (default: $FIG_DIR, else "
                    "<EN course dir>/../assets/figures, the Drive layout; images are left as written if absent)")
    args = ap.parse_args()
    lang = args.lang
    en_src = args.en_src or pathlib.Path(os.environ.get("EN_COURSE_DIR", DOCS / "course"))
    src = args.src or (pathlib.Path(os.environ.get("FR_COURSE_DIR", DOCS / "course" / "fr")) if lang == "fr"
                       else en_src)
    s = L[lang]
    fig_dir = args.fig_dir or (pathlib.Path(os.environ["FIG_DIR"]) if os.environ.get("FIG_DIR")
                               else en_src / ".." / "assets" / "figures")
    fig_dir = fig_dir.resolve() if fig_dir.is_dir() else None
    outdir = DOCS / "pdf" / s["outdir"]
    only = set(args.only or ("textbook", "workbook", "instructor", "week3"))
    print(f"Building {lang.upper()} course books from {src} -> {outdir}"
          + (f" (figures: {fig_dir})" if fig_dir else " (figures: paths as written)"))

    books = {
        "textbook": ["facilitator_book_expanded", "orbit_north_week3", "back_cover"],
        "workbook": ["learner_workbook_expanded", "orbit_north_week3_workbook"],
        "instructor": ["instructor_book"],
    }
    for key, names in books.items():
        if key not in only:
            continue
        got = assemble(src, names)
        if not got:
            print(f"  SKIP {key}: sources missing in {src}")
            continue
        meta, body_md, back_md = got
        en_got = assemble(en_src, names) if lang == "fr" else None
        running, code, stem = s[key]
        title = meta.get("title") or (re.search(r"^# (.+)$", body_md, re.M).group(1))
        if key == "instructor":
            body_md = re.sub(r"^# .+\n", "", body_md, count=1)       # title moves to the cover
            if en_got:
                en_got = (en_got[0], re.sub(r"^# .+\n", "", en_got[1], count=1), en_got[2])
        subtitle = meta.get("subtitle") or s["instructor_sub"]
        build(lang, key, running, code, outdir / f"{stem}.pdf", meta, body_md, back_md,
              en_got[1] if en_got else None, title, subtitle, "SpaceCDF", meta.get("term", "2026"), fig_dir)

    if "week3" in only:
        w_src = DOCS / "orbit_north" / "week3" / ("fr" if lang == "fr" else "")
        w_en = DOCS / "orbit_north" / "week3"
        for n in WEEK3:
            p = w_src / f"{n}.md"
            if not p.exists():
                print(f"  SKIP week3/{n}: {p} missing")
                continue
            meta, body_md = split_yaml(p.read_text(encoding="utf-8"))
            en_md = split_yaml((w_en / f"{n}.md").read_text(encoding="utf-8"))[1] if lang == "fr" else None
            stem = "ORBIT_NORTH_W3_" + "_".join(w.capitalize() for w in n.split("_")) + s["suffix"]
            build(lang, f"week3/{n}", s["week3_running"], meta.get("course-codes", "GNG 3100 · SYS 5186"),
                  outdir / f"{stem}.pdf", meta, body_md, "", en_md,
                  meta.get("title", n), meta.get("subtitle", ""), "ORBIT NORTH", meta.get("term", "2026"), fig_dir)


if __name__ == "__main__":
    main()
