"""SpaceCDF — AI Advisor Service (legacy direct path, used when spacecdf-ai is absent).

SpaceCDF designs with deterministic engines (docs/RULES_AND_AI.md). AI is off by
default and limited to three optional prose tasks:

  - critique_need / general: critique of stakeholder and mission-need prose, free Q&A
  - write_requirements: polish free-text objectives into shall statements
  - narrative: narrative / executive-summary prose for documents

The kill switch is ``configs/genai.yaml`` ``genai.enabled`` (plus the per-capability
toggle): ``genai_allows()`` is checked by the router AND inside ``ask_ai`` so that
no key, header or environment variable can bypass it.

Token budget system prevents runaway costs. API key from environment
or per-request header (never stored in code/git).
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from spacecdf_common.language import apply_language, normalize_language

logger = logging.getLogger(__name__)

# Token usage tracking
_session_usage: dict[str, dict] = {}  # session_id -> {tokens_used, requests, cost_usd}


@dataclass
class AIResponse:
    """Response from the AI advisor."""
    content: str
    tokens_used: int = 0
    model: str = ""
    capability: str = ""
    elapsed_ms: float = 0
    error: str | None = None


@dataclass
class TokenBudget:
    """Token budget for AI usage control."""
    limit: int = 100_000
    used: int = 0
    remaining: int = 100_000
    requests: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def exhausted(self) -> bool:
        return self.used >= self.limit


# System prompt with space mission engineering context
SYSTEM_PROMPT = """You are an AI advisor embedded in SpaceCDF, an AI-supported Concurrent Design Facility for space missions. You assist systems engineers with mission design decisions.

Your knowledge covers:
- NASA Systems Engineering Handbook (SP-2016-6105 Rev2) — all 17 SE processes
- ECSS standards (M-ST-10C, E-ST-10C, etc.) — European space engineering standards
- CubeSat Design Specification (Cal Poly CDS)
- Space mission design: orbital mechanics, power systems, AOCS, comms, thermal, structures, propulsion
- COTS CubeSat components from GomSpace, Endurosat, CubeSpace, ISIS, Enpulsion, ThrustMe, etc.
- Cost estimation (NASA CEH, SSCM parametric models)
- Space debris mitigation (ECSS-U-AS-10C, 25-year/5-year rules)

Respond concisely and technically. When critiquing, be constructive — identify what's missing or weak and suggest specific improvements. When generating requirements, use proper "shall" form per NASA SEH Appendix C.

