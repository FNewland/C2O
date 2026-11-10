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
* ``/studies/{sid}/trades...``                    — trade studies T-01... (routers/trades.py, W6)
* ``/studies/{sid}/link-budgets...``              — named link cases (routers/link_budgets.py, W4.04)
* ``/studies/{sid}/conops/...``                   — ConOps phases and document (routers/conops.py, W7)

Gate review record (W4.08):

* ``GET  /studies/{sid}/rids``                    — every RID and action of the study (``?gate=``)
* ``POST /studies/{sid}/gates/{gate}/rids``       — raise a RID or an action at a gate
* ``PATCH/DELETE /studies/{sid}/rids/{rid}``      — update (status, owner, due date, closure evidence)
* ``PUT  /studies/{sid}/gates/{gate}/record``     — chair note and go / no-go decision
* ``POST /studies/{sid}/gates/{gate}/report``     — the review report (.docx)
* ``GET  /studies/{sid}/gate-baselines/diff``    — what changed between two baselines (``?a=&b=``
                                                    baseline ids, or ``?gate=`` = against the gate before)

Gates after CDR (QR, AR, FRR) have no criteria in gate_exit_criteria.yaml yet: their checklist is
the review-record criteria of services/gate_reviews.py (earlier RIDs closed; board evidence that
the instructor signs off).

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
    try:  # the CDR model (TM/TC database, FDIR, AOCS, TT&C, operations) for the CDR criteria
        gates = (study_profile(study).get("gates") or []) if study else []
        if any("cdr" in (g.get("covers") or []) for g in gates):
            from .cdr import cdr_gate_summary
            ctx["cdr"] = await cdr_gate_summary(study_id)
        else:
            ctx["cdr"] = None
    except Exception:  # noqa: BLE001
        logger.exception("CDR model unavailable for %s", study_id)
        ctx["cdr"] = None
    ctx["rids"] = await list_review_items(study_id)
    ctx["gate_order"] = [g["id"] for g in (study_profile(study).get("gates") or [])] if study else []
    try:  # instructor sign-offs of manual / hybrid items (WP9)
        from ..seats import store as seat_store
        ctx["signoffs"] = dict((await seat_store.get_team(study_id)).get("signoffs") or {})
    except Exception:  # noqa: BLE001
        ctx["signoffs"] = {}
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
            margin_gate=mg, cdr=ctx.get("cdr"),
        )
        if canon in gp.POST_CDR:
            from ..services.gate_reviews import post_cdr_criteria
            order = ctx.get("gate_order") or []
            earlier = set(order[: order.index(pg["id"])]) if pg["id"] in order else set()
            res = {**res, "criteria": [*(res.get("criteria") or []),
                                       *post_cdr_criteria(canon, ctx.get("rids") or [], earlier)]}
        for c in res.get("criteria", []):
            c["canonical_gate"] = canon
            so = (ctx.get("signoffs") or {}).get(c.get("id"))
            if so and c.get("mode") in ("manual", "hybrid"):
                c["signoff"] = so
                if c["status"] != "pass":
                    c["status"] = c["verdict"] = "pass"
                    c["evidence_key"] = ""
                    c["evidence_found"] = f"Signed off by {so.get('by', 'the instructor')}" + (
                        f": {so['note']}" if so.get("note") else "")
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
        "review": dict((entry or {}).get("review") or {}),
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
async def set_gate_profile(study_id: str, body: ProfileBody, request: Request) -> dict:
    study = _study_or_404(study_id)
    from ..seats.service import require_gate_role
    await require_gate_role(request, study_id)
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
    """start | cancel | pass | reopen. ``pass`` saves a baseline snapshot.
    Seat studies: the Team leader or the instructor only (WP9)."""
    study = _study_or_404(study_id)
    from ..seats.service import require_gate_role
    seat = await require_gate_role(request, study_id)
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
    if seat.enabled:
        from ..seats import store as seat_store
        await seat_store.log_event(study_id, "team_leader" if seat.holds("team_leader") else "instructor", seat.person,
                                   f"gate_{body.action}", pg["id"], {"note": body.note})
        request.state.seat_logged = True
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
        "rids": [{k: r.get(k) for k in ("id", "number", "gate", "kind", "status", "owner_seat")}
                 for r in ctx.get("rids") or []],
        "trades": {k: {"status": (v.get("state") or {}).get("status"), "version": v.get("version")}
                   for k, v in _trade_records(study).items()},
        "review": dict((study.gate_states.get(pg["id"]) or {}).get("review") or {}),
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


