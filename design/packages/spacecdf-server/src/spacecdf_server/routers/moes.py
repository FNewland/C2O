"""Stakeholders (categories, authority, engagement), stakeholder needs and measures of
effectiveness (MOEs). Owner S (wave 3, 3.S3).

    GET    /api/studies/{sid}/stakeholders            the register: stakeholders, needs, MOEs, counts
    PUT    /api/studies/{sid}/stakeholders/{stk_id}   edit one stakeholder (category, authority, engagement …)
    POST   /api/studies/{sid}/stakeholders/import     ``stakeholders.yaml`` (stakeholders, needs, MOEs) in one call
    GET    /api/studies/{sid}/moes                    every MOE
    POST   /api/studies/{sid}/moes                    add one
    PATCH  /api/studies/{sid}/moes/{moe_id}           edit one (id or code)
    DELETE /api/studies/{sid}/moes/{moe_id}

Stakeholders and needs live on ``study.mission_need`` (``spacecdf_common.models.mission_need``);
MOEs in the table ``se_moes`` (``db/models_se.py``). An MOE whose measure, threshold or
``defined_by`` says it is still to be co-defined is a **placeholder**: it shows as "to co-define"
and never as a target the engineering team set (the communities define MOE-04 and MOE-10 of the
Northern Fire and Ice mission).
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select

from ._lookup import study_or_404

router = APIRouter()

#: an MOE is a placeholder when its measure or its whole threshold is a placeholder, or when its
#: definer says it is still to be confirmed or co-defined by the stakeholders (MOE-04, MOE-10 of the
#: Northern Fire and Ice mission); a threshold with only one pending part (MOE-11) is not, but it
#: lists that part in ``pending_parts``
_CODEFINE_RE = re.compile(r"\[\s*placeholder|to be co-defined|to co-define|co-defined, not by", re.I)
_MOE_FIELDS = ("code", "name", "name_fr", "measure", "threshold", "goal", "unit", "defined_by", "order")


def _uid() -> str:
    return uuid.uuid4().hex


def is_placeholder(m: dict[str, Any]) -> bool:
    whole = any(str(m.get(k) or "").strip().lower().startswith("[placeholder") for k in ("measure", "threshold"))
    return whole or bool(_CODEFINE_RE.search(str(m.get("defined_by") or "")))


def pending_parts(m: dict[str, Any]) -> list[str]:
    """The ``[PLACEHOLDER: …]`` texts of an MOE (what is still to be defined, and by whom)."""
    return [x.strip() for k in ("measure", "threshold", "defined_by")
            for x in re.findall(r"\[\s*placeholder:?\s*([^\]]*)\]", str(m.get(k) or ""), re.I)]


def moe_dict(r) -> dict[str, Any]:
    d = dict(r.data_json or {})
    return {"id": r.id, "study_id": r.study_id, "code": r.code, "name": r.name, "name_fr": r.name_fr,
            "measure": r.measure, "measure_fr": d.get("measure_fr", ""), "threshold": r.threshold, "goal": r.goal,
            "unit": r.unit, "objectives": list(r.objectives_json or []), "needs": list(r.needs_json or []),
            "defined_by": r.defined_by, "placeholder": bool(r.placeholder), "origin": r.origin, "order": r.order,
            "pending_parts": pending_parts({"measure": r.measure, "threshold": r.threshold, "defined_by": r.defined_by}),
            "approval": d.get("approval") or ""}   # PI approved the co-define wording (2026-11-10)


async def list_moes(study_id: str) -> list[dict[str, Any]]:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeMoeRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(SeMoeRow).where(SeMoeRow.study_id == study_id)
                                .order_by(SeMoeRow.order, SeMoeRow.code))).scalars().all()
        return [moe_dict(r) for r in rows]


def _apply_moe(row, body: dict[str, Any]) -> None:
    for k in _MOE_FIELDS:
        if k in body and body[k] is not None:
            setattr(row, k, body[k])
    if body.get("objectives") is not None:
        row.objectives_json = [str(x) for x in body["objectives"]]
    if body.get("needs") is not None:
        row.needs_json = [str(x) for x in body["needs"]]
    data = dict(row.data_json or {})
    for k in ("measure_fr", "approval"):
        if body.get(k) is not None:
            data[k] = str(body[k])
    row.data_json = data or None
    if body.get("placeholder") is not None:
        row.placeholder = bool(body["placeholder"])
    else:
        row.placeholder = is_placeholder({"measure": row.measure, "threshold": row.threshold,
                                          "defined_by": row.defined_by})


# ─── stakeholders on the mission need ──────────────────────────────────────

def _need(study) -> Any:
    return study.mission_need


async def _save_study(study) -> None:
    from ..db.study_repo import db_save_study
    try:
        await db_save_study(study)
    except Exception:  # noqa: BLE001 — the cache stays authoritative, as in routers/studies.py
        import logging
        logging.getLogger(__name__).exception("Failed to persist study %s", getattr(study, "id", "?"))


def register(study, moes: list[dict[str, Any]]) -> dict[str, Any]:
    """The stakeholder register as the editor, the export section and the diagrams read it."""
    need = _need(study)
    items = [s.model_dump(mode="json") for s in need.stakeholders]
    needs = [n.model_dump(mode="json") for n in need.stakeholder_needs]
    by_cat: dict[str, int] = {}
    for s in items:
        for c in s.get("categories") or []:
            by_cat[c] = by_cat.get(c, 0) + 1
    counts = {"stakeholders": len(items), "needs": len(needs), "moes": len(moes),
              "placeholder_moes": sum(1 for m in moes if m["placeholder"]),
              "categories": len(by_cat), "by_category": by_cat,
              "unclassified": sum(1 for s in items if not s.get("categories")),
              "needs_without_moe": sorted(n["id"] for n in needs
                                          if not any(n["id"] in (m.get("needs") or []) for m in moes))}
    return {"items": items, "needs": needs, "moes": moes, "counts": counts,
            "governance_notes": dict(need.governance_notes or {})}


@router.get("/studies/{study_id}/stakeholders")
async def get_stakeholders(study_id: str) -> dict:
    study = study_or_404(study_id)
    return {"study_id": study_id, **register(study, await list_moes(study_id))}


@router.put("/studies/{study_id}/stakeholders/{stakeholder_id}")
async def put_stakeholder(study_id: str, stakeholder_id: str, body: dict[str, Any]) -> dict:
    """Edit one stakeholder; an unknown id adds it (the editor's "Add")."""
    from spacecdf_common.models.mission_need import Stakeholder
    study = study_or_404(study_id)
    need = _need(study)
    cur = next((s for s in need.stakeholders if s.id == stakeholder_id), None)
    data = {**(cur.model_dump(mode="json") if cur else {"id": stakeholder_id}), **body, "id": stakeholder_id}
    if "category" in body and "categories" not in body:
        data.pop("categories", None)          # a new category text replaces the old list
    if not str(data.get("name") or "").strip():
        raise HTTPException(422, "A stakeholder needs a name.")
    try:
        new = Stakeholder(**data)
    except Exception as e:  # noqa: BLE001 — pydantic validation
        raise HTTPException(422, str(e)[:300]) from e
    need.stakeholders = [new if s.id == stakeholder_id else s for s in need.stakeholders] if cur else \
        [*need.stakeholders, new]
    await _save_study(study)
    return new.model_dump(mode="json")


@router.post("/studies/{study_id}/stakeholders/import")
async def import_stakeholders(study_id: str, body: dict[str, Any]) -> dict:
    """``stakeholders.yaml`` in one call (seed S0): the stakeholders replace the register, the
    needs replace ``stakeholder_needs``, the MOEs are upserted by code (``replace: true`` deletes
    the others first). Each stakeholder's ``needs`` (SN ids) becomes ``need_ids``; its text list
    ``needs`` holds the need statements, as the wizard writes them."""
    from spacecdf_common.models.mission_need import Stakeholder, StakeholderNeed
    from ..db.engine import get_session_factory
    from ..db.models_se import SeMoeRow
    study = study_or_404(study_id)
    if not isinstance(body, dict) or not (body.get("stakeholders") or body.get("needs") or body.get("moes")):
        raise HTTPException(422, "Nothing to import: give stakeholders, needs or moes.")
    need = _need(study)
    needs_in = [n for n in body.get("needs") or [] if isinstance(n, dict) and n.get("id")]
    text_of = {str(n["id"]): str(n.get("need") or n.get("text") or "") for n in needs_in}
    stks: list[Stakeholder] = []
    for s in body.get("stakeholders") or []:
        if not isinstance(s, dict) or not s.get("name"):
            continue
        ids = [str(x) for x in s.get("needs") or [] if re.match(r"^SN-\d+", str(x))]
        stks.append(Stakeholder(**{
            "id": str(s.get("id") or f"STK-{len(stks) + 1:02d}"), "name": s["name"], "role": s.get("role") or "user",
            "category": s.get("category") or "", "authority": s.get("authority") or "",
            "engagement": s.get("engagement") or "", "need_ids": ids,
            "needs": [text_of[i] for i in ids if text_of.get(i)], "note": s.get("note") or "",
            "consent_status": s.get("consent_status") or "", "priority": s.get("priority") or "primary"}))
    holders: dict[str, list[str]] = {}
    for s in stks:
        for i in s.need_ids:
            holders.setdefault(i, []).append(s.id)
    sns = [StakeholderNeed(id=str(n["id"]), text=text_of[str(n["id"])], stakeholder=str(n.get("stakeholder") or ""),
                           role=str(n.get("role") or ""), traces_to=[str(x) for x in n.get("traces_to") or []],
                           stakeholder_ids=holders.get(str(n["id"]), []))
           for n in needs_in]
    if stks:
        need.stakeholders = stks
    if sns:
        need.stakeholder_needs = sns
    # objectives -> the stakeholders who hold the needs they serve ({"O1": ["SN-02", …]})
    for oid, sn_ids in dict(body.get("objective_needs") or {}).items():
        for o in need.objectives:
            if o.id == oid:
                o.stakeholder_ids = list(dict.fromkeys(h for n in sn_ids for h in holders.get(str(n), [])))
    gov = body.get("governance_notes")
    if isinstance(gov, dict):
        need.governance_notes = {str(k): str(v) for k, v in gov.items()}
    await _save_study(study)
    added = updated = 0
    moes_in = [m for m in body.get("moes") or [] if isinstance(m, dict) and (m.get("id") or m.get("code"))]
    async with get_session_factory()() as s:
        if body.get("replace"):
            await s.execute(delete(SeMoeRow).where(SeMoeRow.study_id == study_id))
        have = {r.code: r for r in (await s.execute(select(SeMoeRow).where(SeMoeRow.study_id == study_id))).scalars()}
        for i, m in enumerate(moes_in):
            code = str(m.get("code") or m.get("id"))
            row = have.get(code)
            if row is None:
                row = SeMoeRow(id=_uid(), study_id=study_id, code=code, origin="imported")
                s.add(row)
                added += 1
            else:
                updated += 1
            _apply_moe(row, {**m, "code": code, "order": i})
        await s.commit()
    moes = await list_moes(study_id)
    return {"study_id": study_id, "stakeholders": len(need.stakeholders), "needs": len(need.stakeholder_needs),
            "moes_added": added, "moes_updated": updated, **{"counts": register(study, moes)["counts"]}}


# ─── MOEs ──────────────────────────────────────────────────────────────────

@router.get("/studies/{study_id}/moes")
async def get_moes(study_id: str) -> dict:
    """Every MOE: {id, code, measure, threshold, objectives, needs, defined_by, placeholder}."""
    study_or_404(study_id)
    items = await list_moes(study_id)
    return {"study_id": study_id, "items": items,
            "counts": {"total": len(items), "placeholder": sum(1 for m in items if m["placeholder"])}}


@router.post("/studies/{study_id}/moes")
async def create_moe(study_id: str, body: dict[str, Any]) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeMoeRow
    study_or_404(study_id)
    if not str(body.get("measure") or "").strip():
        raise HTTPException(422, "An MOE needs a measure.")
    async with get_session_factory()() as s:
        codes = {r for r in (await s.execute(select(SeMoeRow.code).where(SeMoeRow.study_id == study_id))).scalars()}
        code = str(body.get("code") or "").strip()
        if not code:
            n = 1
            while f"MOE-{n:02d}" in codes:
                n += 1
            code = f"MOE-{n:02d}"
        elif code in codes:
            raise HTTPException(409, f"MOE {code} already exists.")
        row = SeMoeRow(id=_uid(), study_id=study_id, code=code, origin="user", order=len(codes))
        s.add(row)
        _apply_moe(row, {**body, "code": code})
        await s.commit()
        return moe_dict(row)


async def _moe_row(s, study_id: str, moe_id: str):
    from ..db.models_se import SeMoeRow
    row = await s.get(SeMoeRow, moe_id)
    if row is None or row.study_id != study_id:
        row = (await s.execute(select(SeMoeRow).where(SeMoeRow.study_id == study_id, SeMoeRow.code == moe_id))
               ).scalars().first()
    if row is None:
        raise HTTPException(404, f"MOE {moe_id} not found")
    return row


@router.patch("/studies/{study_id}/moes/{moe_id}")
async def update_moe(study_id: str, moe_id: str, body: dict[str, Any]) -> dict:
    from ..db.engine import get_session_factory
    study_or_404(study_id)
    async with get_session_factory()() as s:
        row = await _moe_row(s, study_id, moe_id)
        _apply_moe(row, body)
        row.origin = "user"
        await s.commit()
        return moe_dict(row)


@router.delete("/studies/{study_id}/moes/{moe_id}")
async def delete_moe(study_id: str, moe_id: str) -> dict:
    from ..db.engine import get_session_factory
    study_or_404(study_id)
    async with get_session_factory()() as s:
        row = await _moe_row(s, study_id, moe_id)
        code = row.code
        await s.delete(row)
        await s.commit()
    return {"deleted": code}