Current design context will be provided with each request."""


# Capability-specific prompts
CAPABILITY_PROMPTS: dict[str, str] = {
    "critique_need": (
        "Review this mission need statement and stakeholder analysis. "
        "Identify: (1) Is the problem clearly defined? (2) Are stakeholders complete? "
        "(3) Are objectives measurable? (4) What's missing? Be specific and constructive."
    ),
    "write_requirements": (
        "Rewrite these objectives as formal requirements, one 'shall' per requirement, "
        "using an EARS pattern (The <system> shall ...; When <trigger>, the <system> shall ...). "
        "Give every numeric value a unit and a bound. Do not use vague terms, escape clauses "
        "or TBD. SpaceCDF checks every statement against EARS and INCOSE rules afterwards."
    ),
    "narrative": (
        "Write the requested document section as clear technical prose from the design data "
        "given. Do not invent numbers: use only values present in the context."
    ),
    "general": (
        "Answer this space mission engineering question. Be specific, cite relevant "
        "standards (ECSS/NASA) where applicable, and provide actionable advice."
    ),
}

#: router / legacy capability name -> genai.yaml capability key
GENAI_CAPABILITY: dict[str, str] = {
    "critique_need": "design_advisor",
    "general": "design_advisor",
    "write_requirements": "requirements_decomposition",
    "narrative": "report_narrative",
}


# ─── Kill switch ──────────────────────────────────────────────────────────────

def _genai_yaml() -> Path | None:
    env = os.environ.get("GENAI_CONFIG")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        p = parent / "configs" / "genai.yaml"
        if p.is_file():
            return p
    return None


def genai_settings() -> dict[str, Any]:
    """{enabled, capabilities, model, max_tokens_per_call} from genai.yaml.

    Uses spacecdf_ai's validated loader when the package is installed, else reads
    the YAML directly. A missing or unreadable file means AI is disabled.
    """
    try:
        from spacecdf_ai.config import RETAINED_CAPABILITIES, load_genai_config
        cfg = load_genai_config()
        return {"enabled": bool(cfg.enabled),
                "capabilities": {k: bool(v) for k, v in cfg.capabilities.items() if k in RETAINED_CAPABILITIES},
                "model": cfg.model, "max_tokens_per_call": cfg.budget.max_tokens_per_call}
    except ImportError:
        pass
    path = _genai_yaml()
    raw: dict[str, Any] = {}
    if path and path.is_file():
        try:
            import yaml
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            raw = data.get("genai", data) if isinstance(data, dict) else {}
        except Exception as exc:  # noqa: BLE001 — a broken file must disable AI, not crash
            logger.warning("genai.yaml unreadable (%s): AI disabled", exc)
            raw = {}
    retained = set(GENAI_CAPABILITY.values())
    return {"enabled": raw.get("enabled") is True,
            "capabilities": {k: bool(v) for k, v in (raw.get("capabilities") or {}).items() if k in retained},
            "model": raw.get("model") or "claude-sonnet-4-6",
            "max_tokens_per_call": int((raw.get("budget") or {}).get("max_tokens_per_call") or 4096)}


def genai_allows(capability: str) -> bool:
    """The single kill-switch test: master switch on AND the mapped capability on."""
    s = genai_settings()
    key = GENAI_CAPABILITY.get(capability, capability)
    return bool(s["enabled"] and s["capabilities"].get(key, False))


async def ask_ai(
    capability: str,
    context: dict[str, Any],
    question: str = "",
    api_key: str | None = None,
    session_id: str = "default",
    model: str | None = None,
    max_tokens: int = 1500,
    language: str | None = None,
) -> AIResponse:
    """Ask the AI advisor a question with design context.

    Args:
        capability: One of the CAPABILITY_PROMPTS keys
        context: Design context (mission need, requirements, parameters, etc.)
        question: Optional specific question (appended to capability prompt)
        api_key: API key (from header or environment)
        session_id: For token budget tracking
        model: Override model (default from env)
        max_tokens: Max response tokens
        language: UI language ('en'/'fr'); 'fr' asks the model to answer in
            French. None/unknown → English (system prompt unchanged).

    Returns:
        AIResponse with content and usage stats
    """
    # Kill switch first: no key, header or env var can bypass genai.enabled: false.
    if not genai_allows(capability):
        return AIResponse(content="", capability=capability,
                          error="AI is disabled (configs/genai.yaml genai.enabled: false or capability off).")

    # Resolve API key: header > environment
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return AIResponse(
            content="", capability=capability,
            error="No API key. Set ANTHROPIC_API_KEY in .env or pass via X-API-Key header."
        )

    # Check token budget
    budget = get_token_budget(session_id)
    if budget.exhausted:
        return AIResponse(
            content="", capability=capability,
            error=f"Token budget exhausted ({budget.used}/{budget.limit} tokens used). Reset or increase budget."
        )

    # Build prompt
    capability_prompt = CAPABILITY_PROMPTS.get(capability, CAPABILITY_PROMPTS["general"])
    context_str = _format_context(context)
    user_message = f"{capability_prompt}\n\n--- DESIGN CONTEXT ---\n{context_str}"
    if question:
        user_message += f"\n\n--- SPECIFIC QUESTION ---\n{question}"

    # Call Claude
    settings = genai_settings()
    resolved_model = model or os.environ.get("AI_MODEL") or settings["model"]
    max_tokens = min(max_tokens, settings["max_tokens_per_call"])
    start = time.monotonic()

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model=resolved_model,
            max_tokens=max_tokens,
            system=build_system_prompt(language),
            messages=[{"role": "user", "content": user_message}],
        )

        elapsed = (time.monotonic() - start) * 1000
        content = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens

        # Update budget
        _track_usage(session_id, total_tokens, resolved_model)

        return AIResponse(
            content=content,
            tokens_used=total_tokens,
            model=resolved_model,
            capability=capability,
            elapsed_ms=elapsed,
        )

    except Exception as e:
        logger.error("AI advisor error: %s", e)
        return AIResponse(
            content="", capability=capability,
            error=str(e),
            elapsed_ms=(time.monotonic() - start) * 1000,
        )


def build_system_prompt(language: str | None = None) -> str:
    """SYSTEM_PROMPT plus the output-language instruction ('en' → unchanged)."""
    return apply_language(SYSTEM_PROMPT, normalize_language(language))


def get_token_budget(session_id: str = "default") -> TokenBudget:
    """Get current token budget for a session."""
    limit = int(os.environ.get("AI_TOKEN_BUDGET", "100000"))
    usage = _session_usage.get(session_id, {"tokens": 0, "requests": 0, "cost_usd": 0})
    return TokenBudget(
        limit=limit,
        used=usage.get("tokens", 0),
        remaining=max(0, limit - usage.get("tokens", 0)),
        requests=usage.get("requests", 0),
        estimated_cost_usd=usage.get("cost_usd", 0),
    )


def reset_token_budget(session_id: str = "default") -> None:
    """Reset token budget for a session."""
    _session_usage.pop(session_id, None)


def _track_usage(session_id: str, tokens: int, model: str) -> None:
    """Track token usage and estimated cost."""
    if session_id not in _session_usage:
        _session_usage[session_id] = {"tokens": 0, "requests": 0, "cost_usd": 0}

    usage = _session_usage[session_id]
    usage["tokens"] += tokens
    usage["requests"] += 1

    # Cost estimation (approximate, per 1M tokens)
    cost_per_million = {
        "claude-sonnet-4-20250514": 3.0,   # $3/M input, $15/M output — blended ~$6
        "claude-haiku-4-5-20251001": 0.25,
    }
    rate = cost_per_million.get(model, 5.0)
    usage["cost_usd"] += tokens * rate / 1_000_000


def _format_context(context: dict[str, Any]) -> str:
    """Format design context for the AI prompt."""
    parts: list[str] = []

    if "mission_need" in context:
        mn = context["mission_need"]
        if isinstance(mn, dict):
            if mn.get("problem_statement"):
                parts.append(f"Problem: {mn['problem_statement']}")
            if mn.get("stakeholders"):
                parts.append(f"Stakeholders: {len(mn['stakeholders'])} identified")
                for sh in mn["stakeholders"][:3]:
                    parts.append(f"  - {sh.get('name', '?')} ({sh.get('role', '?')}): {', '.join(sh.get('needs', [])[:2])}")
            if mn.get("objectives"):
                parts.append(f"Objectives: {len(mn['objectives'])}")
                for obj in mn["objectives"][:5]:
                    parts.append(f"  - [{obj.get('priority', '?')}] {obj.get('text', '?')}")

    if "requirements" in context:
        req = context["requirements"]
        if isinstance(req, dict):
            parts.append(f"Spacecraft class: {req.get('spacecraft_class', '?')}")
            orbit = req.get("orbit", {})
            parts.append(f"Orbit: {orbit.get('orbit_type', '?')} at {orbit.get('altitude_km', '?')} km, {orbit.get('inclination_deg', '?')}°")
            for i, pl in enumerate(req.get("payloads", [])[:3]):
                parts.append(f"Payload {i}: {pl.get('name', '?')} — {pl.get('mass_kg', '?')} kg, {pl.get('power_w', '?')} W")

    if "parameters" in context:
        params = context["parameters"]
        if isinstance(params, dict):
            key_params = ["mass.dry_mass_kg", "mass.wet_mass_kg", "power.sa_power_eol_w",
                          "link.downlink_margin_db", "cost.total_meur",
                          "systems.mass_margin_percent", "systems.power_margin_percent",
                          "sustainability.grade", "reliability.mission_reliability"]
            for pid in key_params:
                p = params.get(pid)
                if p:
                    val = p.value if hasattr(p, "value") else (p.get("value") if isinstance(p, dict) else p)
                    parts.append(f"  {pid}: {val}")

    if "question" in context:
        parts.append(f"\nDesigner's question: {context['question']}")

    return "\n".join(parts) if parts else "No design context provided."


def is_ai_enabled() -> bool:
    """genai.yaml master switch (the key is irrelevant to this answer)."""
    return bool(genai_settings()["enabled"])


def is_ai_available() -> bool:
    """AI can actually answer: switched on in genai.yaml AND a server key is configured."""
    return is_ai_enabled() and bool(os.environ.get("ANTHROPIC_API_KEY", ""))
