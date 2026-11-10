"""Assumption register (SE-08, register part). Owner S (wave 3, 3.S6).

    GET    /api/studies/{sid}/assumptions                  ASM rows (``?status=open``, ``?due_gate=pdr``)
    POST   /api/studies/{sid}/assumptions                  add one
    PATCH  /api/studies/{sid}/assumptions/{id}             edit one (id or code): status, evidence …
    POST   /api/studies/{sid}/assumptions/import           the ``[ASSUMPTION]`` tags of a budget ledger
                                                           and the requirement rows that name one

Table ``se_assumptions`` (``db/models_se.py``). An assumption is a value chosen because nothing
better was known yet. The register says what it is, what rests on it (an element, a field, a
requirement or a budget line), what evidence would replace it, who owns it and by which gate it
must be confirmed or replaced. The Phase panel's "Analysis standard" lists the open ones of the
gate (:func:`open_for_gate`); the PDR analysis check warns on them.
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import delete, select

from ._wave3_stub import study_or_404

router = APIRouter()

STATUSES = ("open", "confirmed", "replaced", "retired")
AFFECT_KINDS = ("element", "field", "requirement", "budget")
GATE_ORDER = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")
#: default gate by which an imported assumption must be confirmed: the allocated baseline (PDR)
#: should rest on confirmed numbers, so every budget input is due there unless the text names a gate
DEFAULT_DUE_GATE = "pdr"
_FIELDS = ("code", "statement", "replace_with", "owner_seat", "due_gate", "status", "source", "order")
_TAG_RE = re.compile(r"\[ASSUMPTION(?::\s*([^\]]*))?\]\s*(.*)", re.I)
_REQ_CODE_RE = re.compile(r"\b[A-Z]{2,4}(?:-[A-Z0-9]{2,4}){1,2}\b")

#: budget section of the ledger -> owner seat of the assumption
_SECTION_SEAT = {"mass": "systems_engineer", "power": "power_engineer", "data": "systems_engineer",
                 "pointing": "aocs_engineer", "registration": "payload_lead", "timing": "systems_engineer",
                 "thermal": "thermal_engineer", "link": "comms_engineer", "cost": "cost_engineer"}
#: requirement subsystem -> owner seat (requirement rows that name an assumption)
_SUBSYSTEM_SEAT = (("payload", "payload_lead"), ("eps", "power_engineer"), ("power", "power_engineer"),
                   ("aocs", "aocs_engineer"), ("adcs", "aocs_engineer"), ("communication", "comms_engineer"),
                   ("thermal", "thermal_engineer"), ("structure", "structures_engineer"),
                   ("disposal", "propulsion_engineer"), ("ground", "mission_analyst"))


def _uid() -> str:
    return uuid.uuid4().hex


def _dict(r) -> dict[str, Any]:
    d = dict(r.data_json or {})
    return {"id": r.id, "study_id": r.study_id, "code": r.code, "statement": r.statement,
            "affects": list(r.affects_json or []), "replace_with": r.replace_with, "owner_seat": r.owner_seat,
            "due_gate": r.due_gate, "status": r.status, "source": r.source, "basis": d.get("basis", "assumed"),
            "evidence": d.get("evidence", ""), "origin": r.origin, "order": r.order}


async def list_assumptions(study_id: str) -> list[dict[str, Any]]:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeAssumptionRow as Row
    async with get_session_factory()() as s:
        rows = (await s.execute(select(Row).where(Row.study_id == study_id).order_by(Row.order, Row.code))).scalars().all()
        return [_dict(r) for r in rows]


def due_by(a: dict[str, Any], gate: str) -> bool:
    """True when the assumption must be settled at or before ``gate``."""
    g, d = str(gate or "").lower(), str(a.get("due_gate") or "").lower()
    if d not in GATE_ORDER or g not in GATE_ORDER:
        return False
    return GATE_ORDER.index(d) <= GATE_ORDER.index(g)


async def open_for_gate(study_id: str, gate: str) -> dict[str, Any]:
    """Open assumptions: all of them, and those due at or before ``gate`` (the Phase panel's
    "Analysis standard" and the PDR analysis check read this)."""
    items = [a for a in await list_assumptions(study_id) if a["status"] == "open"]
    due = [a for a in items if due_by(a, gate)]
    return {"open": items, "due": due, "counts": {"open": len(items), "due": len(due)}}


def _apply(row, body: dict[str, Any]) -> None:
    for k in _FIELDS:
        if k in body and body[k] is not None:
            setattr(row, k, str(body[k]).lower() if k == "due_gate" else body[k])
    if body.get("affects") is not None:
        aff = []
        for a in body["affects"]:
            if isinstance(a, dict) and a.get("ref"):
                kind = str(a.get("kind") or "field")
                if kind not in AFFECT_KINDS:
                    raise HTTPException(422, f"Unknown affects kind {kind}; use {', '.join(AFFECT_KINDS)}.")
                aff.append({"kind": kind, "ref": str(a["ref"]), **({"label": str(a["label"])} if a.get("label") else {})})
        row.affects_json = aff
    data = dict(row.data_json or {})
    for k in ("basis", "evidence"):
        if body.get(k) is not None:
            data[k] = str(body[k])
    row.data_json = data or None
    if row.status not in STATUSES:
        raise HTTPException(422, f"Unknown status {row.status}; use one of {', '.join(STATUSES)}.")
    if row.due_gate and row.due_gate not in GATE_ORDER:
        raise HTTPException(422, f"Unknown gate {row.due_gate}.")
    if row.status in ("confirmed", "replaced") and not (data.get("evidence") or "").strip():
        raise HTTPException(422, "Say what evidence confirmed or replaced the assumption.")


# ─── extraction from a budget ledger and from requirement rows ─────────────

def _walk(node: Any, path: list[str], out: list[tuple[list[str], str, dict]]):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and _TAG_RE.search(v):
                out.append(([*path, str(k)], v, node))
            else:
                _walk(v, [*path, str(k)], out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, [*path, str(i)], out)


def _gate_in(text: str) -> str | None:
    m = re.search(r"\b(?:at|by|before)\s+(MDR|PRR|SRR|PDR|CDR|QR|AR|FRR)\b", str(text or ""))
    return m.group(1).lower() if m else None


def budget_assumptions(budgets: dict[str, Any]) -> list[dict[str, Any]]:
    """One entry per distinct ``[ASSUMPTION…]`` tag of a budget ledger (``budgets.yaml``): the
    same statement on the same item (the camera-mount stability in the nadir and the roll cases)
    is one assumption that affects two budget lines."""
    found: list[tuple[list[str], str, dict]] = []
    for sec, node in (budgets or {}).items():
        if sec in ("margin_policy", "traceability"):
            continue
        _walk(node, [sec], found)
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for path, text, owner in found:
        m = _TAG_RE.search(text)
        tag, rest = (m.group(1) or "").strip(), (m.group(2) or "").strip()
        item = str(owner.get("contributor") or owner.get("unit") or owner.get("item") or path[-2] if len(path) > 1 else path[0])
        reqs = _REQ_CODE_RE.findall(rest) + _REQ_CODE_RE.findall(tag)
        statement = f"{item}: {tag}" if tag else f"{item}: value taken from {', '.join(reqs) or 'the ledger'} without evidence yet"
        key = (item.lower(), tag.lower() or rest.lower())
        line = ".".join(path[:-1])
        e = merged.get(key)
        if e is None:
            replace = ("datasheet limits from the vendor" if "datasheet" in tag.lower() else
                       "bench measurement or analysis" if re.search(r"bench|measure|analysis", tag, re.I) else
                       "a calculation or a vendor figure")
            e = merged[key] = {"statement": statement, "affects": [], "replace_with": replace,
                               "owner_seat": _SECTION_SEAT.get(path[0], "systems_engineer"),
                               "due_gate": _gate_in(text) or DEFAULT_DUE_GATE, "source": f"budgets.yaml {line}",
                               "basis": "assumed"}
            for rc in reqs:
                e["affects"].append({"kind": "requirement", "ref": rc})
        e["affects"].append({"kind": "budget", "ref": line})
    return list(merged.values())


def requirement_assumptions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per requirement row whose ``open_item_note`` names an assumption: the statement
    is the ``[ASSUMPTION: …]`` text of its rationale; it affects the row, its budget line and its
    allocated elements."""
    out = []
    for r in rows:
        if "assumption" not in str(r.get("open_item_note") or "").lower():
            continue
        code = str(r.get("id") or r.get("code") or "")
        m = _TAG_RE.search(str(r.get("rationale") or ""))
        tag = (m.group(1) or "").strip() if m else str(r.get("open_item_note"))
        aff = [{"kind": "requirement", "ref": code}]
        if r.get("budget_ref"):
            aff.append({"kind": "budget", "ref": str(r["budget_ref"])})
        for el in r.get("allocation") or []:
            aff.append({"kind": "element", "ref": str(el)})
        sub = str(r.get("subsystem") or "").lower()
        seat = next((s for w, s in _SUBSYSTEM_SEAT if w in sub), "systems_engineer")
        replace = ("datasheet limits from the vendor" if "datasheet" in tag.lower() else
                   "breadboard measurement" if re.search(r"breadboard|measure", tag, re.I) else
                   "a design analysis or vendor confirmation")
        out.append({"statement": f"{code}: {tag}", "affects": aff, "replace_with": replace, "owner_seat": seat,
                    "due_gate": _gate_in(tag) or DEFAULT_DUE_GATE, "source": f"requirement {code}", "basis": "assumed"})
    return out


