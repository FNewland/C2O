"""Tests for the requires_genai guard decorator."""
import os
import tempfile

import pytest
import yaml

from spacecdf_ai.config import reset_config, load_genai_config
from spacecdf_ai.guard import requires_genai


@pytest.fixture(autouse=True)
def clean_config():
    reset_config()
    yield
    reset_config()


def _write_config(enabled: bool, capabilities: dict) -> str:
    data = {"genai": {"enabled": enabled, "capabilities": capabilities}}
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(data, f)
    f.flush()
    f.close()
    return f.name


@pytest.mark.asyncio
async def test_guard_blocks_when_disabled():
    path = _write_config(False, {"design_advisor": True})
    load_genai_config(path)

    @requires_genai("design_advisor")
    async def my_func():
        return {"content": "should not reach"}

    result = await my_func()
    assert result["ai_available"] is False
    os.unlink(path)


@pytest.mark.asyncio
async def test_guard_passes_when_enabled():
    path = _write_config(True, {"design_advisor": True})
    load_genai_config(path)

    @requires_genai("design_advisor")
    async def my_func():
        return {"content": "AI result"}

    result = await my_func()
    assert result["content"] == "AI result"
    os.unlink(path)


@pytest.mark.asyncio
async def test_guard_uses_fallback():
    path = _write_config(False, {})
    load_genai_config(path)

    @requires_genai("cad_scripting")
    async def generate_cad():
        return {"content": "CAD script"}

    @generate_cad.fallback
    async def generate_cad_fallback():
        return {"content": "", "message": "CAD requires GenAI", "ai_available": False}

    result = await generate_cad()
    assert result["ai_available"] is False
    assert "CAD requires GenAI" in result["message"]
    os.unlink(path)
