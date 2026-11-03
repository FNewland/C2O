#!/usr/bin/env python3
"""doc_viewer.py — Lightweight Markdown documentation browser.

Serves the mission manual and procedure markdown files as rendered HTML
with a sidebar table of contents, navigation, and search. Fully offline —
no CDN dependencies. Uses a simple regex-based Markdown-to-HTML converter.

Usage::

    python tools/doc_viewer.py                          # default port 8095
    python tools/doc_viewer.py --port 9200
    python tools/doc_viewer.py --docs configs/eosat1/manual --port 8095
"""
from __future__ import annotations

import argparse
import html
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[0].parent
DEFAULT_DOCS = REPO / "configs" / "eosat1"
# The shared tool page frame (tools/tool_frame.py) sits next to this file.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
# smo_common (shared HTTP policy + design system) from the checkout when the
# suite is not pip-installed.
_COMMON_SRC = REPO / "packages" / "smo-common" / "src"
if _COMMON_SRC.is_dir() and str(_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(_COMMON_SRC))

try:
    from aiohttp import web
except ImportError:
    print("ERROR: aiohttp required. Install: pip install aiohttp")
    raise SystemExit(1)


# ── Minimal Markdown → HTML converter (no dependencies) ──────────────

#: A pandoc heading attribute block at the end of a heading line:
#: ``## Title {#id}`` (optionally ``{#id .class key=val}``). Author ruling Q33
#: (2026-10-30) puts these in the EN and FR manuals with the same id in both
#: languages; the viewer uses the id and never displays the block.
HEADING_ATTR_RE = re.compile(
    r'\s*\{#([A-Za-z0-9_][\w.:-]*)(?:\s[^}]*)?\}\s*$')


def split_heading_anchor(text: str) -> tuple[str, str | None]:
    """``"Title {#id}"`` -> ``("Title", "id")``; no block -> ``(text, None)``."""
    m = HEADING_ATTR_RE.search(text)
    if not m:
        return text, None
    return text[:m.start()].rstrip(), m.group(1)


def md_to_html(text: str) -> str:
    """Convert Markdown to HTML using regex. Handles headings, bold, italic,
    code blocks, inline code, links, tables, lists, horizontal rules, and
    block quotes. Good enough for documentation browsing."""
    lines = text.split('\n')
    out: list[str] = []
    in_code_block = False
    in_table = False
    in_list = False
    list_type = 'ul'
    para_open = False

    for line in lines:
        if not line.strip().startswith('```') and not in_code_block and line.strip():
            # anything that is not a plain paragraph line closes the paragraph
            st = line.strip()
            if (st.startswith(('#', '|', '> ')) or re.match(r'^[-*+] ', st)
                    or re.match(r'^\d+\. ', st) or re.match(r'^[-*_]{3,}\s*$', st)):
                para_open = False
        # Fenced code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                out.append('</code></pre>')
                in_code_block = False
            else:
                lang = line.strip()[3:].strip()
                cls = f' class="lang-{html.escape(lang)}"' if lang else ''
                out.append(f'<pre tabindex="0"><code{cls}>')
                in_code_block = True
            continue
        if in_code_block:
            out.append(html.escape(line))
            continue

        # Close open list if non-list line
        stripped = line.strip()
        # An indented line under a list item continues that item.
        if (in_list and stripped and line[:1] in (" ", "\t") and out
                and out[-1].endswith('</li>')
                and not re.match(r'^([-*+]|\d+\.) ', stripped)):
            out[-1] = out[-1][:-5] + ' ' + _inline(stripped) + '</li>'
            continue
        is_list_item = bool(re.match(r'^[-*+] ', stripped) or re.match(r'^\d+\. ', stripped))
        if in_list and not is_list_item and stripped:
            out.append(f'</{list_type}>')
            in_list = False

        # Close table
        if in_table and not stripped.startswith('|'):
            out.append('</tbody></table></div>')
            in_table = False

        # Empty line: ends a paragraph (spacing is the stylesheet's job)
        if not stripped:
            para_open = False
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            heading, anchor = split_heading_anchor(m.group(2))
            content = _inline(heading)
            slug = anchor or re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')
            out.append(f'<h{level} id="{html.escape(slug)}">{content}</h{level}>')
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            out.append('<hr>')
            continue

        # Block quote
        if stripped.startswith('> '):
            out.append(f'<blockquote>{_inline(stripped[2:])}</blockquote>')
            continue

        # Table
        if stripped.startswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                # Separator row — skip (already started table)
                continue
            if not in_table:
                out.append('<div class="tbl"><table><thead><tr>')
                for c in cells:
                    out.append(f'<th>{_inline(c)}</th>')
                out.append('</tr></thead><tbody>')
                in_table = True
            else:
                out.append('<tr>')
                for c in cells:
                    out.append(f'<td>{_inline(c)}</td>')
                out.append('</tr>')
            continue

        # Unordered list
        m = re.match(r'^[-*+] (.*)', stripped)
        if m:
            if not in_list:
                list_type = 'ul'
                out.append('<ul>')
                in_list = True
            out.append(f'<li>{_inline(m.group(1))}</li>')
            continue

        # Ordered list
        m = re.match(r'^\d+\. (.*)', stripped)
        if m:
            if not in_list:
                list_type = 'ol'
                out.append('<ol>')
                in_list = True
            out.append(f'<li>{_inline(m.group(1))}</li>')
            continue

        # Paragraph: consecutive lines are one paragraph
        if para_open and out and out[-1].endswith('</p>'):
            # "**Label:** value" lines (document headers) keep their own line
            sep = '<br>' if re.match(r'^\*\*[^*]+:\*\*', stripped) else ' '
            out[-1] = out[-1][:-4] + sep + _inline(stripped) + '</p>'
        else:
            out.append(f'<p>{_inline(stripped)}</p>')
            para_open = True
        continue

    # Close open blocks
    if in_code_block:
        out.append('</code></pre>')
    if in_table:
        out.append('</tbody></table></div>')
    if in_list:
        out.append(f'</{list_type}>')

    return '\n'.join(out)


