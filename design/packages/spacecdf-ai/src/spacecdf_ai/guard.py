"""GenAI capability guard — the key pattern for optional AI integration.

Usage::

    from spacecdf_ai import requires_genai

    @requires_genai("cad_scripting")
    async def generate_cad_model(study_id: str, format: str = "cadquery"):
        # This only runs when genai.enabled=true AND cad_scripting=true
        ...

    @generate_cad_model.fallback
    async def generate_cad_model_fallback(study_id: str, format: str = "cadquery"):
        return {"ai_available": False, "message": "CAD generation requires GenAI"}

When the capability is disabled, the guard returns either the registered
fallback or a standard "not available" response.  This keeps AI checks
out of business logic entirely.
"""
from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Coroutine

from spacecdf_ai.config import load_genai_config

logger = logging.getLogger(__name__)

# Standard disabled response
_DISABLED_RESPONSE = {
    "ai_available": False,
    "content": "",
}


def requires_genai(capability: str):
    """Decorator that gates a function behind a GenAI capability toggle.

    When the capability is disabled:
    - If a .fallback is registered, calls that instead
    - Otherwise returns {"ai_available": False, "capability": <name>}

    When enabled, calls the decorated function normally.
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable:
        _fallback: Callable | None = None

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            config = load_genai_config()
            if not config.is_capable(capability):
                if _fallback is not None:
                    return await _fallback(*args, **kwargs)
                return {
                    **_DISABLED_RESPONSE,
                    "capability": capability,
                    "message": f"GenAI capability '{capability}' is disabled. "
                               f"Enable it in configs/genai.yaml",
                }
            return await func(*args, **kwargs)

        def fallback(fb_func: Callable) -> Callable:
            nonlocal _fallback
            _fallback = fb_func
            return fb_func

        wrapper.fallback = fallback  # type: ignore[attr-defined]
        return wrapper
    return decorator
