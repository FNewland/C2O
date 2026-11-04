"""Link safety for "where to find this" and the documentation viewer
(worksheet screen audit, 2026-11-04).

* where.js (the logbook's Workbook tab): only https becomes an open-reference
  link, and it opens in a new window with rel="noopener noreferrer"; links to
  C2O tools resolve to the tool's own address (cloud host label or local
  port), the MCS deep link carries only validated values, a docs path cannot
  climb out of the documentation tree. Pinned under node.
* doc_viewer.py: relative links stay, https opens a new window, every other
  scheme (javascript:, data:, http:, file:, //host) keeps its text only.
* the MCS reads the deep link (#page=…) with strict patterns.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SIM = Path(__file__).resolve().parents[2]
UI = SIM / "packages" / "smo-common" / "src" / "smo_common" / "ui"
MCS_JS = SIM / "packages" / "smo-mcs" / "src" / "smo_mcs" / "static" / "modern" / "mcs.js"
NODE = shutil.which("node") or shutil.which("nodejs")
needs_node = pytest.mark.skipif(not NODE, reason="node not installed")
_SHARED = re.compile(r"""(["'])/static/shared/([\w.-]+)\.js(\?[^"']*)?\1""")

if str(SIM / "tools") not in sys.path:
    sys.path.insert(0, str(SIM / "tools"))

PRELUDE = """
globalThis.window = globalThis;
globalThis.document = { documentElement: { lang: "en", setAttribute() {}, getAttribute() { return null; } },
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
  createElement: () => ({ style: {}, setAttribute() {}, appendChild() {} }),
  head: { appendChild() {} }, body: { appendChild() {} } };
globalThis.localStorage = { getItem: () => null, setItem() {} };
"""


def run(snippet: str, tmp_path: Path):
    for f in UI.glob("*.js"):
        src = _SHARED.sub(r'"./\2.mjs"', f.read_text(encoding="utf-8"))
        (tmp_path / (f.stem + ".mjs")).write_text(src, encoding="utf-8")
    (tmp_path / "run.mjs").write_text(
        PRELUDE + 'const W = await import("./where.mjs");\n'
        "const out = await (async () => { " + snippet + " })();\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    p = subprocess.run([NODE, str(tmp_path / "run.mjs")], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout.strip().splitlines()[-1])


LOCAL = '{hostname: "10.0.0.5", protocol: "http:"}'
CLOUD = '{hostname: "orbit.c2o.live", protocol: "https:"}'


@needs_node
def test_open_references_https_only_new_window(tmp_path):
    out = run(f"""
      const L = {LOCAL};
      return [
        W.whereLink({{tool: "ext", url: "https://ecss.nl/x"}}, "mcs", L),
        W.whereLink({{tool: "ext", url: "javascript:alert(1)"}}, "mcs", L),
        W.whereLink({{tool: "ext", url: "http://example.org"}}, "mcs", L),
        W.whereLink({{tool: "ext", url: "https://a.b/\\"onclick=x"}}, "mcs", L),
        W.whereLink({{tool: "ext", url: "data:text/html,1"}}, "mcs", L),
      ];""", tmp_path)
    assert out[0] == {"href": "https://ecss.nl/x", "target": "_blank", "rel": "noopener noreferrer", "ext": True}
    assert out[1:] == [None, None, None, None]


@needs_node
def test_tool_addresses_local_and_cloud(tmp_path):
    out = run(f"""
      return [
        W.toolBase("mcs", {LOCAL}), W.toolBase("docs", {LOCAL}),
        W.toolBase("mcs", {CLOUD}), W.toolBase("planner", {CLOUD}),
        W.toolBase("mcs", {{hostname: "evil.example.com", protocol: "https:"}}),
        W.toolBase("nope", {LOCAL}),
      ];""", tmp_path)
    assert out == ["http://10.0.0.5:9090", "http://10.0.0.5:8095",
                   "https://ops.c2o.live", "https://plan.c2o.live",
                   "https://evil.example.com:9090", ""]


@needs_node
def test_mcs_deep_link_and_same_tool(tmp_path):
    out = run(f"""
      const L = {LOCAL};
      return [
        W.whereLink({{tool: "mcs", page: "eps", param: "0x0101"}}, "orbit", L),
        W.whereLink({{tool: "mcs", page: "diag", tab: "s9", focus: "s9-dt"}}, "mcs", L),
        W.whereLink({{tool: "mcs", page: "eps", focus: "x\\" onmouseover=\\"y"}}, "mcs", L),
        W.whereLink({{tool: "mcs", page: "eps", param: "0x01011"}}, "mcs", L),
        W.whereLink({{tool: "orbit", focus: "eclipses"}}, "orbit", L),
        W.whereLink({{tool: "planner", focus: "panel-contacts"}}, "mcs", L),
      ];""", tmp_path)
    assert out[0] == {"href": "http://10.0.0.5:9090/#page=eps&param=0x0101", "target": "c2o-mcs"}
    assert out[1] == {"href": "#page=diag&tab=s9&focus=s9-dt", "same": True}
    assert out[2] == {"href": "#page=eps", "same": True}          # bad focus dropped
    assert out[3] == {"href": "#page=eps", "same": True}          # bad param dropped
    assert out[4] == {"href": "#eclipses", "same": True}
    assert out[5] == {"href": "http://10.0.0.5:9091/#panel-contacts", "target": "c2o-planner"}


@needs_node
def test_docs_paths_stay_in_the_tree(tmp_path):
    out = run(f"""
      const L = {LOCAL};
      return [
        W.whereLink({{tool: "docs", path: "manual/05_ttc.md", anchor: "24-the-tm-data-rate-ladder"}}, "mcs", L),
        W.whereLink({{tool: "docs", path: "../../etc/passwd.md"}}, "mcs", L),
        W.whereLink({{tool: "docs", path: "manual//x.md"}}, "mcs", L),
        W.whereLink({{tool: "docs", path: "manual/x.md", anchor: "a\\"b"}}, "docs", L),
      ];""", tmp_path)
    assert out[0] == {"href": "http://10.0.0.5:8095/doc/manual/05_ttc.md#24-the-tm-data-rate-ladder",
                      "target": "c2o-docs"}
    assert out[1] is None and out[2] is None
    assert out[3] == {"href": "/doc/manual/x.md", "same": True}


@needs_node
def test_where_html_escapes_and_marks_new_window(tmp_path):
    out = run(f"""
      return W.whereHtml([
        {{tool: "ext", url: "https://ecss.nl/x", label: "<b>ECSS</b>"}},
        {{tool: "mcs", page: "eps", label: "MCS › EPS"}},
        {{tool: "ext", url: "javascript:1", label: "bad"}},
      ], "mcs");""", tmp_path)
    assert 'target="_blank"' in out and 'rel="noopener noreferrer"' in out
    assert "&lt;b&gt;ECSS&lt;/b&gt;" in out and "<b>ECSS" not in out
    assert 'href="#page=eps"' in out and 'data-where-same="1"' in out
    assert "bad" not in out and "javascript" not in out
    assert out.startswith('<div class="wb-where">')
    assert run('return W.whereHtml([], "mcs");', tmp_path) == ""


def test_doc_viewer_link_schemes():
    import doc_viewer as dv
    ext = dv._inline("[ECSS](https://ecss.nl/a?b=1&c=2)")
    assert 'href="https://ecss.nl/a?b=1&amp;c=2"' in ext
    assert 'target="_blank"' in ext and 'rel="noopener noreferrer"' in ext
    assert dv._inline("[doc](../manual/05_ttc.md#x)") == '<a href="../manual/05_ttc.md#x">doc</a>'
    for bad in ("javascript:alert(1)", "JavaScript:alert(1)", "java\tscript:alert(1)",
                "data:text/html,1", "http://example.org", "file:///etc/passwd",
                "//evil.example.org/x", "vbscript:x"):
        out = dv._inline(f"[t]({bad})")
        assert "<a " not in out and "href" not in out, (bad, out)
    assert "<img" not in dv._inline("![x](javascript:alert(1))")
    assert '<img src="https://e.org/a.png"' in dv._inline("![x](https://e.org/a.png)")
    assert dv.link_target("https://e.org") == ("ext", "https://e.org")
    assert dv.link_target("05_ttc.md") == ("int", "05_ttc.md")
    assert dv.link_target(" javascript:x")[0] is None


def test_mcs_deep_link_is_validated():
    js = MCS_JS.read_text(encoding="utf-8")
    assert "export function applyNavHash()" in js
    assert 'window.addEventListener("hashchange", applyNavHash)' in js
    body = js.split("export function applyNavHash()", 1)[1].split("\nfunction ", 1)[0]
    # every value reaches a selector only through a strict pattern
    assert "NAV_PARAM.test(param)" in body and "NAV_ID.test(focus)" in body
    assert "BD_TABS.includes(bd)" in body and 'RAIL.some(([id]) => id === page' in body
    assert re.search(r"const NAV_ID = /\^\[A-Za-z\]\[\\w-\]\{0,63\}\$/;", js)
    assert re.search(r"const NAV_PARAM = /\^0x\[0-9A-Fa-f\]\{4\}\$/;", js)
