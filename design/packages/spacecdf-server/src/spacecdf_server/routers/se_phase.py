"""Phase API of the systems-engineering V (SE-01). Owner S (3.S1).

    GET /api/studies/{study_id}/phase              what the phase the study is in asks of it
        ?gate=srr                                  another gate's block (profile gate id)
        &register=learning|plain|practitioner      coaching register (default learning)
        &seat=power_engineer                       only that seat's cards
        &lang=en|fr                                language of the ``evidence`` strings
    GET /api/studies/{study_id}/phase/deliverables the deliverables evaluation alone (gate ``start``
                                                   warnings, the SE-01 criterion and the pack index read it)
    GET /api/se-protocol                           the protocol file as data (validation errors listed)
    POST /api/studies/{study_id}/semp/issue        record the SEMP issue ({"issue": "A", "by": seat, "note"});
                                                   409 until the generator has every SEMP part (SRR-EC-09)

Shape: ``services/se_protocol.py``.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..services import se_deliverables, se_protocol
from ._wave3_stub import study_or_404

router = APIRouter()


def _loaded() -> None:
    _, errs = se_protocol.load_with_errors()
    if errs:
        raise HTTPException(500, detail={"error": "se_protocol.yaml is invalid", "errors": errs[:20]})


@router.get("/studies/{study_id}/phase")
async def get_phase(study_id: str, lang: str = Query("en"), gate: str | None = Query(None),
                    register: str = Query(se_protocol.DEFAULT_REGISTER), seat: str | None = Query(None)) -> dict:
    study = study_or_404(study_id)
    _loaded()
    return await se_protocol.phase(study_id, study, lang=lang, gate=(gate or "").lower() or None,
                                   register=register, seat=seat)


@router.get("/studies/{study_id}/phase/deliverables")
async def get_phase_deliverables(study_id: str, gate: str | None = Query(None), lang: str = Query("en")) -> dict:
    study = study_or_404(study_id)
    _loaded()
    return await se_deliverables.evaluate(study_id, (gate or "").lower() or None, study=study, lang=lang)


@router.get("/se-protocol")
async def get_protocol() -> dict:
    data, errs = se_protocol.load_with_errors()
    return {"protocol": data, "errors": errs, "registers": list(se_protocol.REGISTERS)}


@router.get("/studies/{study_id}/semp/issue")
async def get_semp_issue(study_id: str) -> dict:
    """The SEMP's readiness (parts the generator fills) and the issue the team recorded."""
    from ..services import gate_evidence
    study = study_or_404(study_id)
    sm = await gate_evidence.semp(study_id)
    cur = dict((getattr(study, "document_issues", None) or {}).get("semp") or {})
    return {"study_id": study_id, "ready": bool(sm.get("ready")), "parts": sm.get("parts"), "of": sm.get("of"),
            "issue": cur.get("issue"), "issued_at": cur.get("issued_at"), "by": cur.get("by"),
            "history": list(cur.get("history") or [])}


@router.post("/studies/{study_id}/semp/issue")
async def issue_semp(study_id: str, body: dict | None = None) -> dict:
    """The team issues the SEMP generated from the study (wave 3 integration; SRR-EC-09). The
    issue letter defaults to the next one (A, B, …); the content must be complete first."""
    from datetime import datetime, timezone

    from ..db.study_repo import db_save_study
    from ..services import gate_evidence
    study = study_or_404(study_id)
    body = dict(body or {})
    sm = await gate_evidence.semp(study_id)
    if not sm.get("ready"):
        raise HTTPException(409, detail={"code": "semp_incomplete", "parts": sm.get("parts"), "of": sm.get("of"),
                                         "message": "The SEMP generator does not have every part yet"})
    issues = dict(getattr(study, "document_issues", None) or {})
    cur = dict(issues.get("semp") or {})
    prev = str(cur.get("issue") or "")
    letter = str(body.get("issue") or (chr(ord(prev[0]) + 1) if prev[:1].isalpha() and prev[:1] < "Z" else "A")).strip()[:8]
    if not letter:
        raise HTTPException(422, "issue must not be empty")
    rec = {"issue": letter, "issued_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "by": str(body.get("by") or "systems_engineer")[:64], "note": str(body.get("note") or "")[:500]}
    hist = list(cur.get("history") or [])
    if prev:
        hist.append({k: cur.get(k) for k in ("issue", "issued_at", "by", "note")})
    issues["semp"] = {**rec, "history": hist}
    study.document_issues = issues
    await db_save_study(study)
    return {"study_id": study_id, "semp": {**rec, "history": hist, "parts": sm.get("parts"), "of": sm.get("of")}}
