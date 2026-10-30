"""Wiring Generation — harness diagrams and KiCad schematics from interface matrix."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_study_context


class WiringCapability(BaseCapability):
    name = "wiring_generation"
    prompt_file = "kicad_schematic.txt"
    model_tier = "heavy"

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        interfaces: list[dict] | None = None,
        output_format: str = "kicad",
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        parts.append(f"Generate a {output_format} wiring diagram for this spacecraft.\n")

        if study:
            ctx = build_study_context(study, elements, budgets)
            parts.append(ctx)

        if interfaces:
            parts.append(f"\n## Interface Matrix ({len(interfaces)} connections)")
            for ifc in interfaces:
                src = ifc.get("source_name", ifc.get("source_id", "?"))
                tgt = ifc.get("target_name", ifc.get("target_id", "?"))
                itype = ifc.get("type", "?")
                props = ifc.get("properties", {})
                parts.append(
                    f"- {src} -> {tgt} [{itype}] "
                    f"voltage={props.get('voltage_v', '?')}V "
                    f"current={props.get('current_a', '?')}A "
                    f"protocol={props.get('protocol', '?')}"
                )

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        # Split schematic and harness summary
        schematic = content
        harness_summary = None

        if "---HARNESS_SUMMARY---" in content:
            parts = content.split("---HARNESS_SUMMARY---", 1)
            schematic = parts[0].strip()
            harness_summary = parts[1].strip()

        return {
            "content": content,
            "schematic": schematic,
            "harness_summary": harness_summary,
            "format": "kicad_sch",
        }