def merge_register(budget_items: list[dict], req_items: list[dict]) -> list[dict]:
    """Budget tags and requirement assumptions as one register: a budget tag that names a
    requirement row which is itself an assumption is the same assumption (one row, both sources)."""
    out = [dict(x) for x in req_items]
    by_req = {a["source"].split()[-1]: a for a in out}
    for b in budget_items:
        twin = next((by_req[x["ref"]] for x in b["affects"] if x["kind"] == "requirement" and x["ref"] in by_req), None)
        if twin is not None:
            seen = {(x["kind"], x["ref"]) for x in twin["affects"]}
            twin["affects"] += [x for x in b["affects"] if (x["kind"], x["ref"]) not in seen]
            twin["source"] += f"; {b['source']}"
        else:
            out.append(dict(b))
    return out


# ─── routes ────────────────────────────────────────────────────────────────

@router.get("/studies/{study_id}/assumptions")
async def get_assumptions(study_id: str, status: str | None = Query(None), due_gate: str | None = Query(None)) -> dict:
    """ASM rows: statement, affects, replace_with, owner seat, due gate, status."""
    study_or_404(study_id)
    items = await list_assumptions(study_id)
    if status:
        items = [a for a in items if a["status"] == status]
    if due_gate:
        items = [a for a in items if due_by(a, due_gate)]
    return {"study_id": study_id, "items": items, "statuses": list(STATUSES), "affect_kinds": list(AFFECT_KINDS),
            "counts": {"total": len(items), "open": sum(1 for a in items if a["status"] == "open")}}


