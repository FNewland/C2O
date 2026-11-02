"""Shared HTTP policy (smo_common.web.http, R3 audit A8): gzip + cache headers.

Pins:
  - text responses >= 1 KB are gzipped (Response bodies and static files);
    small, binary, ranged and already-encoded responses are not;
  - a /static/ URL whose ?v= equals the file's content hash is immutable;
    a hand-written ?v=1 is NOT trusted (the 2026-08-20 field defect) and
    falls back to no-cache; vendor prefixes get a max-age;
  - stamp_asset_versions rewrites only resolvable /static/ URLs;
  - relative_display_path never returns an absolute server path;
  - the planner, instructor and tool servers are wired to the policy.
"""
from __future__ import annotations

import gzip
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.web.http import (IMMUTABLE, apply_http_policy, asset_hash,
                                 relative_display_path, setup_tool_app,
                                 stamp_asset_versions)

REPO = Path(__file__).resolve().parents[2]


def _app(tmp_path: Path) -> web.Application:
    static = tmp_path / "static"
    (static / "modern").mkdir(parents=True)
    (static / "vendor").mkdir()
    (static / "modern" / "big.js").write_text("const x = 1;\n" * 400)
    (static / "modern" / "tiny.js").write_text("1")
    (static / "modern" / "pic.png").write_bytes(b"\x89PNG" + b"\0" * 4000)
    (static / "vendor" / "lib.js").write_text("var v;\n" * 400)
    app = web.Application()
    apply_http_policy(app, max_age_prefixes={"/static/vendor/": 86400})

    async def page(request):
        return web.Response(text="<p>hello</p>" * 200, content_type="text/html")

    async def small(request):
        return web.json_response({"ok": True})

    app.router.add_get("/page", page)
    app.router.add_get("/small", small)
    app.router.add_static("/static/", static)
    return app


async def _client(app):
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


async def test_gzip_text_and_files_only_when_large(tmp_path):
    c = await _client(_app(tmp_path))
    try:
        gz = {"Accept-Encoding": "gzip"}
        r = await c.get("/page", headers=gz, auto_decompress=False)
        assert r.headers.get("Content-Encoding") == "gzip"
        assert gzip.decompress(await r.read()).decode().startswith("<p>hello")
        r = await c.get("/static/modern/big.js", headers=gz, auto_decompress=False)
        assert r.status == 200 and r.headers.get("Content-Encoding") == "gzip"
        assert len(await r.read()) < 1000
        for url in ("/small", "/static/modern/tiny.js", "/static/modern/pic.png"):
            r = await c.get(url, headers=gz, auto_decompress=False)
            assert "Content-Encoding" not in r.headers, url
        r = await c.get("/page", headers={"Accept-Encoding": "identity"},
                        auto_decompress=False)
        assert "Content-Encoding" not in r.headers
        r = await c.get("/static/modern/big.js",
                        headers={**gz, "Range": "bytes=0-9"}, auto_decompress=False)
        assert r.status == 206 and "Content-Encoding" not in r.headers
    finally:
        await c.close()


async def test_cache_control_trusts_only_real_hashes(tmp_path):
    app = _app(tmp_path)
    c = await _client(app)
    try:
        h = asset_hash(tmp_path / "static/modern/big.js")
        r = await c.get(f"/static/modern/big.js?v={h}")
        assert r.headers["Cache-Control"] == IMMUTABLE
        r = await c.get("/static/modern/big.js?v=1")         # hand-written
        assert r.headers["Cache-Control"] == "no-cache"
        r = await c.get("/static/modern/big.js")
        assert r.headers["Cache-Control"] == "no-cache"
        r = await c.get("/static/vendor/lib.js")
        assert r.headers["Cache-Control"] == "public, max-age=86400"
        # a revalidation still answers 304 with the policy in place
        etag = r.headers["ETag"]
        r = await c.get("/static/vendor/lib.js", headers={"If-None-Match": etag,
                                                          "Accept-Encoding": "gzip"})
        assert r.status == 304
        r = await c.get("/static/vendor/lib.js", headers={"If-None-Match": '"other"',
                                                          "Accept-Encoding": "gzip"},
                        auto_decompress=False)
        assert r.status == 200 and r.headers.get("Content-Encoding") == "gzip"
        assert "Accept-Encoding" in r.headers.get("Vary", "")
    finally:
        await c.close()


