"""SpaceCDF — review gates per study profile, and the study's team records (WP0/WP6, Nov 2026).

All routes are mounted under ``/api``:

* ``GET  /gate-profiles``                         — the profiles of configs/gate_profiles.yaml
* ``GET  /studies/{sid}/gates``                   — the study's profile and each gate's state
* ``PUT  /studies/{sid}/gate-profile``            — choose the profile ({"profile": id})
* ``GET  /studies/{sid}/rules/gates/{gate}``      — the gate checklist, evaluated on the server
                                                    from the stored study only (routers/rules.py
                                                    delegates here)
* ``POST /studies/{sid}/gates/{gate}/review``     — {"action": start|cancel|pass|reopen}
* ``GET  /studies/{sid}/gates/baselines/{bid}``   — one baseline snapshot
* ``GET/POST /studies/{sid}/risks``, ``PATCH/DELETE /studies/{sid}/risks/{rid}``,
  ``POST /studies/{sid}/risks/import``            — the team risk register (was localStorage)
* ``GET/PUT /studies/{sid}/trades/{key}``         — trade records, e.g. the Pugh matrix
                                                    (was one global localStorage key)

The checklist never reads client state: the request carries no mission need and no
parameters (walkthrough top problems 2 and 19).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..services import gate_profiles as gp
from ..services.gate_reviews import GateTransitionError, display_state, transition

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── server-side inputs ───────────────────────────────────────────────────

async def design_params(study_id: str, study: Any) -> dict[str, Any]:
    """The study's design-loop parameters: the last iteration in memory, else the series
    of the last design-loop run (kept on disk, so it survives a restart)."""
    params: dict[str, Any] = {}
    iterations = getattr(study, "iterations", None) or []
    if iterations:
        params.update(iterations[-1].parameter_snapshot or {})
    if params:
        return params
    try:
        from ..db import analysis_repo
        from ..services.analysis_results import load_series
        run = await analysis_repo.get_last_run(study_id, "design_loop", None)
        series = load_series((run or {}).get("series_ref")) if run else None
        for pid, p in ((series or {}).get("parameters") or {}).items():
            v = p.get("value") if isinstance(p, dict) else p
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                params[pid] = float(v)
    except Exception:  # noqa: BLE001 — no DB / no run: evaluate without parameters
        logger.debug("no design-loop run for %s", study_id, exc_info=True)
    return params


async def _function_count(study_id: str, study: Any) -> int:
    n = 0
    try:
        from ..db.function_repo import list_functions_by_study
        n = len(await list_functions_by_study(study_id))
    except Exception:  # noqa: BLE001
        n = 0
    if not n and study is not None:
        n = len(getattr(getattr(study, "functional_decomposition", None), "functions", None) or [])
    return n


async def gate_inputs(study_id: str, form_factor: str | None = None) -> dict[str, Any]:
    """Everything a gate evaluation reads, from the server's stored study only."""
    from .rules import _context
    ctx = await _context(study_id, form_factor)
    study = ctx["study"]
    if not ctx["params"]:
        ctx["params"] = await design_params(study_id, study)
    ctx["function_count"] = await _function_count(study_id, study)
    ctx["risks"] = list(getattr(study, "risk_register", None) or []) if study else []
    return ctx


def study_profile(study: Any) -> dict[str, Any]:
    return gp.get_profile(getattr(study, "gate_profile", "") or None)


def _seat_labels() -> dict[str, dict[str, str]]:
    try:
        from ..logbook.decisions import catalogue
        return {s["id"]: dict(s.get("label") or {}) for s in catalogue().get("seats") or []}
    except Exception:  # noqa: BLE001
        return {}