# ─── gate review record (W4.08): RIDs and actions ─────────────────────────

def _trade_records(study) -> dict:
    from ..services.trades import normalise_records
    return normalise_records(getattr(study, "trade_records", None))


def _rid_dict(r) -> dict[str, Any]:
    return {"id": r.id, "study_id": r.study_id, "gate": r.gate, "number": r.number, "kind": r.kind,
            "criterion_id": r.criterion_id, "raised_by_seat": r.raised_by_seat, "raised_by": r.raised_by,
            "description": r.description, "severity": r.severity, "owner_seat": r.owner_seat,
            "due_date": r.due_date, "status": r.status, "closure_evidence": r.closure_evidence,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "closed_at": r.closed_at.isoformat() if r.closed_at else None}


async def list_review_items(study_id: str, gate: str | None = None) -> list[dict[str, Any]]:
    """Every RID and action of the study (in raising order); [] when the DB is unavailable."""
    try:
        from sqlalchemy import select
        from ..db.engine import get_session_factory
        from ..db.models_reviews import ReviewItemRow
        async with get_session_factory()() as s:
            q = select(ReviewItemRow).where(ReviewItemRow.study_id == study_id)
            if gate:
                q = q.where(ReviewItemRow.gate == gate)
            rows = (await s.execute(q.order_by(ReviewItemRow.created_at, ReviewItemRow.number))).scalars().all()
            return [_rid_dict(r) for r in rows]
    except Exception:  # noqa: BLE001
        logger.debug("review items unavailable for %s", study_id, exc_info=True)
        return []


_DATE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}$")


class RidBody(BaseModel):
    description: str = Field(..., min_length=1, max_length=4000)
    kind: str = "rid"
    criterion_id: str = Field("", max_length=40)
    raised_by_seat: str = Field("", max_length=40)
    severity: str = "minor"
    owner_seat: str = Field("", max_length=40)
    due_date: str = Field("", max_length=10)
    status: str = "open"
    closure_evidence: str = Field("", max_length=4000)


def _check_rid_fields(d: dict[str, Any]) -> None:
    from ..services.gate_reviews import RID_KINDS, RID_SEVERITIES, RID_STATUSES
    if "kind" in d and d["kind"] not in RID_KINDS:
        raise HTTPException(422, f"kind must be one of {', '.join(RID_KINDS)}")
    if "status" in d and d["status"] not in RID_STATUSES:
        raise HTTPException(422, f"status must be one of {', '.join(RID_STATUSES)}")
    if "severity" in d and d["severity"] not in RID_SEVERITIES:
        raise HTTPException(422, f"severity must be one of {', '.join(RID_SEVERITIES)}")
    if d.get("due_date") and not _DATE.match(str(d["due_date"])):
        raise HTTPException(422, "due_date must be YYYY-MM-DD")


@router.get("/studies/{study_id}/rids")
async def get_rids(study_id: str, gate: str | None = Query(None)) -> dict:
    _study_or_404(study_id)
    items = await list_review_items(study_id, gate)
    from ..services.gate_reviews import RID_OPEN
    return {"study_id": study_id, "items": items, "open": sum(1 for r in items if r["status"] in RID_OPEN)}


