"""AIService — top-level entry point for all GenAI capabilities.

The server imports this single class.  It owns the client, config, and
capability registry.  Each capability is a thin module that composes
a system prompt + context serializer + response parser.

Usage::

    from spacecdf_ai import AIService

    ai = AIService.from_config("configs/genai.yaml")
    result = await ai.run("consistency_checking", study=study, budgets=budgets)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from spacecdf_ai.client import AIClient, AIResponse
from spacecdf_ai.config import GenAIConfig, load_genai_config

logger = logging.getLogger(__name__)


class AIService:
    """Central service managing all AI capabilities."""

    def __init__(self, config: GenAIConfig) -> None:
        self.config = config
        self.client = AIClient(config)
        self._capabilities: dict[str, Any] = {}
        self._register_capabilities()

    @classmethod
    def from_config(cls, path: str | Path | None = None) -> AIService:
        """Create AIService from config file."""
        config = load_genai_config(path)
        return cls(config)

    def _register_capabilities(self) -> None:
        """Register the three retained prose capabilities (see config.RETAINED_CAPABILITIES)."""
        from spacecdf_ai.capabilities import advisor, narrative, requirements
        self._capabilities = {
            "design_advisor": advisor.DesignAdvisorCapability(self.client, self.config),
            "requirements_decomposition": requirements.RequirementsCapability(self.client, self.config),
            "report_narrative": narrative.NarrativeCapability(self.client, self.config),
        }

    async def run(
        self,
        capability: str,
        *,
        api_key: str | None = None,
        session_id: str = "default",
        ui_language: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a capability.

        Args:
            capability: Capability name (must match genai.yaml keys)
            api_key: Per-request API key override
            session_id: For usage tracking
            ui_language: User's UI language ('en'/'fr'); None → genai.yaml
                output.language → 'en'. French makes the model answer in French.
            **kwargs: Capability-specific arguments

        Returns:
            dict with at minimum {ai_available, content} keys.
            Each capability adds its own structured fields.
        """
        if not self.config.is_capable(capability):
            return {
                "ai_available": False,
                "capability": capability,
                "content": "",
                "message": f"Capability '{capability}' is disabled in genai.yaml",
            }

        cap = self._capabilities.get(capability)
        if not cap:
            return {
                "ai_available": False,
                "capability": capability,
                "content": "",
                "message": f"Unknown capability: {capability}",
            }

        # The HTTP layer sends one free-form ``context`` dict; spread its known keys
        # (study, mission_need, elements, budgets, requirements, ...) into the
        # capability's keyword arguments so nothing is silently dropped.
        context = kwargs.pop("context", None)
        if isinstance(context, dict):
            from spacecdf_ai.context import context_to_kwargs
            for k, v in context_to_kwargs(context).items():
                kwargs.setdefault(k, v)

        result = await cap.execute(
            api_key=api_key,
            session_id=session_id,
            ui_language=ui_language,
            **kwargs,
        )

        return {
            "ai_available": True,
            "capability": capability,
            **result,
        }

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def get_status(self, session_id: str = "default") -> dict:
        """Get AI service status and usage."""
        return {
            "enabled": self.config.enabled,
            "provider": self.config.provider,
            "model": self.config.model,
            "capabilities": {
                name: self.config.is_capable(name)
                for name in self._capabilities
            },
            "usage": self.client.get_usage(session_id),
        }