def _evaluate(ctx: dict[str, Any], pg: dict[str, Any]) -> dict[str, Any]:
    """Union of the criteria (and rule checks) of the canonical gates ``pg`` covers."""
    from ..services.gate_checks import evaluate_gate_checks
    from ..services.gate_evaluator import evaluate_gate
    from ..services.margin_policy import system_margin_percent

    study = ctx["study"]
    req_model = getattr(study, "requirements", None) if study else None
    mg = gp.margin_gate(pg)
    seats = _seat_labels()
    criteria: list[dict] = []
    checks: list[dict] = []
    computed: list[dict] = []
    seen_checks: set[str] = set()
    for canon in pg.get("covers") or []:
        res = evaluate_gate(
            canon,
            mission_need=getattr(study, "mission_need", None) if study else None,
            design_params={**ctx["params"], "_elements": ctx["elements"]},
            target_mass_kg=getattr(req_model, "target_mass_kg", None) if req_model else None,
            target_cost_meur=getattr(req_model, "target_cost_meur", None) if req_model else None,
            reliability_target=getattr(req_model, "reliability_target", None) if req_model else None,
            requirements=ctx["requirements"], elements=ctx["elements"], interfaces=ctx["interfaces"],
            mission=req_model, function_count=ctx.get("function_count"), risks=ctx.get("risks"),
            margin_gate=mg,
        )
        for c in res.get("criteria", []):
            c["canonical_gate"] = canon
            c["owner_seat_label"] = seats.get(c.get("owner_seat") or "")
            c["step_label"] = gp.step_label(c.get("step"))
            criteria.append(c)
        chk = evaluate_gate_checks(res.get("gate") or canon.upper(), {**ctx, "margin_gate": mg}, res.get("criteria"))
        for item in chk["checks"]:
            if item["id"] not in seen_checks:
                seen_checks.add(item["id"])
                checks.append(item)
        computed.extend(chk["computed_criteria"])
    must = [c for c in criteria if c["priority"] == "must_pass"]
    summary = {
        "total": len(criteria),
        "pass": sum(1 for c in criteria if c["status"] == "pass"),
        "fail": sum(1 for c in criteria if c["status"] == "fail"),
        "manual": sum(1 for c in criteria if c["status"] == "manual"),
        "not_evaluated": sum(1 for c in criteria if c["status"] == "not_evaluated"),
        "advisory": sum(1 for c in criteria if c["verdict"] == "advisory"),
        "must_pass": len(must),
        "must_pass_met": sum(1 for c in must if c["status"] == "pass"),
    }
    ready = bool(must) and all(c["status"] == "pass" for c in must)
    pending = bool(must) and all(c["status"] in ("pass", "manual") for c in must)
    open_owners = sorted({c.get("owner_seat") for c in must if c["status"] != "pass" and c.get("owner_seat")})
    return {"criteria": criteria, "checks": checks, "computed_criteria": computed, "summary": summary,
            "ready": ready, "ready_pending_manual": pending, "open_owner_seats": open_owners,
            "system_margin": {"gate": mg, "mass_percent": system_margin_percent(mg, "mass"),
                              "power_percent": system_margin_percent(mg, "power")}}


def _gate_public(pg: dict[str, Any]) -> dict[str, Any]:
    return {"id": pg["id"], "short": pg.get("short", pg["id"].upper()), "name": pg.get("name"),
            "covers": list(pg.get("covers") or []), "margin_gate": gp.margin_gate(pg)}