def _inline(text: str) -> str:
    """Process inline Markdown: bold, italic, code, links, images."""
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Images
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


# ── File discovery ────────────────────────────────────────────────────

#: Folders that are not document categories. ``i18n/`` holds the French
#: mirror of the tree (i18n/fr/<same path>); it is reached through the UI
#: language, never listed as a category of its own (R3 audit A9).
HIDDEN_DIRS = {"i18n"}
LANGS = ("en", "fr")


def discover_docs(base: Path) -> dict[str, list[dict]]:
    """Find all English .md files organised by category (top-level folder).

    Each entry carries ``fr_title`` when a French translation exists at
    ``i18n/fr/<path>``.
    """
    categories: dict[str, list[dict]] = {}

    def entry(f: Path) -> dict:
        rel = f.relative_to(base).as_posix()
        fr = base / "i18n" / "fr" / rel
        return {"name": f.stem, "path": rel, "title": _extract_title(f),
                "fr_title": _extract_title(fr) if fr.is_file() else None}

    for subdir in sorted(base.iterdir()):
        if subdir.is_dir() and subdir.name not in HIDDEN_DIRS:
            md_files = sorted(subdir.rglob('*.md'))
            if md_files:
                categories[subdir.name] = [entry(f) for f in md_files]
    # Also include top-level .md files
    top_level = sorted(base.glob('*.md'))
    if top_level:
        categories['_root'] = [entry(f) for f in top_level]
    return categories


def resolve_doc(docs_root: Path, rel_path: str, lang: str) -> tuple[Path | None, str]:
    """(file to render, language actually served) for a document request.

    The French file is used when ``lang == "fr"`` and a translation exists;
    otherwise the English original. Paths outside ``docs_root`` and the
    ``i18n/`` tree itself are refused (None)."""
    root = docs_root.resolve()
    rel = rel_path.strip("/")
    if not rel.endswith(".md") or rel.split("/", 1)[0] in HIDDEN_DIRS:
        return None, "en"
    en = (root / rel).resolve()
    try:
        en.relative_to(root)
    except ValueError:
        return None, "en"
    if not en.is_file():
        return None, "en"
    if lang == "fr":
        fr = (root / "i18n" / "fr" / rel).resolve()
        if fr.is_file():
            return fr, "fr"
    return en, "en"


def request_lang(request) -> str:
    lang = (request.query.get("lang") or "").strip().lower()[:2]
    return lang if lang in LANGS else "en"


