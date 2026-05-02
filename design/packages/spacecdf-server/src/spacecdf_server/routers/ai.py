"""SpaceCDF — AI Advisor API.

Endpoints for Claude-powered design assistance. Two modes:
  - Manual: AI endpoints return 503 (AI not available)
  - AI-assisted: Endpoints call Claude and return suggestions

API key resolution: X-API-Key header > ANTHROPIC_API_KEY env var.
The key is NEVER stored on the server — it's either in the user's
local .env or passed per-request from the frontend (stored in
browser localStorage only).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..services.ai_advisor import (
    ask_ai, get_token_budget, reset_token_budget, is_ai_available,
)

router = APIRouter()


class AIRequest(BaseModel):
    """Request body for AI advisor endpoints."""
    capability: str = Field(description="critique_need / write_requirements / analyze_trade / generate_conops / review_design / recommend_component / general")
    context: dict[str, Any] = Field(default_factory=dict, description="Design context (mission_need, requirements, parameters)")
    question: str = Field(default="", description="Optional specific question")
    max_tokens: int = Field(default=1500, le=4000)
    session_id: str = Field(default="default")


@router.get("/status")
async def ai_status() -> dict:
    """Check if AI advisor is available and current token budget."""
    available = is_ai_available()
    budget = get_token_budget()
    return {
        "available": available,
        "mode": "ai_assisted" if available else "manual",
        "budget": {
            "limit": budget.limit,
            "used": budget.used,
            "remaining": budget.remaining,
            "requests": budget.requests,
            "estimated_cost_usd": round(budget.estimated_cost_usd, 4),
            "exhausted": budget.exhausted,
        },
    }


@router.post("/ask")
async def ai_ask(
    req: AIRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """Ask the AI advisor a question with design context.

    The API key can be provided via:
    1. X-API-Key header (from frontend localStorage — preferred)
    2. ANTHROPIC_API_KEY environment variable (from .env)

    The key is NEVER stored on the server.
    """
    response = await ask_ai(
        capability=req.capability,
        context=req.context,
        question=req.question,
        api_key=x_api_key,
        session_id=req.session_id,
        max_tokens=req.max_tokens,
    )

    if response.error:
        return {
            "content": "",
            "error": response.error,
            "capability": response.capability,
            "tokens_used": 0,
        }

    return {
        "content": response.content,
        "capability": response.capability,
        "model": response.model,
        "tokens_used": response.tokens_used,
        "elapsed_ms": round(response.elapsed_ms, 0),
        "error": None,
    }


@router.get("/budget/{session_id}")
async def ai_budget(session_id: str = "default") -> dict:
    """Get token budget for a session."""
    budget = get_token_budget(session_id)
    return {
        "limit": budget.limit,
        "used": budget.used,
        "remaining": budget.remaining,
        "requests": budget.requests,
        "estimated_cost_usd": round(budget.estimated_cost_usd, 4),
        "exhausted": budget.exhausted,
    }


@router.post("/budget/{session_id}/reset")
async def ai_budget_reset(session_id: str = "default") -> dict:
    """Reset token budget for a session."""
    reset_token_budget(session_id)
    return {"reset": True, "session_id": session_id}


# --- Convenience endpoints for common AI tasks ---

@router.post("/critique-need")
async def critique_need(
    context: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """Critique the mission need statement — is the problem well-defined?"""
    response = await ask_ai("critique_need", context, api_key=x_api_key)
    return {"content": response.content, "error": response.error, "tokens_used": response.tokens_used}


@router.post("/write-requirements")
async def write_requirements(
    context: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """Generate formal requirements from objectives."""
    response = await ask_ai("write_requirements", context, api_key=x_api_key)
    return {"content": response.content, "error": response.error, "tokens_used": response.tokens_used}


@router.post("/review-design")
async def review_design(
    context: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """Review current design from a systems engineering perspective."""
    response = await ask_ai("review_design", context, api_key=x_api_key, max_tokens=2000)
    return {"content": response.content, "error": response.error, "tokens_used": response.tokens_used}
