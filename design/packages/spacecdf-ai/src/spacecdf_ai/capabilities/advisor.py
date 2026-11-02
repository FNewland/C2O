"""Design Advisor — general SE chat capability."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_study_context


class DesignAdvisorCapability(BaseCapability):
    name = "design_advisor"
    prompt_file = "se_advisor.txt"
    model_tier = "default"

    def build_user_message(
        self,
        question: str = "",
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        requirements: list[dict] | None = None,
        capability_hint: str = "general",
        mission_need: dict | None = None,
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        # Capability-specific framing
        hints = {
            "critique_need": "Review this mission need statement. Identify gaps, ambiguities, and missing stakeholders.",
        }
        if capability_hint in hints:
            parts.append(hints[capability_hint])

        # Context
        if study:
            ctx = build_study_context(
                study, elements, budgets, requirements,
                max_elements=self.config.budget.max_context_elements,
            )
            parts.append(f"\n--- DESIGN CONTEXT ---\n{ctx}")

        # Stakeholders are what a need critique is mostly about.
        stakeholders = (mission_need or (study or {}).get("mission_need") or {}).get("stakeholders") or []
        if stakeholders:
            parts.append("\n--- STAKEHOLDERS ---")
            for sh in stakeholders[:20]:
                needs = "; ".join(str(n) for n in (sh.get("needs") or [])[:5])
                parts.append(f"- {sh.get('name', '?')} ({sh.get('role', '?')}): {needs}")

        # Question
        if question:
            parts.append(f"\n--- QUESTION ---\n{question}")

        return "\n".join(parts) or "Describe the current design status and provide SE recommendations."
