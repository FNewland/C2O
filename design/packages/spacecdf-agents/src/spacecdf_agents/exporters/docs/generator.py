"""SpaceCDF — Design Review Document Generator.

Generates SRR/PDR/CDR documents from converged design state.

Produces three artefacts that are bundled into a zip:
  - docs/{review}.md    — Jinja2-rendered Markdown
  - docs/{review}.docx  — python-docx Word document
  - budgets/master_budget.xlsx — openpyxl master budget workbook

Budget tables, equipment lists, and compliance matrices are 100% auto-generated.
ConOps, trade rationale, and risk narratives include human input markers.
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


def _budget_to_dict(budget: SystemBudget) -> dict[str, Any]:
    """Serialise a SystemBudget to a plain dict for templates/docx/xlsx."""
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


def _cost_to_dict(state: DesignState) -> dict[str, Any] | None:
    """Run the cost engine and serialise results, or return None on failure."""
    try:
        # Local import to avoid circular deps at module load
        from spacecdf_server.services.cost_engine import estimate_cost
    except Exception:
        return None
    try:
        est = estimate_cost(state)
    except Exception:
        return None
    return {
        "model_used": est.model_used,
        "p50_keur": est.p50_keur,
        "p70_keur": est.p70_keur,
        "p80_keur": est.p80_keur,
        "p90_keur": est.p90_keur,
        "p50_meur": est.p50_keur / 1000,
        "p70_meur": est.p70_keur / 1000,
        "p80_meur": est.p80_keur / 1000,
        "p90_meur": est.p90_keur / 1000,
        "total_lcc_keur": est.total_lcc_keur,
        "total_lcc_meur": est.total_lcc_keur / 1000,
        "wbs": [
            {
                "wbs_id": w.wbs_id,
                "name": w.name,
                "ddte_keur": w.ddte_keur,
                "recurring_keur": w.recurring_keur,
                "total_keur": w.total_keur,
            }
            for w in est.wbs
        ],
    }


def _compliance_to_dict(state: DesignState, requirements: MissionRequirements) -> dict[str, Any] | None:
    """Build the compliance matrix as a plain dict, or None on failure."""
    try:
        from spacecdf_server.services.verification import build_compliance_matrix
    except Exception:
        return None
    try:
        matrix = build_compliance_matrix(state, worst_case="nominal")
    except Exception:
        return None
    return {
        "total_requirements": matrix.total_requirements,
        "compliant": matrix.compliant_count,
        "marginal": matrix.marginal_count,
        "non_compliant": matrix.non_compliant_count,
        "compliance_percent": matrix.compliance_percent,
        "requirements": [r.model_dump() for r in matrix.requirements],
        "verifications": [v.model_dump() for v in matrix.verifications],
    }


def _equipment_list(state: DesignState) -> list[dict[str, Any]]:
    """Extract KB-selected equipment from design state parameters."""
    out = []
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


def build_context(
    state: DesignState,
    requirements: MissionRequirements,
    result: DesignLoopResult,
    study_name: str = "",
) -> dict[str, Any]:
    """Build the template/docx/xlsx context from design artefacts."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    budgets_dict = {
        btype: _budget_to_dict(b) for btype, b in (result.budgets or {}).items()
    }

    orbit = {
        "orbit_type": requirements.orbit.orbit_type,
        "altitude_km": requirements.orbit.altitude_km,
        "inclination_deg": requirements.orbit.inclination_deg,
        "mission_duration_years": requirements.orbit.mission_duration_years,
        "period_min": state.get("orbit.period_min", 0) or 0,
        "eclipse_fraction": state.get("orbit.eclipse_fraction", 0) or 0,
    }

    state_params = {
        pid: p.model_dump() for pid, p in state.parameters.items()
    }

    trl_assessments = []
    trl_agent_result = (result.agent_results or {}).get("trl")
    if trl_agent_result and getattr(trl_agent_result, "trl_assessments", None):
        for trl in trl_agent_result.trl_assessments:
            trl_assessments.append({
                "subsystem": trl.subsystem,
                "baseline_component": trl.baseline_component,
                "baseline_trl": trl.baseline_trl,
                "innovation_component": trl.innovation_component,
                "innovation_trl": trl.innovation_trl,
                "recommendation": trl.recommendation,
            })

    return {
        "mission_name": requirements.name,
        "study_name": study_name or requirements.name,
        "date": now,
        "mission_type": requirements.mission_type.value if hasattr(requirements.mission_type, "value") else str(requirements.mission_type),
        "spacecraft_class": requirements.spacecraft_class,
        "num_spacecraft": requirements.num_spacecraft,
        "orbit": orbit,
        "budgets": budgets_dict,
        "state_params": state_params,
        "requirements_list": requirements.model_dump(),
        "cost": _cost_to_dict(state),
        "compliance": _compliance_to_dict(state, requirements),
        "equipment": _equipment_list(state),
        "trl_assessments": trl_assessments,
        "risks": list(result.all_warnings or []),
        "convergence": {
            "converged": result.converged,
            "iterations": len(result.iterations or []),
            "time_s": result.total_time_s,
        },
    }


def render_markdown(context: dict[str, Any], review_type: str) -> str:
    """Render the Markdown template for the given review type."""
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
    """Generates design review documents from SpaceCDF design state.

    The primary entry point is :meth:`generate` which returns Markdown for
    backwards compatibility, and :meth:`generate_bundle` which produces a
    zip containing Markdown + Word + Excel artefacts.
    """

    def generate(
        self,
        state: DesignState,
        requirements: MissionRequirements,
        result: DesignLoopResult,
        review_type: str = "srr",
    ) -> str:
        """Generate a design review document (Markdown only).

        Returns:
            Markdown document string.
        """
        ctx = build_context(state, requirements, result)
        return render_markdown(ctx, review_type)

    def generate_bundle(
        self,
        state: DesignState,
        requirements: MissionRequirements,
        result: DesignLoopResult,
        review_type: str = "srr",
        study_name: str = "",
    ) -> bytes:
        """Generate the full review bundle as zip bytes.

        Zip contents:
            docs/{review}.md
            docs/{review}.docx
            budgets/master_budget.xlsx
        """
        review_type = review_type.lower()
        if review_type not in ("srr", "pdr", "cdr"):
            review_type = "srr"

        ctx = build_context(state, requirements, result, study_name=study_name)
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
