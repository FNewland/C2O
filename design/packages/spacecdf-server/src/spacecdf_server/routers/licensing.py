"""SpaceCDF — Licensing tab API (W5.01-W5.03).

Included by ``routers/lifecycle.py`` (prefix ``/api/lifecycle``):

* ``GET  /licensing/{study_id}`` — the stored record (team inputs and filing tracker) with its
  ``version``, plus what the design derives: frequency assignments (W5.01), the disposal analysis
  (W5.02), stations, orbit node times and sensor performance;
* ``PUT  /licensing/{study_id}`` — merge a patch into the record (``version`` must match the stored
  one; lists are replaced whole). In a study with seats the team_leader and comms_engineer seats
  (and the instructor) may write; the propulsion_engineer seat, which owns the disposal function
  (PI decision), may write the ``disposal`` part only;
* ``POST /licensing/{study_id}/evidence`` — import a DRAMA or DAS result (structured fields, or the
  tool's text report, from which lifetime, collision probability and casualty risk are read);
* ``GET  /payload-geometry/{study_id}`` — wave 3 (3.L5): GSD, swath, FOV, frame size, CSI-2 rate,
  trigger interval and product sizes of the payload cameras from their optics and detectors.

The GET also returns ``progress`` (3.L1): the required team inputs filled, n/m overall, per tab and
for RSSSA sections 14 to 30, with the missing fields and the format problems.
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ..services import licensing as lic

router = APIRouter()

WRITE_SEATS = ("team_leader", "comms_engineer")
#: seats that may write only some parts of the record: the Propulsion seat owns the disposal function
PARTIAL_SEATS: dict[str, tuple[str, ...]] = {"propulsion_engineer": ("disposal", "evidence")}


async def _context(study_id: str):
    from ..services.export_context import collect
    try:
        return await collect(study_id, sections=["mission", "elements", "rollup", "licensing"])
    except LookupError:
        raise HTTPException(404, f"Study {study_id} not found") from None


async def _check_seat(request: Request, study_id: str, parts: set[str] | None = None) -> str:
    """Seat studies: team_leader / comms_engineer (or the instructor); the propulsion_engineer seat
    for the disposal part only (``parts`` = the record keys written). Returns the actor."""
    try:
        from ..seats import store
        from ..seats.service import seat_ctx
        state = store.peek_team(study_id) or await store.get_team(study_id)
        if not state.get("enabled"):
            return ""
        ctx = await seat_ctx(request, study_id)
    except Exception:  # noqa: BLE001 — seats unavailable: behave as a solo study
        return ""
    if ctx.instructor:
        return "instructor"
    if any(ctx.holds(s) for s in WRITE_SEATS):
        return ctx.active or ""
    for seat, allowed in PARTIAL_SEATS.items():
        if ctx.holds(seat) and parts is not None and parts <= set(allowed):
            return ctx.active or seat
    raise HTTPException(403, detail={"code": "licensing_seat",
                                     "message": "The Licensing tab is edited by the Team leader and the "
                                                "Comms engineer seats (the Propulsion seat edits the "
                                                "disposal part)"})


@router.get("/licensing/{study_id}")
async def get_licensing(study_id: str, lang: str = "en") -> dict:
    sx = await _context(study_id)
    record, version = await lic.load_record(study_id)
    sec = sx.licensing
    return {"study_id": study_id, "version": version, "record": record,
            "filings": sec.get("filings") or [], "filing_statuses": list(lic.FILING_STATUSES),
            "derived": {k: sec.get(k) for k in ("assignments", "disposal", "stations", "orbit", "sensor", "launch")},
            "to_be_confirmed": sec.get("to_be_confirmed") or [], "progress": lic.progress(record),
            "errors": sx.errors}


@router.put("/licensing/{study_id}")
async def put_licensing(study_id: str, body: dict[str, Any], request: Request) -> dict:
    from ..routers.studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    body = dict(body or {})
    version = body.pop("version", None)
    body.pop("study_id", None)
    actor = await _check_seat(request, study_id, set(body))
    allowed = set(lic.EMPTY_RECORD)
    unknown = sorted(set(body) - allowed)
    if unknown:
        raise HTTPException(422, f"Unknown licensing fields: {unknown}")
    errs = lic.validate_record(body)
    if errs:
        raise HTTPException(422, "; ".join(errs))
    try:
        record, ver = await lic.save_record(study_id, body, version=version, actor=actor)
    except lic.VersionConflict as exc:
        raise HTTPException(409, detail={"code": "version_conflict", "current_version": exc.current}) from None
    try:
        from ._arcadia_events import broadcast_mutation
        await broadcast_mutation(study_id, "licensing_updated", "licensing", study_id, {"version": ver})
    except Exception:  # noqa: BLE001
        pass
    return {"study_id": study_id, "version": ver, "record": record}


_NUM = r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
_PATTERNS = {
    "lifetime_years": [rf"orbital\s+lifetime[^\n:=]*[:=]\s*{_NUM}", rf"lifetime\s*\[?y(?:ea)?rs?\]?\s*[:=]?\s*{_NUM}",
                       rf"remaining\s+lifetime[^\n:=]*[:=]\s*{_NUM}"],
    "collision_probability": [rf"collision\s+probability[^\n:=]*[:=]\s*{_NUM}",
                              rf"probability\s+of\s+(?:collision|impact)[^\n:=]*[:=]\s*{_NUM}"],
    "casualty_risk": [rf"(?:human\s+)?casualty\s+(?:risk|expectation|probability)[^\n:=]*[:=]\s*(?:1\s*:\s*)?{_NUM}",
                      rf"risk\s+of\s+human\s+casualty[^\n:=]*[:=]\s*(?:1\s*:\s*)?{_NUM}"],
}


def parse_tool_report(text: str) -> dict:
    """Read the key numbers from a DRAMA (OSCAR/ARES/SARA) or DAS text report (best effort)."""
    out: dict[str, Any] = {}
    for key, pats in _PATTERNS.items():
        for p in pats:
            m = re.search(p, text, re.I)
            if m:
                out[key] = float(m.group(1))
                break
    m = re.search(r"\b(DRAMA|DAS|OSCAR|ARES|SARA|STELA)\b[^\n]*?(\d+(?:\.\d+)+)?", text)
    if m:
        out.setdefault("tool_detected", m.group(1))
        if m.group(2):
            out.setdefault("version_detected", m.group(2))
    return out


@router.post("/licensing/{study_id}/evidence")
async def add_evidence(study_id: str, body: dict[str, Any], request: Request) -> dict:
    from ..routers.studies import get_study_store
    if get_study_store().get(study_id) is None:
        raise HTTPException(404, f"Study {study_id} not found")
    actor = await _check_seat(request, study_id, {"evidence"})
    tool = str(body.get("tool") or "").strip()
    text = body.get("text") or ""
    parsed = parse_tool_report(text) if text else {}
    tool = tool or parsed.get("tool_detected") or ""
    if not tool:
        raise HTTPException(422, "give the tool (DRAMA, DAS, ...) or a report that names it")
    row = {"tool": tool, "version": body.get("version") or parsed.get("version_detected") or "",
           "date": body.get("date") or "", "phase": body.get("phase") or "disposal",
           "lifetime_years": body.get("lifetime_years", parsed.get("lifetime_years")),
           "collision_probability": body.get("collision_probability", parsed.get("collision_probability")),
           "casualty_risk": body.get("casualty_risk", parsed.get("casualty_risk")),
           "file_name": body.get("file_name") or "", "notes": body.get("notes") or ""}
    record, version = await lic.load_record(study_id)
    evidence = list(record.get("evidence") or []) + [row]
    record, ver = await lic.save_record(study_id, {"evidence": evidence}, actor=actor)
    return {"study_id": study_id, "version": ver, "evidence": row, "parsed": parsed}


@router.get("/payload-geometry/{study_id}")
async def payload_geometry(study_id: str) -> dict:
    """3.L5: the payload cameras' geometry and product sizes proposed from the optics."""
    from ..routers.studies import get_study_store
    from ..services import rollup as ru
    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(404, f"Study {study_id} not found")
    try:
        from ..db import cdr_repo
        rows = await cdr_repo.list_rows(study_id)
    except Exception:  # noqa: BLE001
        rows = []
    return {"study_id": study_id, **lic.payload_geometry(study, ru.study_elements(study_id), rows)}
