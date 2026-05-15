"""FMEA Generation — AI-assisted failure mode analysis."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.capabilities.consistency import _extract_json_array
from spacecdf_ai.context import build_study_context


class FMEACapability(BaseCapability):
    name = "fmea_generation"
    prompt_file = "fmea.txt"
    model_tier = "default"

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        **kwargs: Any,
    ) -> str:
        parts = ["Generate FMECA for this spacecraft design.\n"]
        if study:
            ctx = build_study_context(study, elements)
            parts.append(ctx)
        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        fmea_rows = _extract_json_array(content)
        spf_count = sum(1 for r in fmea_rows if r.get("criticality") == "SPF")
        high_rpn = [r for r in fmea_rows if r.get("rpn", 0) > 100]
        return {
            "content": content,
            "fmea_rows": fmea_rows,
            "total_failure_modes": len(fmea_rows),
            "single_point_failures": spf_count,
            "high_rpn_count": len(high_rpn),
        }
