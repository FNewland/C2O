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
        """Lazy-import and register all capability modules."""
        from spacecdf_ai.capabilities import (
            advisor,
            consistency,
            requirements,
            narrative,
            trade,
            cost,
            fmea,
            cad,
            wiring,
            fsw,
            aocs,
            thermal,
            structural,
        )
        self._capabilities = {
            "design_advisor": advisor.DesignAdvisorCapability(self.client, self.config),
            "consistency_checking": consistency.ConsistencyCapability(self.client, self.config),
            "requirements_decomposition": requirements.RequirementsCapability(self.client, self.config),
            "report_narrative": narrative.NarrativeCapability(self.client, self.config),
            "trade_analysis": trade.TradeCapability(self.client, self.config),
            "cost_estimation": cost.CostCapability(self.client, self.config),
            "fmea_generation": fmea.FMEACapability(self.client, self.config),
            "cad_scripting": cad.CADCapability(self.client, self.config),
            "wiring_generation": wiring.WiringCapability(self.client, self.config),
            "fsw_generation": fsw.FSWCapability(self.client, self.config),
            "aocs_design": aocs.AOCSCapability(self.client, self.config),
            "thermal_setup": thermal.ThermalCapability(self.client, self.config),
            "structural_setup": structural.StructuralCapability(self.client, self.config),
        }

    async def run(
        self,
        capability: str,
        *,
        api_key: str | None = None,
        session_id: str = "default",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a capability.

        Args:
            capability: Capability name (must match genai.yaml keys)
            api_key: Per-request API key override
            session_id: For usage tracking
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

        result = await cap.execute(
            api_key=api_key,
            session_id=session_id,
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