def _extract_title(path: Path) -> str:
    """Extract the first heading from a markdown file."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^#\s+(.*)', line.strip())
                if m:
                    return split_heading_anchor(m.group(1))[0]
        return path.stem.replace('_', ' ').title()
    except Exception:
        return path.stem


# ── HTML templates ────────────────────────────────────────────────────
# Light-touch restyle (R3 audit A9/§8): the page loads the shared design
# system and language runtime (TOOL_HEAD) and its own rules are written
# against the DS tokens, so it reads as part of the suite. Full restyle and
# portal chrome are a later phase.

PAGE_CSS = """
/* Documentation. A reading page: the text sits at ~70 characters a line,
   the document list on the left, this document's contents on the right
   (sticky), both scrolling on their own. Tokens only. */
.dv{ display:grid; grid-template-columns:280px minmax(0,1fr) 240px; align-items:start; }
.dv-nav{ position:sticky; top:49px; height:calc(100vh - 49px); overflow:auto;
  border-right:1px solid var(--line); padding:var(--sp-3) var(--sp-3) var(--sp-5); }
.dv-nav .ds-field{ margin:0 var(--sp-1) var(--sp-3); }
.dv-nav h2{ font-size:var(--fs-label); font-weight:600; color:var(--tx3); margin:var(--sp-4) var(--sp-2) var(--sp-1); }
.dv-nav a.doc-link{ display:block; padding:4px var(--sp-2); color:var(--tx2); text-decoration:none;
  font-size:var(--fs-body); line-height:1.35; border-radius:var(--radius-sm); }
.dv-nav a.doc-link:hover{ background:var(--s2); color:var(--tx); }
.dv-nav a.doc-link[aria-current]{ color:var(--val); background:var(--s2); box-shadow:inset 2px 0 0 var(--accent); }
.dv-nav a.doc-link.en-only::after{ content:" EN"; font-family:var(--mono); font-size:var(--fs-label); color:var(--tx3); }
.dv-nav .none{ display:none; padding:var(--sp-2); color:var(--tx3); font-size:var(--fs-label); }
.dv-main{ min-width:0; padding:var(--sp-5) var(--sp-6) var(--sp-6); }
.dv-toc{ position:sticky; top:49px; max-height:calc(100vh - 49px); overflow:auto;
  padding:var(--sp-5) var(--sp-4) var(--sp-5) 0; font-size:var(--fs-label); }
.dv-toc h2{ font-size:var(--fs-label); font-weight:600; color:var(--tx3); margin:0 0 var(--sp-2) var(--sp-3); }
.dv-toc ol{ list-style:none; border-left:1px solid var(--line); }
.dv-toc a{ display:block; padding:3px var(--sp-3); color:var(--tx2); text-decoration:none; line-height:1.35; }
.dv-toc a:hover{ color:var(--tx); }
.dv-toc a.l3{ padding-left:var(--sp-5); color:var(--tx3); }
.dv-toc a[aria-current="true"]{ color:var(--val); box-shadow:-1px 0 0 var(--accent); }
.dv-toc-inline{ display:none; margin-bottom:var(--sp-4); border:1px solid var(--line); border-radius:var(--radius); }
.docbar{ display:flex; gap:var(--sp-4); align-items:baseline; justify-content:space-between; flex-wrap:wrap;
  font-size:var(--fs-label); color:var(--tx3); max-width:70ch; margin-bottom:var(--sp-4); }
.docbar a{ color:var(--tx2); }
.note-lang{ max-width:70ch; font-size:var(--fs-body); color:var(--tx2); border:1px solid var(--line-2);
  border-left:3px solid var(--tx3); border-radius:var(--radius-sm); padding:var(--sp-2) var(--sp-3); margin-bottom:var(--sp-4); }
article{ max-width:70ch; font-size:15px; line-height:1.6; color:var(--tx); }
/* procedure card working copy (smo_common/ui/procard.js): below the frame bar */
article .pc-bar{ top:48px; }
article .pc-ctl{ font-size:var(--fs-label); }
article h1{ font-size:var(--fs-title); line-height:1.25; font-weight:600; color:var(--val); margin:0 0 var(--sp-4); }
article h2{ font-size:17px; font-weight:600; line-height:1.3; color:var(--val); margin:var(--sp-6) 0 var(--sp-2);
  padding-top:var(--sp-3); border-top:1px solid var(--line); scroll-margin-top:64px; }
