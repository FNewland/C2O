"""Explicit heading anchors `{#id}` in the manual viewers (author ruling Q33).

The EN and FR manuals and the PUS reference carry pandoc attribute blocks at
the end of heading lines (`## Link budget {#ttc-link-budget}`), with the same
id in both languages. Every viewer must use the id as the heading's HTML id,
must never display the `{#id}` text, and must make in-document `[text](#id)`
links reach the heading:

* the modern MCS console (static/modern/mcs.js `renderMarkdown`),
* the classic fallback MCS console (static/index.html `renderMarkdown`),
* the MCS server's `{title, content_md}` envelope (title has no block),
* the standalone doc viewer (tools/doc_viewer.py).
"""
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MCS_STATIC = REPO / "packages" / "smo-mcs" / "src" / "smo_mcs" / "static"
MODERN_HARNESS = Path(__file__).resolve().parent / "js" / "modern_harness.js"
CLASSIC_HARNESS = Path(__file__).resolve().parent / "js" / "mcs_harness.js"
CLASSIC = MCS_STATIC / "index.html"

NODE = shutil.which("node") or shutil.which("nodejs")
requires_node = pytest.mark.skipif(NODE is None, reason="node required")

MD = (
    "# EOSAT-1 TT&C {#ttc}\n\n"
    "See [the budget](#ttc-link-budget) below.\n\n"
    "## Link budget {#ttc-link-budget}\n\n"
    "### Plain heading\n\n"
    "### Classed heading {#ttc-fdir .unnumbered}\n"
)


def _run(harness: Path, first_arg: Path, snippet: str, tmp_path: Path):
    f = tmp_path / "snippet.js"
    f.write_text(snippet, encoding="utf-8")
    proc = subprocess.run([NODE, str(harness), str(first_arg), str(f)],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout)


@requires_node
class TestModernViewer:
    def test_heading_ids_used_and_blocks_hidden(self, tmp_path):
        out = _run(MODERN_HARNESS, REPO,
                   f"return T.renderMarkdown({json.dumps(MD)});", tmp_path)
        assert "{#" not in out
        assert '<h2 id="ttc">EOSAT-1 TT&amp;C</h2>' in out
        assert '<h3 id="ttc-link-budget">Link budget</h3>' in out
        assert '<h4 id="ttc-fdir">Classed heading</h4>' in out
        assert "<h4>Plain heading</h4>" in out

    def test_in_document_link_becomes_an_anchor(self, tmp_path):
        out = _run(MODERN_HARNESS, REPO,
                   f"return T.renderMarkdown({json.dumps(MD)});", tmp_path)
        assert ('<a href="#ttc-link-budget" data-man-anchor="ttc-link-budget">'
                'the budget</a>') in out

    def test_anchor_click_scrolls_to_the_heading_in_its_document(self, tmp_path):
        out = _run(MODERN_HARNESS, REPO, """
            let scrolled = null, asked = null;
            const heading = { scrollIntoView(o) { scrolled = o; } };
            const host = { querySelector(sel) { asked = sel;
                             return sel === '[id="ttc-fdir"]' ? heading : null; } };
            const link = { closest(sel) { return host; } };
            const hit = T.scrollToManualAnchor(link, "ttc-fdir") === heading;
            const miss = T.scrollToManualAnchor(link, "nope");
            return { hit, miss, asked, scrolled };
        """, tmp_path)
        assert out["hit"] is True
        assert out["miss"] is None
        assert out["scrolled"] == {"block": "start"}

    def test_delegated_click_handler_routes_anchor_links(self):
        src = (MCS_STATIC / "modern" / "mcs.js").read_text(encoding="utf-8")
        assert "[data-man-anchor]" in src
        assert "d.manAnchor" in src


@requires_node
class TestClassicViewer:
    def test_heading_ids_used_blocks_hidden_links_rendered(self, tmp_path):
        out = _run(CLASSIC_HARNESS, CLASSIC,
                   f"return renderMarkdown({json.dumps(MD)});", tmp_path)
        assert "{#" not in out
        assert '<h1 id="ttc">EOSAT-1 TT&amp;C</h1>' in out
        assert '<h2 id="ttc-link-budget">Link budget</h2>' in out
        assert '<h3 id="ttc-fdir">Classed heading</h3>' in out
        assert "<h3>Plain heading</h3>" in out
        assert 'href="#ttc-link-budget"' in out
        assert "manualAnchor(this, 'ttc-link-budget')" in out


def test_server_title_drops_the_anchor_block(tmp_path):
    """The MCS envelope's title comes from the first line of the file."""
    import re
    server = (REPO / "packages" / "smo-mcs" / "src" / "smo_mcs"
              / "server.py").read_text(encoding="utf-8")
    m = re.search(r'title = re\.sub\(r"(.+?)", "", title\)', server)
    assert m, "title anchor strip missing from _md_doc_response"
    pat = m.group(1)
    assert re.sub(pat, "", "EOSAT-1 TT&C {#ttc}") == "EOSAT-1 TT&C"
    assert re.sub(pat, "", "Plain title") == "Plain title"


def _doc_viewer():
    spec = importlib.util.spec_from_file_location(
        "doc_viewer", REPO / "tools" / "doc_viewer.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDocViewer:
    def test_heading_ids_used_and_blocks_hidden(self):
        dv = _doc_viewer()
        out = dv.md_to_html(MD)
        assert "{#" not in out
        assert '<h1 id="ttc">' in out
        assert '<h2 id="ttc-link-budget">Link budget</h2>' in out
        assert '<h3 id="ttc-fdir">Classed heading</h3>' in out
        # headings without a block keep the generated slug
        assert '<h3 id="plain-heading">Plain heading</h3>' in out
        assert '<a href="#ttc-link-budget">the budget</a>' in out

    def test_title_drops_the_anchor_block(self, tmp_path):
        dv = _doc_viewer()
        f = tmp_path / "x.md"
        f.write_text("# Telemetry & Telecommand {#ttc}\n", encoding="utf-8")
        assert dv._extract_title(f) == "Telemetry & Telecommand"

    def test_split_heading_anchor(self):
        dv = _doc_viewer()
        assert dv.split_heading_anchor("A {#a-1}") == ("A", "a-1")
        assert dv.split_heading_anchor("A {#a .cls}") == ("A", "a")
        assert dv.split_heading_anchor("No anchor") == ("No anchor", None)
