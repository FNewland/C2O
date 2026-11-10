"""SpaceCDF — review-readiness evidence of the SRR and PDR (wave 3, agent D; PI addendum).

``collect(study_id)`` reads, without writing, the records the other agents' tools keep, so the
readiness criteria of ``services/gate_reviews.py`` (``READINESS_CRITERIA``: SRR-RD-*, PDR-RD-*)
can say whether the team has produced each item of the v2 review-readiness list:

=================  ===========================================================  =========
probe              read from                                                    owner
=================  ===========================================================  =========
``semp``           export section ``semp`` (content ready; ``issue`` once issued)  X 3.X3
``debris``         ``debris_assessments`` (latest version)                       L 3.L8
``changes``        ``change_proposals`` (code, status, decision gate)           L 3.L4
``icds``           ``icd_issues`` (latest issue per ``icd_ref``, both sign-offs)  R 3.R6
``reliability``    ``reliability_blocks`` (computed blocks)                     A 3.A5
``fmea``           ``fmea_rows``                                                A 3.A5
``thermal``        ``thermal_nodes``, ``thermal_cases`` (solved, margins)        A 3.A6
=================  ===========================================================  =========

Every probe is defensive: a table that is empty or a section that is still a stub gives "no
evidence", never an error. Returns plain dicts (no ORM objects).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

#: SEMP parts the generator fills (export section ``semp``, X)
SEMP_PARTS = ("organisation", "lifecycle", "processes", "tailoring", "configuration_management")


async def _rows(model, study_id: str) -> list[Any]:
    from sqlalchemy import select

    from ..db.engine import get_session_factory
    async with get_session_factory()() as s:
        return list((await s.execute(select(model).where(model.study_id == study_id))).scalars().all())


def _when(v: Any) -> str | None:
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


async def semp(study_id: str) -> dict[str, Any]:
    """The SEMP section's readiness: parts filled and the issue the team recorded (if any)."""
    try:
        from .export_context import collect
        sx = await collect(study_id, sections=["semp"])
        sec = dict(getattr(sx, "semp", None) or {})
    except Exception:  # noqa: BLE001 — no study / generator not ready
        logger.debug("semp section unavailable for %s", study_id, exc_info=True)
        return {"ready": False, "parts": 0, "of": len(SEMP_PARTS), "issue": None}
    if sec.get("status") == "not_implemented":
        return {"ready": False, "parts": 0, "of": len(SEMP_PARTS), "issue": None, "stub": True}
    parts = sum(1 for k in SEMP_PARTS if sec.get(k))
    iss = sec.get("issue") or sec.get("issued")
    if isinstance(iss, dict):
        issue, at = iss.get("issue") or iss.get("letter") or iss.get("id"), iss.get("at") or iss.get("issued_at")
    else:
        issue, at = (str(iss) if iss else None), sec.get("issued_at")
    return {"ready": parts == len(SEMP_PARTS), "parts": parts, "of": len(SEMP_PARTS), "issue": issue, "issued_at": at}


async def debris(study_id: str) -> dict[str, Any] | None:
    from ..db.models_debris import DebrisAssessmentRow
    rows = await _rows(DebrisAssessmentRow, study_id)
    live = [r for r in rows if r.status != "superseded"] or rows
    if not live:
        return None
    r = max(live, key=lambda x: (x.version or 0, _when(x.updated_at) or ""))
    return {"id": r.id, "version": r.version, "status": r.status, "lifetime_y": r.lifetime_y,
            "casualty_risk": r.casualty_risk, "collision_probability": r.collision_probability,
            "accepted_gate": r.accepted_gate, "accepted_by": r.accepted_by, "accepted_at": _when(r.accepted_at)}


async def changes(study_id: str) -> list[dict[str, Any]]:
    from ..db.models_changes import ChangeProposalRow
    rows = await _rows(ChangeProposalRow, study_id)
    return [{"id": r.id, "code": r.code, "kind": r.kind, "title": r.title, "status": r.status,
             "decision_gate": (r.decision_gate or "").lower(), "source_trade": r.source_trade}
            for r in sorted(rows, key=lambda r: (r.order or 0, r.code or ""))]


