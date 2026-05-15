"""Structural Setup — FEM model and launch load analysis generation."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.capabilities.fsw import _split_files
from spacecdf_ai.context import build_study_context


class StructuralCapability(BaseCapability):
    name = "structural_setup"
    prompt_file = "structural_model.txt"
    model_tier = "heavy"

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        launch_vehicle: dict | None = None,
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []
        parts.append("Generate a structural analysis model for this spacecraft.\n")

        if study:
            ctx = build_study_context(study, elements, budgets)
            parts.append(ctx)

        if launch_vehicle:
            parts.append("\n## Launch Vehicle Loads")
            parts.append(f"- Vehicle: {launch_vehicle.get('name', '?')}")
            parts.append(f"- Axial limit load: {launch_vehicle.get('axial_g', '?')} g")
            parts.append(f"- Lateral limit load: {launch_vehicle.get('lateral_g', '?')} g")
            parts.append(f"- Min fundamental freq (axial): {launch_vehicle.get('min_freq_axial_hz', '?')} Hz")
            parts.append(f"- Min fundamental freq (lateral): {launch_vehicle.get('min_freq_lateral_hz', '?')} Hz")
            if launch_vehicle.get("random_vibration_grms"):
                parts.append(f"- Random vibration: {launch_vehicle['random_vibration_grms']} gRMS")
            if launch_vehicle.get("shock_srs"):
                parts.append(f"- Shock SRS: {launch_vehicle['shock_srs']}")

        # Mass properties for FEM
        if budgets and "mass" in budgets:
            mass = budgets["mass"]
            parts.append(f"\n## Mass Properties")
            parts.append(f"- Dry mass: {mass.get('dry_mass_kg', '?')} kg")
            parts.append(f"- Wet mass: {mass.get('wet_mass_kg', '?')} kg")
            if mass.get("cg_mm"):
                parts.append(f"- CG: {mass['cg_mm']}")
            if mass.get("inertia_kg_m2"):
                parts.append(f"- Inertia: {mass['inertia_kg_m2']}")

        # Component masses and locations
        if elements:
            parts.append("\n## Component Mass Distribution")
            for el in elements:
                props = el.get("properties", {})
                mass_kg = props.get("mass_kg")
                if mass_kg:
                    loc = props.get("location", "not specified")
                    parts.append(f"- {el.get('name', '?')}: {mass_kg} kg at {loc}")

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        files = _split_files(content)
        # Detect if output is Nastran BDF or Python
        is_nastran = any(f.endswith(".bdf") or f.endswith(".dat") for f in files)
        return {
            "content": content,
            "files": files,
            "file_count": len(files),
            "format": "nastran" if is_nastran else "python",
            "package_name": "structural",
        }