async def evaluate_study_gate(study_id: str, gate: str, form_factor: str | None = None,
                              ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or await gate_inputs(study_id, form_factor)
    study = ctx["study"]
    profile = study_profile(study)
    pg = gp.gate_of(profile, gate)
    if pg is None:
        raise HTTPException(status_code=404, detail=f"Unknown review gate for profile {profile['id']}: {gate}")
    ev = _evaluate(ctx, pg)
    entry = (getattr(study, "gate_states", None) or {}).get(pg["id"]) if study else None
    return {
        "study_id": study_id, "study_found": study is not None,
        "profile": gp.public_profile(profile), "gate": _gate_public(pg),
        "state": display_state(entry, ev["ready"]),
        "history": list((entry or {}).get("history") or []),
        "baselines": list((entry or {}).get("baselines") or []),
        "products_baselined": gp.products_baselined(pg),
        **ev,
    }


def current_gate(profile: dict[str, Any], study: Any) -> dict[str, Any] | None:
    """The first gate of the profile that has not passed (None when all passed)."""
    states = getattr(study, "gate_states", None) or {}
    for g in profile.get("gates") or []:
        if (states.get(g["id"]) or {}).get("state") != "passed":
            return g
    return None


def study_margin_gate(study: Any) -> str | None:
    """The margin-ladder step for the study's budgets: that of the gate it prepares for."""
    if study is None:
        return None
    profile = study_profile(study)
    g = current_gate(profile, study)
    return gp.margin_gate(g) if g else "cdr"


# ─── routes: profiles and gates ───────────────────────────────────────────

@router.get("/gate-profiles")
async def list_gate_profiles() -> dict:
    data = gp.load()
    return {"default": gp.default_profile_id(), "profiles": gp.list_profiles(),
            "steps": data.get("steps") or {}, "errors": gp.validate(data)}


def _study_or_404(study_id: str):
    from .studies import get_study_store
    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    return study


@router.get("/studies/{study_id}/gates")
async def study_gates(study_id: str) -> dict:
    """The study's profile, each gate's state and must-pass count, and the current gate."""
    study = _study_or_404(study_id)
    ctx = await gate_inputs(study_id)
    profile = study_profile(study)
    cur = current_gate(profile, study)
    gates = []
    for pg in profile.get("gates") or []:
        ev = _evaluate(ctx, pg)
        entry = (study.gate_states or {}).get(pg["id"])
        gates.append({**_gate_public(pg), "state": display_state(entry, ev["ready"]),
                      "ready": ev["ready"], "summary": ev["summary"],
                      "open_owner_seats": ev["open_owner_seats"],
                      "passed_at": next((h["at"] for h in reversed((entry or {}).get("history") or [])
                                         if h.get("to") == "passed"), None)})
    return {"study_id": study_id, "profile": gp.public_profile(profile),
            "current_gate": cur["id"] if cur else None, "gates": gates}


class ProfileBody(BaseModel):
    profile: str


@router.put("/studies/{study_id}/gate-profile")
async def set_gate_profile(study_id: str, body: ProfileBody) -> dict:
    study = _study_or_404(study_id)
    if body.profile not in gp.profile_ids():
        raise HTTPException(status_code=400, detail=f"Unknown gate profile: {body.profile}")
    study.gate_profile = body.profile
    await _save(study)
    await _broadcast(study_id, "gate_profile_changed", {"profile": body.profile})
    return {"study_id": study_id, "profile": gp.public_profile(gp.get_profile(body.profile))}


class ReviewBody(BaseModel):
    action: str
    note: str = ""
    by: str = ""


def _who(request: Request, body_by: str) -> str:
    raw = request.headers.get("x-goog-authenticated-user-email", "")
    email = raw.split(":", 1)[-1] if raw else ""
    return email or body_by.strip()[:120]


@router.post("/studies/{study_id}/gates/{gate}/review")
async def gate_review_action(study_id: str, gate: str, body: ReviewBody, request: Request) -> dict:
    """start | cancel | pass | reopen. ``pass`` saves a baseline snapshot."""
    study = _study_or_404(study_id)
    ctx = await gate_inputs(study_id)
    profile = study_profile(study)
    pg = gp.gate_of(profile, gate)
    if pg is None:
        raise HTTPException(status_code=404, detail=f"Unknown review gate: {gate}")
    ev = _evaluate(ctx, pg)
    states = dict(study.gate_states or {})
    by = _who(request, body.by)
    try:
        entry = transition(states.get(pg["id"]), body.action, ready=ev["ready"], by=by, note=body.note)
    except GateTransitionError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code, "message": str(exc)}) from exc
    if body.action == "pass":
        baseline = await _save_baseline(study, profile, pg, ev, ctx, by)
        entry["baselines"] = [*entry.get("baselines", []), baseline]
    states[pg["id"]] = entry
    study.gate_states = states
    await _save(study)
    await _broadcast(study_id, "gate_state_changed", {"gate": pg["id"], "state": entry.get("state")})
    return await evaluate_study_gate(study_id, pg["id"])


