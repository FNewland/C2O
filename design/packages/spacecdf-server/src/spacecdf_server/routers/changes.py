"""Change proposals register (ECP / CR). Owner L (3.L4).

Table ``change_proposals`` (``db/models_changes.py``, ``ChangeProposalRow``: L's class only).
An engineering change proposal (ECP) or change request (CR) carries its class (I / II, ECSS-M-ST-40C),
impact, the requirement codes it affects (resolved to the study's requirement ids; references that
are not requirements are kept apart), the source trade, status and the gate that decides it, and the
impact-preview specs (``previews``) the change-control flow (agent D, ``routers/change_control.py``)
shows to the affected seats.

* ``GET    /studies/{id}/changes``                — every record, newest code last, with counts;
* ``POST   /studies/{id}/changes``                — one record;
* ``PATCH  /studies/{id}/changes/{change_id}``    — edit (id or code); D's flow sets ``status``,
  ``decided_by`` and ``baseline_ref`` here (or calls ``set_status``);
* ``POST   /studies/{id}/changes/import``         — ``{records: [...]}`` or ``{document: risks.yaml}``
  (``configuration_management.change_records``), idempotent by code (seed S3);
* ``POST   /studies/{id}/changes/from-trade/{trade_id}`` — "Raise change from trade" on a decided trade;
* ``POST   /studies/{id}/changes/{change_id}/preview`` — the impact preview of the record's specs.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from ._lookup import study_or_404

router = APIRouter()
OWNER, WP = "L", "3.L4"

KINDS = ("ecp", "cr")
CLASSES = ("I", "II", "")
STATUSES = ("proposed", "under_review", "accepted", "rejected", "implemented", "closed", "withdrawn")
GATES = ("mdr", "mcr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr", "")
_CODE = re.compile(r"^[A-Z]{2,4}(?:-[A-Z0-9]{1,6}){1,3}$")


def _row_dict(r) -> dict[str, Any]:
    d = r.data_json or {}
    return {"id": r.id, "study_id": r.study_id, "code": r.code, "kind": r.kind, "title": r.title,
            "change_class": r.change_class, "class_text": d.get("class_text", ""), "description": r.description,
            "impact": r.impact_json or {}, "affected_codes": list(r.affected_codes_json or []),
            "affected_requirement_ids": list(r.affected_requirement_ids_json or []),
            "unresolved_codes": list(d.get("unresolved_codes") or []), "affected_other": list(d.get("affected_other") or []),
            "source_trade": r.source_trade, "status": r.status, "status_text": d.get("status_text", ""),
            "decision_gate": r.decision_gate, "decided_by": r.decided_by, "baseline_ref": d.get("baseline_ref", ""),
            "previews": list(d.get("previews") or []), "apply": list(d.get("apply") or []),
            "history": list(d.get("history") or []),
            "origin": r.origin, "order": r.order,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None}


def _requirement_ids(study_id: str) -> dict[str, str]:
    from .requirements import _requirements
    return {str(r.get("code")): r["id"] for r in _requirements.values()
            if r.get("study_id") == study_id and r.get("code") and r.get("status") != "retired"}


def split_affected(items: list[Any], study_id: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """(requirement codes, their ids, codes not in the study, other references) from ``affected``."""
    by_code = _requirement_ids(study_id)
    codes, ids, unresolved, other = [], [], [], []
    for raw in items or []:
        s = str(raw).strip()
        if not s:
            continue
        head = s.split()[0].rstrip(",;:")
        if _CODE.match(head) and not head.startswith(("NUMBERS",)):
            if head not in codes:
                codes.append(head)
                if head in by_code:
                    ids.append(by_code[head])
                else:
                    unresolved.append(head)
            if s != head:
                other.append(s)
        else:
            other.append(s)
    return codes, ids, unresolved, other


def parse_class(text: str) -> tuple[str, str]:
    """``"I (form, fit, function of the payload)"`` -> ("I", the text)."""
    m = re.match(r"^\s*(II|I)\b", str(text or ""))
    return (m.group(1) if m else ""), str(text or "")


def parse_status(text: str) -> tuple[str, str]:
    """(status, decision gate) from a free status line such as "proposed - decision at PDR (PI / CCB)"."""
    t = str(text or "").lower()
    status = next((s for s in STATUSES if t.startswith(s.replace("_", " ")) or t.startswith(s)), "proposed")
    gate = ""
    m = re.search(r"\b(?:decision|approval|decided)\s+(?:at|before)\s+(?:the\s+)?(mdr|mcr|prr|srr|pdr|cdr|qr|ar|frr)\b", t)
    if m:
        gate = m.group(1)
    return status, gate


def _impact(v: Any) -> dict:
    if isinstance(v, dict):
        return v
    text = str(v or "")
    return {"summary": text, "items": [x.strip() for x in text.split(";") if x.strip()]} if text else {}


def _clean(body: dict[str, Any], study_id: str, *, partial: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "kind" in body or not partial:
        k = str(body.get("kind") or ("cr" if str(body.get("code") or body.get("id") or "").startswith("CR") else "ecp")).lower()
        if k not in KINDS:
            raise HTTPException(422, f"kind must be one of {', '.join(KINDS)}")
        out["kind"] = k
    for f, lim in (("code", 24), ("title", 240), ("description", 20000), ("source_trade", 24), ("decided_by", 120)):
        if f in body:
            out[f] = str(body.get(f) or "")[:lim]
    if "change_class" in body or "class_" in body or "class" in body:
        cls, txt = parse_class(body.get("change_class") or body.get("class_") or body.get("class") or "")
        out["change_class"], out["class_text"] = cls, str(body.get("class_text") or txt)
    if "status" in body:
        st = str(body.get("status") or "")
        if st in STATUSES:
            out["status"] = st
        else:
            s2, g2 = parse_status(st)
            out["status"], out["status_text"] = s2, st
            if g2 and "decision_gate" not in body:
                out["decision_gate"] = g2
    if "decision_gate" in body:
        g = str(body.get("decision_gate") or "").lower()
        if g not in GATES:
            raise HTTPException(422, f"decision_gate must be one of {', '.join(x for x in GATES if x)}")
        out["decision_gate"] = g
    if "impact" in body:
        out["impact"] = _impact(body.get("impact"))
    if "affected" in body or "affected_codes" in body:
        codes, ids, unres, other = split_affected(body.get("affected") or body.get("affected_codes") or [], study_id)
        out.update(affected_codes=codes, affected_requirement_ids=ids, unresolved_codes=unres, affected_other=other)
    for f in ("previews", "baseline_ref", "apply"):   # apply: requirement edits on approval (D's change control)
        if f in body:
            out[f] = body[f]
    if out.get("source_trade") is not None:
        out["source_trade"] = re.sub(r"^\s*trade\s+", "", out["source_trade"], flags=re.I)
    return out


def _apply(row, c: dict[str, Any]) -> None:
    for f in ("code", "kind", "title", "description", "source_trade", "status", "decision_gate", "decided_by",
              "change_class"):
        if f in c:
            setattr(row, f, c[f])
    if "impact" in c:
        row.impact_json = c["impact"]
    if "affected_codes" in c:
        row.affected_codes_json = c["affected_codes"]
        row.affected_requirement_ids_json = c["affected_requirement_ids"]
    d = dict(row.data_json or {})
    for f in ("class_text", "status_text", "unresolved_codes", "affected_other", "previews", "baseline_ref", "apply"):
        if f in c:
            d[f] = c[f]
    row.data_json = d


async def _rows(study_id: str):
    from sqlalchemy import select
    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeProposalRow
    async with get_session_factory()() as s:
        return (await s.execute(select(ChangeProposalRow).where(ChangeProposalRow.study_id == study_id)
                                .order_by(ChangeProposalRow.order, ChangeProposalRow.code))).scalars().all()


async def list_records(study_id: str) -> list[dict]:
    """Every change record of the study (export section, open-item register, change control)."""
    return [_row_dict(r) for r in await _rows(study_id)]


def counts_of(items: list[dict]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for it in items:
        by_status[it["status"]] = by_status.get(it["status"], 0) + 1
        by_kind[it["kind"]] = by_kind.get(it["kind"], 0) + 1
    return {"total": len(items), "by_status": by_status, "by_kind": by_kind,
            "open": sum(1 for it in items if it["status"] in ("proposed", "under_review"))}


def _resolve(rows, change_id: str):
    return next((r for r in rows if r.id == change_id), None) or next((r for r in rows if r.code == change_id), None)


async def _seat(request: Request | None, study_id: str) -> str:
    """Anyone in the team may raise a change; the actor is recorded."""
    if request is None:
        return ""
    try:
        from ..seats import store
        from ..seats.service import seat_ctx
        state = store.peek_team(study_id) or await store.get_team(study_id)
        if not state.get("enabled"):
            return ""
        ctx = await seat_ctx(request, study_id)
        return "instructor" if ctx.instructor else (ctx.active or "")
    except Exception:  # noqa: BLE001
        return ""


async def _broadcast(study_id: str, row_id: str) -> None:
    try:
        from ._arcadia_events import broadcast_mutation
        await broadcast_mutation(study_id, "changes_updated", "change_proposal", row_id, {})
    except Exception:  # noqa: BLE001
        pass


async def upsert(study_id: str, body: dict[str, Any], *, origin: str = "user", by: str = "") -> tuple[dict, bool]:
    """Create a record, or update the one with the same code. Returns (record, created)."""
    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeProposalRow
    c = _clean({**body, "code": body.get("code") or body.get("id") or ""}, study_id)
    async with get_session_factory()() as s:
        from sqlalchemy import select
        rows = (await s.execute(select(ChangeProposalRow).where(ChangeProposalRow.study_id == study_id))).scalars().all()
        row = next((r for r in rows if c.get("code") and r.code == c["code"]), None)
        created = row is None
        if created:
            n = len(rows) + 1
            if not c.get("code"):
                prefix = "CR" if c["kind"] == "cr" else "ECP"
                used = {r.code for r in rows}
                k = n
                while f"{prefix}-{k:02d}" in used:
                    k += 1
                c["code"] = f"{prefix}-{k:02d}"
            row = ChangeProposalRow(id=uuid4().hex[:16], study_id=study_id, origin=origin[:16], order=n,
                                    status="proposed", data_json={})
            s.add(row)
        _apply(row, c)
        d = dict(row.data_json or {})
        d["history"] = list(d.get("history") or []) + [{"event": "created" if created else "updated", "by": by,
                                                        "status": row.status}]
        row.data_json = d
        await s.commit()
        return _row_dict(row), created


async def set_status(study_id: str, change_id: str, status: str, *, by: str = "", baseline_ref: str = "",
                     note: str = "") -> dict:
    """Agent D's change-control flow: the board decision on a record (accepted / rejected …)."""
    from sqlalchemy import select
    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeProposalRow
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    async with get_session_factory()() as s:
        rows = (await s.execute(select(ChangeProposalRow).where(ChangeProposalRow.study_id == study_id))).scalars().all()
        row = _resolve(rows, change_id)
        if row is None:
            raise LookupError(change_id)
        row.status = status
        if by:
            row.decided_by = by[:120]
        d = dict(row.data_json or {})
        if baseline_ref:
            d["baseline_ref"] = baseline_ref
        d["history"] = list(d.get("history") or []) + [{"event": "status", "status": status, "by": by, "note": note}]
        row.data_json = d
        await s.commit()
        return _row_dict(row)