@router.post("/studies/{study_id}/gates/{gate}/rids")
async def raise_rid(study_id: str, gate: str, body: RidBody, request: Request) -> dict:
    """Raise a RID (review item discrepancy) or an action at a gate. Any editing seat may raise
    one (``raised_by_seat`` defaults to the active seat)."""
    from uuid import uuid4

    from ..db.engine import get_session_factory
    from ..db.models_reviews import ReviewItemRow
    from ..services.gate_reviews import rid_number
    study = _study_or_404(study_id)
    pg = gp.gate_of(study_profile(study), gate)
    if pg is None:
        raise HTTPException(404, f"Unknown review gate: {gate}")
    d = body.model_dump()
    _check_rid_fields(d)
    seat = d["raised_by_seat"]
    if not seat:
        try:
            from ..seats.service import seat_ctx
            ctx = await seat_ctx(request, study_id)
            seat = ctx.active or ""
        except Exception:  # noqa: BLE001
            seat = ""
    existing = [r for r in await list_review_items(study_id, pg["id"]) if r["kind"] == d["kind"]]
    row = ReviewItemRow(id=uuid4().hex[:16], study_id=study_id, gate=pg["id"],
                        number=rid_number(d["kind"], pg.get("short") or pg["id"], len(existing) + 1),
                        kind=d["kind"], criterion_id=d["criterion_id"], raised_by_seat=seat,
                        raised_by=_who(request, ""), description=d["description"].strip(),
                        severity=d["severity"], owner_seat=d["owner_seat"], due_date=d["due_date"],
                        status=d["status"], closure_evidence=d["closure_evidence"])
    async with get_session_factory()() as s:
        s.add(row)
        await s.commit()
        await s.refresh(row)
        out = _rid_dict(row)
    await _broadcast(study_id, "study_records_changed", {"kind": "rids"})
    return out


@router.patch("/studies/{study_id}/rids/{rid_id}")
async def update_rid(study_id: str, rid_id: str, body: dict[str, Any]) -> dict:
    from datetime import datetime, timezone

    from ..db.engine import get_session_factory
    from ..db.models_reviews import ReviewItemRow
    _study_or_404(study_id)
    fields = ("description", "kind", "criterion_id", "severity", "owner_seat", "due_date", "status",
              "closure_evidence", "raised_by_seat")
    patch = {k: v for k, v in (body or {}).items() if k in fields}
    _check_rid_fields(patch)
    async with get_session_factory()() as s:
        row = await s.get(ReviewItemRow, rid_id)
        if row is None or row.study_id != study_id:
            raise HTTPException(404, f"RID {rid_id} not found")
        for k, v in patch.items():
            setattr(row, k, str(v if v is not None else "")[:4000])
        if "status" in patch:
            row.closed_at = datetime.now(timezone.utc) if patch["status"] in ("closed", "rejected") else None
        await s.commit()
        await s.refresh(row)
        out = _rid_dict(row)
    await _broadcast(study_id, "study_records_changed", {"kind": "rids"})
    return out


@router.delete("/studies/{study_id}/rids/{rid_id}")
async def delete_rid(study_id: str, rid_id: str) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_reviews import ReviewItemRow
    _study_or_404(study_id)
    async with get_session_factory()() as s:
        row = await s.get(ReviewItemRow, rid_id)
        if row is None or row.study_id != study_id:
            raise HTTPException(404, f"RID {rid_id} not found")
        await s.delete(row)
        await s.commit()
    await _broadcast(study_id, "study_records_changed", {"kind": "rids"})
    return {"deleted": rid_id}


class RecordBody(BaseModel):
    chair_note: str = Field("", max_length=4000)
    decision: str | None = None      # go | go_with_actions | no_go
    board: str = Field("", max_length=1000)
    by: str = ""


@router.put("/studies/{study_id}/gates/{gate}/record")
async def put_review_record(study_id: str, gate: str, body: RecordBody, request: Request) -> dict:
    """The review's chair note and go / no-go decision (Team leader or instructor in a seat study)."""
    from ..services.gate_reviews import DECISIONS, clean_review
    study = _study_or_404(study_id)
    from ..seats.service import require_gate_role
    await require_gate_role(request, study_id)
    pg = gp.gate_of(study_profile(study), gate)
    if pg is None:
        raise HTTPException(404, f"Unknown review gate: {gate}")
    if body.decision is not None and body.decision not in DECISIONS:
        raise HTTPException(422, f"decision must be one of {', '.join(DECISIONS)}")
    states = dict(study.gate_states or {})
    entry = {"state": None, "history": [], "baselines": [], **(states.get(pg["id"]) or {})}
    entry["review"] = clean_review(body.model_dump(), by=_who(request, body.by))
    states[pg["id"]] = entry
    study.gate_states = states
    await _save(study)
    await _broadcast(study_id, "gate_state_changed", {"gate": pg["id"], "state": entry.get("state")})
    return {"gate": pg["id"], "review": entry["review"]}


