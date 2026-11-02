"""SpaceCDF — optional AI drafting API (off by default).

SpaceCDF designs with deterministic engines; see docs/RULES_AND_AI.md. Only three
prose capabilities remain, all optional and never required by a workflow:

  * ``critique_need`` / ``general`` → genai ``design_advisor`` (stakeholder-text
    critique, free Q&A);
  * ``write_requirements`` → ``requirements_decomposition`` (polish objectives into
    shall statements);
  * ``narrative`` → ``report_narrative`` (document prose).

Kill switch: when ``configs/genai.yaml`` has ``enabled: false`` (the default) or the
capability is off, every call answers **503** before any model or key is touched —
for the spacecdf-ai service and for the legacy direct path alike. Retired
capabilities (trade, design review, component recommendation, ConOps) answer
**410** and name the deterministic endpoint that replaced them.

Every AI answer passes ``services.ai_output_checks`` (EARS / INCOSE checks) and is
returned with ``rule_checks``; nothing is shown unchecked.

API key resolution: X-API-Key header > ANTHROPIC_API_KEY env var. The key is never
stored on the server.
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..services.ai_advisor import (
    GENAI_CAPABILITY, ask_ai, genai_allows, genai_settings, get_token_budget,
    is_ai_available, reset_token_budget,
)
from ..services.ai_output_checks import check_ai_output

#: router capability -> what replaced it (deterministic). Answered with 410.
RETIRED: dict[str, dict[str, Any]] = {
    "review_design": {"use": "/api/studies/{study_id}/rules/gates/{gate}",
                      "en": "Design review is done by the rule engines (margins, CDS, requirement quality, FMECA, gate checks).",
                      "fr": "La revue de conception est faite par les moteurs de règles (marges, CDS, qualité des exigences, AMDEC, revues)."},
    "analyze_trade": {"use": "/api/lifecycle/trade-study",
                      "en": "Trade studies are scored by the weighted tabular trade engine.",
                      "fr": "Les études de compromis sont notées par le moteur de compromis pondéré."},
    "recommend_component": {"use": "/api/engineering/equipment/needs/{study_id}; /api/engineering/equipment/check-compatibility",
                            "en": "Component choice uses the knowledge base fit-gap and compatibility checks.",
                            "fr": "Le choix des composants utilise l’analyse d’adéquation et les contrôles de compatibilité de la base."},
    "generate_conops": {"use": "/api/design/quick-design (default ConOps from the mission requirements)",
                        "en": "The ConOps skeleton (phases, modes, CDS timers) is generated from rules.",
                        "fr": "Le squelette du ConOps (phases, modes, délais CDS) est généré par des règles."},
}

_DISABLED = {"code": "genai_disabled",
             "message": {"en": "AI is switched off (configs/genai.yaml). SpaceCDF works fully without it.",
                         "fr": "L’IA est désactivée (configs/genai.yaml). SpaceCDF fonctionne entièrement sans elle."}}

_HINT_CAPABILITIES = {"critique_need"}

router = APIRouter()


class AIRequest(BaseModel):
    """Request body for AI advisor endpoints."""
    capability: str = Field(description="critique_need / write_requirements / narrative / general")
    context: dict[str, Any] = Field(default_factory=dict, description="Design context (mission_need, requirements, parameters)")
    question: str = Field(default="", description="Optional specific question")
    max_tokens: int = Field(default=1500, le=4000)
    session_id: str = Field(default="default")
    language: Literal["en", "fr"] | None = Field(
        default=None,
        description="UI language of the requesting browser. 'fr' makes the model answer in French; "
                    "omitted → genai.yaml output.language → 'en'.",
    )


def _gate(capability: str) -> str:
    """Kill switch + retirement check. Returns the router capability to run."""
    if capability in RETIRED:
        r = RETIRED[capability]
        raise HTTPException(status_code=410, detail={"code": "retired", "capability": capability,
                                                     "use": r["use"], "message": {"en": r["en"], "fr": r["fr"]}})
    cap = capability if capability in GENAI_CAPABILITY else "general"
    if not genai_allows(cap):
        raise HTTPException(status_code=503, detail={**_DISABLED, "capability": cap})
    return cap


@router.get("/status")
async def ai_status() -> dict:
    """AI switch state, availability and the current token budget."""
    s = genai_settings()
    available = is_ai_available()
    budget = get_token_budget()
    return {
        "enabled": s["enabled"],
        "available": available,
        "mode": "ai_assisted" if available else "manual",
        "capabilities": {k: bool(s["enabled"] and v) for k, v in s["capabilities"].items()},
        "retired": sorted(RETIRED),
        "budget": {
            "limit": budget.limit,
            "used": budget.used,
            "remaining": budget.remaining,
            "requests": budget.requests,
            "estimated_cost_usd": round(budget.estimated_cost_usd, 4),
            "exhausted": budget.exhausted,
        },
    }


@router.get("/capabilities")
async def ai_capabilities(request: Request) -> dict:
    """Capability status from AIService, if installed."""
    ai_service = getattr(request.app.state, "ai_service", None)
    if ai_service is None:
        s = genai_settings()
        return {"available": False, "message": "spacecdf-ai package is not installed",
                "enabled": s["enabled"], "capabilities": {}}
    status = ai_service.get_status()
    return {"available": True, **status}


async def _run(cap: str, context: dict[str, Any], question: str, *, request: Request | None,
               api_key: str | None, session_id: str, max_tokens: int, language: str | None) -> dict[str, Any]:
    """Run one allowed capability (AIService if installed, else the legacy path) and rule-check it."""
    ai_service = getattr(request.app.state, "ai_service", None) if request is not None else None
    if ai_service is not None:
        mapped = GENAI_CAPABILITY[cap]
        kwargs: dict[str, Any] = {"context": context, "question": question, "max_tokens": max_tokens}
        if cap in _HINT_CAPABILITIES:
            kwargs["capability_hint"] = cap
        result = await ai_service.run(mapped, api_key=api_key, session_id=session_id,
                                      ui_language=language, **kwargs)
        out = {
            "content": result.get("content", ""),
            "capability": cap,
            "model": result.get("model", ""),
            "tokens_used": result.get("tokens_used", 0),
            "elapsed_ms": round(result.get("elapsed_ms", 0), 0),
            "error": result.get("error") or (result.get("message") if not result.get("ai_available") else None),
        }
        if isinstance(result.get("requirements"), list):
            out["requirements"] = result["requirements"]
    else:
        response = await ask_ai(capability=cap, context=context, question=question, api_key=api_key,
                                session_id=session_id, max_tokens=max_tokens, language=language)
        out = {"content": response.content, "capability": response.capability, "model": response.model,
               "tokens_used": response.tokens_used, "elapsed_ms": round(response.elapsed_ms, 0),
               "error": response.error}
    if not out.get("error"):
        out = check_ai_output(cap, out, language)
    return out


@router.post("/ask")
async def ai_ask(
    req: AIRequest,
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """Ask the (optional) AI with design context. 503 when AI is off; 410 for retired capabilities."""
    cap = _gate(req.capability)
    return await _run(cap, req.context, req.question, request=request, api_key=x_api_key,
                      session_id=req.session_id, max_tokens=req.max_tokens, language=req.language)


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


# --- Convenience endpoints ----------------------------------------------------

@router.post("/critique-need")
async def critique_need(
    context: dict[str, Any],
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    language: Literal["en", "fr"] | None = Query(default=None, description="UI language; 'fr' → French answer"),
) -> dict:
    """Critique the mission need statement (prose). The MCR gate checks are the deterministic part."""
    cap = _gate("critique_need")
    return await _run(cap, context, "", request=request, api_key=x_api_key, session_id="default",
                      max_tokens=1500, language=language)


@router.post("/write-requirements")
async def write_requirements(
    context: dict[str, Any],
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    language: Literal["en", "fr"] | None = Query(default=None, description="UI language; 'fr' → French answer"),
) -> dict:
    """Polish objectives into shall statements; every statement comes back rule-checked."""
    cap = _gate("write_requirements")
    return await _run(cap, context, "", request=request, api_key=x_api_key, session_id="default",
                      max_tokens=1500, language=language)


@router.post("/review-design")
async def review_design(context: dict[str, Any]) -> dict:
    """Retired: design review is deterministic (410 with the replacement endpoint)."""
    _gate("review_design")
    return {}  # pragma: no cover — _gate always raises for a retired capability
