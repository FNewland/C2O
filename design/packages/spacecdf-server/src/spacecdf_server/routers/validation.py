"""Validation activities and need validation: the right side of the V that asks "did we build the
right thing?" (needs → MOEs → validation). Owner S (wave 3, 3.S5).

    GET    /api/studies/{sid}/validation/activities          V1 … rows
    POST   /api/studies/{sid}/validation/activities          add one
    PATCH  /api/studies/{sid}/validation/activities/{id}     edit one (id or code)
    POST   /api/studies/{sid}/validation/propose             one proposed activity per primary objective
    POST   /api/studies/{sid}/validation/import              the v2 validation plan and the need validation
    GET    /api/studies/{sid}/validation/need-validation     one row per stakeholder need
    GET    /api/studies/{sid}/validation/coverage            per objective: activities, stakeholder performer

Tables ``se_validation_activities`` and ``se_need_validation`` (``db/models_se.py``).

Verification asks whether the product meets its requirements; validation asks whether it meets
the need of the people it is for, in their setting. So an activity names a **performer** from
the stakeholder register; one performed by the engineering team alone is flagged
(``engineers_only``): the team cannot validate its own reading of the need.

:func:`coverage` is the evidence function R wires into the SRR / FRR validation criteria (3.R4).
ORR and CRR are validation **stages** here, not review gates (PI default).
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select

from ._lookup import study_or_404

router = APIRouter()

#: validation stages, in life-cycle order (ORR and CRR are stages, not gates; PI default)
STAGES = ("MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "ORR", "FRR", "CRR", "IOV", "PHASE_E")
STAGE_LABEL = {
    "MDR": {"en": "Mission definition review", "fr": "Revue de définition de la mission"},
    "PRR": {"en": "Preliminary requirements review", "fr": "Revue des exigences préliminaires"},
    "SRR": {"en": "System requirements review", "fr": "Revue des exigences système"},
    "PDR": {"en": "Preliminary design review", "fr": "Revue de conception préliminaire"},
    "CDR": {"en": "Critical design review", "fr": "Revue critique de conception"},
    "QR": {"en": "Qualification review", "fr": "Revue de qualification"},
    "AR": {"en": "Acceptance review", "fr": "Revue de recette"},
    "ORR": {"en": "Operational readiness (stage)", "fr": "Aptitude opérationnelle (étape)"},
    "FRR": {"en": "Flight readiness review", "fr": "Revue d’aptitude au vol"},
    "CRR": {"en": "Commissioning results (stage)", "fr": "Résultats de la mise en service (étape)"},
    "IOV": {"en": "In-orbit validation", "fr": "Validation en orbite"},
    "PHASE_E": {"en": "Operations (Phase E)", "fr": "Exploitation (phase E)"},
}
METHODS = ("walkthrough", "scenario_trace", "simulated_products", "operational_rehearsal", "in_orbit_matchup",
           "operational_assessment", "results_review", "user_acceptance", "other")
STATUSES = ("proposed", "planned", "in_progress", "done", "failed")
_ACT_FIELDS = ("code", "title", "title_fr", "method", "environment", "stage", "performer", "acceptance", "evidence",
               "status", "order")

#: performers that are the engineering team itself (flagged "engineers only")
_ENGINEER_RE = re.compile(r"\b(engineer|engineering team|student team|design team|the team)\b", re.I)
#: words of a ``when`` / ``stage`` text -> stage id (first match wins, in text order)
_STAGE_WORDS = (("phase e", "PHASE_E"), ("first break-up", "PHASE_E"), ("fire season", "PHASE_E"),
                ("end of year", "PHASE_E"), ("end of mission", "PHASE_E"), ("commissioning", "CRR"),
                ("launch -", "FRR"), ("launch-", "FRR"))
_METHOD_WORDS = (("walkthrough", "walkthrough"), ("trace each conops", "scenario_trace"),
                 ("simulated", "simulated_products"), ("rehearsal", "operational_rehearsal"),
                 ("matchup", "in_orbit_matchup"), ("seasonal assessment", "operational_assessment"),
                 ("delivered per site agreement", "operational_assessment"), ("mops measured", "results_review"),
                 ("moes measured", "results_review"))


def _uid() -> str:
    return uuid.uuid4().hex


def stages_in(text: str) -> list[str]:
    """Stage ids named in a ``when`` / ``stage`` text, in order (``"MDR to PRR"`` → [MDR, PRR])."""
    t = str(text or "")
    found: list[tuple[int, str]] = []
    for m in re.finditer(r"\b(MDR|PRR|SRR|PDR|CDR|QR|AR|ORR|FRR|CRR|IOV)\b", t):
        found.append((m.start(), m.group(1)))
    low = t.lower()
    for word, sid in _STAGE_WORDS:
        i = low.find(word)
        if i >= 0:
            found.append((i, sid))
    out: list[str] = []
    for _, sid in sorted(found):
        if sid not in out:
            out.append(sid)
    return out


def method_of(text: str) -> str:
    low = str(text or "").lower()
    return next((m for w, m in _METHOD_WORDS if w in low), "other")


def engineers_only(performer: str, performer_ids: list[str], stakeholders: list[dict]) -> bool:
    """True when nobody but the engineering team performs the activity."""
    by_id = {s.get("id"): s for s in stakeholders}
    known = [by_id[i] for i in performer_ids if i in by_id]
    if known:
        return all(_ENGINEER_RE.search(str(s.get("name") or "")) for s in known)
    p = str(performer or "").strip()
    if not p:
        return True
    return bool(_ENGINEER_RE.search(p)) and not re.search(
        r"stakeholder|communit|operator|science|sponsor|user|regulator|launch", p, re.I)


def performer_ids_for(text: str, stakeholders: list[dict]) -> list[str]:
    """Stakeholder ids a free-text performer names ("operators, science team, community
    representatives" → the operations team, the science team, the community bodies)."""
    low = str(text or "").lower()
    if re.search(r"each stakeholder group|every stakeholder|all stakeholders", low):
        return [s["id"] for s in stakeholders if s.get("id")]
    keys = (("communit", ("communit",)), ("operator", ("operations team", "mission operations")), ("science", ("science",)),
            ("sponsor", ("funding", "sponsor")), ("regulator", ("regulator", "licens")), ("launch", ("launch",)),
            ("user", ("data users", "open-data")))
    out: list[str] = []
    for word, names in keys:
        if word in low:
            for s in stakeholders:
                n = str(s.get("name") or "").lower()
                if any(x in n for x in names) and s.get("id") not in out:
                    out.append(s["id"])
    return out


def _act_dict(r, stakeholders: list[dict] | None = None) -> dict[str, Any]:
    d = dict(r.data_json or {})
    pids = list(d.get("performer_ids") or [])
    out = {"id": r.id, "study_id": r.study_id, "code": r.code, "title": r.title, "title_fr": r.title_fr,
           "objectives": list(r.objectives_json or []), "needs": list(r.needs_json or []),
           "moes": list(r.moes_json or []), "requirement_codes": list(r.requirement_codes_json or []),
           "method": r.method, "method_text": d.get("method_text", ""), "environment": r.environment,
           "stage": r.stage, "stages": list(d.get("stages") or ([r.stage] if r.stage else [])),
           "when": d.get("when", ""), "performer": r.performer, "performer_ids": pids,
           "acceptance": r.acceptance, "evidence": r.evidence, "status": r.status, "origin": r.origin,
           "order": r.order}
    out["engineers_only"] = engineers_only(r.performer, pids, stakeholders or [])
    return out


def _nv_dict(r) -> dict[str, Any]:
    d = dict(r.data_json or {})
    return {"id": r.id, "study_id": r.study_id, "need_code": r.need_code,
            "activity_codes": list(r.activity_codes_json or []), "method": r.method, "criterion": r.criterion,
            "stage": r.stage, "stages": list(d.get("stages") or []), "stage_text": d.get("stage_text", ""),
            "status": r.status, "order": r.order}


def _stakeholders(study) -> list[dict]:
    try:
        return [s.model_dump(mode="json") for s in study.mission_need.stakeholders]
    except Exception:  # noqa: BLE001
        return []


async def list_activities(study_id: str) -> list[dict[str, Any]]:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeValidationActivityRow as Row
    from .studies import get_study_store
    stk = _stakeholders(get_study_store().get(study_id))
    async with get_session_factory()() as s:
        rows = (await s.execute(select(Row).where(Row.study_id == study_id).order_by(Row.order, Row.code))).scalars().all()
        return [_act_dict(r, stk) for r in rows]


async def list_need_validation(study_id: str) -> list[dict[str, Any]]:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeNeedValidationRow as Row
    async with get_session_factory()() as s:
        rows = (await s.execute(select(Row).where(Row.study_id == study_id).order_by(Row.order, Row.need_code))
                ).scalars().all()
        return [_nv_dict(r) for r in rows]


def _apply(row, body: dict[str, Any], stakeholders: list[dict]) -> None:
    for k in _ACT_FIELDS:
        if k in body and body[k] is not None:
            setattr(row, k, body[k] if k != "stage" else str(body[k]).upper())
    for k, col in (("objectives", "objectives_json"), ("needs", "needs_json"), ("moes", "moes_json"),
                   ("requirement_codes", "requirement_codes_json")):
        if body.get(k) is not None:
            setattr(row, col, [str(x) for x in body[k]])
    data = dict(row.data_json or {})
    for k in ("method_text", "when"):
        if body.get(k) is not None:
            data[k] = str(body[k])
    if body.get("stages") is not None:
        data["stages"] = [str(x).upper() for x in body["stages"]]
    if body.get("performer_ids") is not None:
        data["performer_ids"] = [str(x) for x in body["performer_ids"]]
    elif "performer" in body:
        data["performer_ids"] = performer_ids_for(row.performer, stakeholders)
    row.data_json = data or None
    if row.stage and row.stage not in STAGES:
        raise HTTPException(422, f"Unknown validation stage {row.stage}; use one of {', '.join(STAGES)}.")
    if row.status not in STATUSES:
        raise HTTPException(422, f"Unknown status {row.status}; use one of {', '.join(STATUSES)}.")


async def _row(s, study_id: str, key: str):
    from ..db.models_se import SeValidationActivityRow as Row
    row = await s.get(Row, key)
    if row is None or row.study_id != study_id:
        row = (await s.execute(select(Row).where(Row.study_id == study_id, Row.code == key))).scalars().first()
    if row is None:
        raise HTTPException(404, f"Validation activity {key} not found")
    return row


# ─── evidence: coverage ────────────────────────────────────────────────────

def _objectives(study) -> list[dict[str, Any]]:
    out = []
    for o in getattr(getattr(study, "mission_need", None), "objectives", None) or []:
        out.append({"id": o.id, "text": o.text, "priority": str(getattr(o.priority, "value", o.priority)),
                    "measurable_criterion": o.measurable_criterion, "stakeholder_ids": list(o.stakeholder_ids)})
    return out


async def coverage(study_id: str) -> dict[str, Any]:
    """Per objective: its validation activities and whether a stakeholder (not the engineering
    team alone) performs one; per need: its validation row. ``ok`` is true when every primary
    objective has at least one activity with a stakeholder performer (the SRR criterion)."""
    from .studies import get_study_store
    study = get_study_store().get(study_id)
    acts = await list_activities(study_id)
    nvs = await list_need_validation(study_id)
    objectives: dict[str, Any] = {}
    for o in _objectives(study) if study is not None else []:
        mine = [a for a in acts if o["id"] in a["objectives"] or f"OBJ-{o['id']}" in a["objectives"]]
        objectives[o["id"]] = {"priority": o["priority"], "activities": [a["code"] for a in mine],
                               "stakeholder_performed": any(not a["engineers_only"] for a in mine),
                               "in_orbit": any(set(a["stages"]) & {"CRR", "IOV", "PHASE_E"} for a in mine)}
    primary = [k for k, v in objectives.items() if v["priority"] == "primary"]
    uncovered = [k for k in primary if not objectives[k]["stakeholder_performed"]]
    needs = [n.id for n in getattr(getattr(study, "mission_need", None), "stakeholder_needs", None) or []]
    nv_codes = {n["need_code"] for n in nvs}
    return {"objectives": objectives, "primary": primary, "uncovered_primary": uncovered,
            "needs": {n: n in nv_codes for n in needs}, "needs_without_validation": [n for n in needs if n not in nv_codes],
            "activities": len(acts), "need_validation": len(nvs),
            "engineers_only": [a["code"] for a in acts if a["engineers_only"]],
            "in_orbit_planned": any(set(a["stages"]) & {"CRR", "IOV", "PHASE_E"} for a in acts),
            "ok": bool(primary) and not uncovered}


# ─── routes ────────────────────────────────────────────────────────────────

@router.get("/studies/{study_id}/validation/activities")
async def get_validation_activities(study_id: str) -> dict:
    study_or_404(study_id)
    items = await list_activities(study_id)
    return {"study_id": study_id, "items": items, "stages": list(STAGES), "stage_labels": STAGE_LABEL,
            "methods": list(METHODS), "statuses": list(STATUSES)}


@router.post("/studies/{study_id}/validation/activities")
async def create_validation_activity(study_id: str, body: dict[str, Any]) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeValidationActivityRow as Row
    study = study_or_404(study_id)
    if not str(body.get("title") or "").strip():
        raise HTTPException(422, "A validation activity needs a title.")
    async with get_session_factory()() as s:
        codes = set((await s.execute(select(Row.code).where(Row.study_id == study_id))).scalars())
        code = str(body.get("code") or "").strip()
        if not code:
            n = 1
            while f"VAL-{n:02d}" in codes:
                n += 1
            code = f"VAL-{n:02d}"
        elif code in codes:
            raise HTTPException(409, f"Validation activity {code} already exists.")
        row = Row(id=_uid(), study_id=study_id, code=code, origin="user", order=len(codes), status="planned")
        s.add(row)
        _apply(row, {**body, "code": code, "performer": body.get("performer", "")}, _stakeholders(study))
        await s.commit()
        return _act_dict(row, _stakeholders(study))


@router.patch("/studies/{study_id}/validation/activities/{activity_id}")
async def update_validation_activity(study_id: str, activity_id: str, body: dict[str, Any]) -> dict:
    from ..db.engine import get_session_factory
    study = study_or_404(study_id)
    async with get_session_factory()() as s:
        row = await _row(s, study_id, activity_id)
        _apply(row, body, _stakeholders(study))
        if row.origin == "proposed":
            row.origin = "user"
        await s.commit()
        return _act_dict(row, _stakeholders(study))


@router.delete("/studies/{study_id}/validation/activities/{activity_id}")
async def delete_validation_activity(study_id: str, activity_id: str) -> dict:
    from ..db.engine import get_session_factory
    study_or_404(study_id)
    async with get_session_factory()() as s:
        row = await _row(s, study_id, activity_id)
        code = row.code
        await s.delete(row)
        await s.commit()
    return {"deleted": code}


@router.post("/studies/{study_id}/validation/propose")
async def propose_validation(study_id: str) -> dict:
    """One proposed activity per primary objective that has none: its measure as the acceptance,
    the stakeholders who hold its needs as performers, stage PRR (needs validation with them) …
    the team edits it. Existing activities of that objective are left alone."""
    from ..db.engine import get_session_factory
    from ..db.models_se import SeValidationActivityRow as Row
    study = study_or_404(study_id)
    stk = _stakeholders(study)
    need_of = {}
    for s in stk:
        for n in s.get("need_ids") or []:
            need_of.setdefault(n, []).append(s["id"])
    acts = await list_activities(study_id)
    reqs_by_obj = await _requirements_by_objective(study_id)
    added = []
    async with get_session_factory()() as s:
        codes = {a["code"] for a in acts}
        for o in _objectives(study):
            if o["priority"] != "primary" or any(o["id"] in a["objectives"] for a in acts):
                continue
            needs = list(dict.fromkeys(_needs_of_objective(study, o["id"])))
            pids = list(dict.fromkeys(p for n in needs for p in need_of.get(n, []))) or list(o["stakeholder_ids"])
            code = f"VAL-{o['id']}"
            if code in codes:
                continue
            row = Row(id=_uid(), study_id=study_id, code=code, origin="proposed", status="proposed",
                      order=len(codes) + len(added), objectives_json=[o["id"]], needs_json=needs,
                      requirement_codes_json=reqs_by_obj.get(o["id"], []),
                      title=f"Validate objective {o['id']} with the people it serves",
                      title_fr=f"Valider l’objectif {o['id']} avec les personnes concernées",
                      method="walkthrough", stage="PRR",
                      performer=", ".join(next((x["name"] for x in stk if x["id"] == p), p) for p in pids)
                      or "[PLACEHOLDER: who holds this need]",
                      acceptance=o["measurable_criterion"] or "[PLACEHOLDER: how the stakeholders judge success]",
                      environment="plain-language walkthrough of the need, the objective and its measure",
                      data_json={"performer_ids": pids, "stages": ["PRR"]})
            s.add(row)
            added.append(code)
        await s.commit()
    return {"study_id": study_id, "added": added, "items": await list_activities(study_id)}


def _needs_of_objective(study, obj_id: str) -> list[str]:
    """SN ids an objective serves: the MOEs that name it, else the needs whose holders it lists."""
    out: list[str] = []
    for o in study.mission_need.objectives:
        if o.id == obj_id:
            for sid in o.stakeholder_ids:
                for s in study.mission_need.stakeholders:
                    if s.id == sid:
                        out.extend(s.need_ids)
    return out


async def _requirements_by_objective(study_id: str) -> dict[str, list[str]]:
    """Mission requirement codes whose parent is ``OBJ-<id>`` (the v2 baseline's parents)."""
    out: dict[str, list[str]] = {}
    try:
        from .requirements import _requirements, ensure_requirements_loaded
        await ensure_requirements_loaded()
        rows = [r for r in _requirements.values() if r.get("study_id") == study_id]
        by_id = {r.get("id"): r for r in rows}
        for r in rows:
            par = by_id.get(r.get("parent_id")) or {}
            code = str(par.get("code") or "")
            if code.startswith("OBJ-"):
                out.setdefault(code[4:], []).append(str(r.get("code")))
    except Exception:  # noqa: BLE001 — no requirements yet
        pass
    return {k: sorted(v) for k, v in out.items()}


@router.post("/studies/{study_id}/validation/import")
async def import_validation(study_id: str, body: dict[str, Any]) -> dict:
    """The v2 validation plan (``vv_plan.yaml`` ``validation_plan``: V1 … V7 with ``who``,
    ``when``, ``method``, ``requirements``, ``exit``) and the need validation (``need_validation``)
    in one call (seed S3). Upserts by code; ``replace: true`` deletes the rows first. Each
    activity's objectives, needs and MOEs come from the need validation that names it and from
    the MOEs of those needs (``moes`` in the body: the stakeholders.yaml MOE list)."""
    from ..db.engine import get_session_factory
    from ..db.models_se import SeNeedValidationRow as NV, SeValidationActivityRow as Row
    study = study_or_404(study_id)
    stk = _stakeholders(study)
    plan = [v for v in body.get("validation_plan") or body.get("activities") or [] if isinstance(v, dict) and v.get("id")]
    nv_in = [n for n in body.get("need_validation") or [] if isinstance(n, dict) and n.get("need")]
    moes = [m for m in body.get("moes") or [] if isinstance(m, dict)]
    if not plan and not nv_in:
        raise HTTPException(422, "Nothing to import: give validation_plan and/or need_validation.")
    act_codes = [str(v["id"]) for v in plan]
    needs_of_act: dict[str, list[str]] = {}
    nv_rows = []
    for i, n in enumerate(nv_in):
        acts = [c for c in re.findall(r"\bV\d+\b", str(n.get("method") or "")) if c in act_codes or not act_codes]
        acts = list(dict.fromkeys(acts))
        for a in acts:
            needs_of_act.setdefault(a, []).append(str(n["need"]))
        nv_rows.append({"need_code": str(n["need"]), "activity_codes_json": acts, "method": str(n.get("method") or "")[:64],
                        "criterion": str(n.get("method") or ""), "stage": (stages_in(n.get("stage")) or [""])[0],
                        "order": i, "data_json": {"stages": stages_in(n.get("stage")), "stage_text": str(n.get("stage") or "")}})
    moe_by_need: dict[str, list[str]] = {}
    obj_by_moe: dict[str, list[str]] = {}
    for m in moes:
        mid = str(m.get("id") or m.get("code") or "")
        obj_by_moe[mid] = [str(x) for x in m.get("objectives") or []]
        for n in m.get("needs") or []:
            moe_by_need.setdefault(str(n), []).append(mid)
    async with get_session_factory()() as s:
        if body.get("replace"):
            await s.execute(delete(Row).where(Row.study_id == study_id))
            await s.execute(delete(NV).where(NV.study_id == study_id))
        have = {r.code: r for r in (await s.execute(select(Row).where(Row.study_id == study_id))).scalars()}
        added = updated = 0
        for i, v in enumerate(plan):
            code = str(v["id"])
            needs = needs_of_act.get(code, [])
            text = " ".join(str(v.get(k) or "") for k in ("method", "exit"))
            moe_ids = list(dict.fromkeys([*re.findall(r"\bMOE-\d+\b", text),
                                          *(x for n in needs for x in moe_by_need.get(n, []))]))
            objs = list(dict.fromkeys(o for x in moe_ids for o in obj_by_moe.get(x, [])))
            stages = stages_in(v.get("when"))
            fields = {"code": code, "title": str(v.get("name") or code), "title_fr": str(v.get("name_fr") or ""),
                      "method": method_of(v.get("method")), "method_text": str(v.get("method") or ""),
                      "environment": str(v.get("environment") or v.get("method") or ""),
                      "stage": stages[0] if stages else "", "stages": stages, "when": str(v.get("when") or ""),
                      "performer": str(v.get("who") or ""), "acceptance": str(v.get("exit") or ""),
                      "requirement_codes": [str(x) for x in v.get("requirements") or []],
                      "needs": needs, "moes": moe_ids, "objectives": objs, "order": i,
                      "status": str(v.get("status") or "planned")}
            row = have.get(code)
            if row is None:
                row = Row(id=_uid(), study_id=study_id, code=code, origin="imported")
                s.add(row)
                added += 1
            else:
                updated += 1
            _apply(row, fields, stk)
        nv_have = {r.need_code: r for r in (await s.execute(select(NV).where(NV.study_id == study_id))).scalars()}
        for f in nv_rows:
            row = nv_have.get(f["need_code"])
            if row is None:
                row = NV(id=_uid(), study_id=study_id, need_code=f["need_code"])
                s.add(row)
            for k, val in f.items():
                setattr(row, k, val)
        await s.commit()
    return {"study_id": study_id, "activities_added": added, "activities_updated": updated,
            "need_validation": len(nv_rows), "coverage": await coverage(study_id)}


@router.get("/studies/{study_id}/validation/need-validation")
async def get_need_validation(study_id: str) -> dict:
    """One row per stakeholder need: the activities that validate it, the method and the stages."""
    study_or_404(study_id)
    return {"study_id": study_id, "items": await list_need_validation(study_id)}


@router.get("/studies/{study_id}/validation/coverage")
async def validation_coverage(study_id: str) -> dict:
    study_or_404(study_id)
    return {"study_id": study_id, **await coverage(study_id)}
