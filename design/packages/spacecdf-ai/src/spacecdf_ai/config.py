"""GenAI configuration loader.

Reads configs/genai.yaml and exposes a validated Pydantic model.
The config is loaded once at server startup and cached.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class BudgetConfig(BaseModel):
    max_tokens_per_call: int = 4096
    max_context_elements: int = 200
    session_token_limit: int = 100_000
    rate_limit_rpm: int = 30


class OutputConfig(BaseModel):
    include_reasoning: bool = False
    include_references: bool = True
    language: str = "en"


class GenAIConfig(BaseModel):
    """Validated GenAI configuration."""
    enabled: bool = False
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    model_heavy: str = "claude-opus-4-6"
    model_fast: str = "claude-haiku-4-5-20251001"
    api_key_env: str = "ANTHROPIC_API_KEY"
    capabilities: dict[str, bool] = Field(default_factory=dict)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @property
    def api_key(self) -> str | None:
        """Resolve API key from environment. Never stored in config."""
        return os.environ.get(self.api_key_env) or None

    def is_capable(self, capability: str) -> bool:
        """Check if a specific capability is enabled."""
        return self.enabled and self.capabilities.get(capability, False)


# Module-level singleton
_config: GenAIConfig | None = None


def load_genai_config(path: str | Path | None = None) -> GenAIConfig:
    """Load and cache GenAI configuration.

    Searches in order:
    1. Explicit path argument
    2. GENAI_CONFIG env var
    3. configs/genai.yaml relative to project root
    4. Defaults (everything disabled)
    """
    global _config
    if _config is not None:
        return _config

    config_path = _resolve_config_path(path)
    if config_path and config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        genai_block = raw.get("genai", raw)
        _config = GenAIConfig(**genai_block)
    else:
        _config = GenAIConfig()  # All defaults — disabled

    return _config


def reset_config() -> None:
    """Reset cached config (for testing)."""
    global _config
    _config = None


def _resolve_config_path(path: str | Path | None) -> Path | None:
    if path:
        return Path(path)
    env = os.environ.get("GENAI_CONFIG")
    if env:
        return Path(env)
    # Walk up from this file to find project root
    candidate = Path(__file__).resolve()
    for _ in range(10):
        candidate = candidate.parent
        p = candidate / "configs" / "genai.yaml"
        if p.exists():
            return p
    return None