@router.get("/studies/{study_id}/changes")
async def list_changes(study_id: str) -> dict:
    """ECP and CR records with class, impact, affected requirements, status."""
    study_or_404(study_id)
    items = await list_records(study_id)
    return {"study_id": study_id, "items": items, "counts": counts_of(items), "statuses": list(STATUSES)}


@router.post("/studies/{study_id}/changes")
async def create_change(study_id: str, body: dict[str, Any], request: Request) -> dict:
    study_or_404(study_id)
    if not str(body.get("title") or "").strip():
        raise HTTPException(422, "a change needs a title")
    by = await _seat(request, study_id)
    rec, _created = await upsert(study_id, body, by=by)
    await _broadcast(study_id, rec["id"])
    return rec


@router.patch("/studies/{study_id}/changes/{change_id}")
async def update_change(study_id: str, change_id: str, body: dict[str, Any], request: Request) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeProposalRow
    from sqlalchemy import select
    study_or_404(study_id)
    c = _clean(body, study_id, partial=True)
    by = await _seat(request, study_id)
    async with get_session_factory()() as s:
        rows = (await s.execute(select(ChangeProposalRow).where(ChangeProposalRow.study_id == study_id))).scalars().all()
        row = _resolve(rows, change_id)
        if row is None:
            raise HTTPException(404, f"Unknown change: {change_id}")
        if c.get("code") and any(r.code == c["code"] and r.id != row.id for r in rows):
            raise HTTPException(409, f"code {c['code']} is already used")
        _apply(row, c)
        d = dict(row.data_json or {})
        d["history"] = list(d.get("history") or []) + [{"event": "updated", "by": by, "status": row.status,
                                                        "fields": sorted(c)}]
        row.data_json = d
        await s.commit()
        rec = _row_dict(row)
    await _broadcast(study_id, rec["id"])
    return rec


