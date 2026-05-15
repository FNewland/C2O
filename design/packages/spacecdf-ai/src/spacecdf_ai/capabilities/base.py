"""Base class for all AI capabilities."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from spacecdf_ai.client import AIClient
from spacecdf_ai.config import GenAIConfig

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class BaseCapability(ABC):
    """Abstract base for an AI capability.

    Subclasses implement:
    - name: capability identifier (matches genai.yaml key)
    - prompt_file: filename in prompts/ directory
    - build_user_message(): serialize inputs into the user message
    - parse_response(): extract structured data from AI response
    """

    name: str = ""
    prompt_file: str = ""
    model_tier: str = "default"  # "default", "heavy", or "fast"

    def __init__(self, client: AIClient, config: GenAIConfig) -> None:
        self.client = client
        self.config = config

    def get_system_prompt(self) -> str:
        """Load system prompt from prompts/ directory."""
        path = PROMPTS_DIR / self.prompt_file
        if path.exists():
            return path.read_text()
        logger.warning("Prompt file not found: %s — using fallback", path)
        return self._fallback_prompt()

    def _fallback_prompt(self) -> str:
        """Override to provide inline fallback when prompt file is missing."""
        return (
            "You are an AI advisor embedded in SpaceCDF, an AI-supported "
            "Concurrent Design Facility for space missions."
        )

    def get_model(self) -> str:
        """Resolve model based on tier."""
        if self.model_tier == "heavy":
            return self.config.model_heavy
        elif self.model_tier == "fast":
            return self.config.model_fast
        return self.config.model

    @abstractmethod
    def build_user_message(self, **kwargs: Any) -> str:
        """Build the user message from capability-specific inputs."""
        ...

    def parse_response(self, content: str) -> dict[str, Any]:
        """Parse AI response into structured output.

        Default: return raw content. Override for structured parsing.
        """
        return {"content": content}

    async def execute(
        self,
        *,
        api_key: str | None = None,
        session_id: str = "default",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute the capability end-to-end."""
        system = self.get_system_prompt()
        user_message = self.build_user_message(**kwargs)
        model = self.get_model()

        response = await self.client.call(
            system=system,
            user_message=user_message,
            capability=self.name,
            model=model,
            api_key=api_key,
            session_id=session_id,
        )

        if response.error:
            return {
                "content": "",
                "error": response.error,
                "tokens_used": response.tokens_used,
                "elapsed_ms": response.elapsed_ms,
            }

        result = self.parse_response(response.content)
        result["tokens_used"] = response.tokens_used
        result["model"] = response.model
        result["elapsed_ms"] = response.elapsed_ms
        return result
