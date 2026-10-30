"""Anthropic client wrapper with lazy initialization and rate limiting.

The client is created on first use, not at import time, so the server
starts cleanly even without an API key configured.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import anthropic

from spacecdf_ai.config import GenAIConfig

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structured response from an AI call."""
    content: str
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    capability: str = ""
    elapsed_ms: float = 0
    error: str | None = None


@dataclass
class UsageTracker:
    """Per-session token and cost tracking."""
    tokens: int = 0
    requests: int = 0
    cost_usd: float = 0.0
    _request_times: list[float] = field(default_factory=list)

    def record(self, input_tokens: int, output_tokens: int, model: str) -> None:
        total = input_tokens + output_tokens
        self.tokens += total
        self.requests += 1
        self._request_times.append(time.monotonic())
        # Cost estimation per 1M tokens (blended input+output)
        rates = {
            "claude-opus-4-6": 30.0,
            "claude-sonnet-4-6": 6.0,
            "claude-haiku-4-5-20251001": 1.0,
        }
        rate = rates.get(model, 6.0)
        self.cost_usd += total * rate / 1_000_000

    def rpm_in_window(self, window_seconds: float = 60.0) -> int:
        """Count requests in the last N seconds."""
        cutoff = time.monotonic() - window_seconds
        self._request_times = [t for t in self._request_times if t > cutoff]
        return len(self._request_times)


class AIClient:
    """Manages Anthropic API calls with rate limiting and usage tracking.

    Lazily initializes the anthropic.Anthropic client on first call.
    """

    def __init__(self, config: GenAIConfig) -> None:
        self.config = config
        self._client: anthropic.Anthropic | None = None
        self._async_client: anthropic.AsyncAnthropic | None = None
        self._usage: dict[str, UsageTracker] = {}
        self._lock = asyncio.Lock()

    def _get_client(self, api_key: str | None = None) -> anthropic.Anthropic:
        """Get or create synchronous client."""
        key = api_key or self.config.api_key
        if not key:
            raise ValueError(
                "No API key. Set ANTHROPIC_API_KEY in environment "
                "or pass via X-API-Key header."
            )
        if self._client is None or api_key:
            self._client = anthropic.Anthropic(api_key=key)
        return self._client

    def _get_async_client(self, api_key: str | None = None) -> anthropic.AsyncAnthropic:
        """Get or create async client."""
        key = api_key or self.config.api_key
        if not key:
            raise ValueError(
                "No API key. Set ANTHROPIC_API_KEY in environment "
                "or pass via X-API-Key header."
            )
        if self._async_client is None or api_key:
            self._async_client = anthropic.AsyncAnthropic(api_key=key)
        return self._async_client

    def _get_tracker(self, session_id: str) -> UsageTracker:
        if session_id not in self._usage:
            self._usage[session_id] = UsageTracker()
        return self._usage[session_id]

    async def call(
        self,
        *,
        system: str,
        user_message: str,
        capability: str = "general",
        model: str | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
        session_id: str = "default",
    ) -> AIResponse:
        """Make an AI API call with rate limiting and usage tracking.

        Args:
            system: System prompt text
            user_message: User message content
            capability: Capability name (for tracking)
            model: Model override (default from config)
            max_tokens: Max output tokens (default from config budget)
            api_key: Per-request API key override
            session_id: For usage tracking and budget enforcement
        """
        resolved_model = model or self.config.model
        resolved_max = max_tokens or self.config.budget.max_tokens_per_call

        # Check budget
        tracker = self._get_tracker(session_id)
        if tracker.tokens >= self.config.budget.session_token_limit:
            return AIResponse(
                content="", capability=capability,
                error=f"Session token budget exhausted ({tracker.tokens}/{self.config.budget.session_token_limit}). "
                      f"Reset budget or increase session_token_limit in genai.yaml."
            )

        # Check rate limit
        if tracker.rpm_in_window() >= self.config.budget.rate_limit_rpm:
            return AIResponse(
                content="", capability=capability,
                error=f"Rate limit reached ({self.config.budget.rate_limit_rpm} req/min). Please wait."
            )

        start = time.monotonic()
        try:
            client = self._get_async_client(api_key)
            response = await client.messages.create(
                model=resolved_model,
                max_tokens=resolved_max,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )

            elapsed = (time.monotonic() - start) * 1000
            content = response.content[0].text if response.content else ""
            input_tok = response.usage.input_tokens
            output_tok = response.usage.output_tokens

            tracker.record(input_tok, output_tok, resolved_model)

            return AIResponse(
                content=content,
                tokens_used=input_tok + output_tok,
                input_tokens=input_tok,
                output_tokens=output_tok,
                model=resolved_model,
                capability=capability,
                elapsed_ms=elapsed,
            )

        except anthropic.AuthenticationError:
            return AIResponse(
                content="", capability=capability,
                error="Invalid API key. Check your ANTHROPIC_API_KEY.",
                elapsed_ms=(time.monotonic() - start) * 1000,
            )
        except anthropic.RateLimitError:
            return AIResponse(
                content="", capability=capability,
                error="Anthropic rate limit exceeded. Wait a moment and retry.",
                elapsed_ms=(time.monotonic() - start) * 1000,
            )
        except Exception as e:
            logger.error("AI call failed (%s): %s", capability, e)
            return AIResponse(
                content="", capability=capability,
                error=str(e),
                elapsed_ms=(time.monotonic() - start) * 1000,
            )

    def get_usage(self, session_id: str = "default") -> dict:
        """Get usage stats for a session."""
        tracker = self._get_tracker(session_id)
        return {
            "tokens_used": tracker.tokens,
            "token_limit": self.config.budget.session_token_limit,
            "tokens_remaining": max(0, self.config.budget.session_token_limit - tracker.tokens),
            "requests": tracker.requests,
            "estimated_cost_usd": round(tracker.cost_usd, 4),
            "rpm_current": tracker.rpm_in_window(),
            "rpm_limit": self.config.budget.rate_limit_rpm,
        }

    def reset_usage(self, session_id: str = "default") -> None:
        """Reset usage for a session."""
        self._usage.pop(session_id, None)
