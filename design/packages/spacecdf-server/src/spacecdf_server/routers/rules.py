"""SpaceCDF — deterministic design-rule endpoints (the engines that replace AI).

All routes are mounted under ``/api``:

* ``GET  /rules/catalogue``                          — every rule file, its sources and whether
                                                       each is a cited standard or a C2O default
* ``POST /rules/requirement-quality``                — check ad-hoc texts (live check while typing)
* ``GET  /studies/{sid}/rules/margins``              — ESA margin policy on the element tree
* ``GET  /studies/{sid}/rules/cds``                  — CubeSat Design Specification checks
* ``GET  /studies/{sid}/rules/requirements-quality`` — EARS / INCOSE checks of the study's requirements
* ``GET  /studies/{sid}/rules/verification-defaults``— ECSS-E-ST-10-02C method per requirement
* ``POST /studies/{sid}/rules/verification-defaults/apply`` — fill EMPTY methods only
* ``GET  /studies/{sid}/rules/fmeca-skeleton``       — FMECA rows from the failure-mode library
* ``GET  /studies/{sid}/rules/gates/{gate}``         — the gate checklist of the study's profile
                                                       (YAML criteria + rule checks; routers/gates.py)
* ``GET  /studies/{sid}/rules/summary``              — one call for a dashboard tile per engine

Every check item has ``{id, label{en,fr}, status, severity, detail{en,fr},
standard_ref, c2o_default, source}``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services import rule_config as rc

router = APIRouter()


# ---------------------------------------------------------------------- context

async def _context(study_id: str, form_factor: str | None = None,
                   params_override: dict[str, Any] | None = None) -> dict[str, Any]:
    from ..services.rule_inputs import form_factor as find_form_factor
    from .elements import _elements, _interfaces
    from .requirements import _requirements, ensure_requirements_loaded
    from .studies import get_study_store

    study = get_study_store().get(study_id)
    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    if study is None and not elements:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    interfaces = [i for i in _interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")]
    try:
        await ensure_requirements_loaded()
    except Exception:  # noqa: BLE001 — DB unavailable: use what is cached
        pass
    reqs = [r for r in _requirements.values() if r.get("study_id") == study_id and r.get("status") != "retired"]

    params: dict[str, Any] = {}
    target_mass = None
    if study is not None:
        iterations = getattr(study, "iterations", None) or []
        if iterations:
            params.update(iterations[-1].parameter_snapshot or {})
        req_model = getattr(study, "requirements", None)
        target_mass = getattr(req_model, "target_mass_kg", None) if req_model is not None else None
    if params_override:
        params.update(params_override)

    ff = find_form_factor(elements, params, form_factor)
    mass_limit, mass_ref = None, None
    if ff:
        cds = rc.load("cds_rules")
        lim = cds["max_mass_kg"]["values"].get(ff)
        if lim:
            mass_limit, mass_ref = float(lim), rc.ref_of(cds, cds["max_mass_kg"])
    if mass_limit is None and target_mass:
        mass_limit = float(target_mass)
        mass_ref = rc.ref_of({"sources": {}}, {"source": "c2o_default", "clause": "study mass target"})
    return {"study": study, "elements": elements, "interfaces": interfaces, "requirements": reqs,
            "params": params, "form_factor": ff, "mass_limit_kg": mass_limit, "mass_limit_ref": mass_ref}


def _guard() -> None:
    errs = rc.config_errors()
    if errs:
        raise HTTPException(status_code=500, detail={"code": "rule_config_invalid", "errors": errs})


def _wrap(fn):
    try:
        return fn()
    except rc.RuleConfigError as exc:
        raise HTTPException(status_code=500, detail={"code": "rule_config_invalid", "errors": str(exc)}) from exc


# ---------------------------------------------------------------------- catalogue

@router.get("/rules/catalogue")
async def rules_catalogue() -> dict:
    """Every rule file with its sources (cited standard vs C2O default) and validation state."""
    from ..services.requirement_quality import rule_catalogue
    out: dict[str, Any] = {"errors": rc.config_errors(), "files": {}}
    for name in rc.RULE_FILES:
        try:
            cfg = rc.load(name)
        except rc.RuleConfigError as exc:
            out["files"][name] = {"error": str(exc)}
            continue
        out["files"][name] = {"sources": {sid: rc.source(cfg, sid) for sid in cfg.get("sources", {})}}
    out["requirement_checks"] = _wrap(rule_catalogue)
    return out


class QualityBody(BaseModel):
    texts: list[str] = Field(default_factory=list, max_length=500)
    language: str | None = None


@router.post("/rules/requirement-quality")
async def requirement_quality_adhoc(body: QualityBody) -> dict:
    from ..services.requirement_quality import check_text
    _guard()
    return {"rows": _wrap(lambda: [check_text(t, body.language) for t in body.texts])}


# ---------------------------------------------------------------------- per study

@router.get("/studies/{study_id}/rules/margins")
async def study_margins(study_id: str, form_factor: str | None = Query(None),
                        gate: str | None = Query(None)) -> dict:
    """Margin policy on the element tree. The system margin is the ladder step of ``gate``
    (mdr/prr/srr/pdr/cdr), by default that of the gate the study is preparing for."""
    from ..services.margin_policy import evaluate_margins
    from .gates import study_margin_gate
    _guard()
    ctx = await _context(study_id, form_factor)
    mg = gate or study_margin_gate(ctx["study"])
    res = _wrap(lambda: evaluate_margins(ctx["elements"], ctx["params"], mass_limit_kg=ctx["mass_limit_kg"],
                                         mass_limit_ref=ctx["mass_limit_ref"], gate=mg))
    return {"study_id": study_id, "form_factor": ctx["form_factor"], **res}


@router.get("/studies/{study_id}/rules/cds")
async def study_cds(study_id: str, form_factor: str | None = Query(None)) -> dict:
    from ..services.cds_checks import evaluate_cds
    _guard()
    ctx = await _context(study_id, form_factor)
    res = _wrap(lambda: evaluate_cds(ctx["elements"], ctx["interfaces"], ctx["params"], ctx["form_factor"]))
    return {"study_id": study_id, **res}


@router.get("/studies/{study_id}/rules/requirements-quality")
async def study_requirement_quality(study_id: str) -> dict:
    from ..services.requirement_quality import check_requirements
    _guard()
    ctx = await _context(study_id)
    return {"study_id": study_id, **_wrap(lambda: check_requirements(ctx["requirements"]))}


@router.get("/studies/{study_id}/rules/verification-defaults")
async def study_verification_defaults(study_id: str) -> dict:
    from ..services.verification_defaults import suggest_all
    _guard()
    ctx = await _context(study_id)
    return {"study_id": study_id, **_wrap(lambda: suggest_all(ctx["requirements"]))}


@router.post("/studies/{study_id}/rules/verification-defaults/apply")
async def apply_verification_defaults(study_id: str) -> dict:
    """Set the default method on requirements that have NONE. Never overwrites a choice."""
    from ..services.verification_defaults import suggest
    from .requirements import update_requirement
    _guard()
    ctx = await _context(study_id)
    applied = []
    for r in ctx["requirements"]:
        if (r.get("verification_method") or "").strip():
            continue
        s = _wrap(lambda r=r: suggest(r))
        await update_requirement(r["id"], {"verification_method": s["default_method"]})
        applied.append({"requirement_id": r["id"], "code": r.get("code", ""), "method": s["default_method"],
                        "type": s["type"]})
    return {"study_id": study_id, "applied": applied, "count": len(applied)}


@router.get("/studies/{study_id}/rules/fmeca-skeleton")
async def study_fmeca_skeleton(study_id: str) -> dict:
    from ..services.fmeca_library import build_skeleton
    _guard()
    ctx = await _context(study_id)
    return {"study_id": study_id, **_wrap(lambda: build_skeleton(ctx["elements"], ctx["interfaces"]))}


@router.get("/studies/{study_id}/rules/gates/{gate}")
async def study_gate_checks(study_id: str, gate: str, form_factor: str | None = Query(None)) -> dict:
    """The review-gate checklist of the study's gate profile, evaluated on the server only.

    ``gate`` is a gate of the study's profile (mdr, prr, srr, pdr; cr in the ESA IOD profile;
    the old ``mcr`` still means MDR). The criteria of every canonical gate it covers
    (configs/gate_exit_criteria.yaml, services/gate_evaluator.py) are merged with the rule
    checks (services/gate_checks.py); each criterion carries its status, evidence, owning
    seat and the step / Fix target that closes it. No client state is read.
    """
    from .gates import evaluate_study_gate
    _guard()
    return await evaluate_study_gate(study_id, gate, form_factor)


@router.get("/studies/{study_id}/rules/summary")
async def study_rules_summary(study_id: str, form_factor: str | None = Query(None)) -> dict:
    """One summary per engine (counts only) for a dashboard."""
    from ..services.cds_checks import evaluate_cds
    from ..services.fmeca_library import build_skeleton
    from ..services.margin_policy import evaluate_margins
    from ..services.requirement_quality import check_requirements
    from ..services.verification_defaults import suggest_all
    from .gates import study_margin_gate
    _guard()
    ctx = await _context(study_id, form_factor)

    def run() -> dict:
        cds = evaluate_cds(ctx["elements"], ctx["interfaces"], ctx["params"], ctx["form_factor"])
        return {
            "margins": evaluate_margins(ctx["elements"], ctx["params"], mass_limit_kg=ctx["mass_limit_kg"],
                                        gate=study_margin_gate(ctx["study"]))["summary"],
            "cds": {"applicable": cds["applicable"], **cds["summary"]},
            "requirements_quality": check_requirements(ctx["requirements"])["summary"],
            "verification": suggest_all(ctx["requirements"])["summary"],
            "fmeca": build_skeleton(ctx["elements"], ctx["interfaces"])["summary"],
        }
    return {"study_id": study_id, "form_factor": ctx["form_factor"], **_wrap(run)}
