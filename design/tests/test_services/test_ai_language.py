"""i18n packet C0: the UI language reaches the AI system prompts.

English (the default) must leave every system prompt byte-identical; 'fr'
appends an instruction to answer in French while keeping identifiers,
standard numbers and units unchanged.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from spacecdf_common.language import (
    FRENCH_OUTPUT_INSTRUCTION,
    apply_language,
    normalize_language,
)


@pytest.mark.parametrize("raw, expected", [
    (None, "en"), ("", "en"), ("en", "en"), ("fr", "fr"), ("FR", "fr"),
    ("fr-FR", "fr"), ("fr_CA", "fr"), ("fr-FR,fr;q=0.9,en;q=0.8", "fr"),
    ("en-GB,fr;q=0.5", "en"), ("de", "en"), ("xx-YY", "en"),
])
def test_normalize_language(raw, expected):
    assert normalize_language(raw) == expected


def test_normalize_language_bad_default_falls_back_to_english():
    assert normalize_language("de", default="es") == "en"
    assert normalize_language(None, default="fr") == "fr"


def test_apply_language_english_is_identity_and_french_appends():
    assert apply_language("PROMPT", "en") == "PROMPT"
    assert apply_language("PROMPT", None) == "PROMPT"
    fr = apply_language("PROMPT", "fr")
    assert fr.startswith("PROMPT") and fr.endswith(FRENCH_OUTPUT_INSTRUCTION)
    assert "Respond in French" in fr
    assert "ECSS" in FRENCH_OUTPUT_INSTRUCTION and "units" in FRENCH_OUTPUT_INSTRUCTION


def test_ai_advisor_system_prompt():
    from spacecdf_server.services.ai_advisor import SYSTEM_PROMPT, build_system_prompt

    assert build_system_prompt() == SYSTEM_PROMPT
    assert build_system_prompt("en") == SYSTEM_PROMPT
    assert build_system_prompt("fr") == SYSTEM_PROMPT + FRENCH_OUTPUT_INSTRUCTION


# --- spacecdf-ai capability layer -------------------------------------------

class _RecordingClient:
    """Stands in for AIClient: records the system prompt instead of calling the API."""

    def __init__(self):
        self.calls: list[dict] = []

    async def call(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(error=None, content="ok", tokens_used=1, model=kw["model"], elapsed_ms=0.0)


def _service(output_language: str = "en"):
    pytest.importorskip("spacecdf_ai")
    from spacecdf_ai.config import GenAIConfig
    from spacecdf_ai.service import AIService

    cfg = GenAIConfig(enabled=True, capabilities={"design_advisor": True, "fsw_generation": True})
    cfg.output.language = output_language
    svc = AIService(cfg)
    client = _RecordingClient()
    for cap in svc._capabilities.values():
        cap.client = client
    return svc, client


async def test_capability_english_prompt_unchanged():
    svc, client = _service()
    base = svc._capabilities["design_advisor"].get_system_prompt()
    await svc.run("design_advisor", question="Q?")
    assert client.calls[-1]["system"] == base


async def test_capability_french_prompt_gets_instruction():
    svc, client = _service()
    base = svc._capabilities["design_advisor"].get_system_prompt()
    await svc.run("design_advisor", question="Q?", ui_language="fr")
    assert client.calls[-1]["system"] == base + FRENCH_OUTPUT_INSTRUCTION


async def test_config_output_language_is_the_default_and_request_overrides():
    svc, client = _service(output_language="fr")
    await svc.run("design_advisor", question="Q?")
    assert client.calls[-1]["system"].endswith(FRENCH_OUTPUT_INSTRUCTION)
    await svc.run("design_advisor", question="Q?", ui_language="en")
    assert not client.calls[-1]["system"].endswith(FRENCH_OUTPUT_INSTRUCTION)


async def test_retired_capability_is_never_capable():
    """fsw_generation (and every other retired capability) stays off even if genai.yaml enables it."""
    svc, client = _service()
    out = await svc.run("fsw_generation", language="c", ui_language="fr")
    assert out["ai_available"] is False and not client.calls


async def test_router_context_reaches_the_prompt():
    """Defect (audit §1.4.2): the HTTP ``context`` used to be dropped on the AIService path."""
    svc, client = _service()
    await svc.run("design_advisor", context={"mission_need": {"problem_statement": "Wildfire smoke maps",
                                                              "stakeholders": [{"name": "CIFFC", "role": "user",
                                                                                "needs": ["daily maps"]}]}},
                  capability_hint="critique_need")
    msg = client.calls[-1]["user_message"]
    assert "Wildfire smoke maps" in msg and "CIFFC" in msg


async def test_max_tokens_forwarded_and_capped():
    svc, client = _service()
    await svc.run("design_advisor", question="Q?", max_tokens=999)
    assert client.calls[-1]["max_tokens"] == 999
    await svc.run("design_advisor", question="Q?", max_tokens=10**6)
    assert client.calls[-1]["max_tokens"] == svc.config.budget.max_tokens_per_call


# --- HTTP layer ---------------------------------------------------------------

def _ai_on(monkeypatch, *caps: str):
    """Switch AI on for the router/legacy path without touching configs/genai.yaml."""
    from spacecdf_server.routers import ai as ai_router
    from spacecdf_server.services import ai_advisor

    settings = {"enabled": True, "capabilities": {c: True for c in caps}, "model": "m", "max_tokens_per_call": 4096}
    monkeypatch.setattr(ai_advisor, "genai_settings", lambda: settings)
    monkeypatch.setattr(ai_router, "genai_settings", lambda: settings)


async def test_ai_router_forwards_language(monkeypatch):
    from spacecdf_server.app import app
    from spacecdf_server.routers import ai as ai_router
    from spacecdf_server.services.ai_advisor import AIResponse

    seen: list[str | None] = []

    async def fake_ask_ai(capability, context, question="", api_key=None,
                          session_id="default", model=None, max_tokens=1500, language=None):
        seen.append(language)
        return AIResponse(content="ok", capability=capability)

    _ai_on(monkeypatch, "design_advisor", "requirements_decomposition")
    monkeypatch.setattr(ai_router, "ask_ai", fake_ask_ai)
    monkeypatch.setattr(app.state, "ai_service", None, raising=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        assert (await c.post("/api/ai/ask", json={"capability": "general"})).status_code == 200
        assert (await c.post("/api/ai/ask", json={"capability": "general", "language": "fr"})).status_code == 200
        assert (await c.post("/api/ai/ask", json={"capability": "general", "language": "de"})).status_code == 422
        assert (await c.post("/api/ai/write-requirements?language=fr", json={})).status_code == 200
        assert (await c.post("/api/ai/critique-need", json={})).status_code == 200
    assert seen == [None, "fr", "fr", None]


async def test_kill_switch_blocks_every_path_even_with_a_key(monkeypatch):
    """Defect (audit §1.4.1): genai.enabled: false did not stop the legacy path."""
    from spacecdf_server.app import app
    from spacecdf_server.routers import ai as ai_router
    from spacecdf_server.services import ai_advisor

    called: list[str] = []

    async def fake_ask_ai(capability, *a, **k):
        called.append(capability)
        return ai_advisor.AIResponse(content="ok", capability=capability)

    off = {"enabled": False, "capabilities": {"design_advisor": True}, "model": "m", "max_tokens_per_call": 4096}
    monkeypatch.setattr(ai_advisor, "genai_settings", lambda: off)
    monkeypatch.setattr(ai_router, "genai_settings", lambda: off)
    monkeypatch.setattr(ai_router, "ask_ai", fake_ask_ai)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-used")
    monkeypatch.setattr(app.state, "ai_service", None, raising=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/ai/ask", json={"capability": "general"}, headers={"X-API-Key": "sk-x"})
        assert r.status_code == 503 and r.json()["detail"]["code"] == "genai_disabled"
        assert r.json()["detail"]["message"]["fr"]
        assert (await c.post("/api/ai/critique-need", json={})).status_code == 503
        assert (await c.post("/api/ai/write-requirements", json={})).status_code == 503
        st = (await c.get("/api/ai/status")).json()
        assert st["enabled"] is False and st["available"] is False and st["mode"] == "manual"
    assert called == []
    # Defence in depth: the legacy function refuses on its own too.
    res = await ai_advisor.ask_ai("general", {}, api_key="sk-x")
    assert res.error and "disabled" in res.error


def test_shipped_genai_yaml_is_off_and_limited_to_three_capabilities():
    import yaml
    from spacecdf_server.services.ai_advisor import _genai_yaml

    data = yaml.safe_load(_genai_yaml().read_text(encoding="utf-8"))["genai"]
    assert data["enabled"] is False
    assert set(data["capabilities"]) == {"design_advisor", "requirements_decomposition", "report_narrative"}


async def test_retired_capabilities_answer_410(monkeypatch):
    from spacecdf_server.app import app

    _ai_on(monkeypatch, "design_advisor")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for cap in ("review_design", "analyze_trade", "recommend_component", "generate_conops"):
            r = await c.post("/api/ai/ask", json={"capability": cap})
            assert r.status_code == 410 and r.json()["detail"]["use"], cap
        assert (await c.post("/api/ai/review-design", json={})).status_code == 410


async def test_ai_output_comes_back_rule_checked(monkeypatch):
    from spacecdf_server.app import app
    from spacecdf_server.routers import ai as ai_router
    from spacecdf_server.services.ai_advisor import AIResponse

    async def fake_ask_ai(capability, *a, **k):
        return AIResponse(content="1. The OBC shall boot within 10 s.\n2. The EPS shall be efficient.",
                          capability=capability)

    _ai_on(monkeypatch, "requirements_decomposition")
    monkeypatch.setattr(ai_router, "ask_ai", fake_ask_ai)
    monkeypatch.setattr(app.state, "ai_service", None, raising=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        body = (await c.post("/api/ai/ask", json={"capability": "write_requirements"})).json()
    assert body["validated"] is True
    assert body["rule_checks"]["summary"] == {"statements": 2, "needs_revision": 1, "pass": 1, "open_items": 0}


# --- export templates ---------------------------------------------------------

def test_export_template_search_path(tmp_path, monkeypatch):
    pytest.importorskip("docx")  # generator imports the python-docx helpers
    from spacecdf_agents.exporters.docs import generator

    en_only = generator.template_search_path("en")
    assert en_only == [str(generator.TEMPLATE_DIR)]
    # No templates/fr/ yet → French falls back to the English templates.
    if not (generator.TEMPLATE_DIR / "fr").is_dir():
        assert generator.template_search_path("fr") == en_only

    (tmp_path / "fr").mkdir()
    (tmp_path / "srr.md.j2").write_text("# System Requirements Review\n")
    (tmp_path / "fr" / "srr.md.j2").write_text("# Revue des exigences système\n")
    monkeypatch.setattr(generator, "TEMPLATE_DIR", tmp_path)
    assert generator.render_markdown({}, "srr") == "# System Requirements Review\n"
    assert generator.render_markdown({}, "srr", lang="fr") == "# Revue des exigences système\n"
    assert generator.render_markdown({}, "srr", lang="de") == "# System Requirements Review\n"
