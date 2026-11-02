"""Tests for GenAI configuration loading."""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from spacecdf_ai.config import GenAIConfig, load_genai_config, reset_config


@pytest.fixture(autouse=True)
def clean_config():
    """Reset cached config between tests."""
    reset_config()
    yield
    reset_config()


def test_default_config_disabled():
    """Default config has everything disabled."""
    config = GenAIConfig()
    assert config.enabled is False
    assert config.is_capable("design_advisor") is False


def test_config_enabled_capability():
    config = GenAIConfig(
        enabled=True,
        capabilities={"design_advisor": True, "cad_scripting": False},
    )
    assert config.is_capable("design_advisor") is True
    assert config.is_capable("cad_scripting") is False
    assert config.is_capable("nonexistent") is False


def test_config_disabled_master_switch():
    """When master switch is off, no capability is available."""
    config = GenAIConfig(
        enabled=False,
        capabilities={"design_advisor": True},
    )
    assert config.is_capable("design_advisor") is False


def test_api_key_from_env():
    config = GenAIConfig(api_key_env="TEST_AI_KEY")
    os.environ["TEST_AI_KEY"] = "sk-test-123"
    try:
        assert config.api_key == "sk-test-123"
    finally:
        del os.environ["TEST_AI_KEY"]


def test_api_key_missing():
    config = GenAIConfig(api_key_env="NONEXISTENT_KEY_12345")
    assert config.api_key is None


def test_load_from_yaml():
    """Load config from a YAML file."""
    data = {
        "genai": {
            "enabled": True,
            "model": "claude-sonnet-4-6",
            "capabilities": {
                "design_advisor": True,
                "cad_scripting": False,
            },
            "budget": {
                "max_tokens_per_call": 2048,
                "session_token_limit": 50000,
            },
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        f.flush()
        config = load_genai_config(f.name)

    assert config.enabled is True
    assert config.model == "claude-sonnet-4-6"
    assert config.is_capable("design_advisor") is True
    assert config.is_capable("cad_scripting") is False
    assert config.budget.max_tokens_per_call == 2048
    assert config.budget.session_token_limit == 50000

    os.unlink(f.name)


def test_retired_capabilities_are_never_capable():
    """Only the three prose capabilities remain (docs/RULES_AND_AI.md)."""
    from spacecdf_ai.config import RETAINED_CAPABILITIES

    assert set(RETAINED_CAPABILITIES) == {"design_advisor", "requirements_decomposition", "report_narrative"}
    config = GenAIConfig(enabled=True, capabilities={"fsw_generation": True, "consistency_checking": True,
                                                     "report_narrative": True})
    assert config.is_capable("fsw_generation") is False
    assert config.is_capable("consistency_checking") is False
    assert config.is_capable("report_narrative") is True


def test_shipped_config_is_disabled():
    from spacecdf_ai.config import _resolve_config_path

    path = _resolve_config_path(None)
    assert path is not None
    assert load_genai_config(path).enabled is False
