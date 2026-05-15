"""SpaceCDF — Design Review Document Generator.

Produces SRR/PDR/CDR documents from a converged design state.

Bundle layout (zip):
    docs/{review}.md            — Jinja2 Markdown rendering
    docs/{review}.docx          — Rich DID-style Word document (uOttawa style)
    budgets/master_budget.xlsx  — openpyxl workbook

The Word document is the primary deliverable; the Markdown serves as a
plain-text twin and the spreadsheet as the editable budget workbook.

build_context() pulls everything the renderer needs out of the agents'
result objects — including the new ``rationale``, ``assumptions`` and
``extras`` fields populated by the Tier-1 and Tier-2 agents.  See
``agent_extras.py`` for the extras schema.
"""
from __future__ import annotations

import io
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.parameter import ParameterSource, SystemBudget
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents.orchestrator import DesignLoopResult

from .docx_generator import generate_docx
from .xlsx_generator import generate_xlsx


TEMPLATE_DIR = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# Per-object serialisers
# ---------------------------------------------------------------------------

def _budget_to_dict(budget: SystemBudget) -> dict[str, Any]:
    return {
        "budget_type": budget.budget_type,
        "unit": budget.unit,
        "allocation": budget.allocation,
        "total_nominal": budget.total_nominal,
        "total_with_margin": budget.total_with_margin,
        "margin_percent": budget.margin_percent,
        "status": budget.status.value,
        "lines": [
            {
                "subsystem": line.subsystem,
                "equipment": line.equipment,
                "nominal_value": line.nominal_value,
                "margin_percent": line.margin_percent,
                "with_margin": line.with_margin,
                "unit": line.unit,
                "trl": line.trl,
                "notes": line.notes,
            }
            for line in budget.lines
        ],
    }


def _cost_to_dict(state: DesignState, agent_results: dict[str, Any]) -> dict[str, Any] | None:
    """Prefer the cost agent's structured summary; fall back to cost_engine."""
    cost_agent = (agent_results or {}).get("cost")
    if cost_agent is not None:
        summary = getattr(cost_agent, "extras", {}).get("cost.summary")
        wbs = getattr(cost_agent, "extras", {}).get("cost.wbs")
        if summary:
            out = dict(summary)
            out["wbs"] = wbs or []
            out["rationale"] = cost_agent.rationale
            out["assumptions"] = list(cost_agent.assumptions)
            # Legacy aliases consumed by markdown templates
            total_meur = out.get("total_meur", 0)
            out.setdefault("p50_meur", total_meur)
            out.setdefault("p70_meur", total_meur * 1.15)
            out.setdefault("p80_meur", total_meur * 1.25)
            out.setdefault("p90_meur", total_meur * 1.50)
            out.setdefault("total_lcc_keur", out.get("total_keur", 0))
            out.setdefault("total_lcc_meur", total_meur)
            out.setdefault("model_used", out.get("model_used", "SpaceCDF Cost Agent"))
            return out
    try:
        from spacecdf_server.services.cost_engine import estimate_cost
    except Exception:
        return None
    try:
        est = estimate_cost(state)
    except Exception:
        return None
    return {
        "model_used": est.model_used,
        "p50_keur": est.p50_keur, "p70_keur": est.p70_keur,
        "p80_keur": est.p80_keur, "p90_keur": est.p90_keur,
        "p50_meur": est.p50_keur / 1000, "p70_meur": est.p70_keur / 1000,
        "p80_meur": est.p80_keur / 1000, "p90_meur": est.p90_keur / 1000,
        "total_lcc_keur": est.total_lcc_keur,
        "total_lcc_meur": est.total_lcc_keur / 1000,
        "wbs": [
            {"wbs_id": w.wbs_id, "name": w.name,
             "ddte_keur": w.ddte_keur, "recurring_keur": w.recurring_keur,
             "total_keur": w.total_keur}
            for w in est.wbs
        ],
    }


def _compliance_to_dict(state: DesignState, requirements: MissionRequirements) -> dict[str, Any] | None:
    try:
        from spacecdf_server.services.verification import build_compliance_matrix
    except Exception:
        return None
    try:
        matrix = build_compliance_matrix(state, worst_case="nominal")
    except Exception:
        return None

    def _normalise(d: dict[str, Any]) -> dict[str, Any]:
        # Flatten any "ENUM.VALUE" string back to "value"
        out = {}
        for k, v in d.items():
            if isinstance(v, str) and "." in v and v.split(".")[0].lower().endswith("status"):
                v = v.split(".", 1)[1].lower()
            elif hasattr(v, "value"):
                v = v.value
            out[k] = v
        return out

    return {
        "total_requirements": matrix.total_requirements,
        "compliant": matrix.compliant_count,
        "marginal": matrix.marginal_count,
        "non_compliant": matrix.non_compliant_count,
        "compliance_percent": matrix.compliance_percent,
        "requirements": [_normalise(r.model_dump()) for r in matrix.requirements],
        "verifications": [_normalise(v.model_dump()) for v in matrix.verifications],
    }


