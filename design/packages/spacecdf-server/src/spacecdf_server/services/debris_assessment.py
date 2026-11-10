"""The debris assessment in the tool (wave 3, 3.L8; PI addendum): DRAMA/DAS-like outputs that a
review can accept, and the evidence the SRR criterion reads.

One run (``run(study_id)``) takes the study as it stands and writes one ``debris_assessments`` row
(``db/models_debris.py``) with:

* **lifetime** (OSCAR-like): post-mission lifetime per solar-cycle scenario with the drag sail
  (deployed at launch: the early-failure case, and at the end of operations) and without it, the
  ISED 5-year line and the legacy 25-year line, and the highest start altitude that still
  decays in 5 years (``physics/disposal.assess_disposal``);
* **collision probability** (ARES-like): objects >= 10 cm and < 10 cm over the operational life
  (stowed area) and over the disposal phase (sail area);
* **casualty risk** (DAS/SARA-like): surviving fragments of an uncontrolled re-entry, debris
  casualty area and casualty expectation (``physics/debris.reentry_casualty``);
* **compliance**: the ISED checks (ISED-DM-01…06) plus the casualty check (DM-07), and the
  imported DRAMA/DAS result (licensing record ``evidence``) quoted beside the tool's numbers.

A run supersedes the previous one. ``accept(study_id, gate, by)`` records the acceptance of the
latest run at a gate (SRR in the walkthrough); a run whose checks fail can be accepted only with a
deviation note. ``srr_evidence(study_id)`` is the evidence function agent R wires into the gate
criteria: accepted, at which gate, compliant, and whether the design changed since (stale).

Screening models: a licence application quotes ESA DRAMA or NASA DAS; this assessment is what the
team reviews before running them.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

ACCEPT_SEATS = ("propulsion_engineer", "team_leader", "systems_engineer")
STATUSES = ("draft", "accepted", "superseded")


class AssessmentError(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _inputs(study_id: str) -> tuple[dict, dict, Any, list[dict]]:
    """(disposal analysis as the Licensing tab shows it, rollup, study, elements)."""
    from . import licensing as lic
    from . import rollup as ru
    from ..routers.studies import get_study_store
    study = get_study_store().get(study_id)
    if study is None:
        raise LookupError(study_id)
    els = ru.study_elements(study_id)
    roll = (await ru.compute(study_id)).as_dict()
    rec, _v = await lic.load_record(study_id)
    return lic.disposal_analysis(study, els, roll, rec), roll, study, els


def _fingerprint(d: dict, comps: list[dict], incl: Any) -> str:
    key = {"alt": d.get("altitude_km"), "ecc": d.get("apogee_km"), "mass": d.get("mass_kg"),
           "sail": (d.get("sail") or {}).get("deployed_area_m2"), "start": d.get("start_year"),
           "ops": d.get("operations_years"), "incl": incl,
           "comps": sorted((c["name"], round(float(c["mass_kg"] or 0), 4), int(c["quantity"] or 1)) for c in comps)}
    return hashlib.sha1(json.dumps(key, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _components(els: list[dict]) -> list[dict]:
    return [{"name": e.get("name"), "mass_kg": e.get("mass_kg") or 0.0, "quantity": e.get("quantity") or 1}
            for e in els if e.get("element_type") == "component" and (e.get("segment") or "space") == "space"
            and not e.get("deleted_at")]


async def compute(study_id: str) -> dict[str, Any]:
    """The assessment of the study as it stands (nothing written)."""
    from spacecdf_common.physics.debris import reentry_casualty
    d, _roll, study, els = await _inputs(study_id)
    orb = getattr(getattr(study, "requirements", None), "orbit", None)
    incl = getattr(orb, "inclination_deg", None) or 97.0
    comps = _components(els)
    cas = reentry_casualty(comps, incl)
    checks = list(d.get("checks") or [])
    checks.append({"id": "ISED-DM-07", "rule": "Casualty expectation of the uncontrolled re-entry < 1:10 000",
                   "value": cas["casualty_expectation"], "limit": cas["limit"], "unit": "",
                   "pass": cas["compliant"], "basis": "DAS-like screening (surviving fragments, 15 J threshold)"})
    ws, wo = d.get("lifetime_with_sail_y") or {}, d.get("lifetime_without_sail_y") or {}
    eol = [r for r in d.get("scenarios") or [] if r.get("case") == "device_at_end_of_operations"]
    lifetime = {
        "with_device_y": ws, "without_device_y": wo, "without_device_range_y": d.get("without_sail_range_y"),
        "with_device_after_operations_y": {r["scenario"]: r["lifetime_years"] for r in eol},
        "worst_with_device_y": max(ws.values()) if ws else None,
        "worst_without_device_y": max(wo.values()) if wo else None,
        "highest_start_altitude_5y_km": d.get("highest_start_altitude_5y_km"),
        "rule_5y": 5.0, "rule_25y": 25.0,
        "compliant_5y": (max(ws.values()) <= 5.0) if ws else (max(wo.values()) <= 5.0 if wo else None),
        "compliant_25y": (max(ws.values()) <= 25.0) if ws else (max(wo.values()) <= 25.0 if wo else None),
    }
    collision = {"operational_large": d.get("collision_probability_large"),
                 "operational_small": d.get("collision_probability_small"),
                 "disposal_large": d.get("collision_probability_disposal_large"),
                 "limit_large": (d.get("rules") or {}).get("collision_probability_max_large"),
                 "limit_small": (d.get("rules") or {}).get("collision_probability_max_small"),
                 "method": "ARES-like screening flux (public catalogue spatial density x 10 km/s)"}
    inputs = {"altitude_km": d.get("altitude_km"), "apogee_km": d.get("apogee_km"), "inclination_deg": incl,
              "mass_kg": d.get("mass_kg"), "mass_basis": d.get("mass_basis"), "start_year": d.get("start_year"),
              "end_of_ops_year": d.get("end_of_ops_year"), "operations_years": d.get("operations_years"),
              "launch_date": d.get("launch_date"), "area_stowed_m2": d.get("area_stowed_m2"),
              "area_deployed_effective_m2": d.get("area_deployed_effective_m2"),
              "device": d.get("sail"), "disposal_reliability": d.get("disposal_reliability"),
              "components": len(comps), "fingerprint": _fingerprint(d, comps, incl)}
    compliant = all(c.get("pass") is not False for c in checks)
    return {"inputs": inputs, "lifetime": lifetime, "collision": collision, "casualty": cas, "checks": checks,
            "compliant": compliant, "evidence": d.get("evidence") or [], "model": d.get("model"),
            "notes": list(d.get("notes") or []) + [
                "Screening assessment in the tool (OSCAR-, ARES- and DAS-like). The licence application quotes "
                "the result of ESA DRAMA or NASA DAS; import it on the Licensing tab (DRAMA / DAS result)."]}


def _row_dict(r) -> dict[str, Any]:
    res = r.results_json or {}
    return {"id": r.id, "study_id": r.study_id, "version": r.version, "status": r.status,
            "inputs": r.inputs_json or {}, "lifetime_y": r.lifetime_y,
            "lifetime_without_device_y": r.lifetime_without_device_y, "casualty_risk": r.casualty_risk,
            "collision_probability": r.collision_probability, **res,
            "accepted_by": r.accepted_by, "accepted_gate": r.accepted_gate,
            "accepted_at": r.accepted_at.isoformat() if r.accepted_at else None,
            "note": (r.data_json or {}).get("note", ""), "deviation": (r.data_json or {}).get("deviation", ""),
            "run_by": (r.data_json or {}).get("run_by", ""),
            "created_at": r.created_at.isoformat() if r.created_at else None}


async def history(study_id: str) -> list[dict]:
    from sqlalchemy import select
    from ..db.engine import get_session_factory
    from ..db.models_debris import DebrisAssessmentRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(DebrisAssessmentRow).where(DebrisAssessmentRow.study_id == study_id)
                                .order_by(DebrisAssessmentRow.version.desc()))).scalars().all()
        return [_row_dict(r) for r in rows]


async def latest(study_id: str) -> dict | None:
    h = await history(study_id)
    return h[0] if h else None


async def run(study_id: str, *, by: str = "") -> dict:
    """Compute and store a new assessment (the previous ones are superseded)."""
    from sqlalchemy import select
    from ..db.engine import get_session_factory
    from ..db.models_debris import DebrisAssessmentRow
    a = await compute(study_id)
    lt = a["lifetime"]
    async with get_session_factory()() as s:
        prev = (await s.execute(select(DebrisAssessmentRow).where(DebrisAssessmentRow.study_id == study_id))).scalars().all()
        ver = max([p.version or 0 for p in prev] or [0]) + 1
        for p in prev:
            if p.status != "superseded":
                p.status = "superseded"
        row = DebrisAssessmentRow(
            id=uuid4().hex[:16], study_id=study_id, version=ver, inputs_json=a["inputs"],
            lifetime_y=lt["worst_with_device_y"] if lt["worst_with_device_y"] is not None else lt["worst_without_device_y"],
            lifetime_without_device_y=lt["worst_without_device_y"],
            casualty_risk=a["casualty"]["casualty_expectation"],
            collision_probability=a["collision"]["operational_large"],
            results_json={k: a[k] for k in ("lifetime", "collision", "casualty", "checks", "compliant", "evidence",
                                            "model", "notes")},
            status="draft", data_json={"run_by": by[:120]}, order=ver)
        s.add(row)
        await s.commit()
        return _row_dict(row)


async def accept(study_id: str, *, gate: str, by: str, note: str = "", deviation: str = "") -> dict:
    """Accept the latest run at ``gate``. A non-compliant run needs a deviation note."""
    from sqlalchemy import select
    from ..db.engine import get_session_factory
    from ..db.models_debris import DebrisAssessmentRow
    g = str(gate or "").strip().lower()
    if not g:
        raise AssessmentError("give the gate the assessment is accepted at (e.g. srr)")
    async with get_session_factory()() as s:
        rows = (await s.execute(select(DebrisAssessmentRow).where(DebrisAssessmentRow.study_id == study_id)
                                .order_by(DebrisAssessmentRow.version.desc()))).scalars().all()
        if not rows:
            raise AssessmentError("run the assessment first")
        r = rows[0]
        if r.status == "superseded":
            raise AssessmentError("the latest assessment is superseded: run it again")
        if not (r.results_json or {}).get("compliant") and not deviation.strip():
            raise AssessmentError("the assessment does not meet every check: accept it with a deviation note, or "
                                  "change the design and run it again")
        r.status = "accepted"
        r.accepted_by, r.accepted_gate, r.accepted_at = by[:120], g[:16], _now()
        r.data_json = {**(r.data_json or {}), "note": note, "deviation": deviation}
        await s.commit()
        return _row_dict(r)


async def srr_evidence(study_id: str, gate: str = "srr") -> dict:
    """Evidence for the gate criterion (agent R wires it): is the debris assessment accepted at or
    before ``gate``, compliant, and still about the current design?

    ``{status: pass | fail | open, accepted, gate, compliant, stale, version, message}``"""
    lt = await latest(study_id)
    if lt is None:
        return {"status": "open", "accepted": False, "gate": None, "compliant": None, "stale": None, "version": None,
                "message": "No debris assessment has been run"}
    stale = None
    try:
        cur = await compute(study_id)
        stale = cur["inputs"].get("fingerprint") != (lt.get("inputs") or {}).get("fingerprint")
    except Exception:  # noqa: BLE001
        logger.debug("debris evidence: recompute failed", exc_info=True)
    accepted = lt["status"] == "accepted"
    ok = accepted and not stale and (lt.get("compliant") or bool(lt.get("deviation")))
    msg = (f"Debris assessment v{lt['version']} accepted at {str(lt.get('accepted_gate') or '').upper()} by "
           f"{lt.get('accepted_by')}" if accepted else f"Debris assessment v{lt['version']} not accepted yet")
    if stale:
        msg += "; the design changed since the run (run it again)"
    return {"status": "pass" if ok else ("fail" if accepted else "open"), "accepted": accepted,
            "gate": lt.get("accepted_gate"), "compliant": lt.get("compliant"), "stale": stale,
            "version": lt["version"], "message": msg}


async def sweep(study_id: str, altitudes_km: list[float]) -> dict:
    """Lifetime against altitude for the study's mass basis and sail (3.L3; used by 3.H5)."""
    from .regulatory import disposal_sweep
    return await disposal_sweep(study_id, altitudes_km)


__all__ = ["ACCEPT_SEATS", "AssessmentError", "accept", "compute", "history", "latest", "run", "srr_evidence", "sweep"]
