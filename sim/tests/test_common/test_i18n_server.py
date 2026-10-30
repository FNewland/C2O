"""i18n packet S0 — server side: smo_common.i18n, the additive ?lang= on the
MCS procedure/manual document endpoints, the server-default language
(SMO_LANG > mission.yaml ui_lang > en) injected into the modern pages, and
catalog hygiene for the shipped JSON catalogs.

Invariants pinned here:
  * English is served exactly as before (no ?lang -> identical body; modern
    index byte-identical unless a non-English default is configured).
  * ?lang= is display-only and falls back to English per file.
  * The translations live outside procedures/ (the runner scans it).
  * Classic pages never load the i18n runtime.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from pydantic import ValidationError

from smo_common.config.schemas import MCSDisplayConfig, MissionConfig
from smo_common.i18n import (inject_default_lang, localized_md_path,
                             normalize_lang, resolve_lang, server_default_lang)

REPO = Path(__file__).resolve().parents[2]
SHARED_UI = REPO / "packages/smo-common/src/smo_common/ui"
APP_CATALOGS = [
    REPO / "packages/smo-mcs/src/smo_mcs/static/modern/i18n/fr.json",
    REPO / "packages/smo-planner/src/smo_planner/static/modern/i18n/fr.json",
    REPO / "packages/smo-simulator/src/smo_simulator/instructor/static/modern/i18n/fr.json",
    REPO / "packages/smo-rfsim/src/smo_rfsim/static/modern/i18n/fr.json",
]
CLASSIC = [
    "packages/smo-mcs/src/smo_mcs/static/index.html",
    "packages/smo-planner/src/smo_planner/static/index.html",
    "packages/smo-rfsim/src/smo_rfsim/static/radio.html",
    "packages/smo-simulator/src/smo_simulator/instructor/static/index.html",
]


# ── smo_common.i18n ──────────────────────────────────────────────────────

def test_normalize_and_resolve_lang():
    assert normalize_lang("fr-CA") == "fr" and normalize_lang("EN_gb") == "en"
    assert normalize_lang("de") is None and normalize_lang(None) is None
    assert resolve_lang({"lang": "fr"}) == "fr"
    assert resolve_lang("?lang=fr&ui=modern") == "fr"
    assert resolve_lang("lang=de", "fr") == "fr"          # unsupported -> default
    assert resolve_lang(None) == "en"

    class Req:
        query = {"lang": "FR"}
    assert resolve_lang(Req()) == "fr"


def test_server_default_precedence(monkeypatch):
    monkeypatch.delenv("SMO_LANG", raising=False)
    assert server_default_lang() == "en"
    assert server_default_lang(mission_lang="fr") == "fr"
    monkeypatch.setenv("SMO_LANG", "en")
    assert server_default_lang(mission_lang="fr") == "en"   # env beats mission
    assert server_default_lang(cli="fr", mission_lang="en") == "fr"
    monkeypatch.setenv("SMO_LANG", "klingon")
    assert server_default_lang(mission_lang="fr") == "en"   # loud fallback


def test_mission_schema_accepts_ui_lang_strictly():
    assert MissionConfig().ui_lang is None
    assert MissionConfig(ui_lang="fr").ui_lang == "fr"
    with pytest.raises(ValidationError):
        MissionConfig(ui_lang="de")


def test_inject_default_lang_is_identity_for_english():
    html = '<!DOCTYPE html>\n<html lang="en" data-theme="dark">\n<body></body></html>'
    assert inject_default_lang(html, "en") == html
    assert inject_default_lang(html, None) == html
    out = inject_default_lang(html, "fr")
    assert '<html data-default-lang="fr" lang="en" data-theme="dark">' in out
    assert out.replace(' data-default-lang="fr"', "") == html


def _cfg(tmp_path: Path) -> Path:
    cfg = tmp_path / "cfg"
    (cfg / "procedures/nominal").mkdir(parents=True)
    (cfg / "manual").mkdir(parents=True)
    (cfg / "i18n/fr/procedures/nominal").mkdir(parents=True)
    (cfg / "procedures/nominal/pass.md").write_text("# Pass setup\n**TC:** X\n", encoding="utf-8")
    (cfg / "i18n/fr/procedures/nominal/pass.md").write_text(
        "# Préparation du passage\n**TC:** X\n", encoding="utf-8")
    (cfg / "manual/01_intro.md").write_text("# Introduction\n", encoding="utf-8")
    return cfg


def test_localized_md_path_maps_and_falls_back(tmp_path):
    cfg = _cfg(tmp_path)
    en = cfg / "procedures/nominal/pass.md"
    assert localized_md_path(en, "fr") == cfg / "i18n/fr/procedures/nominal/pass.md"
    assert localized_md_path(en, "fr", cfg) == cfg / "i18n/fr/procedures/nominal/pass.md"
    assert localized_md_path(en, "en") == en
    assert localized_md_path(en, "de") == en
    man = cfg / "manual/01_intro.md"
    assert localized_md_path(man, "fr") == man                 # no translation yet
    other = cfg / "telemetry/x.md"
    assert localized_md_path(other, "fr") == other             # not a localized tree
    assert localized_md_path(en, "fr", tmp_path / "elsewhere") == en


def test_translations_are_not_under_procedures():
    """The MCS loads procedures/**/*.md recursively; FR must live elsewhere."""
    assert not (REPO / "configs/eosat1/procedures/i18n").exists()
    assert not list((REPO / "configs/eosat1/procedures").rglob("fr"))


# ── MCS document endpoints: additive ?lang= ──────────────────────────────

def _make_mcs(config_dir, mission_lang=None):
    from smo_mcs.server import MCSServer
    mc = MissionConfig(ui_lang=mission_lang)
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}), \
         patch("smo_mcs.server.load_tc_catalog", return_value=[]), \
         patch("smo_common.config.loader.load_mission_config", return_value=mc):
        return MCSServer(config_dir=str(config_dir), connect_host="localhost",
                         connect_port=9999, http_port=0)


async def _client(app) -> TestClient:
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


@pytest.mark.asyncio
async def test_procedure_and_manual_endpoints_take_lang(tmp_path, monkeypatch):
    monkeypatch.delenv("SMO_LANG", raising=False)
    srv = _make_mcs(_cfg(tmp_path))
    app = web.Application()
    app.router.add_get("/api/procedures/{path:.+}", srv._handle_procedure_file)
    app.router.add_get("/api/manual/{path:.+}", srv._handle_manual_file)
    c = await _client(app)
    try:
        plain = await (await c.get("/api/procedures/nominal/pass.md")).json()
        assert plain == {"title": "Pass setup",
                         "content_md": "# Pass setup\n**TC:** X\n"}   # unchanged shape
        fr = await (await c.get("/api/procedures/nominal/pass.md?lang=fr")).json()
        assert fr["lang"] == "fr" and fr["title"] == "Préparation du passage"
        en = await (await c.get("/api/procedures/nominal/pass.md?lang=en")).json()
        assert en["lang"] == "en" and en["content_md"] == plain["content_md"]
        de = await (await c.get("/api/procedures/nominal/pass.md?lang=de")).json()
        assert de["lang"] == "en" and de["title"] == "Pass setup"
        man = await (await c.get("/api/manual/01_intro.md?lang=fr")).json()
        assert man["lang"] == "en" and man["title"] == "Introduction"  # fallback
        miss = await c.get("/api/procedures/nominal/nope.md?lang=fr")
        assert miss.status == 404
    finally:
        await c.close()


# ── server default language on the modern pages ──────────────────────────

MCS_MODERN = REPO / "packages/smo-mcs/src/smo_mcs/static/modern/index.html"


@pytest.mark.asyncio
async def test_mcs_modern_index_default_lang(tmp_path, monkeypatch):
    monkeypatch.delenv("SMO_LANG", raising=False)
    for lang, env in (("en", None), ("fr", "fr")):
        if env:
            monkeypatch.setenv("SMO_LANG", env)
        srv = _make_mcs(tmp_path)
        assert srv._ui_lang == lang
        app = web.Application()
        app.router.add_get("/modern", srv._handle_index_modern)
        app.router.add_get("/classic", srv._handle_index_classic)
        c = await _client(app)
        try:
            r = await c.get("/modern")
            assert r.headers.get("Cache-Control") == "no-cache"
            body = await r.text()
            if lang == "en":
                assert body == MCS_MODERN.read_text(encoding="utf-8")
            else:
                assert 'data-default-lang="fr"' in body
                assert body.replace(' data-default-lang="fr"', "") == \
                    MCS_MODERN.read_text(encoding="utf-8")
            classic = await (await c.get("/classic")).text()
            assert "data-default-lang" not in classic
        finally:
            await c.close()


def test_mcs_mission_yaml_ui_lang_is_the_default(tmp_path, monkeypatch):
    monkeypatch.delenv("SMO_LANG", raising=False)
    assert _make_mcs(tmp_path, mission_lang="fr")._ui_lang == "fr"
    monkeypatch.setenv("SMO_LANG", "en")
    assert _make_mcs(tmp_path, mission_lang="fr")._ui_lang == "en"


@pytest.mark.asyncio
async def test_instructor_injects_default_lang(monkeypatch):
    monkeypatch.setenv("SMO_LANG", "fr")
    from smo_simulator.instructor.app import create_instructor_app
    c = await _client(create_instructor_app(MagicMock(), ui_mode="modern"))
    try:
        assert 'data-default-lang="fr"' in await (await c.get("/")).text()
        assert "data-default-lang" not in await (await c.get("/classic")).text()
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_rfsim_injects_default_lang(monkeypatch):
    pytest.importorskip("smo_rfsim")      # not on the conftest path by default
    monkeypatch.setenv("SMO_LANG", "fr")
    from smo_rfsim.radio.frontend import RadioFrontend
    from smo_rfsim.radio.web_ui import build_app
    c = await _client(build_app(RadioFrontend(), ui_mode="modern"))
    try:
        for url in ("/", "/modern", "/sim"):
            assert 'data-default-lang="fr"' in await (await c.get(url)).text(), url
        assert "data-default-lang" not in await (await c.get("/classic")).text()
    finally:
        await c.close()


# ── shipped catalogs + classic freeze ────────────────────────────────────

_PH = re.compile(r"\{\{-?\s*([\w.]+)\s*\}\}")
_SUFFIX = re.compile(r"_(one|many|other|zero|two|few)$")


@pytest.mark.parametrize("path", [SHARED_UI / "i18n/fr.json", *APP_CATALOGS],
                         ids=lambda p: str(p.relative_to(REPO)))
def test_catalogs_are_flat_string_maps_with_placeholder_parity(path):
    cat = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(cat, dict)
    for k, v in cat.items():
        assert v is None or isinstance(v, str), f"{path.name}: {k!r} is not a string"
        if not v:
            continue                       # untranslated entry (null / "")
        base = _SUFFIX.sub("", k)
        want = set(_PH.findall(base)) - {"count"}
        got = set(_PH.findall(v)) - {"count"}
        assert want == got, f"{path.name}: placeholder mismatch in {k!r}: {got} != {want}"


def test_every_shared_component_string_has_a_french_entry():
    """Dictionary completeness for the design system (S0 owns it)."""
    cat = json.loads((SHARED_UI / "i18n/fr.json").read_text(encoding="utf-8"))
    src = (SHARED_UI / "components.js").read_text(encoding="utf-8")
    keys = set(re.findall(r'\bt(?:Text|Html)?\("((?:[^"\\]|\\.)*)"', src))
    assert keys, "components.js no longer calls t()?"
    missing = sorted(k for k in keys if not cat.get(k))
    assert not missing, f"shared fr.json lacks: {missing}"


def test_db_overlay_placeholder_is_valid_json():
    assert isinstance(json.loads((SHARED_UI / "i18n/fr.db.json").read_text()), dict)


@pytest.mark.parametrize("rel", CLASSIC)
def test_classic_pages_never_load_the_runtime(rel):
    html = (REPO / rel).read_text(encoding="utf-8")
    assert "i18n" not in html and "lang-toggle" not in html


# ── wiring of the modern shells ──────────────────────────────────────────

PKG = REPO / "packages"
SHELLS = {   # page -> (script that imports i18n.js, has toggle?)
    "smo-mcs/src/smo_mcs/static/modern/index.html":
        ("smo-mcs/src/smo_mcs/static/modern/mcs.js", True),
    "smo-planner/src/smo_planner/static/modern/index.html":
        ("smo-planner/src/smo_planner/static/modern/planner.js", True),
    "smo-planner/src/smo_planner/static/modern/wide.html":
        ("smo-planner/src/smo_planner/static/modern/wide.js", False),
    "smo-simulator/src/smo_simulator/instructor/static/modern/index.html":
        ("smo-simulator/src/smo_simulator/instructor/static/modern/instructor.js", True),
    "smo-rfsim/src/smo_rfsim/static/modern/index.html":
        ("smo-rfsim/src/smo_rfsim/static/modern/index.html", True),
    "smo-rfsim/src/smo_rfsim/static/modern/sim.html":
        ("smo-rfsim/src/smo_rfsim/static/modern/sim.html", True),
}


@pytest.mark.parametrize("page", sorted(SHELLS))
def test_modern_shell_wiring(page):
    script, toggle = SHELLS[page]
    html = (PKG / page).read_text(encoding="utf-8")
    js = (PKG / script).read_text(encoding="utf-8")
    assert 'from "/static/shared/i18n.js"' in js     # no ?v=: one module instance
    assert ('id="lang-toggle"' in html) is toggle
    assert ("mountLangToggle" in js) is toggle
    if not toggle:                                   # wall display: ?lang= only
        assert "storage: false" in js


def test_mcs_passes_its_language_to_the_document_endpoints():
    js = (PKG / "smo-mcs/src/smo_mcs/static/modern/mcs.js").read_text(encoding="utf-8")
    assert "`/api/procedures/${encodeURIComponent(v)}?lang=${getLang()}`" in js
    assert '"?lang=" + getLang()' in js
    assert "await I18n.ready" in js
