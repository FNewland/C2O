"""SpaceCDF — Design Execution API.

Runs the design convergence loop and returns results.
Now accepts full V-model input: requirements + mission_need → auto-generates
ConOps modes that are passed to DesignState so agents use them.

SCDF-171 (model coupling): ``POST /{study_id}/run`` builds an
``AnalysisContext`` for the study, seeds the orchestrator's ``DesignState``
from ``ctx.flat`` (overridden element parameters become sticky
``POSITION_OVERRIDE`` values the agents cannot overwrite) and, after the run,
writes the agent outputs back through ``ResultsSink`` (element parameters via
the projection registry's reverse map, ``owner_domain='agent:<domain>'``,
cross-domain conflicts into ``analysis_conflicts``) and records a
``design_loop`` row in ``analysis_runs``. The response shape is unchanged;
the coupling is best-effort — a persistence failure is logged, not raised.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator, ConvergenceConfig

from .studies import get_study_store, _generate_default_conops

logger = logging.getLogger(__name__)

router = APIRouter()

DESIGN_LOOP = "design_loop"

#: Study-level agent outputs written onto the mission root (parameter name =
#: path with dots replaced by underscores); subsystem-level outputs go through
#: ``element_projection.reverse_map``.
STUDY_LEVEL_OUTPUTS: tuple[str, ...] = (
    "mass.dry_mass_kg", "mass.wet_mass_kg", "mass.payload_kg", "mass.platform_kg",
    "power.sa_area_m2", "power.sa_power_bol_w", "power.sa_power_eol_w",
    "power.total_sunlight_w", "power.total_eclipse_w",
    "link.margin_db", "data.storage_gb", "cost.total_meur",
)


def _agent_param_writes(loop_result, elements: list[dict], root: dict | None) -> list:
    """Agent outputs -> ``ParamWrite`` list (registry reverse map + study-level set)."""
    from ..services.analysis_results import ParamWrite
    from ..services.element_projection import PROPERTY_TO_PARAM, reverse_map

    writes: list = []
    state = loop_result.final_state
    if state is None:
        return writes
    for path in PROPERTY_TO_PARAM:
        p = state.get_param(path)
        if p is None or isinstance(p.value, bool) or not isinstance(p.value, (int, float)):
            continue
        target = reverse_map(path, elements)
        if target is None:
            continue
        el, name = target
        writes.append(ParamWrite(name=name, value=float(p.value), element_id=el["id"], unit=p.unit or ""))
    if root is not None:
        for path in STUDY_LEVEL_OUTPUTS:
            p = state.get_param(path)
            if p is None or isinstance(p.value, bool) or not isinstance(p.value, (int, float)):
                continue
            writes.append(ParamWrite(name=path.replace(".", "_"), value=float(p.value),
                                     element_id=root["id"], unit=p.unit or "",
                                     description=f"Design loop output {path}"))
    return writes


def _loop_conflicts(loop_result) -> list:
    from ..services.analysis_results import Conflict
    out = []
    for c in loop_result.conflicts:
        d = c.model_dump() if hasattr(c, "model_dump") else dict(c)
        sev = d.get("severity")
        sev = sev.value if hasattr(sev, "value") else str(sev or "major")
        out.append(Conflict(
            severity=sev if sev in ("critical", "major", "minor", "warning", "info") else "major",
            code=str(d.get("id") or ""), title=str(d.get("title") or ""),
            detail=str(d.get("description") or ""),
            suggested_fix="; ".join(str(r.get("description") or r.get("title") or r)
                                    for r in (d.get("resolutions") or [])) or None,
        ))
    return out


async def _persist_merged_elements(elements: list[dict], modified_ids: list[str]) -> None:
    from ..db.element_repo import db_update_element
    by_id = {e["id"]: e for e in elements}
    for eid in modified_ids:
        el = by_id.get(eid)
        if el is None:
            continue
        el["version"] = int(el.get("version") or 1) + 1
        await db_update_element(eid, el)


class DesignRunRequest(BaseModel):
    """Request to run the design loop."""
    max_iterations: int = 50
    convergence_threshold: float = 0.001


class DesignRunResponse(BaseModel):
    """Response from a design loop execution."""
    converged: bool
    iterations: int
    total_time_s: float
    parameters: dict
    budgets: dict
    warnings: list[str]
    recommendations: list[str]
    conflicts: list[dict] = []
    #: wave 3 (3.A1): the study's own figures the loop read (``{path: {value, unit, source}}``)
    #: and the summary the Analyses tab quotes (study figure next to the loop's Phase 0 estimate)
    study_values: dict = {}
    summary: dict = {}


def _summary(params: dict, study_inputs: dict) -> dict:
    """The design-loop summary on the study's figures: EOL power, mass margin, link margin, contact,
    ΔV for disposal, reliability over the mission-success horizon, cost; each with the loop's own
    Phase 0 estimate where it differs."""
    def v(path: str):
        p = params.get(path)
        return p.get("value") if isinstance(p, dict) else None

    def s(path: str):
        return (study_inputs.get(path) or {}).get("source")

    rows = {
        "eol_power_w": {"value": v("power.sa_power_eol_w"), "source": s("power.sa_power_eol_w") or "design loop sizing",
                        "phase0_estimate": v("power.phase0_sa_power_eol_w")},
        "mass_margin_to_limit_kg": {"value": v("mass.margin_to_limit_kg"), "source": s("mass.margin_to_limit_kg"),
                                    "percent": v("systems.mass_margin_percent"),
                                    "phase0_estimate_kg": v("mass.phase0_dry_mass_kg")},
        "link_margin_db": {"value": v("link.downlink_margin_db"), "source": s("link.downlink_margin_db") or "design loop"},
        "contact_min_per_day": {"value": (v("orbit.contact_time_per_day_s") or 0) / 60.0 or None,
                                "source": s("orbit.contact_time_per_day_s") or "design loop estimate"},
        "delta_v_deorbit_ms": {"value": v("orbit.delta_v_deorbit_ms"), "method": v("orbit.disposal_method")},
        "reliability": {"value": v("reliability.mission_reliability"), "horizon_months": v("reliability.horizon_months"),
                        "phase0_estimate": v("reliability.phase0_mission_reliability")},
        "cost_keur": {"value": v("cost.total_keur"), "launch_keur": v("cost.launch_keur"),
                      "source": s("cost.study_total_keur") or "design loop parametric model",
                      "phase0_estimate_keur": v("cost.phase0_estimate_keur")},
    }
    return rows


@router.post("/{study_id}/run")
async def run_design_loop(study_id: str, request: DesignRunRequest | None = None,
                          option_id: str | None = Query(None)) -> DesignRunResponse:
    """Execute the design convergence loop for a study (model-coupled, SCDF-171)."""
    studies = get_study_store()
    study = studies.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    config = ConvergenceConfig(
        max_iterations=request.max_iterations if request else 50,
        convergence_threshold=request.convergence_threshold if request else 0.001,
    )

    orchestrator = DesignLoopOrchestrator(config=config)
    orchestrator.initialise_agents()

    # SCDF-171: seed the design state from the model (best-effort)
    ctx = None
    initial_state = None
    run_id = None
    study_inputs: dict = {}
    try:
        from ..services.analysis_context import (build_context, context_hash, conops_from_modes, seed_design_state,
                                                 study_design_inputs)
        from ..services.analysis_results import input_keys_for, start_run
        ctx = await build_context(study_id, option_id=option_id)
        # wave 3 (3.A1): the Modes tab is the ConOps; the study's own figures are sticky inputs
        try:
            study_inputs = await study_design_inputs(ctx)
        except Exception:  # noqa: BLE001 — never block the run on a missing study figure
            logger.warning("design loop: study inputs unavailable for %s", study_id, exc_info=True)
            study_inputs = {}
        initial_state = seed_design_state(ctx, requirements=study.requirements,
                                          conops=conops_from_modes(ctx, study.conops), study_inputs=study_inputs)
        if option_id:   # the roll-up is the baseline's: an option run keeps the agents' own mass
            for k in [k for k in initial_state.parameters if k.startswith("mass.study_")]:
                del initial_state.parameters[k]
        # wave 3 (3.H1): the study's data budget (science product set, capacity of the union of the
        # passes, closure) feeds the tier-1 data and link agents as sticky study figures
        try:
            from spacecdf_common.models.parameter import ParameterSource, ParameterValue

            from ..services.data_budget import design_overlay_for_study
            for path, value in (await design_overlay_for_study(study_id)).items():
                initial_state.parameters[path] = ParameterValue(
                    id=path, name=path, value=value, unit="", domain=path.split(".")[0],
                    source=ParameterSource.POSITION_OVERRIDE, confidence=1.0, margin_percent=0.0,
                    updated_by="study", rationale="study value: data budget (Modes tab and contact plan)")
        except Exception:  # noqa: BLE001 — the loop keeps its own Phase 0 estimate
            logger.warning("design loop: data budget overlay unavailable for %s", study_id, exc_info=True)
        run_id =await start_run(study_id, DESIGN_LOOP, context_hash(ctx, input_keys_for(DESIGN_LOOP)), option_id)
    except Exception:
        logger.warning("design loop: model coupling unavailable for %s (running uncoupled)", study_id, exc_info=True)
        ctx, initial_state, run_id = None, None, None

    loop_result = await orchestrator.run(study.requirements, initial_state=initial_state, conops=study.conops)

    # Update study with results — and persist them: the review gates read the last
    # iteration on the server (walkthrough: "Run the design loop first" after it ran).
    study.iterations = loop_result.iterations
    # The per-iteration snapshots are taken before the Tier 2 agents (systems margins,
    # cost, risk, debris) run on convergence: add the final state to the last one, which
    # is what the review gates read.
    if loop_result.final_state and study.iterations:
        final = {pid: float(p.value) for pid, p in loop_result.final_state.parameters.items()
                 if isinstance(p.value, (int, float)) and not isinstance(p.value, bool)}
        study.iterations[-1].parameter_snapshot = {**study.iterations[-1].parameter_snapshot, **final}
    try:
        from ..db.study_repo import db_save_study
        await db_save_study(study)
    except Exception:  # noqa: BLE001 — never fail the run on persistence
        logger.warning("design loop: study %s not persisted", study_id, exc_info=True)

    # Serialise parameters
    params = {}
    if loop_result.final_state:
        for pid, p in loop_result.final_state.parameters.items():
            params[pid] = {
                "value": p.value,
                "unit": p.unit,
                "confidence": p.confidence,
                "margin_percent": p.margin_percent,
                "source": p.source.value,
                "domain": p.domain,
            }

    # Serialise budgets
    budgets = {}
    for btype, budget in loop_result.budgets.items():
        budgets[btype] = {
            "total_nominal": budget.total_nominal,
            "total_with_margin": budget.total_with_margin,
            "allocation": budget.allocation,
            "margin_percent": budget.margin_percent,
            "status": budget.status.value,
            "lines": [line.model_dump() for line in budget.lines],
        }

    # SCDF-171: write agent outputs back to the model + record the run
    if ctx is not None:
        try:
            from ..services.analysis_results import ResultsSink, finish_run, refresh_inputs_hash
            from ..services.element_projection import merge_agent_params_to_elements
            agent_values = {pid: p["value"] for pid, p in params.items()}
            modified = merge_agent_params_to_elements(ctx.elements, agent_values)
            if modified and ctx.option_id is None:
                # SCDF-172: element columns are baseline state; option runs
                # only write option-scoped parameter rows (ResultsSink below).
                await _persist_merged_elements(ctx.elements, modified)
            publish = await ResultsSink().publish(
                study_id, DESIGN_LOOP,
                parameters=_agent_param_writes(loop_result, ctx.elements, ctx.mission_root),
                conflicts=_loop_conflicts(loop_result),
                notes=list(loop_result.all_warnings)[:20],
                option_id=option_id, run_id=run_id, ctx=ctx,
            )
            if run_id:
                summary = {
                    "converged": loop_result.converged, "iterations": len(loop_result.iterations),
                    "total_time_s": round(loop_result.total_time_s, 3),
                    "sticky_paths": sorted(ctx.overridden_paths),
                    "parameters_written": len(publish.written), "shadowed": len(publish.shadowed),
                    "conflicts": len(publish.conflicts), "warnings": len(loop_result.all_warnings),
                    "budgets": {k: {"total_with_margin": v["total_with_margin"], "status": v["status"]}
                                for k, v in budgets.items()},
                    "compliance": publish.compliance_results,
                }
                await finish_run(run_id, "ok", summary=summary, series={"parameters": params, "budgets": budgets})
                await refresh_inputs_hash(run_id)   # the run's own outputs are now part of the context
        except Exception:
            logger.warning("design loop: write-back failed for %s", study_id, exc_info=True)
            if run_id:
                try:
                    from ..services.analysis_results import finish_run
                    await finish_run(run_id, "failed", summary={"error": "write-back failed"})
                except Exception:
                    pass

    return DesignRunResponse(
        converged=loop_result.converged,
        iterations=len(loop_result.iterations),
        total_time_s=round(loop_result.total_time_s, 3),
        parameters=params,
        budgets=budgets,
        warnings=loop_result.all_warnings,
        recommendations=loop_result.all_recommendations,
        conflicts=[c.model_dump() if hasattr(c, 'model_dump') else c for c in loop_result.conflicts],
        study_values=study_inputs, summary=_summary(params, study_inputs),
    )


class QuickDesignRequest(BaseModel):
    """Accepts requirements + optional mission_need for full V-model flow."""
    requirements: MissionRequirements | None = None
    mission_need: dict[str, Any] | None = None
    # User-set parameter overrides — injected as sticky values so agents don't overwrite
    parameter_overrides: dict[str, Any] | None = None
    # Backward compat: if sent as flat MissionRequirements, parse at validation
    name: str | None = None
    mission_type: str | None = None


@router.post("/quick-design")
async def quick_design(body: QuickDesignRequest | MissionRequirements) -> DesignRunResponse:
    """One-shot design: create study + run loop in a single call.

    Accepts either {requirements, mission_need} or flat MissionRequirements
    for backward compatibility. When mission_need is provided, auto-generates
    ConOps modes that drive multi-mode power/thermal/AOCS sizing.
    """
    # Parse input — handle both new format and legacy flat requirements
    if isinstance(body, MissionRequirements):
        requirements = body
        conops = _generate_default_conops(requirements)
    elif body.requirements:
        requirements = body.requirements
        conops = _generate_default_conops(requirements)
    else:
        # Legacy: body might be flat MissionRequirements fields
        requirements = MissionRequirements(**body.model_dump(exclude_none=True))
        conops = _generate_default_conops(requirements)

    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    loop_result = await orchestrator.run(requirements, conops=conops)

    # Apply user parameter overrides as sticky values (POSITION_OVERRIDE)
    overrides = getattr(body, 'parameter_overrides', None) or {}
    if overrides and loop_result.final_state:
        from spacecdf_common.models.parameter import ParameterSource, ParameterValue
        for param_id, value in overrides.items():
            # Skip non-scalar values (dicts, lists) — only float/str/bool are valid
            if isinstance(value, (dict, list)):
                continue
            try:
                existing = loop_result.final_state.get_param(param_id)
                loop_result.final_state._parameters[param_id] = ParameterValue(
                    id=param_id,
                    name=existing.name if existing else param_id,
                    value=value,
                    unit=existing.unit if existing else "",
                    domain=existing.domain if existing else param_id.split(".")[0],
                    source=ParameterSource.POSITION_OVERRIDE,
                    confidence=1.0,
                )
            except Exception:
                continue  # Skip any value that can't be coerced

    params = {}
    if loop_result.final_state:
        for pid, p in loop_result.final_state.parameters.items():
            params[pid] = {
                "value": p.value,
                "unit": p.unit,
                "confidence": p.confidence,
                "margin_percent": p.margin_percent,
                "source": p.source.value,
                "domain": p.domain,
            }

    budgets = {}
    for btype, budget in loop_result.budgets.items():
        budgets[btype] = {
            "total_nominal": budget.total_nominal,
            "total_with_margin": budget.total_with_margin,
            "allocation": budget.allocation,
            "margin_percent": budget.margin_percent,
            "status": budget.status.value,
            "lines": [line.model_dump() for line in budget.lines],
        }

    return DesignRunResponse(
        converged=loop_result.converged,
        iterations=len(loop_result.iterations),
        total_time_s=round(loop_result.total_time_s, 3),
        parameters=params,
        budgets=budgets,
        warnings=loop_result.all_warnings,
        recommendations=loop_result.all_recommendations,
        conflicts=[c.model_dump() if hasattr(c, 'model_dump') else c for c in loop_result.conflicts],
    )