async def review_report_data(study_id: str, gate: str) -> dict[str, Any]:
    """Everything the review report shows: the gate evaluation, the review record, the RIDs and
    actions raised at this gate and still open from earlier ones, and the baseline diff against
    the previous gate's baseline."""
    from ..services.gate_reviews import RID_OPEN
    study = _study_or_404(study_id)
    ev = await evaluate_study_gate(study_id, gate)
    gid = ev["gate"]["id"]
    entry = (study.gate_states or {}).get(gid) or {}
    rids = await list_review_items(study_id)
    order = [g["id"] for g in ev["profile"]["gates"]]
    earlier = set(order[: order.index(gid)]) if gid in order else set()
    diff = None
    try:
        diff = await baseline_diff(study_id, a=None, b=None, gate=gid)
    except HTTPException:
        diff = None
    return {"study_name": study.name, "evaluation": ev, "review": entry.get("review") or {},
            "history": entry.get("history") or [],
            "rids": [r for r in rids if r["gate"] == gid],
            "carried": [r for r in rids if r["gate"] in earlier and r["status"] in RID_OPEN],
            "diff": diff}


@router.post("/studies/{study_id}/gates/{gate}/report")
async def gate_review_report(study_id: str, gate: str, lang: str = Query("en")):
    """The review report (.docx): criteria with results and evidence, open items, RIDs and
    actions, chair note, go / no-go, and the baseline diff against the previous gate."""
    import io

    from fastapi.responses import StreamingResponse

    from ..services.docx.review_report import generate_review_report_docx
    data = await review_report_data(study_id, gate)
    blob = generate_review_report_docx(data, lang=lang)
    short = data["evaluation"]["gate"]["short"].replace("/", "-")
    name = (data["study_name"] or "study").replace(" ", "_")
    return StreamingResponse(io.BytesIO(blob),
                             media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             headers={"Content-Disposition": f'attachment; filename="SpaceCDF_{short}_review_report_{name}.docx"'})


@router.get("/studies/{study_id}/gate-baselines/diff")
async def baseline_diff(study_id: str, a: str | None = Query(None), b: str | None = Query(None),
                        gate: str | None = Query(None)) -> dict:
    """Changes between two baselines: ``a`` and ``b`` (baseline ids), or ``gate``: the latest
    baseline of that gate against the latest baseline of the gate before it."""
    from ..db.gate_baseline_repo import get_baseline, list_baselines
    from ..services.gate_reviews import diff_snapshots
    study = _study_or_404(study_id)
    if gate:
        profile = study_profile(study)
        pg = gp.gate_of(profile, gate)
        if pg is None:
            raise HTTPException(404, f"Unknown review gate: {gate}")
        order = [g["id"] for g in profile.get("gates") or []]
        rows = await list_baselines(study_id)
        latest: dict[str, dict] = {}
        for r in rows:
            latest[r["gate"]] = r
        prev = [g for g in order[: order.index(pg["id"])] if g in latest]
        if pg["id"] not in latest or not prev:
            raise HTTPException(404, "No two baselines to compare")
        a, b = latest[prev[-1]]["id"], latest[pg["id"]]["id"]
    if not a or not b:
        raise HTTPException(422, "Give two baseline ids (a, b) or a gate")
    ra, rb = await get_baseline(a), await get_baseline(b)
    if not ra or not rb or ra["study_id"] != study_id or rb["study_id"] != study_id:
        raise HTTPException(404, "Baseline not found")
    return {"a": {k: ra[k] for k in ("id", "gate", "created_at", "created_by")},
            "b": {k: rb[k] for k in ("id", "gate", "created_at", "created_by")},
            "changes": diff_snapshots(ra.get("snapshot") or {}, rb.get("snapshot") or {})}


# ─── sub-routers of the Decide / mission / ConOps work (wave 1, agent D) ───
# Included here so app.py needs no new line; they share the "/api" prefix of this router.
from . import conops as _conops_router  # noqa: E402
from . import link_budgets as _link_budgets_router  # noqa: E402
from . import trades as _trades_router  # noqa: E402

router.include_router(_trades_router.router)
router.include_router(_link_budgets_router.router)
router.include_router(_conops_router.study_router)