async def icds(study_id: str) -> list[dict[str, Any]]:
    """The latest issue of each ICD with the two owners' sign-off state."""
    from ..db.models_icd import IcdIssueRow
    rows = [r for r in await _rows(IcdIssueRow, study_id) if r.state != "superseded"]
    latest: dict[str, Any] = {}
    for r in rows:
        key = r.icd_ref or r.interface_id or r.id
        cur = latest.get(key)
        rank = ((r.issue or ""), r.revision or 0, _when(r.updated_at) or "")
        if cur is None or rank > ((cur.issue or ""), cur.revision or 0, _when(cur.updated_at) or ""):
            latest[key] = r
    out = []
    for key, r in sorted(latest.items()):
        so = dict(r.signoffs_json or {})
        need = [s for s in (r.provider_seat, r.consumer_seat) if s]
        signed = [s for s in need if so.get(s)]
        out.append({"icd_ref": key, "title": r.title, "issue": r.issue, "revision": r.revision, "state": r.state,
                    "provider_seat": r.provider_seat, "consumer_seat": r.consumer_seat, "signed": signed,
                    "signed_by_both": bool(need) and len(signed) == len(need) and len(need) == 2})
    return out


async def reliability(study_id: str) -> dict[str, Any]:
    from ..db.models_reliability import ReliabilityBlockRow
    rows = await _rows(ReliabilityBlockRow, study_id)
    computed = [r for r in rows if r.reliability is not None]
    top = [r for r in computed if not r.parent_block] or computed
    system = None
    for r in top:
        if (r.data_json or {}).get("system") or (r.name or "").lower() in ("system", "space segment", "mission"):
            system = r.reliability
            break
    if system is None and top:
        system = 1.0
        for r in top:
            system *= float(r.reliability)
    horizon = next((r.horizon_months for r in computed if r.horizon_months), None)
    return {"blocks": len(rows), "computed": len(computed), "system": system, "horizon_months": horizon}


async def fmea(study_id: str) -> dict[str, Any]:
    from ..db.models_reliability import FmeaRow
    rows = await _rows(FmeaRow, study_id)
    return {"rows": len(rows), "subsystems": sorted({r.subsystem for r in rows if r.subsystem}),
            "single_points": sum(1 for r in rows if r.single_point)}


def _min_margin(results: Any) -> float | None:
    vals: list[float] = []
    for v in (results or {}).values() if isinstance(results, dict) else []:
        if isinstance(v, dict):
            for k in ("margin_design_c", "margin_c", "design_margin_c"):
                if isinstance(v.get(k), (int, float)):
                    vals.append(float(v[k]))
                    break
    return min(vals) if vals else None


async def thermal(study_id: str) -> dict[str, Any]:
    from ..db.models_thermal import ThermalCaseRow, ThermalNodeRow
    nodes = [n for n in await _rows(ThermalNodeRow, study_id) if (n.kind or "diffusion") != "boundary"]
    cases = await _rows(ThermalCaseRow, study_id)
    return {"nodes": len(nodes),
            "cases": [{"code": c.code, "kind": c.kind, "status": c.status,
                       "solved": c.status == "solved" or bool(c.results_json),
                       "min_margin_c": _min_margin(c.results_json)} for c in cases]}


async def collect(study_id: str, probes: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Every probe (or ``probes``), each defensive."""
    fns = {"semp": semp, "debris": debris, "changes": changes, "icds": icds, "reliability": reliability,
           "fmea": fmea, "thermal": thermal}
    out: dict[str, Any] = {}
    for name, fn in fns.items():
        if probes is not None and name not in probes:
            continue
        try:
            out[name] = await fn(study_id)
        except Exception:  # noqa: BLE001 — a missing table or a broken record is "no evidence"
            logger.debug("gate evidence %s unavailable for %s", name, study_id, exc_info=True)
            out[name] = None
    return out


__all__ = ["SEMP_PARTS", "collect"]
