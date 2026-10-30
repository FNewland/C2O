"""CAD Scripting — generate CadQuery/FreeCAD/Fusion 360 scripts from design data."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_study_context


class CADCapability(BaseCapability):
    name = "cad_scripting"
    prompt_file = "cad_cadquery.txt"
    model_tier = "heavy"  # Complex spatial reasoning

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        cad_format: str = "cadquery",
        configuration: str = "deployed",
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        parts.append(f"Generate a {cad_format} script for this spacecraft in {configuration} configuration.\n")

        if study:
            ctx = build_study_context(study, elements, budgets)
            parts.append(ctx)

        # Add mass/dimension data for realistic proportions
        if elements:
            parts.append("\n## Component Dimensions & Mass")
            for el in elements:
                props = el.get("properties", {})
                if props.get("mass_kg") or props.get("dimensions"):
                    parts.append(
                        f"- {el.get('name', '?')}: "
                        f"mass={props.get('mass_kg', '?')} kg, "
                        f"dims={props.get('dimensions', 'not specified')}"
                    )

        format_notes = {
            "cadquery": "Use CadQuery 2.x API. Export STEP at the end.",
            "freecad": "Use FreeCAD Python API (FreeCAD, Part, Draft modules).",
            "fusion360": "Use Fusion 360 Python API (adsk.core, adsk.fusion).",
            "openscad": "Use OpenSCAD syntax with modules for each subsystem.",
        }
        if cad_format in format_notes:
            parts.append(f"\nFormat: {format_notes[cad_format]}")

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        # Extract the script (strip markdown fences if present)
        script = content
        if "```python" in content:
            start = content.find("```python") + len("```python")
            end = content.find("```", start)
            if end > start:
                script = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                script = content[start:end].strip()

        return {
            "content": content,
            "script": script,
            "format": "python",
            "filename": "spacecraft_model.py",
        }
