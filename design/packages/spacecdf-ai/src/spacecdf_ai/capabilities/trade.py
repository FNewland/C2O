"""Trade Analysis — structured trade study evaluation."""
from __future__ import annotations

import json
from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_study_context


class TradeCapability(BaseCapability):
    name = "trade_analysis"
    prompt_file = "trade_study.txt"
    model_tier = "default"

    def build_user_message(
        self,
        decision: str = "",
        alternatives: list[dict] | None = None,
        criteria: list[str] | None = None,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        parts.append(f"Trade Study: {decision}\n")

        if alternatives:
            parts.append("Alternatives:")
            for alt in alternatives:
                name = alt.get("name", "?")
                desc = alt.get("description", "")
                parts.append(f"- {name}: {desc}")

        if criteria:
            parts.append(f"\nEvaluation criteria: {', '.join(criteria)}")

        if study:
            ctx = build_study_context(study, elements, budgets)
            parts.append(f"\nDesign context:\n{ctx}")

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        # Try to extract JSON trade study result
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end > start:
                result = json.loads(content[start:end + 1])
                return {"content": content, "trade_result": result}
        except json.JSONDecodeError:
            pass
        return {"content": content}