article h3{ font-size:15px; font-weight:600; color:var(--tx); margin:var(--sp-5) 0 var(--sp-1); scroll-margin-top:64px; }
article h4,article h5,article h6{ font-size:var(--fs-body); font-weight:600; color:var(--tx2); margin:var(--sp-4) 0 var(--sp-1); }
article p{ margin:0 0 var(--sp-3); }
article a{ color:var(--accent); }
article strong{ font-weight:600; color:var(--val); }
article code{ font-family:var(--mono); font-size:.87em; background:var(--s2); padding:1px 4px; border-radius:var(--radius-sm); }
article pre{ background:var(--s1); border:1px solid var(--line); padding:var(--sp-3); border-radius:var(--radius);
  overflow-x:auto; margin:0 0 var(--sp-3); font-size:var(--fs-label); line-height:1.5; }
article pre code{ padding:0; background:none; font-size:inherit; }
article .tbl{ overflow-x:auto; margin:0 0 var(--sp-4); }
article table{ border-collapse:collapse; width:100%; font-size:var(--fs-body); line-height:1.4; }
article th,article td{ border-bottom:1px solid var(--line); padding:6px 10px 6px 0; text-align:left; vertical-align:top; }
article th{ color:var(--tx3); font-weight:500; font-size:var(--fs-label); border-bottom-color:var(--line-2); }
article blockquote{ border-left:3px solid var(--line-2); padding:0 0 0 var(--sp-3); color:var(--tx2); margin:0 0 var(--sp-3); }
article hr{ border:none; border-top:1px solid var(--line); margin:var(--sp-5) 0; }
article hr + h2{ border-top:0; padding-top:0; margin-top:0; }
article img{ max-width:100%; }
article ul,article ol{ padding-left:var(--sp-5); margin:0 0 var(--sp-3); }
article li{ margin:2px 0; }
.dv-cats{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:var(--sp-5) var(--sp-6); max-width:none; margin-top:var(--sp-5); }
.dv-cats h2{ border:0; margin:0 0 var(--sp-2); padding:0; font-size:var(--fs-body); display:flex; gap:var(--sp-2); align-items:baseline; }
.dv-cats h2 .n{ font-family:var(--mono); font-size:var(--fs-label); color:var(--tx3); font-weight:400; }
.dv-cats ul{ list-style:none; padding:0; margin:0; font-size:var(--fs-body); }
.dv-cats li{ border-top:1px solid var(--line); margin:0; }
.dv-cats li a{ display:block; padding:5px 0; color:var(--tx); text-decoration:none; }
.dv-cats li a:hover{ color:var(--accent); }
@media (max-width:1280px){
  .dv{ grid-template-columns:260px minmax(0,1fr); }
  .dv-toc{ display:none; }
  .dv-toc-inline{ display:block; }
}
@media (max-width:760px){
  .dv{ grid-template-columns:minmax(0,1fr); }
  .dv-nav{ position:static; height:auto; max-height:45vh; border-right:0; border-bottom:1px solid var(--line); }
  .dv-main{ padding:var(--sp-4); }
  .dv-cats{ grid-template-columns:minmax(0,1fr); }
  article{ font-size:var(--fs-body); }
}
"""

#: English category label (data-i18n key) per folder; FR lives in the tools
#: catalog (smo_common/ui/i18n/tools/fr.json).
CATEGORY_LABELS = {"_root": "Overview", "manual": "Manual", "mcs": "MCS",
                   "procedures": "Procedures"}


#: Attribute for the folder-driven category names. Spelt through a constant
#: so the catalog scanner does not read the f-string placeholder as a key;
#: the names themselves are kept by the `keep:` rule of the tools catalog
#: in i18n.yaml.
_DYN_I18N = "data-i18n"


def _cat_label(cat: str) -> str:
    return CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())


def _q(lang: str) -> str:
    return "?lang=fr" if lang == "fr" else ""


def _sidebar(categories: dict[str, list[dict]], lang: str, current: str | None) -> str:
    out = ['<div class="ds-field"><label for="search" data-i18n>Filter documents</label>',
           '<input class="ds-input text" type="search" id="search" autocomplete="off"></div>']
    # Course PDFs (smo_common/downloads.yaml, student list): one page.
    cur_dl = ' aria-current="page"' if current == "/downloads" else ""
    out.append('<h2 data-i18n>Downloads</h2>')
    out.append(f'<a href="/downloads{_q(lang)}" class="doc-link"{cur_dl} data-title="pdf" '
               f'data-i18n>Course PDFs</a>')
    cat_order = sorted(categories.keys(), key=lambda c: (c == '_root', c))
    for cat in cat_order:
        out.append(f'<h2 {_DYN_I18N}>{html.escape(_cat_label(cat))}</h2>')
        for doc in categories[cat]:
            title = doc["fr_title"] if lang == "fr" and doc.get("fr_title") else doc["title"]
            cls = "doc-link" + (" en-only" if lang == "fr" and not doc.get("fr_title") else "")
            cur = ' aria-current="page"' if doc["path"] == current else ""
            out.append(
                f'<a href="/doc/{html.escape(doc["path"])}{_q(lang)}" class="{cls}"{cur} '
                f'data-title="{html.escape(title.lower())}">{html.escape(title)}</a>')
    out.append('<p class="none" id="none" data-i18n>No document matches.</p>')
    return "\n".join(out)


#: Filter, the language switch (the server picks the document language, so a
#: language change reloads with ?lang=) and the contents highlight.
_PAGE_JS = """<script type="module">
const q = document.getElementById("search");
if (q) q.addEventListener("input", () => {
  const v = q.value.trim().toLowerCase();
  let shown = 0;
  document.querySelectorAll(".doc-link").forEach((a) => {
    const on = a.dataset.title.includes(v); a.style.display = on ? "" : "none"; if (on) shown++;
  });
  document.querySelectorAll(".dv-nav h2").forEach((h) => {
    let n = h.nextElementSibling, any = false;
    while (n && n.tagName === "A") { if (n.style.display !== "none") any = true; n = n.nextElementSibling; }
    h.style.display = any ? "" : "none";
  });
  document.getElementById("none").style.display = shown ? "" : "block";
});
window.addEventListener("smo:langchange", (e) => {
  const u = new URL(location.href);
  if (u.searchParams.get("lang") !== e.detail.lang) { u.searchParams.set("lang", e.detail.lang); location.replace(u); }
});
const cur = document.querySelector('.doc-link[aria-current]');
if (cur) cur.scrollIntoView({ block: "center" });
const links = [...document.querySelectorAll(".dv-toc a")];
const heads = links.map((a) => document.getElementById(decodeURIComponent(a.hash.slice(1)))).filter(Boolean);
if (heads.length && "IntersectionObserver" in window) {
  const seen = new Map();
  const io = new IntersectionObserver((es) => {
    es.forEach((e) => seen.set(e.target.id, e.isIntersecting));
    const first = heads.find((h) => seen.get(h.id)) ;
    if (!first) return;
    links.forEach((a) => a.setAttribute("aria-current", String(a.hash.slice(1) === first.id)));
  }, { rootMargin: "-56px 0px -70% 0px" });
  heads.forEach((h) => io.observe(h));
}
</script>"""


def _page(title: str, lang: str, sidebar: str, content: str, toc: str = "",
          meta: str = "") -> str:
    import tool_frame
    bar = tool_frame.bar('<span data-i18n>Documentation</span>', meta_html=meta, logbook="docs")
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{html.escape(title)}</title>
{tool_frame.head(extra_css=PAGE_CSS)}
</head><body data-server-lang="{lang}">
<a class="ds-skip" href="#content" data-i18n>Skip to content</a>
{bar}
<div class="dv">
<nav class="dv-nav" aria-label="Documents" data-i18n-aria-label>
{sidebar}
</nav>
<main id="content" class="dv-main">
{content}
</main>
{toc}
</div>
{tool_frame.SCRIPT}
{_PAGE_JS}
</body></html>"""


