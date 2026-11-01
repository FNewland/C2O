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

    for line in lines:
        # Fenced code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                out.append('</code></pre>')
                in_code_block = False
            else:
                lang = line.strip()[3:].strip()
                cls = f' class="lang-{html.escape(lang)}"' if lang else ''
                out.append(f'<pre><code{cls}>')
                in_code_block = True
            continue
        if in_code_block:
            out.append(html.escape(line))
            continue

        # Close open list if non-list line
        stripped = line.strip()
        is_list_item = bool(re.match(r'^[-*+] ', stripped) or re.match(r'^\d+\. ', stripped))
        if in_list and not is_list_item and stripped:
            out.append(f'</{list_type}>')
            in_list = False

        # Close table
        if in_table and not stripped.startswith('|'):
            out.append('</tbody></table>')
            in_table = False

        # Empty line
        if not stripped:
            if not in_list and not in_table:
                out.append('<br>')
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
                out.append('<table><thead><tr>')
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

        # Paragraph
        out.append(f'<p>{_inline(line)}</p>')

    # Close open blocks
    if in_code_block:
        out.append('</code></pre>')
    if in_table:
        out.append('</tbody></table>')
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
body { font-size:15px; line-height:1.6; display:flex; height:100vh; }
#sidebar { width:300px; min-width:300px; background:var(--s1);
  border-right:1px solid var(--line); overflow-y:auto; padding:12px 12px 24px; }
#sidebar .home { display:block; color:var(--tx); font-weight:600; font-size:15px;
  text-decoration:none; padding:4px 8px 10px; }
#sidebar h2 { color:var(--tx3); font-size:12px; font-weight:600; text-transform:uppercase;
  letter-spacing:1px; margin:16px 8px 4px; }
#sidebar a.doc-link { display:block; padding:3px 8px; color:var(--tx2); text-decoration:none;
  font-size:13px; border-radius:3px; }
#sidebar a.doc-link:hover, #sidebar a.doc-link[aria-current] { background:var(--s3); color:var(--tx); }
#sidebar a.doc-link.en-only::after { content:" EN"; font-family:var(--mono); font-size:12px;
  color:var(--tx3); }
#sidebar label { display:block; font-size:12px; color:var(--tx3); margin:0 8px 4px; }
#sidebar input { width:100%; padding:6px 8px; background:var(--s2); border:1px solid var(--line-2);
  border-radius:3px; color:var(--tx); font:inherit; font-size:13px; margin-bottom:4px; }
#content { flex:1; overflow-y:auto; padding:24px 40px 64px; }
#content > * { max-width:820px; }
#content h1 { font-size:24px; line-height:1.25; border-bottom:1px solid var(--line);
  padding-bottom:8px; margin-bottom:16px; color:var(--val); }
#content h2 { font-size:19px; margin-top:28px; border-bottom:1px solid var(--line); padding-bottom:4px; }
#content h3 { font-size:16px; margin-top:20px; }
#content p { margin:8px 0; }
#content a { color:var(--info); }
#content code { font-family:var(--mono); background:var(--s2); padding:1px 5px; border-radius:3px; font-size:13px; }
#content pre { background:var(--s1); border:1px solid var(--line); padding:12px; border-radius:3px;
  overflow-x:auto; margin:12px 0; }
#content pre code { padding:0; background:none; }
#content table { border-collapse:collapse; margin:12px 0; width:100%; font-size:14px; }
#content th, #content td { border:1px solid var(--line); padding:6px 10px; text-align:left; vertical-align:top; }
#content th { background:var(--s1); color:var(--tx2); font-weight:600; }
#content blockquote { border-left:3px solid var(--line-2); padding-left:12px; color:var(--tx2); margin:8px 0; }
#content hr { border:none; border-top:1px solid var(--line); margin:16px 0; }
#content img { max-width:100%; }
#content ul, #content ol { padding-left:24px; margin:8px 0; }
#content li { margin:2px 0; }
.docbar { display:flex; gap:16px; align-items:baseline; justify-content:space-between;
  font-size:13px; color:var(--tx3); margin-bottom:12px; }
.docbar a { color:var(--info); text-decoration:none; }
.note-lang { font-size:13px; color:var(--tx2); border:1px solid var(--line-2); border-radius:3px;
  padding:6px 10px; margin-bottom:16px; }
.cats { list-style:none; padding:0 !important; }
.cats li { display:flex; gap:12px; padding:4px 0; border-bottom:1px solid var(--line); }
.cats .n { font-family:var(--mono); color:var(--tx3); margin-left:auto; }
@media (max-width: 760px) {
  body { flex-direction:column; height:auto; }
  #sidebar { width:auto; min-width:0; max-height:40vh; border-right:none;
    border-bottom:1px solid var(--line); }
  #content { padding:16px; }
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
    out = ['<a class="home" href="/' + _q(lang) + '" data-i18n>EOSAT-1 documentation</a>',
           '<label for="search" data-i18n>Filter documents</label>',
           '<input type="search" id="search" oninput="filterDocs()">']
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
    return "\n".join(out)


_FILTER_JS = """<script>
function filterDocs() {
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.doc-link').forEach(a => {
    a.style.display = a.dataset.title.includes(q) ? '' : 'none';
  });
}
</script>"""


def _page(title: str, lang: str, sidebar: str, content: str) -> str:
    from smo_common.web.http import TOOL_HEAD
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{html.escape(title)}</title>
{TOOL_HEAD}<style>{PAGE_CSS}</style>
</head><body data-server-lang="{lang}">
<nav id="sidebar" aria-label="Documents" data-i18n-aria-label>
{sidebar}
</nav>
<main id="content">
{content}
</main>
{_FILTER_JS}
</body></html>"""


def build_index_html(categories: dict[str, list[dict]], lang: str = "en") -> str:
    rows = "".join(
        f'<li><span {_DYN_I18N}>{html.escape(_cat_label(cat))}</span>'
        f'<span class="n">{len(docs)}</span></li>'
        for cat, docs in sorted(categories.items(), key=lambda kv: (kv[0] == '_root', kv[0])))
    content = ('<h1 data-i18n>EOSAT-1 mission documentation</h1>\n'
               '<p data-i18n="Choose a document from the list. Documents open in the interface language when a translation exists.">'
               'Choose a document from the list. Documents open in the interface '
               'language when a translation exists.</p>\n'
               f'<ul class="cats">{rows}</ul>')
    return _page("EOSAT-1 documentation", lang, _sidebar(categories, lang, None), content)


def build_doc_html(title: str, body_html: str, breadcrumb: str,
                   categories: dict[str, list[dict]], lang: str = "en",
                   rel_path: str | None = None, served_lang: str | None = None) -> str:
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
    content = f'{bar}\n{note}\n<article lang="{served_lang}">\n{body_html}\n</article>'
    return _page(f"{title} — EOSAT-1", lang, _sidebar(categories, lang, rel_path), content)


# ── aiohttp server ────────────────────────────────────────────────────

def create_app(docs_root: Path) -> web.Application:
    from smo_common.web.http import setup_tool_app, tool_html_response
    categories = discover_docs(docs_root)
    app = setup_tool_app(web.Application())

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
        return tool_html_response(
            build_doc_html(title, body, breadcrumb, categories, lang,
                           rel_path=rel_path, served_lang=served), app)

    app.router.add_get('/', index)
    app.router.add_get('/doc/{path:.+}', doc_handler)
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