async def _save_baseline(study, profile, pg, ev, ctx, by) -> dict:
    from datetime import datetime, timezone
    products = gp.products_baselined(pg)
    snapshot = {
        "profile": profile["id"], "gate": pg["id"], "covers": pg.get("covers"),
        "mission_need": study.mission_need.model_dump(mode="json"),
        "requirements_model": study.requirements.model_dump(mode="json"),
        "elements": ctx["elements"], "interfaces": ctx["interfaces"], "requirements": ctx["requirements"],
        "risk_register": list(study.risk_register or []), "parameters": ctx["params"],
        "criteria": [{k: c.get(k) for k in ("id", "status", "verdict", "evidence_found")} for c in ev["criteria"]],
        "products": products,
    }
    summary = {"summary": ev["summary"], "products": [p["id"] for p in products],
               "elements": len(ctx["elements"]), "requirements": len(ctx["requirements"])}
    try:
        from ..db.gate_baseline_repo import save_baseline
        row = await save_baseline(study.id, pg["id"], profile["id"], by, summary, snapshot)
        return {"id": row["id"], "at": row["created_at"], "by": by, "products": summary["products"]}
    except Exception:  # noqa: BLE001 — the pass is recorded even if the DB is down
        logger.exception("baseline snapshot not saved for %s/%s", study.id, pg["id"])
        return {"id": None, "at": datetime.now(timezone.utc).isoformat(), "by": by,
                "products": summary["products"], "error": "snapshot not saved"}


@router.get("/studies/{study_id}/gates/baselines/{baseline_id}")
async def get_gate_baseline(study_id: str, baseline_id: str) -> dict:
    from ..db.gate_baseline_repo import get_baseline
    row = await get_baseline(baseline_id)
    if row is None or row["study_id"] != study_id:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return row


# ─── team records: risk register and trade records ────────────────────────

RISK_FIELDS = ("description", "category", "likelihood", "consequence", "mitigation", "owner", "status", "source")
RISK_STATUSES = ("open", "mitigating", "closed", "accepted")


class RiskBody(BaseModel):
    description: str = Field("", max_length=2000)
    category: str = Field("Technical", max_length=40)
    likelihood: int = Field(3, ge=1, le=5)
    consequence: int = Field(3, ge=1, le=5)
    mitigation: str = Field("", max_length=2000)
    owner: str = Field("", max_length=120)
    status: str = "open"
    source: str = Field("", max_length=120)


def _clean_risk(d: dict[str, Any], rid: str) -> dict[str, Any]:
    r = {k: d.get(k) for k in RISK_FIELDS if k in d}
    r["id"] = rid
    try:
        r["likelihood"] = min(5, max(1, int(r.get("likelihood") or 3)))
        r["consequence"] = min(5, max(1, int(r.get("consequence") or 3)))
    except (TypeError, ValueError):
        r["likelihood"], r["consequence"] = 3, 3
    r["rpn"] = r["likelihood"] * r["consequence"]
    if r.get("status") not in RISK_STATUSES:
        r["status"] = "open"
    for k in ("description", "category", "mitigation", "owner", "source"):
        r[k] = str(r.get(k) or "")[:2000]
    return r


def _next_risk_id(risks: list[dict]) -> str:
    n = 0
    for r in risks:
        try:
            n = max(n, int(str(r.get("id", "")).split("-")[-1]))
        except ValueError:
            continue
    return f"RSK-{n + 1:03d}"


@router.get("/studies/{study_id}/risks")
async def list_risks(study_id: str) -> list[dict]:
    return list(_study_or_404(study_id).risk_register or [])


@router.post("/studies/{study_id}/risks")
async def add_risk(study_id: str, body: RiskBody) -> dict:
    study = _study_or_404(study_id)
    risks = list(study.risk_register or [])
    r = _clean_risk(body.model_dump(), _next_risk_id(risks))
    study.risk_register = [*risks, r]
    await _save(study)
    await _broadcast(study_id, "study_records_changed", {"kind": "risks"})
    return r


@router.patch("/studies/{study_id}/risks/{risk_id}")
async def update_risk(study_id: str, risk_id: str, body: dict[str, Any]) -> dict:
    study = _study_or_404(study_id)
    risks = list(study.risk_register or [])
    for i, r in enumerate(risks):
        if r.get("id") == risk_id:
            risks[i] = _clean_risk({**r, **{k: v for k, v in body.items() if k in RISK_FIELDS}}, risk_id)
            study.risk_register = risks
            await _save(study)
            await _broadcast(study_id, "study_records_changed", {"kind": "risks"})
            return risks[i]
    raise HTTPException(status_code=404, detail=f"Risk {risk_id} not found")