def test_stamp_asset_versions(tmp_path):
    app = _app(tmp_path)
    h = asset_hash(tmp_path / "static/modern/big.js")
    html = ('<script type="module" src="/static/modern/big.js?v=1"></script>'
            "<link rel='stylesheet' href=\"/static/modern/missing.css?v=1\">"
            '<script src="/static/modern/big.js?x=2"></script>')
    out = stamp_asset_versions(html, app)
    assert f'src="/static/modern/big.js?v={h}"' in out
    assert '/static/modern/missing.css?v=1' in out          # unresolvable: untouched
    assert f'src="/static/modern/big.js?x=2&v={h}"' in out
    # content change -> new hash
    (tmp_path / "static/modern/big.js").write_text("changed")
    assert asset_hash(tmp_path / "static/modern/big.js") != h


def test_relative_display_path_never_absolute(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "workspace" / "dumps").mkdir(parents=True)
    assert relative_display_path(tmp_path / "workspace" / "dumps") == "workspace/dumps"
    out = relative_display_path("/srv/elsewhere/c2o/dumps")
    assert not out.startswith("/") and out.endswith("c2o/dumps")
    assert relative_display_path("workspace/dumps") == "workspace/dumps"
    assert relative_display_path(None) == ""


async def test_tool_app_serves_shared_ui_gzipped():
    app = setup_tool_app(web.Application())
    c = await _client(app)
    try:
        for f in ("design-system.css", "i18n.js", "tool-page.js",
                  "i18n/tools/fr.json"):
            r = await c.get(f"/static/shared/{f}", headers={"Accept-Encoding": "gzip"},
                            auto_decompress=False)
            assert r.status == 200, f
        r = await c.get("/static/shared/design-system.css",
                        headers={"Accept-Encoding": "gzip"}, auto_decompress=False)
        assert r.headers.get("Content-Encoding") == "gzip"
    finally:
        await c.close()


async def test_instructor_index_is_gzipped_and_stamped():
    from smo_simulator.instructor.app import create_instructor_app
    app = create_instructor_app(MagicMock(), ui_mode="modern")
    c = await _client(app)
    try:
        r = await c.get("/", headers={"Accept-Encoding": "gzip"}, auto_decompress=False)
        assert r.status == 200 and r.headers.get("Content-Encoding") == "gzip"
        assert r.headers["Cache-Control"] == "no-cache"
        text = gzip.decompress(await r.read()).decode()
        js = (REPO / "packages/smo-simulator/src/smo_simulator/instructor/static"
              / "modern/instructor.js")
        assert f"/static/modern/instructor.js?v={asset_hash(js)}" in text
        r = await c.get(f"/static/modern/instructor.js?v={asset_hash(js)}")
        assert r.headers["Cache-Control"] == IMMUTABLE
    finally:
        await c.close()


def _load_tool(name):
    spec = importlib.util.spec_from_file_location(f"_tool_{name}", REPO / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("tool", ["delayed_tm_viewer", "orbit_tools", "doc_viewer",
                                  "scenario_generator", "adcs_sim_viewer"])
def test_tool_sources_use_the_shared_policy(tool):
    src = (REPO / "tools" / f"{tool}.py").read_text(encoding="utf-8")
    # TOOL_HEAD directly, or through the shared page frame that emits it.
    assert "setup_tool_app" in src and ("TOOL_HEAD" in src or "tool_frame" in src)
    if "tool_frame" in src:
        assert "TOOL_HEAD" in (REPO / "tools" / "tool_frame.py").read_text(encoding="utf-8")