def build_index_html(categories: dict[str, list[dict]], lang: str = "en") -> str:
    cols = []
    for cat, docs in sorted(categories.items(), key=lambda kv: (kv[0] == '_root', kv[0])):
        items = "".join(
            f'<li><a href="/doc/{html.escape(d["path"])}{_q(lang)}">'
            f'{html.escape(d["fr_title"] if lang == "fr" and d.get("fr_title") else d["title"])}</a></li>'
            for d in docs)
        cols.append(f'<section><h2><span {_DYN_I18N}>{html.escape(_cat_label(cat))}</span>'
                    f'<span class="n">{len(docs)}</span></h2><ul>{items}</ul></section>')
    content = ('<article>'
               '<h1 data-i18n>EOSAT-1 mission documentation</h1>\n'
               '<p data-i18n="Choose a document from the list. Documents open in the interface language when a translation exists.">'
               'Choose a document from the list. Documents open in the interface '
               'language when a translation exists.</p></article>\n'
               f'<div class="dv-cats">{"".join(cols)}</div>')
    n = sum(len(d) for d in categories.values())
    return _page("EOSAT-1 documentation", lang, _sidebar(categories, lang, None), content,
                 meta=f'<span class="num">{n}</span> <span data-i18n>documents</span>')


_HEAD_RE = re.compile(r'<h([23]) id="([^"]+)">(.*?)</h\1>')


