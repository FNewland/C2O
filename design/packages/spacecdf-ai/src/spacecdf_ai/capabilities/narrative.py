"""Report Narrative — AI-written document sections for ECSS exports."""
from __future__ import annotations

from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_study_context


class NarrativeCapability(BaseCapability):
    name = "report_narrative"
    prompt_file = "narrative.txt"
    model_tier = "default"

    def build_user_message(
        self,
        section: str = "",
        document_type: str = "MRD",
        study: dict | None = None,
        elements: list[dict] | None = None,
        budgets: dict | None = None,
        requirements: list[dict] | None = None,
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        parts.append(f"Generate the '{section}' section for an ECSS {document_type} document.\n")

        if study:
            ctx = build_study_context(study, elements, budgets, requirements)
            parts.append(f"Design data:\n{ctx}")

        doc_guidance = {
            "MRD": "Mission Requirements Document per ECSS-E-ST-10-06C. Focus on mission objectives, constraints, and top-level requirements.",
            "TS": "Technical Specification per ECSS-E-ST-10C. Focus on system design description and performance characteristics.",
            "IRD": "Interface Requirements Document per ECSS-E-ST-10-24C. Focus on interface definitions and compatibility.",
            "SEMP": "Systems Engineering Management Plan per ECSS-M-ST-10C. Focus on SE approach, processes, and organisation.",
            "ConOps": "Concept of Operations. Focus on mission phases, operational modes, and ground segment interaction.",
            "VP": "Verification Plan per ECSS-E-ST-10-02C. Focus on verification approach, methods, and success criteria.",
        }
        if document_type in doc_guidance:
            parts.append(f"\nDocument guidance: {doc_guidance[document_type]}")

        return "\n".join(parts)
