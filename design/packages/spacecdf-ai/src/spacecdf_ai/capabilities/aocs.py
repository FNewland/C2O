"""AOCS Design — control law design, EKF, and closed-loop simulation."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.capabilities.fsw import _split_files
from spacecdf_ai.context import build_study_context


class AOCSCapability(BaseCapability):
    name = "aocs_design"
    prompt_file = "aocs_design.txt"
    model_tier = "heavy"  # Complex control engineering

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        pointing_requirements: dict | None = None,
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []
        parts.append("Design the complete AOCS for this spacecraft.\n")

        if study:
            ctx = build_study_context(study, elements, budgets)
            parts.append(ctx)

        # Extract AOCS-specific data from elements
        if elements:
            sensors = [e for e in elements if e.get("type") in
                       ("star_tracker", "sun_sensor", "magnetometer", "gyroscope", "gps_receiver")]
            actuators = [e for e in elements if e.get("type") in
                         ("reaction_wheel", "magnetorquer", "thruster", "cmg")]

            if sensors:
                parts.append("\n## Attitude Sensors")
                for s in sensors:
                    props = s.get("properties", {})
                    parts.append(
                        f"- {s.get('name', '?')} ({s.get('type', '?')}): "
                        f"accuracy={props.get('accuracy_arcsec', props.get('accuracy_deg', '?'))}, "
                        f"rate={props.get('update_rate_hz', '?')} Hz"
                    )

            if actuators:
                parts.append("\n## Attitude Actuators")
                for a in actuators:
                    props = a.get("properties", {})
                    parts.append(
                        f"- {a.get('name', '?')} ({a.get('type', '?')}): "
                        f"torque={props.get('max_torque_nm', '?')} Nm, "
                        f"momentum={props.get('momentum_nms', '?')} Nms"
                    )

        if pointing_requirements:
            parts.append("\n## Pointing Requirements")
            for key, val in pointing_requirements.items():
                parts.append(f"- {key}: {val}")

        # Spacecraft inertia
        if budgets and "mass" in budgets:
            mass = budgets["mass"]
            parts.append(f"\n## Mass Properties")
            parts.append(f"- Total mass: {mass.get('total_kg', '?')} kg")
            if mass.get("inertia_kg_m2"):
                parts.append(f"- Inertia: {mass['inertia_kg_m2']}")

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        files = _split_files(content)
        return {
            "content": content,
            "files": files,
            "file_count": len(files),
            "language": "python",
            "package_name": "aocs",
        }