@router.post("/studies/{study_id}/changes/import")
async def import_changes(study_id: str, body: dict[str, Any], request: Request) -> dict:
    """``risks.yaml`` ``configuration_management.change_records`` in one call (seed S3); by code."""
    study_or_404(study_id)
    recs = body.get("records")
    if recs is None:
        doc = body.get("document") or {}
        recs = ((doc.get("configuration_management") or {}).get("change_records")) if isinstance(doc, dict) else None
    if not isinstance(recs, list):
        raise HTTPException(422, "give records: [...] or document: {configuration_management: {change_records}}")
    previews = body.get("previews") or {}
    by = await _seat(request, study_id)
    created = updated = 0
    items = []
    for r in recs:
        if not isinstance(r, dict) or not (r.get("id") or r.get("code")):
            raise HTTPException(422, "every change record needs an id (ECP-01, CR-V2 …)")
        code = str(r.get("code") or r.get("id"))
        b = {"code": code, "kind": r.get("kind") or ("cr" if code.startswith("CR") else "ecp"),
             "title": r.get("title") or code, "description": r.get("description") or "",
             "change_class": r.get("change_class") or r.get("class_") or r.get("class") or "",
             "status": r.get("status") or "proposed", "impact": r.get("impact") or "",
             "affected": r.get("affected") or r.get("affected_codes") or [],
             "source_trade": r.get("source_trade") or r.get("source") or ""}
        if r.get("decision_gate") is not None:
            b["decision_gate"] = r["decision_gate"]
        if r.get("previews") or previews.get(code):
            b["previews"] = r.get("previews") or previews.get(code)
        if isinstance(r.get("apply"), list):
            b["apply"] = r["apply"]
        rec, was_created = await upsert(study_id, b, origin="import", by=by)
        created += int(was_created)
        updated += int(not was_created)
        items.append(rec)
    await _broadcast(study_id, "import")
    return {"study_id": study_id, "created": created, "updated": updated, "items": items}


