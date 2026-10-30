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


async def test_fsw_programming_language_kwarg_is_not_confused_with_ui_language():
    svc, client = _service()
    await svc.run("fsw_generation", language="c", ui_language="fr")
    call = client.calls[-1]
    assert "in C for this spacecraft" in call["user_message"]
    assert call["system"].endswith(FRENCH_OUTPUT_INSTRUCTION)


# --- HTTP layer ---------------------------------------------------------------

async def test_ai_router_forwards_language(monkeypatch):
    from spacecdf_server.app import app
    from spacecdf_server.routers import ai as ai_router
    from spacecdf_server.services.ai_advisor import AIResponse

    seen: list[str | None] = []

    async def fake_ask_ai(capability, context, question="", api_key=None,
                          session_id="default", model=None, max_tokens=1500, language=None):
        seen.append(language)
        return AIResponse(content="ok", capability=capability)

    monkeypatch.setattr(ai_router, "ask_ai", fake_ask_ai)
    monkeypatch.setattr(app.state, "ai_service", None, raising=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        assert (await c.post("/api/ai/ask", json={"capability": "general"})).status_code == 200
        assert (await c.post("/api/ai/ask", json={"capability": "general", "language": "fr"})).status_code == 200
        assert (await c.post("/api/ai/ask", json={"capability": "general", "language": "de"})).status_code == 422
        assert (await c.post("/api/ai/review-design?language=fr", json={})).status_code == 200
        assert (await c.post("/api/ai/critique-need", json={})).status_code == 200
    assert seen == [None, "fr", "fr", None]


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
