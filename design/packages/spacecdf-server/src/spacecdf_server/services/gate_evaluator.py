"""SpaceCDF — Gate exit criteria evaluator.

Loads gate_exit_criteria.yaml and evaluates each criterion against the
current study state (MissionNeed + DesignState + position answers).
Returns a structured pass/fail/not-evaluated checklist.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from spacecdf_common.models.mission_need import MissionNeed

logger = logging.getLogger(__name__)


def _criteria_file() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "configs" / "gate_exit_criteria.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("configs/gate_exit_criteria.yaml not found")


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    try:
        path = _criteria_file()
        return yaml.safe_load(path.read_text()) or {"phases": {}}
    except (FileNotFoundError, yaml.YAMLError) as exc:
        logger.warning("Gate criteria file failed to load: %s", exc)
        return {"phases": {}}


def list_gates() -> list[str]:
    return list(_load().get("phases", {}).keys())


def get_gate(phase_id: str) -> dict[str, Any] | None:
    return _load().get("phases", {}).get(phase_id)


def evaluate_gate(
    phase_id: str,
    mission_need: MissionNeed | None = None,
    design_params: dict[str, Any] | None = None,
    position_answers: list[Any] | None = None,
    target_mass_kg: float | None = None,
    target_cost_meur: float | None = None,
    reliability_target: float | None = None,
) -> dict[str, Any]:
    """Evaluate all exit criteria for a gate and return structured results.

    Returns:
        {
            "phase": str,
            "gate": str,
            "gate_name": str,
            "purpose": str,
            "criteria": [
                {"id": str, "question": str, "status": "pass"|"fail"|"not_evaluated"|"manual",
                 "evidence_found": str, "priority": str, "category": str}
            ],
            "summary": {"total": int, "pass": int, "fail": int, "manual": int, "not_evaluated": int},
            "ready": bool  # True if all must_pass criteria pass
        }
    """
    gate = get_gate(phase_id)
    if not gate:
        return {"phase": phase_id, "gate": "?", "criteria": [], "summary": {}, "ready": False}

    mn = mission_need or MissionNeed()
    dp = design_params or {}
    answers = position_answers or []

    results = []
    for ec in gate.get("exit_criteria", []):
        result = _evaluate_criterion(ec, mn, dp, answers, target_mass_kg, target_cost_meur, reliability_target)
        results.append(result)

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "manual": sum(1 for r in results if r["status"] == "manual"),
        "not_evaluated": sum(1 for r in results if r["status"] == "not_evaluated"),
    }

    # Ready if all must_pass criteria pass
    must_pass = [r for r in results if r["priority"] == "must_pass"]
    ready = all(r["status"] == "pass" for r in must_pass) if must_pass else False

    return {
        "phase": phase_id,
        "gate": gate.get("gate", ""),
        "gate_name": gate.get("gate_name", ""),
        "purpose": gate.get("purpose", "").strip(),
        "authority": gate.get("authority", ""),
        "criteria": results,
        "summary": summary,
        "ready": ready,
    }


def _evaluate_criterion(
    ec: dict, mn: MissionNeed, dp: dict, answers: list,
    target_mass: float | None, target_cost: float | None, rel_target: float | None,
) -> dict[str, Any]:
    """Evaluate a single exit criterion."""
    cid = ec.get("id", "")
    status_mode = ec.get("status", "manual")
    result = {
        "id": cid,
        "question": ec.get("question", ""),
        "category": ec.get("category", ""),
        "priority": ec.get("priority", "should_pass"),
        "status": "not_evaluated",
        "evidence_found": "",
    }

    if status_mode == "manual":
        result["status"] = "manual"
        result["evidence_found"] = "Requires manual assessment"
        return result

    # Auto-evaluate based on criterion ID patterns
    try:
        if cid == "MCR-EC-01":
            ok = bool(mn.problem_statement.strip())
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"Problem statement: {'defined' if ok else 'empty'}"

        elif cid == "MCR-EC-02":
            ok = len(mn.stakeholders) >= 1
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"{len(mn.stakeholders)} stakeholder(s) identified"

        elif cid == "MCR-EC-03":
            primary = [o for o in mn.objectives if o.priority.value == "primary" and o.measurable_criterion]
            ok = len(primary) >= 1
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"{len(primary)} primary objective(s) with measurable criteria"

        elif cid == "MCR-EC-04":
            has_non_space = mn.has_non_space_alternative
            has_multiple = len(mn.alternatives_considered) >= 2
            ok = has_multiple and has_non_space
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"{len(mn.alternatives_considered)} alternatives, non-space: {'yes' if has_non_space else 'no'}"

        elif cid == "MCR-EC-05":
            ok = bool(mn.selected_alternative_id and mn.selection_rationale.strip())
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"Selected: {'yes' if mn.selected_alternative_id else 'no'}, rationale: {'provided' if mn.selection_rationale.strip() else 'missing'}"

        elif cid == "MCR-EC-06":
            ok = bool(mn.conops_summary.strip())
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"ConOps summary: {'documented' if ok else 'empty'}"

        elif cid == "MCR-EC-07":
            mass_margin = _get_param(dp, "systems.mass_margin_percent", -999)
            power_margin = _get_param(dp, "systems.power_margin_percent", -999)
            ok = mass_margin > -50 and power_margin > 0
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"Mass margin: {mass_margin:.0f}%, Power margin: {power_margin:.0f}%"

        elif cid == "MCR-EC-08":
            cost = _get_param(dp, "cost.total_meur", 0)
            if target_cost and target_cost > 0:
                ok = cost <= target_cost * 1.2  # 20% slack for Phase 0 estimates
                result["status"] = "pass" if ok else "fail"
                result["evidence_found"] = f"Cost: {cost:.1f} MEUR vs target {target_cost:.1f} MEUR"
            else:
                result["status"] = "pass"
                result["evidence_found"] = "No cost target set"

        elif cid == "MCR-EC-10":
            score = _get_param(dp, "debris.compliance_score", 0)
            ok = score >= 50
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"Debris compliance score: {score:.0f}/100"

        elif cid.startswith("SRR-EC-06"):
            mass_m = _get_param(dp, "systems.mass_margin_percent", -999)
            power_m = _get_param(dp, "systems.power_margin_percent", -999)
            ok = mass_m >= 0 and power_m >= 0
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"Mass: {mass_m:.0f}%, Power: {power_m:.0f}%"

        elif cid.startswith("SRR-EC-10") or cid.startswith("PDR-EC-05"):
            rel = _get_param(dp, "reliability.mission_reliability", 0)
            target = rel_target or 0.9
            ok = rel >= target
            result["status"] = "pass" if ok else "fail"
            result["evidence_found"] = f"Reliability: {rel:.3f} vs target {target:.2f}"

        else:
            # Generic: try to evaluate from evidence string pattern
            result["status"] = "not_evaluated"
            result["evidence_found"] = "Auto-evaluation not implemented for this criterion"

    except Exception as e:
        result["status"] = "not_evaluated"
        result["evidence_found"] = f"Evaluation error: {e}"

    return result


def _get_param(dp: dict, pid: str, default: float) -> float:
    """Extract a numeric parameter value from design params dict."""
    p = dp.get(pid)
    if p is None:
        return default
    if isinstance(p, (int, float)):
        return float(p)
    if hasattr(p, "value") and isinstance(p.value, (int, float)):
        return float(p.value)
    return default
