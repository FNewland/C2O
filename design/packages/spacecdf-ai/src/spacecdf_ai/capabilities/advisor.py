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
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        # Capability-specific framing
        hints = {
            "critique_need": "Review this mission need statement. Identify gaps, ambiguities, and missing stakeholders.",
            "write_requirements": "Generate formal requirements in 'shall' form from the objectives below.",
            "analyze_trade": "Evaluate these design alternatives and recommend the best option.",
            "generate_conops": "Generate a Concept of Operations for this mission.",
            "review_design": "Review this spacecraft design from a systems engineering perspective.",
            "recommend_component": "Recommend the best COTS component for the specified requirement.",
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

        # Question
        if question:
            parts.append(f"\n--- QUESTION ---\n{question}")

        return "\n".join(parts) or "Describe the current design status and provide SE recommendations."