@router.delete("/studies/{study_id}/risks/{risk_id}")
async def delete_risk(study_id: str, risk_id: str) -> dict:
    study = _study_or_404(study_id)
    risks = list(study.risk_register or [])
    keep = [r for r in risks if r.get("id") != risk_id]
    if len(keep) == len(risks):
        raise HTTPException(status_code=404, detail=f"Risk {risk_id} not found")
    study.risk_register = keep
    await _save(study)
    await _broadcast(study_id, "study_records_changed", {"kind": "risks"})
    return {"deleted": risk_id}


class RiskImport(BaseModel):
    risks: list[dict[str, Any]] = Field(default_factory=list, max_length=500)
    only_if_empty: bool = True


@router.post("/studies/{study_id}/risks/import")
async def import_risks(study_id: str, body: RiskImport) -> dict:
    """Move a browser's old localStorage register (or a save file's) to the study."""
    study = _study_or_404(study_id)
    risks = list(study.risk_register or [])
    if body.only_if_empty and risks:
        return {"imported": 0, "risks": risks}
    taken = {r.get("id") for r in risks}
    added = 0
    for raw in body.risks:
        if not isinstance(raw, dict) or not str(raw.get("description") or "").strip():
            continue
        rid = str(raw.get("id") or "")
        if not rid or rid in taken or len(rid) > 32:
            rid = _next_risk_id(risks)
        r = _clean_risk(raw, rid)
        risks.append(r)
        taken.add(rid)
        added += 1
    study.risk_register = risks
    if added:
        await _save(study)
        await _broadcast(study_id, "study_records_changed", {"kind": "risks"})
    return {"imported": added, "risks": risks}


TRADE_KEYS = ("pugh",)


class TradeBody(BaseModel):
    state: dict[str, Any]
    version: int | None = None   # the version the client edited; None = overwrite


@router.get("/studies/{study_id}/trades/{key}")
async def get_trade(study_id: str, key: str) -> dict:
    if key not in TRADE_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown trade record: {key}")
    rec = (_study_or_404(study_id).trade_records or {}).get(key)
    return rec or {"state": None, "version": 0}


@router.put("/studies/{study_id}/trades/{key}")
async def put_trade(study_id: str, key: str, body: TradeBody) -> dict:
    if key not in TRADE_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown trade record: {key}")
    study = _study_or_404(study_id)
    recs = dict(study.trade_records or {})
    cur = recs.get(key) or {"version": 0}
    if body.version is not None and body.version != cur.get("version", 0):
        raise HTTPException(status_code=409, detail={"code": "stale", "current": cur})
    import json
    if len(json.dumps(body.state)) > 200_000:
        raise HTTPException(status_code=413, detail="Trade record too large")
    recs[key] = {"state": body.state, "version": int(cur.get("version", 0)) + 1}
    study.trade_records = recs
    await _save(study)
    await _broadcast(study_id, "study_records_changed", {"kind": f"trade:{key}"})
    return recs[key]


# ─── helpers ──────────────────────────────────────────────────────────────

async def _save(study) -> None:
    from ..db.study_repo import db_save_study
    await db_save_study(study)


async def _broadcast(study_id: str, event: str, payload: dict) -> None:
    try:
        from .ws import _broadcast_study
        await _broadcast_study(study_id, {"type": event, "study_id": study_id, **payload})
    except Exception:  # noqa: BLE001
        logger.debug("broadcast %s failed", event, exc_info=True)


@router.get("/studies/{study_id}/rules/margin-ladder")
async def study_margin_ladder(study_id: str, gate: str | None = Query(None)) -> dict:
    """The C2O system margin ladder and the step that applies to this study now."""
    from ..services.margin_policy import ladder, system_margin_percent
    study = _study_or_404(study_id)
    g = gp.legacy_gate_id(gate) if gate else study_margin_gate(study)
    return {"study_id": study_id, "gate": g, "mass_percent": system_margin_percent(g, "mass"),
            "power_percent": system_margin_percent(g, "power"), **ladder()}