def _toc(body_html: str) -> tuple[str, str]:
    """(sticky contents column, inline disclosure for narrow screens)."""
    items = [(int(m.group(1)), m.group(2), re.sub(r"<[^>]+>", "", m.group(3)))
             for m in _HEAD_RE.finditer(body_html)]
    if len(items) < 2:
        return "", ""
    lis = "".join(f'<li><a class="l{lv}" href="#{html.escape(i)}">{t}</a></li>' for lv, i, t in items)
    side = (f'<nav class="dv-toc" aria-labelledby="toc-h"><h2 id="toc-h" data-i18n>On this page</h2>'
            f'<ol>{lis}</ol></nav>')
    inline = (f'<details class="ds-disclosure dv-toc-inline"><summary data-i18n>On this page</summary>'
              f'<div class="bd dv-toc" style="position:static;display:block;padding:0 0 var(--sp-2)"><ol>{lis}</ol></div></details>')
    return side, inline


#: A procedure card in the documentation viewer is a working copy too
#: (smo_common/ui/procard.js, 2026-11-03): its steps and prerequisites are
#: recorded into the participant's logbook, the same records the MCS card
#: and the Workbook tab write. No live telemetry here, so no capture: the
#: values are captured in the MCS. ### renders as <h3> and ## as <h2>.
_CARD_JS = """<script type="module">
import { mountProcCard } from "/static/shared/procard.js";
const art = document.querySelector("article[data-procedure]");
window.c2oLogbookContext = () => ({ doc: art.dataset.doc, procedure: art.dataset.procedure });
function go() {
  if (window.C2O_LOGBOOK) mountProcCard(art, { procedure: art.dataset.procedure, lb: window.C2O_LOGBOOK,
    levels: { step: "H3", section: "H2" }, live: false });
}
if (window.C2O_LOGBOOK) go(); else window.addEventListener("c2o:frameready", go, { once: true });
</script>"""


def build_doc_html(title: str, body_html: str, breadcrumb: str,
                   categories: dict[str, list[dict]], lang: str = "en",
                   rel_path: str | None = None, served_lang: str | None = None,
                   procedure: str | None = None) -> str:
    served_lang = served_lang or lang
    bar = f'<div class="docbar"><span>{breadcrumb}</span>'
    if rel_path:
        other = "en" if served_lang == "fr" else "fr"
        has_other = other == "en" or any(
            d["path"] == rel_path and d.get("fr_title")
            for docs in categories.values() for d in docs)
        if has_other:
            label = "English original" if other == "en" else "Version française"
            bar += (f'<a href="/doc/{html.escape(rel_path)}?lang={other}" '
                    f'hreflang="{other}" lang="{other}">{label}</a>')
    bar += '</div>'
    note = ""
    if lang == "fr" and served_lang == "en":
        note = ('<p class="note-lang" data-i18n="No French translation of this document yet; showing the English original.">'
                'No French translation of this document yet; showing the English original.</p>')
    side, inline = _toc(body_html)
    card = (f' data-procedure="{html.escape(procedure)}" data-doc="{html.escape(rel_path or "")}"'
            if procedure else "")
    content = (f'{bar}\n{note}\n{inline}\n<article lang="{served_lang}"{card}>\n{body_html}\n</article>'
               + (_CARD_JS if procedure else ""))
    meta = f'<code>{html.escape(rel_path)}</code>' if rel_path else ""
    return _page(f"{title} — EOSAT-1", lang, _sidebar(categories, lang, rel_path), content,
                 toc=side, meta=meta)


