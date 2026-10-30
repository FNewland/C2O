"""Thermal Setup — thermal mathematical model generation."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.capabilities.fsw import _split_files
from spacecdf_ai.context import build_study_context


class ThermalCapability(BaseCapability):
    name = "thermal_setup"
    prompt_file = "thermal_model.txt"
    model_tier = "heavy"

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        orbit_data: dict | None = None,
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []
        parts.append("Generate a thermal mathematical model for this spacecraft.\n")

        if study:
            ctx = build_study_context(study, elements, budgets)
            parts.append(ctx)

        if orbit_data:
            parts.append("\n## Orbital Environment")
            parts.append(f"- Altitude: {orbit_data.get('altitude_km', '?')} km")
            parts.append(f"- Eclipse fraction: {orbit_data.get('eclipse_fraction', '?')}")
            parts.append(f"- Solar flux: {orbit_data.get('solar_flux_w_m2', 1361)} W/m2")
            parts.append(f"- Albedo factor: {orbit_data.get('albedo', 0.3)}")
            parts.append(f"- Earth IR: {orbit_data.get('earth_ir_w_m2', 237)} W/m2")

        # Extract thermal-relevant properties from elements
        if elements:
            parts.append("\n## Component Power Dissipation & Temperature Limits")
            for el in elements:
                props = el.get("properties", {})
                power = props.get("power_w")
                t_min = props.get("temp_min_c")
                t_max = props.get("temp_max_c")
                if power or t_min or t_max:
                    parts.append(
                        f"- {el.get('name', '?')}: "
                        f"power={power or '?'}W, "
                        f"temp_range=[{t_min or '?'}, {t_max or '?'}]C"
                    )

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        files = _split_files(content)
        return {
            "content": content,
            "files": files,
            "file_count": len(files),
            "language": "python",
            "package_name": "thermal",
        }