def _equipment_list(state: DesignState) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for pid, p in sorted(state.parameters.items()):
        if p.source == ParameterSource.KB_COMPONENT and p.equipment_id:
            out.append({
                "parameter_id": pid,
                "domain": p.domain,
                "equipment_id": p.equipment_id,
                "equipment_name": p.equipment_name or p.equipment_id,
                "trl": p.trl,
                "manufacturer": "",
                "heritage": p.heritage or "",
            })
    return out


def _agent_payload(agent_result: Any) -> dict[str, Any]:
    """Convert an AgentResult into a renderer-friendly dict."""
    if agent_result is None:
        return {}
    parameters = {}
    for pid, p in (getattr(agent_result, "parameters", {}) or {}).items():
        parameters[pid] = {
            "id": pid,
            "name": getattr(p, "name", pid),
            "value": getattr(p, "value", None),
            "unit": getattr(p, "unit", ""),
            "margin_percent": getattr(p, "margin_percent", 0),
            "rationale": getattr(p, "rationale", ""),
            "trl": getattr(p, "trl", None),
            "heritage": getattr(p, "heritage", ""),
        }
    return {
        "domain": getattr(agent_result, "domain", ""),
        "rationale": getattr(agent_result, "rationale", "") or "",
        "assumptions": list(getattr(agent_result, "assumptions", []) or []),
        "warnings": list(getattr(agent_result, "warnings", []) or []),
        "recommendations": list(getattr(agent_result, "recommendations", []) or []),
        "computation_log": list(getattr(agent_result, "computation_log", []) or []),
        "confidence": getattr(agent_result, "confidence", 0.8),
        "parameters": parameters,
        "extras": dict(getattr(agent_result, "extras", {}) or {}),
    }


def _trl_assessments(result: DesignLoopResult) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    trl_agent = (result.agent_results or {}).get("trl")
    if trl_agent and getattr(trl_agent, "trl_assessments", None):
        for trl in trl_agent.trl_assessments:
            out.append({
                "subsystem": trl.subsystem,
                "baseline_component": trl.baseline_component,
                "baseline_trl": trl.baseline_trl,
                "innovation_component": getattr(trl, "innovation_component", None),
                "innovation_trl": getattr(trl, "innovation_trl", None),
                "recommendation": getattr(trl, "recommendation", ""),
            })
    return out


# ---------------------------------------------------------------------------
# build_context — the renderer's single input
# ---------------------------------------------------------------------------

