"""Consistency Checking — cross-domain design review."""
from __future__ import annotations

import json
from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_review_context


class ConsistencyCapability(BaseCapability):
    name = "consistency_checking"
    prompt_file = "consistency.txt"
    model_tier = "heavy"  # Needs deep reasoning over full design

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        requirements: list[dict] | None = None,
        interfaces: list[dict] | None = None,
        conops: dict | None = None,
        conflicts: list[dict] | None = None,
        **kwargs: Any,
    ) -> str:
        ctx = build_review_context(
            study or {},
            elements=elements,
            budgets=budgets,
            requirements=requirements,
            interfaces=interfaces,
            conops=conops,
            conflicts=conflicts,
            max_elements=self.config.budget.max_context_elements,
        )
        return (
            "Perform a comprehensive consistency review of this spacecraft design.\n\n"
            f"{ctx}"
        )

    def parse_response(self, content: str) -> dict[str, Any]:
        """Extract JSON array of issues from response."""
        issues = _extract_json_array(content)
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 2))
        return {
            "content": content,
            "issues": issues,
            "critical_count": sum(1 for i in issues if i.get("severity") == "critical"),
            "warning_count": sum(1 for i in issues if i.get("severity") == "warning"),
            "total_count": len(issues),
        }


def _extract_json_array(text: str) -> list[dict]:
    """Extract a JSON array from text that may contain markdown fences."""
    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code block
    import re
    match = re.search(r"```(?:json)?\s*\n(\[.*?\])\s*\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding array anywhere in text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return []
