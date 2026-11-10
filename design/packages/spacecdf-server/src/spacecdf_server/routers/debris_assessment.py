"""Debris assessment in the tool (PI addendum). Owner L (3.L8): DRAMA/DAS-like lifetime, casualty
risk and collision probability, accepted at SRR; table ``debris_assessments``
(``db/models_debris.py``); service ``services/debris_assessment.py``.

* ``GET  /studies/{id}/debris-assessment`` — the latest assessment (``items``: every run, newest
  first), the current figures (``current``, not stored) and the gate evidence (``evidence``);
* ``POST /studies/{id}/debris-assessment/run`` — compute and store a new run (supersedes the last);
* ``POST /studies/{id}/debris-assessment/accept`` — ``{gate, by?, note?, deviation?}``: accept the
  latest run at a gate (a failing run needs a deviation note);
* ``GET  /studies/{id}/debris-assessment/sweep?altitudes=500,550,590`` — lifetime against altitude
  with and without the sail (3.L3, used by the sensitivity view 3.H5 and ECP-02).

Seats: the Propulsion seat (disposal function), the Team leader and the Comms engineer run it (the
Licensing tab's writers); the Propulsion seat, the Team leader and the Systems engineer accept it.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from ._wave3_stub import study_or_404

router = APIRouter()
OWNER, WP = "L", "3.L8"


async def _actor(request: Request, study_id: str, seats: tuple[str, ...]) -> str:
    try:
        from ..seats import store
        from ..seats.service import seat_ctx
        state = store.peek_team(study_id) or await store.get_team(study_id)
        if not state.get("enabled"):
            return ""
        ctx = await seat_ctx(request, study_id)
    except Exception:  # noqa: BLE001 — seats unavailable: a solo study
        return ""
    if ctx.instructor:
        return "instructor"
    for s in seats:
        if ctx.holds(s):
            return s
    raise HTTPException(403, detail={"code": "debris_seat",
                                     "message": "The debris assessment is run by the Propulsion seat, the Team "
                                                "leader or the Comms engineer, and accepted by the Propulsion "
                                                "seat, the Team leader or the Systems engineer"})


@router.get("/studies/{study_id}/debris-assessment")
async def get_debris_assessment(study_id: str, current: bool = Query(True)) -> dict:
    """The latest assessment and its acceptance."""
    from ..services import debris_assessment as da
    study_or_404(study_id)
    items = await da.history(study_id)
    out: dict[str, Any] = {"study_id": study_id, "items": items, "latest": items[0] if items else None,
                           "evidence": await da.srr_evidence(study_id)}
    if current:
        try:
            out["current"] = await da.compute(study_id)
        except Exception as exc:  # noqa: BLE001 — an incomplete design: the error is shown
            out["current"] = {"error": f"{type(exc).__name__}: {exc}"}
    return out


@router.post("/studies/{study_id}/debris-assessment/run")
async def run_debris_assessment(study_id: str, request: Request, body: dict[str, Any] | None = None) -> dict:
    """Lifetime with / without the device, casualty risk, collision probability (stored)."""
    from ..services import debris_assessment as da
    study_or_404(study_id)
    actor = await _actor(request, study_id, ("propulsion_engineer", "team_leader", "comms_engineer"))
    row = await da.run(study_id, by=str((body or {}).get("by") or actor or ""))
    try:
        from ._arcadia_events import broadcast_mutation
        await broadcast_mutation(study_id, "debris_assessment_updated", "debris_assessment", row["id"],
                                 {"version": row["version"]})
    except Exception:  # noqa: BLE001
        pass
    return row


@router.post("/studies/{study_id}/debris-assessment/accept")
async def accept_debris_assessment(study_id: str, body: dict[str, Any], request: Request) -> dict:
    """Accepted by a seat at a gate."""
    from ..services import debris_assessment as da
    study_or_404(study_id)
    actor = await _actor(request, study_id, da.ACCEPT_SEATS)
    try:
        row = await da.accept(study_id, gate=str(body.get("gate") or ""), by=str(body.get("by") or actor or "team"),
                              note=str(body.get("note") or ""), deviation=str(body.get("deviation") or ""))
    except da.AssessmentError as exc:
        raise HTTPException(422, str(exc)) from None
    try:
        from ._arcadia_events import broadcast_mutation
        await broadcast_mutation(study_id, "debris_assessment_updated", "debris_assessment", row["id"],
                                 {"version": row["version"], "status": row["status"]})
    except Exception:  # noqa: BLE001
        pass
    return row


@router.get("/studies/{study_id}/debris-assessment/sweep")
async def debris_sweep(study_id: str, altitudes: str = Query("450,500,550,590,600,650,700")) -> dict:
    """Lifetime against altitude, with and without the sail, for the three solar-cycle scenarios."""
    from ..services import debris_assessment as da
    study_or_404(study_id)
    try:
        alts = [float(x) for x in altitudes.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(422, "altitudes: comma-separated numbers (km)") from None
    if not alts or len(alts) > 40:
        raise HTTPException(422, "give 1 to 40 altitudes")
    return await da.sweep(study_id, alts)