def build_context(
    state: DesignState,
    requirements: MissionRequirements,
    result: DesignLoopResult,
    study_name: str = "",
    *,
    review_type: str = "srr",
    document_code: str | None = None,
    issue: str = "1.0",
    classification: str = "Internal",
) -> dict[str, Any]:
    """Build the rendering context.

    Aggregates: mission descriptor, orbit & ConOps, budgets, every agent's
    rationale + assumptions + extras, cost estimate, compliance matrix,
    equipment list, TRL assessments, risk register, convergence statistics,
    and the metadata required for a DID-style cover page.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    budgets_dict = {
        btype: _budget_to_dict(b) for btype, b in (result.budgets or {}).items()
    }

    def _stringify_enum(v: Any) -> str:
        if v is None:
            return ""
        if hasattr(v, "value"):
            return str(v.value)
        s = str(v)
        # Strip "ENUMCLASS." prefix from str(Enum) form
        if "." in s and s.split(".")[0].isupper():
            return s.split(".", 1)[1].lower().replace("_", " ")
        return s

    orbit = {
        "orbit_type": _stringify_enum(requirements.orbit.orbit_type),
        "altitude_km": requirements.orbit.altitude_km,
        "inclination_deg": requirements.orbit.inclination_deg,
        "mission_duration_years": getattr(requirements.orbit, "mission_duration_years", 3.0),
        "period_min": state.get("orbit.period_min", 0) or 0,
        "eclipse_fraction": state.get("orbit.eclipse_fraction", 0) or 0,
        "velocity_ms": state.get("orbit.velocity_ms", 0) or 0,
        "orbits_per_day": state.get("orbit.orbits_per_day", 0) or 0,
        "footprint_radius_km": state.get("orbit.footprint_radius_km", 0) or 0,
        "contact_time_per_day_s": state.get("orbit.contact_time_per_day_s", 0) or 0,
    }

    agent_results = result.agent_results or {}
    agents_payload = {domain: _agent_payload(ar) for domain, ar in agent_results.items()}

    sc_class = (
        getattr(requirements, "spacecraft_class", "") or ""
    )

    return {
        # ---- Identity ----
        "mission_name": requirements.name,
        "study_name": study_name or requirements.name,
        "date": now,
        "review_type": review_type.upper(),
        "document_code": document_code or f"SCDF-{review_type.upper()}-001",
        "issue": issue,
        "classification": classification,
        "publisher": "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)",
        # ---- Mission descriptor ----
        "mission_type": _stringify_enum(requirements.mission_type).replace("_", " ").title(),
        "spacecraft_class": sc_class,
        "num_spacecraft": getattr(requirements, "num_spacecraft", 1),
        "design_lifetime_years": getattr(requirements, "design_lifetime_years", 0),
        "target_cost_meur": getattr(requirements, "target_cost_meur", None),
        "target_mass_kg": getattr(requirements, "target_mass_kg", None),
        "reliability_target": getattr(requirements, "reliability_target", None),
        "ground_stations": list(getattr(requirements, "ground_stations", []) or []),
        # ---- Payloads ----
        "payloads": [
            {
                "name": pl.name, "type": pl.type, "mass_kg": pl.mass_kg,
                "power_w": pl.power_w, "power_peak_w": getattr(pl, "power_peak_w", pl.power_w),
                "data_rate_mbps": pl.data_rate_mbps,
                "data_volume_per_day_gb": getattr(pl, "data_volume_per_day_gb", 0),
                "pointing_accuracy_deg": getattr(pl, "pointing_accuracy_deg", 0),
                "duty_cycle_percent": getattr(pl, "duty_cycle_percent", 0),
                "description": getattr(pl, "description", ""),
            }
            for pl in (getattr(requirements, "payloads", []) or [])
        ],
        "orbit": orbit,
        # ---- Engineering data ----
        "budgets": budgets_dict,
        "agents": agents_payload,                  # New: full per-domain blob
        "cost": _cost_to_dict(state, agent_results),
        "compliance": _compliance_to_dict(state, requirements),
        "equipment": _equipment_list(state),
        "trl_assessments": _trl_assessments(result),
        # ---- Risk: prefer structured register from RiskAgent ----
        "risk_register": (
            agent_results.get("risk").extras.get("risk.register")
            if agent_results.get("risk") and getattr(agent_results.get("risk"), "extras", None)
            else []
        ),
        "warnings": list(result.all_warnings or []),
        "recommendations": list(getattr(result, "all_recommendations", []) or []),
        # ---- Convergence ----
        "convergence": {
            "converged": result.converged,
            "iterations": len(result.iterations or []),
            "iterations_data": [
                {"index": idx, "warnings": len(getattr(it, "warnings", []) or [])}
                for idx, it in enumerate(result.iterations or [], 1)
            ],
            "time_s": getattr(result, "total_time_s", 0),
        },
        # ---- Acronyms / references — defaults; renderers can extend ----
        "acronyms": DEFAULT_ACRONYMS,
        "applicable_documents": DEFAULT_APPLICABLE_DOCS,
        "reference_documents": DEFAULT_REFERENCE_DOCS,
        # ---- Raw state for templates that need it ----
        "state_params": {pid: p.model_dump() for pid, p in state.parameters.items()},
        "requirements_dict": requirements.model_dump(),
    }


DEFAULT_ACRONYMS = {
    "AIT": "Assembly, Integration and Test",
    "AOCS": "Attitude and Orbit Control Subsystem",
    "BoL": "Beginning of Life",
    "CDR": "Critical Design Review",
    "CDF": "Concurrent Design Facility",
    "ConOps": "Concept of Operations",
    "DDT&E": "Design, Development, Test and Evaluation",
    "EoL": "End of Life",
    "EPS": "Electrical Power Subsystem",
    "FMECA": "Failure Mode, Effects and Criticality Analysis",
    "GS": "Ground Station",
    "IADC": "Inter-Agency Space Debris Coordination Committee",
    "ITU": "International Telecommunication Union",
    "MLI": "Multi-Layer Insulation",
    "MRD": "Mission Requirements Document",
    "MTBF": "Mean Time Between Failures",
    "OBDH": "On-Board Data Handling",
    "PDR": "Preliminary Design Review",
    "RPN": "Risk Priority Number",
    "RW": "Reaction Wheel",
    "SA": "Solar Array",
    "SCDF": "SpaceCDF Concurrent Design Facility",
    "SRR": "System Requirements Review",
    "SSO": "Sun-Synchronous Orbit",
    "TCS": "Thermal Control Subsystem",
    "TT&C": "Telemetry, Tracking and Command",
    "TRL": "Technology Readiness Level",
    "VP": "Verification Plan",
    "WBS": "Work Breakdown Structure",
}

DEFAULT_APPLICABLE_DOCS = [
    {"id": "AD-01", "ref": "ECSS-M-ST-10C Rev.1", "title": "Space project management"},
    {"id": "AD-02", "ref": "ECSS-E-ST-10C Rev.1", "title": "System engineering general requirements"},
    {"id": "AD-03", "ref": "ECSS-E-ST-10-02C", "title": "Verification requirements"},
    {"id": "AD-04", "ref": "ECSS-E-ST-10-06C", "title": "Technical requirements specification"},
    {"id": "AD-05", "ref": "ECSS-Q-ST-30C", "title": "Dependability"},
    {"id": "AD-06", "ref": "ECSS-Q-ST-40C Rev.1", "title": "Safety"},
]

DEFAULT_REFERENCE_DOCS = [
    {"id": "RD-01", "ref": "NASA SP-2016-6105", "title": "NASA Systems Engineering Handbook Rev. 2"},
    {"id": "RD-02", "ref": "NPR 7123.1D", "title": "NASA Systems Engineering Processes and Requirements"},
    {"id": "RD-03", "ref": "SMAD-4", "title": "Space Mission Analysis and Design (4th ed.)"},
    {"id": "RD-04", "ref": "ECSS-U-AS-10C Rev.2", "title": "Space debris mitigation requirements"},
    {"id": "RD-05", "ref": "ISO 24113:2023", "title": "Space debris mitigation requirements"},
    {"id": "RD-06", "ref": "ITU-R P.618-13", "title": "Propagation data for Earth-space links"},
    {"id": "RD-07", "ref": "ITU-R P.676-13", "title": "Attenuation by atmospheric gases"},
]


# ---------------------------------------------------------------------------
# Public API: DocumentGenerator
# ---------------------------------------------------------------------------

def render_markdown(context: dict[str, Any], review_type: str) -> str:
    review_type = review_type.lower()
    if review_type not in ("srr", "pdr", "cdr"):
        review_type = "srr"
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        keep_trailing_newline=True,
    )
    template = env.get_template(f"{review_type}.md.j2")
    return template.render(ctx=context)


class DocumentGenerator:
    """Generates DID-style design review documents.

    The primary deliverable is the Word document.  Markdown and Excel
    artefacts are bundled for downstream tooling.
    """

    def generate(
        self,
        state: DesignState,
        requirements: MissionRequirements,
        result: DesignLoopResult,
        review_type: str = "srr",
    ) -> str:
        """Return Markdown only (legacy interface)."""
        ctx = build_context(state, requirements, result, review_type=review_type)
        return render_markdown(ctx, review_type)

    def generate_bundle(
        self,
        state: DesignState,
        requirements: MissionRequirements,
        result: DesignLoopResult,
        review_type: str = "srr",
        study_name: str = "",
        *,
        document_code: str | None = None,
        issue: str = "1.0",
        classification: str = "Internal",
    ) -> bytes:
        review_type = review_type.lower()
        if review_type not in ("srr", "pdr", "cdr"):
            review_type = "srr"

        ctx = build_context(
            state, requirements, result,
            study_name=study_name, review_type=review_type,
            document_code=document_code, issue=issue, classification=classification,
        )
        markdown = render_markdown(ctx, review_type)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            docx_path = tmp_path / f"{review_type}.docx"
            xlsx_path = tmp_path / "master_budget.xlsx"
            generate_docx(ctx, review_type, docx_path)
            generate_xlsx(ctx, xlsx_path)

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"docs/{review_type}.md", markdown)
                zf.write(docx_path, arcname=f"docs/{review_type}.docx")
                zf.write(xlsx_path, arcname="budgets/master_budget.xlsx")
            return buf.getvalue()