def build_downloads_html(categories: dict[str, list[dict]], lang: str = "en") -> str:
    """The course-PDF page: drawn in the browser by the shared
    /static/shared/downloads.js from GET /api/downloads (student list)."""
    content = ('<div class="docbar"><span><a href="/' + _q(lang) + '" data-i18n>Home</a></span></div>'
               '<article><h1 data-i18n>Course PDFs</h1>\n'
               '<p data-i18n="Textbooks, workbooks and references for the course, in English and French. Open a PDF in a new tab or download it.">'
               'Textbooks, workbooks and references for the course, in English and '
               'French. Open a PDF in a new tab or download it.</p></article>\n'
               '<div id="dl-list" style="max-width:920px"></div>\n'
               '<script type="module">import { mountDownloads } from "/static/shared/downloads.js";\n'
               'mountDownloads(document.getElementById("dl-list"));</script>')
    return _page("Course PDFs — EOSAT-1", lang, _sidebar(categories, lang, "/downloads"), content)


# ── aiohttp server ────────────────────────────────────────────────────

def _procedure_cards(docs_root: Path):
    """({card file -> procedure id}, checklist provider factory | None) from
    ``procedures/procedure_index.yaml`` under *docs_root*: the logbook's
    ``/api/logbook/checklist`` for the cards shown here."""
    idx_path = docs_root / "procedures" / "procedure_index.yaml"
    if not idx_path.is_file():
        return {}, None
    import yaml
    from smo_common.logbook.checklist import ChecklistProvider
    index = (yaml.safe_load(idx_path.read_text(encoding="utf-8")) or {}).get("procedures") or []
    ids = {e["file"]: e["id"] for e in index if e.get("file") and e.get("id")}

    def factory(catalog):
        return ChecklistProvider(index, docs_root / "procedures",
                                 docs_root / "i18n" / "fr" / "procedures", catalog.sheets)
    factory.wants_catalog = True
    return ids, factory


def create_app(docs_root: Path) -> web.Application:
    from smo_common.web.http import setup_tool_app, tool_html_response
    categories = discover_docs(docs_root)
    app = setup_tool_app(web.Application())
    from smo_common.logbook import register_logbook_routes   # participant logbook
    proc_ids, checklists = _procedure_cards(docs_root)
    register_logbook_routes(app, tool="docs", checklists=checklists)

    async def index(request):
        return tool_html_response(build_index_html(categories, request_lang(request)), app)

    async def doc_handler(request):
        rel_path = request.match_info['path']
        lang = request_lang(request)
        full_path, served = resolve_doc(docs_root, rel_path, lang)
        if full_path is None:
            raise web.HTTPNotFound(text=f"Document not found: {rel_path}")
        md_text = full_path.read_text(encoding='utf-8')
        title = _extract_title(full_path)
        body = md_to_html(md_text)
        parts = rel_path.split('/')
        breadcrumb = f'<a href="/{_q(lang)}" data-i18n>Home</a>'
        if len(parts) > 1:
            breadcrumb += (f' / <a href="/{_q(lang)}" {_DYN_I18N}>'
                           f'{html.escape(_cat_label(parts[0]))}</a>')
        proc = proc_ids.get(rel_path[len("procedures/"):]) if rel_path.startswith("procedures/") else None
        return tool_html_response(
            build_doc_html(title, body, breadcrumb, categories, lang,
                           rel_path=rel_path, served_lang=served, procedure=proc), app)

    async def downloads_page(request):
        return tool_html_response(build_downloads_html(categories, request_lang(request)), app)

    app.router.add_get('/', index)
    app.router.add_get('/doc/{path:.+}', doc_handler)
    # Course PDFs: student audience only (docs.c2o.live is student-visible).
    from smo_common.downloads import register_download_routes
    app.router.add_get('/downloads', downloads_page)
    register_download_routes(app, audience="student")
    return app


def main():
    parser = argparse.ArgumentParser(description='EOSAT-1 Documentation Viewer')
    parser.add_argument('--port', type=int, default=8095,
                        help='HTTP port (default: 8095)')
    parser.add_argument('--docs', type=str, default=None,
                        help='Documentation root directory')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [doc_viewer] %(message)s')

    docs_root = Path(args.docs) if args.docs else DEFAULT_DOCS
    if not docs_root.exists():
        print(f"ERROR: docs directory not found: {docs_root}")
        raise SystemExit(1)

    app = create_app(docs_root)
    logger.info("Documentation viewer: http://localhost:%d", args.port)
    web.run_app(app, host='0.0.0.0', port=args.port, print=None)


if __name__ == '__main__':
    main()
