"""Cost Estimation — parametric cost with AI sanity checking."""
from __future__ import annotations

import json
from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_study_context


class CostCapability(BaseCapability):
    name = "cost_estimation"
    prompt_file = "cost_estimation.txt"
    model_tier = "default"

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        existing_cost: dict | None = None,
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        if study:
            ctx = build_study_context(study, elements, budgets)
            parts.append(f"Design data:\n{ctx}")

        if existing_cost:
            parts.append(f"\nExisting parametric cost estimate: {json.dumps(existing_cost, indent=2)}")
            parts.append("\nReview and refine this estimate. Flag any subsystems that seem over/under-estimated.")
        else:
            parts.append("\nGenerate a parametric cost estimate for this spacecraft.")

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end > start:
                result = json.loads(content[start:end + 1])
                return {"content": content, "cost_estimate": result}
        except json.JSONDecodeError:
            pass
        return {"content": content}