@router.post("/studies/{study_id}/changes/from-trade/{trade_id}")
async def change_from_trade(study_id: str, trade_id: str, request: Request) -> dict:
    """"Raise change from trade" on a decided trade: an ECP whose source is the trade, its title
    the decision, its affected codes the trade's linked requirements."""
    from ..services import trades as tr
    study = study_or_404(study_id)
    recs = tr.normalise_records(getattr(study, "trade_records", None))
    tid = tr.resolve_id(trade_id)
    if tid not in recs:
        raise HTTPException(404, f"Unknown trade: {trade_id}")
    st = recs[tid].get("state") or {}
    dec = st.get("decision") or {}
    if st.get("status") != "decided" or not dec.get("selected"):
        raise HTTPException(409, f"{tid} is not decided yet: decide the trade first")
    existing = [r for r in await list_records(study_id) if r["source_trade"] == tid]
    if existing:
        return {**existing[0], "existing": True}
    links = st.get("links") or {}
    by = await _seat(request, study_id)
    body = {"kind": "ecp", "title": f"{st.get('title') or tid}: {dec['selected']}",
            "description": dec.get("rationale") or "", "change_class": "",
            "status": "proposed", "source_trade": tid, "affected": list(links.get("requirements") or []),
            "impact": {"summary": f"Trade {tid} selected {dec['selected']}", "items": []},
            "decision_gate": str(st.get("gate") or "").lower() if str(st.get("gate") or "").lower() in GATES else ""}
    rec, _c = await upsert(study_id, body, origin="trade", by=by)
    await _broadcast(study_id, rec["id"])
    return rec


@router.post("/studies/{study_id}/changes/{change_id}/preview")
async def preview_change(study_id: str, change_id: str) -> dict:
    """The impact preview of the record's ``previews`` (applied together, a dry run)."""
    from ..services.impact_preview import PreviewError, preview
    study_or_404(study_id)
    rows = await _rows(study_id)
    row = _resolve(rows, change_id)
    if row is None:
        raise HTTPException(404, f"Unknown change: {change_id}")
    specs = (row.data_json or {}).get("previews") or []
    if not specs:
        raise HTTPException(409, f"{row.code} has no impact-preview spec (previews)")
    try:
        out = await preview(study_id, {"changes": specs})
    except PreviewError as exc:
        raise HTTPException(422, str(exc)) from None
    return {**out, "change_code": row.code, "change_id": row.id}
