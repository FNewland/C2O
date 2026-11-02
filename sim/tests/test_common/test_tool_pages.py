"""The sim/tools web pages (R3 audit A9 and §8, 2026-11 quick wins).

Pins:
  - the doc viewer picks the document language from ?lang= (the client
    adds it from the shared c2o.lang setting), falls back to English with a
    note, never lists the i18n/ tree as a category, and refuses paths
    outside the docs root;
  - the delayed-TM viewer never sends the absolute server path to the page;
  - every tool page loads the shared design system and language runtime,
    declares <html lang>, and every string it marks for translation has a
    French entry in smo_common/ui/i18n/tools/fr.json.
"""
from __future__ import annotations

import html as _html
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools"
CATALOG = (REPO / "packages/smo-common/src/smo_common/ui/i18n/tools/fr.json")
TOOL_FILES = ["doc_viewer.py", "delayed_tm_viewer.py", "orbit_tools.py",
              "scenario_generator.py", "adcs_sim_viewer.py"]
#: The page frame every tool shares (title bar, theme + language switches);
#: it emits TOOL_HEAD (shared design system + language runtime).
FRAME = "tool_frame.py"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"_tp_{name}", TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _docs(tmp_path: Path) -> Path:
    root = tmp_path / "docs"
    (root / "manual").mkdir(parents=True)
    (root / "manual" / "a.md").write_text("# Power {#eps}\nEnglish body\n", encoding="utf-8")
    (root / "manual" / "b.md").write_text("# Thermal\nEnglish only\n", encoding="utf-8")
    (root / "i18n" / "fr" / "manual").mkdir(parents=True)
    (root / "i18n" / "fr" / "manual" / "a.md").write_text(
        "# Puissance {#eps}\nCorps français\n", encoding="utf-8")
    (tmp_path / "secret.md").write_text("# Secret\n", encoding="utf-8")
    return root


async def _client(app):
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


def test_doc_discovery_hides_i18n_and_records_translations(tmp_path):
    dv = _load("doc_viewer")
    cats = dv.discover_docs(_docs(tmp_path))
    assert set(cats) == {"manual"}
    by = {d["path"]: d for d in cats["manual"]}
    assert by["manual/a.md"]["fr_title"] == "Puissance"
    assert by["manual/b.md"]["fr_title"] is None


async def test_doc_viewer_serves_the_ui_language(tmp_path):
    dv = _load("doc_viewer")
    c = await _client(dv.create_app(_docs(tmp_path)))
    try:
        r = await c.get("/?lang=fr")
        t = await r.text()
        assert r.status == 200 and '<html lang="fr">' in t
        assert "I18n" not in t and "i18n/fr" not in t
        assert "/static/shared/tool-page.js" in t and "design-system.css" in t
        assert 'href="/doc/manual/a.md?lang=fr"' in t
        r = await c.get("/doc/manual/a.md?lang=fr")
        t = await r.text()
        assert "Corps français" in t and 'article lang="fr"' in t
        assert 'href="/doc/manual/a.md?lang=en"' in t        # switch to original
        r = await c.get("/doc/manual/b.md?lang=fr")             # untranslated
        t = await r.text()
        assert "English only" in t and 'class="note-lang"' in t
        r = await c.get("/doc/manual/a.md")
        assert "English body" in await r.text()
        for bad in ("/doc/i18n/fr/manual/a.md", "/doc/%2e%2e/secret.md",
                    "/doc/manual/../../secret.md"):
            r = await c.get(bad)
            assert r.status == 404, bad
    finally:
        await c.close()


async def test_delayed_tm_listing_has_no_absolute_path(tmp_path):
    dtm = _load("delayed_tm_viewer")
    d = dtm.REPO / "workspace" / "dumps"
    app = dtm.make_app(d)
    c = await _client(app)
    try:
        j = await (await c.get("/api/dumps")).json()
        assert not j["dump_dir"].startswith("/")
        assert str(dtm.REPO) not in j["dump_dir"]
        page = await (await c.get("/")).text()
        assert "/static/shared/tool-page.js" in page
        assert str(dtm.REPO) not in page
    finally:
        await c.close()


def _marked_strings(src: str) -> set[str]:
    keys = set()
    # Python implicit concatenation ('...' '...') inside an f-string template
    # is one runtime string: join it before comparing with the catalog.
    norm = lambda k: _html.unescape(
        re.sub(r"\s+", " ", re.sub(r"'\s*f?'", "", k)).strip())
    for m in re.finditer(r'<\w+[^>]*?\sdata-i18n(?=[\s>])(?![^>]*data-i18n-context)[^>]*>([^<{$]*)<', src):
        if norm(m.group(1)):
            keys.add(norm(m.group(1)))
    for m in re.finditer(r'\bT\(\s*(?:"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')', src):
        keys.add(norm(m.group(1) if m.group(1) is not None else m.group(2)))
    return keys


@pytest.mark.parametrize("tool", TOOL_FILES + [FRAME])
def test_tool_page_strings_have_french(tool):
    src = (TOOLS / tool).read_text(encoding="utf-8")
    if tool == FRAME:
        assert "TOOL_HEAD" in src
    else:
        assert "setup_tool_app" in src
        assert "TOOL_HEAD" in src or "tool_frame" in src
    fr = json.loads(CATALOG.read_text(encoding="utf-8"))
    missing = sorted(k for k in _marked_strings(src) if k not in fr)
    assert not missing, f"{tool}: no French for {missing}"
    assert all(isinstance(v, str) and v for v in fr.values())
