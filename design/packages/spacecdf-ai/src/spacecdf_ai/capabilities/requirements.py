"""Requirements Decomposition — mission statement to L0/L1 requirements."""
from __future__ import annotations

import json
from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.capabilities.consistency import _extract_json_array
from spacecdf_ai.context import build_study_context


class RequirementsCapability(BaseCapability):
    name = "requirements_decomposition"
    prompt_file = "requirements.txt"
    model_tier = "default"

    def build_user_message(
        self,
        study: dict | None = None,
        mission_need: dict | None = None,
        existing_requirements: list[dict] | None = None,
        target_level: str = "system",
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        parts.append(f"Generate {target_level}-level requirements from the following mission definition.\n")

        if study:
            ctx = build_study_context(study)
            parts.append(ctx)
        elif mission_need:
            if mission_need.get("problem_statement"):
                parts.append(f"Problem Statement: {mission_need['problem_statement']}")
            if mission_need.get("objectives"):
                parts.append("\nObjectives:")
                for obj in mission_need["objectives"]:
                    parts.append(f"- [{obj.get('priority', '?')}] {obj.get('text', '?')}")

        if existing_requirements:
            parts.append(f"\nExisting requirements ({len(existing_requirements)}):")
            for req in existing_requirements[:20]:
                parts.append(f"- [{req.get('id', '?')}] {req.get('text', '?')}")
            parts.append("\nDerive NEW requirements that complement (not duplicate) the above.")

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        requirements = _extract_json_array(content)
        return {
            "content": content,
            "requirements": requirements,
            "count": len(requirements),
        }
