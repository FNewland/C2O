"""SpaceCDF GenAI — Optional AI-powered design capabilities.

This package is intentionally separate from the core SpaceCDF stack so that
the tool works perfectly without it.  When installed, the server detects it
at startup and enables AI-enhanced endpoints gated by configs/genai.yaml.

Usage from spacecdf-server::

    try:
        from spacecdf_ai import AIService
        ai = AIService.from_config("configs/genai.yaml")
    except ImportError:
        ai = None  # graceful degradation — tool runs in manual mode
"""
from spacecdf_ai.config import GenAIConfig, load_genai_config
from spacecdf_ai.service import AIService
from spacecdf_ai.guard import requires_genai

__all__ = [
    "AIService",
    "GenAIConfig",
    "load_genai_config",
    "requires_genai",
]
