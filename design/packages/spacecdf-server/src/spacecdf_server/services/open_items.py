"""SpaceCDF — the open-item register (wave 3, 3.D4; negotiation #5, SE matrix #20). Owner D.

One register joins everything still open that a review must see, each with the gate it blocks:

=====================  ======================================================  ==============
kind                   from                                                     editable here
=====================  ======================================================  ==============
``pi_decision``,       ``open_items`` rows (NUMBERS ``open_decisions``, the     yes
``seat_decision``,     team's own entries, conflict resolutions)
``decision``,
``action``,
``conflict_resolution``
``rid``, ``action``    the gate review record (``review_items``, W4.08)         at the gate
``conditional_decision`` a decided trade with a condition not yet met           in Decide
``undecided_trade``    a mission, system or architecture trade of a gate,       in Decide
                       still open
``change``             a change proposal not yet decided (L's                   change control
                       ``change_proposals``)
=====================  ======================================================  ==============

``blocks_gate`` is a canonical gate (mdr … frr). A filter "blocks gate X" returns the open items
whose gate is X or an earlier one (an item that should have closed at SRR still blocks the PDR);
``exact`` limits it to X. Reads never write.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

KINDS = ("pi_decision", "seat_decision", "decision", "action", "rid", "conditional_decision", "undecided_trade",
         "change", "conflict_resolution")
STORED_KINDS = ("pi_decision", "seat_decision", "decision", "action", "conditional_decision", "change",
                "conflict_resolution", "rid")
STATUSES = ("open", "closed")
CANON = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: change-proposal statuses that are no longer open (L's table)
CHANGE_DONE = ("accepted", "approved", "rejected", "closed", "implemented", "withdrawn")
FIELDS = ("code", "kind", "title", "description", "owner_seat", "status", "blocks_gate", "due", "condition",
          "fallback", "resolution", "source_ref", "links", "data")


def gate_index(g: str | None) -> int:
    g = str(g or "").lower()
    return CANON.index(g) if g in CANON else 99


def seat_for_label(label: str | None) -> str:
    """A seat id from a seat id or its EN/FR label ("Comms & OBDH" → comms_engineer); "" if none."""
    from ..seats import config as seats_cfg
    lab = str(label or "").strip()
    if not lab:
        return ""
    ids = seats_cfg.seat_ids()
    if lab in ids:
        return lab
    low = lab.lower()
    for sid in ids:
        names = seats_cfg.label(sid) or {}
        if low in {str(v).lower() for v in names.values()}:
            return sid
    return ""


def _iso(v: Any) -> str | None:
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


def row_dict(r: Any) -> dict[str, Any]:
    return {"id": r.id, "code": r.code, "kind": r.kind, "title": r.title, "description": r.description,
            "owner_seat": r.owner_seat, "status": r.status, "blocks_gate": r.blocks_gate, "due": r.due,
            "condition": r.condition, "fallback": r.fallback, "resolution": r.resolution, "source_ref": r.source_ref,
            "links": dict(r.links_json or {}), "data": dict(r.data_json or {}), "origin": r.origin,
            "source": "register", "editable": True, "created_at": _iso(r.created_at), "updated_at": _iso(r.updated_at)}


def clean(body: dict[str, Any], partial: bool = False) -> dict[str, Any]:
    """Validated fields of a stored item; raises ValueError with the reason."""
    out: dict[str, Any] = {}
    for k in FIELDS:
        if k not in body:
            continue
        v = body[k]
        if k in ("links", "data"):
            if v is not None and not isinstance(v, dict):
                raise ValueError(f"{k} must be an object")
            out[k] = dict(v or {})
            continue
        v = "" if v is None else str(v)
        lim = {"code": 32, "kind": 24, "title": 240, "owner_seat": 48, "status": 16, "blocks_gate": 16, "due": 10,
               "source_ref": 64}.get(k, 4000)
        out[k] = v.strip()[:lim]
    if "kind" in out and out["kind"] not in STORED_KINDS:
        raise ValueError(f"kind must be one of {', '.join(STORED_KINDS)}")
    if "status" in out and out["status"] not in STATUSES:
        raise ValueError("status must be open or closed")
    if out.get("blocks_gate"):
        out["blocks_gate"] = out["blocks_gate"].lower()
        if out["blocks_gate"] not in CANON:
            raise ValueError(f"blocks_gate must be one of {', '.join(CANON)}")
    if out.get("due") and not _DATE.match(out["due"]):
        raise ValueError("due must be YYYY-MM-DD")
    if "owner_seat" in out and out["owner_seat"]:
        out["owner_seat"] = seat_for_label(out["owner_seat"]) or out["owner_seat"]
    if not partial and not (out.get("title") or out.get("code")):
        raise ValueError("an open item needs a title or a code")
    return out


# ─── storage ─────────────────────────────────────────────────────────────

async def list_stored(study_id: str) -> list[dict[str, Any]]:
    from sqlalchemy import select

    from ..db.engine import get_session_factory
    from ..db.models_changes import OpenItemRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(OpenItemRow).where(OpenItemRow.study_id == study_id)
                                .order_by(OpenItemRow.order, OpenItemRow.created_at))).scalars().all()
        return [row_dict(r) for r in rows]


async def create(study_id: str, body: dict[str, Any], origin: str = "user") -> dict[str, Any]:
    from sqlalchemy import func, select

    from ..db.engine import get_session_factory
    from ..db.models_changes import OpenItemRow
    d = clean(body)
    async with get_session_factory()() as s:
        n = (await s.execute(select(func.count()).select_from(OpenItemRow)
                             .where(OpenItemRow.study_id == study_id))).scalar() or 0
        row = OpenItemRow(id=uuid4().hex[:16], study_id=study_id, code=d.get("code", ""), kind=d.get("kind", "decision"),
                          title=d.get("title", ""), description=d.get("description", ""),
                          owner_seat=d.get("owner_seat", ""), status=d.get("status", "open"),
                          blocks_gate=d.get("blocks_gate", ""), due=d.get("due", ""), condition=d.get("condition", ""),
                          fallback=d.get("fallback", ""), resolution=d.get("resolution", ""),
                          source_ref=d.get("source_ref", ""), links_json=d.get("links") or None,
                          data_json=d.get("data") or None, origin=origin, order=int(n))
        s.add(row)
        await s.commit()
        await s.refresh(row)
        return row_dict(row)


async def update(study_id: str, item_id: str, body: dict[str, Any]) -> dict[str, Any] | None:
    from ..db.engine import get_session_factory
    from ..db.models_changes import OpenItemRow
    d = clean(body, partial=True)
    async with get_session_factory()() as s:
        row = await s.get(OpenItemRow, item_id)
        if row is None or row.study_id != study_id:
            return None
        for k, v in d.items():
            if k == "links":
                row.links_json = v or None
            elif k == "data":
                row.data_json = {**dict(row.data_json or {}), **v} or None
            else:
                setattr(row, k, v)
        if d.get("status") == "closed":
            row.data_json = {**dict(row.data_json or {}), "closed_at": datetime.now(timezone.utc).isoformat()}
        await s.commit()
        await s.refresh(row)
        return row_dict(row)


async def import_items(study_id: str, items: list[dict[str, Any]], *, replace: bool = False) -> dict[str, Any]:
    """Many items in one call (NUMBERS ``open_decisions``: ``id``, ``owner``, ``question``, plus
    optional ``status``, ``blocks_gate``, ``resolution``, ``due``). An item whose code exists is
    skipped (or replaced with ``replace``)."""
    have = {r["code"]: r for r in await list_stored(study_id) if r["code"]}
    added, replaced, skipped = [], [], []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("code") or raw.get("id") or "").strip()
        owner = str(raw.get("owner") or raw.get("owner_seat") or "")
        kind = raw.get("kind") or ("pi_decision" if owner.upper() == "PI" else "seat_decision")
        body = {"code": code, "kind": kind, "title": raw.get("title") or str(raw.get("question") or "")[:240],
                "description": raw.get("description") or raw.get("question") or "",
                "owner_seat": "" if owner.upper() == "PI" else (seat_for_label(owner) or owner),
                "status": raw.get("status") or "open", "blocks_gate": raw.get("blocks_gate") or "",
                "due": raw.get("due") or "", "condition": raw.get("condition") or "",
                "fallback": raw.get("fallback") or "", "resolution": raw.get("resolution") or "",
                "source_ref": raw.get("source_ref") or "", "links": raw.get("links") or {},
                "data": {**dict(raw.get("data") or {}), **({"owner": owner} if owner else {})}}
        if code in have:
            if not replace:
                skipped.append(code)
                continue
            await update(study_id, have[code]["id"], body)
            replaced.append(code)
        else:
            await create(study_id, body, origin="import")
            added.append(code)
    return {"added": added, "replaced": replaced, "skipped": skipped}


# ─── the joined register ─────────────────────────────────────────────────

def _next_gate(order: list[str], g: str) -> str:
    """The canonical gate after ``g`` (a RID raised at MDR is closed before the PRR)."""
    gi = gate_index(g)
    return CANON[gi + 1] if gi + 1 < len(CANON) else (g or "")


def _profile_canon(study: Any, gate: str | None) -> tuple[str | None, list[str]]:
    """(the last canonical gate a profile gate covers, the profile gate order)."""
    from . import gate_profiles as gp
    profile = gp.get_profile(getattr(study, "gate_profile", "") or None)
    order = [g["id"] for g in profile.get("gates") or []]
    if not gate:
        return None, order
    pg = gp.gate_of(profile, gate)
    if pg is None:
        g = str(gate).lower()
        return (g if g in CANON else None), order
    return (list(pg.get("covers") or [None])[-1]), order


def _canon_of_profile_gate(study: Any, gid: str) -> str:
    from . import gate_profiles as gp
    pg = gp.gate_of(gp.get_profile(getattr(study, "gate_profile", "") or None), gid)
    return (list((pg or {}).get("covers") or [gid])[0] or "").lower()


async def _rid_items(study_id: str, study: Any) -> list[dict[str, Any]]:
    from ..routers.gates import list_review_items
    from .gate_reviews import RID_OPEN
    out = []
    for r in await list_review_items(study_id):
        canon = _canon_of_profile_gate(study, r["gate"])
        out.append({"id": f"rid:{r['id']}", "code": r["number"], "kind": r["kind"], "title": r["description"][:240],
                    "description": r["description"], "owner_seat": r["owner_seat"],
                    "status": "open" if r["status"] in RID_OPEN else "closed", "blocks_gate": _next_gate([], canon),
                    "due": r["due_date"], "condition": "", "fallback": "", "resolution": r["closure_evidence"],
                    "source_ref": r["gate"], "links": {"criterion": r["criterion_id"]} if r["criterion_id"] else {},
                    "data": {"severity": r["severity"], "raised_at": r["gate"]}, "source": "review", "editable": False})
    return out


def _trade_items(study: Any) -> list[dict[str, Any]]:
    from .trades import normalise_records
    out = []
    for tid, rec in normalise_records(getattr(study, "trade_records", None)).items():
        st = rec.get("state") or {}
        dec = st.get("decision") or {}
        if st.get("status") == "decided" and dec.get("condition"):
            out.append({"id": f"trade:{tid}", "code": dec.get("record_id") or tid, "kind": "conditional_decision",
                        "title": f"{tid} {st.get('title') or ''}: {dec.get('selected')}".strip()[:240],
                        "description": dec.get("rationale") or "", "owner_seat": st.get("seat") or "",
                        "status": "open", "blocks_gate": dec.get("blocks_gate") or st.get("gate") or "",
                        "due": dec.get("due") or "", "condition": dec.get("condition") or "",
                        "fallback": dec.get("fallback") or "", "resolution": "", "source_ref": tid,
                        "links": {"risks": list(dec.get("risks") or []), "trade": tid}, "data": {},
                        "source": "trade", "editable": False})
        elif st.get("status") != "decided" and st.get("level") in ("mission", "system", "architecture") and st.get("gate"):
            out.append({"id": f"trade:{tid}", "code": tid, "kind": "undecided_trade",
                        "title": f"{tid} {st.get('title') or ''}".strip()[:240],
                        "description": st.get("recommendation") or "", "owner_seat": st.get("seat") or "",
                        "status": "open", "blocks_gate": st.get("gate"), "due": "", "condition": "", "fallback": "",
                        "resolution": "", "source_ref": tid, "links": {"trade": tid}, "data": {},
                        "source": "trade", "editable": False})
    return out


async def _change_items(study_id: str) -> list[dict[str, Any]]:
    try:
        from .gate_evidence import changes
        rows = await changes(study_id)
    except Exception:  # noqa: BLE001 — no change table yet
        return []
    out = []
    for c in rows:
        done = str(c.get("status") or "").lower() in CHANGE_DONE
        out.append({"id": f"change:{c['id']}", "code": c.get("code") or c["id"], "kind": "change",
                    "title": (c.get("title") or "")[:240], "description": "", "owner_seat": "team_leader",
                    "status": "closed" if done else "open", "blocks_gate": c.get("decision_gate") or "",
                    "due": "", "condition": "", "fallback": "", "resolution": c.get("status") if done else "",
                    "source_ref": c.get("source_trade") or "", "links": {"change": c["id"]}, "data": {"status": c.get("status")},
                    "source": "change", "editable": False})
    return out


async def register(study_id: str, study: Any, *, blocks_gate: str | None = None, exact: bool = False,
                   include_closed: bool = False) -> dict[str, Any]:
    """The joined register (see the module doc), filtered by the gate the items block."""
    items = [*await list_stored(study_id), *await _rid_items(study_id, study), *_trade_items(study),
             *await _change_items(study_id)]
    # a change with a stored mirror (code) is listed once: the change itself
    change_codes = {i["code"] for i in items if i["source"] == "change"}
    items = [i for i in items if not (i["source"] == "register" and i["kind"] == "change" and i["code"] in change_codes)]
    # a conditional decision recorded under a stored decision's code (T-07 → D-COM-01) is one item:
    # the stored one, with the trade's condition, fallback and linked risks
    stored = {i["code"]: i for i in items if i["source"] == "register" and i["code"]}
    keep = []
    for i in items:
        twin = stored.get(i["code"]) if i["source"] == "trade" and i["kind"] == "conditional_decision" else None
        if twin is None:
            keep.append(i)
            continue
        for k in ("condition", "fallback", "due"):
            if not twin.get(k) and i.get(k):
                twin[k] = i[k]
        twin["links"] = {**i.get("links", {}), **twin.get("links", {}),
                         "risks": list(dict.fromkeys([*(twin.get("links", {}).get("risks") or []),
                                                      *(i.get("links", {}).get("risks") or [])]))}
        twin["source_ref"] = twin.get("source_ref") or i["source_ref"]
        if not twin.get("blocks_gate"):
            twin["blocks_gate"] = i.get("blocks_gate") or ""
    items = keep
    canon, _order = _profile_canon(study, blocks_gate)
    sel = []
    for i in items:
        if not include_closed and i["status"] != "open":
            continue
        if blocks_gate:
            gi, ci = gate_index(i.get("blocks_gate")), gate_index(canon)
            if exact and gi != ci:
                continue
            if not exact and gi > ci:
                continue
        sel.append(i)
    by_gate: dict[str, list[str]] = {}
    for i in sel:
        by_gate.setdefault(i.get("blocks_gate") or "", []).append(i["code"] or i["id"])
    counts = {"total": len(sel), "open": sum(1 for i in sel if i["status"] == "open"),
              "by_kind": {k: sum(1 for i in sel if i["kind"] == k) for k in KINDS if any(i["kind"] == k for i in sel)}}
    return {"items": sel, "by_gate": by_gate, "counts": counts, "blocks_gate": canon if blocks_gate else None}


async def record_resolution(study_id: str, conflict: dict[str, Any], rationale: str, seat: str, by: str = "") -> dict[str, Any]:
    """A resolved analysis conflict's rationale and seat, kept in the register (closed)."""
    return await create(study_id, {
        "code": str(conflict.get("code") or "")[:32], "kind": "conflict_resolution",
        "title": str(conflict.get("title") or conflict.get("code") or "Conflict")[:240],
        "description": str(conflict.get("detail") or ""), "owner_seat": seat, "status": "closed",
        "resolution": rationale, "source_ref": str(conflict.get("id") or "")[:64],
        "data": {"analysis": conflict.get("analysis"), "by": by,
                 "resolved_at": datetime.now(timezone.utc).isoformat()}}, origin="conflict")


__all__ = ["KINDS", "create", "import_items", "list_stored", "record_resolution", "register", "seat_for_label", "update"]