@router.post("/studies/{study_id}/assumptions")
async def create_assumption(study_id: str, body: dict[str, Any]) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeAssumptionRow as Row
    study_or_404(study_id)
    if not str(body.get("statement") or "").strip():
        raise HTTPException(422, "An assumption needs a statement.")
    async with get_session_factory()() as s:
        codes = set((await s.execute(select(Row.code).where(Row.study_id == study_id))).scalars())
        code = str(body.get("code") or "").strip()
        if not code:
            n = 1
            while f"ASM-{n:02d}" in codes:
                n += 1
            code = f"ASM-{n:02d}"
        elif code in codes:
            raise HTTPException(409, f"Assumption {code} already exists.")
        row = Row(id=_uid(), study_id=study_id, code=code, origin="user", order=len(codes), status="open",
                  due_gate=DEFAULT_DUE_GATE)
        s.add(row)
        _apply(row, {**body, "code": code})
        await s.commit()
        return _dict(row)


@router.patch("/studies/{study_id}/assumptions/{assumption_id}")
async def update_assumption(study_id: str, assumption_id: str, body: dict[str, Any]) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_se import SeAssumptionRow as Row
    study_or_404(study_id)
    async with get_session_factory()() as s:
        row = await s.get(Row, assumption_id)
        if row is None or row.study_id != study_id:
            row = (await s.execute(select(Row).where(Row.study_id == study_id, Row.code == assumption_id))).scalars().first()
        if row is None:
            raise HTTPException(404, f"Assumption {assumption_id} not found")
        _apply(row, body)
        await s.commit()
        return _dict(row)


@router.post("/studies/{study_id}/assumptions/import")
async def import_assumptions(study_id: str, body: dict[str, Any]) -> dict:
    """The ``[ASSUMPTION]`` tags of a budget ledger (``budgets``: the parsed ``budgets.yaml``) and
    the requirement rows whose ``open_item_note`` names an assumption (``requirements``: rows with
    ``id``, ``rationale``, ``open_item_note``, ``budget_ref``, ``allocation``, ``subsystem``), in
    one call (seed S3). ``items`` may also give ready rows. Codes ASM-01 … in register order;
    an existing row with the same source is updated, never duplicated."""
    from ..db.engine import get_session_factory
    from ..db.models_se import SeAssumptionRow as Row
    study_or_404(study_id)
    items = merge_register(budget_assumptions(body.get("budgets") or {}),
                           requirement_assumptions(body.get("requirements") or []))
    items += [dict(i) for i in body.get("items") or [] if isinstance(i, dict) and i.get("statement")]
    if not items:
        raise HTTPException(422, "Nothing to import: give budgets, requirements or items.")
    async with get_session_factory()() as s:
        if body.get("replace"):
            await s.execute(delete(Row).where(Row.study_id == study_id))
        have = list((await s.execute(select(Row).where(Row.study_id == study_id))).scalars())
        # a row is matched by any part of its source ("requirement X; budgets.yaml thermal.units.2")
        by_source = {part.strip(): r for r in have for part in str(r.source or "").split(";") if part.strip()}
        codes = {r.code for r in have}
        added = updated = 0
        n = len(have)
        for it in items:
            row = next((by_source[p.strip()] for p in str(it.get("source") or "").split(";") if p.strip() in by_source), None)
            if row is None:
                k = n + 1
                while f"ASM-{k:02d}" in codes:
                    k += 1
                code = f"ASM-{k:02d}"
                codes.add(code)
                row = Row(id=_uid(), study_id=study_id, code=code, origin="imported", order=n, status="open")
                s.add(row)
                n += 1
                added += 1
            else:
                updated += 1
                # an existing row keeps its statement, source and owner (a merged row has more than
                # this item; a user may have edited it); only the affected lines are added
                seen = {(a.get("kind"), a.get("ref")) for a in row.affects_json or []}
                it = {"affects": [*(row.affects_json or []),
                                  *(a for a in it.get("affects") or [] if (a.get("kind"), a.get("ref")) not in seen)]}
            _apply(row, {k: v for k, v in it.items() if k != "code"})
        await s.commit()
    return {"study_id": study_id, "added": added, "updated": updated, "items": await list_assumptions(study_id)}
