"""SpaceCDF — named link-budget cases (W4.04) and the band presets (W1.04), Nov 2026.

Mounted under ``/api`` (included by routers/gates.py):

* ``GET    /link-budgets/presets``                      band × direction starting values (UHF, VHF, S, X)
* ``GET    /studies/{sid}/link-budgets``                the design case (``requirements.link``), the tool's
                                                        starting values for the study, and the named cases
* ``POST   /studies/{sid}/link-budgets``                save a named case (margin computed on the server)
* ``POST   /studies/{sid}/link-budgets/compute``        the cascade of a case, not saved
* ``PATCH  /studies/{sid}/link-budgets/{cid}``          edit (margin recomputed)
* ``DELETE /studies/{sid}/link-budgets/{cid}``
* ``POST   /studies/{sid}/link-budgets/{cid}/apply``    make the case the study's design case for its
                                                        direction (writes ``requirements.link``, which the
                                                        analyses read; their runs become stale); once the
                                                        study has a licensing record, also syncs the
                                                        licensing overrides below
* ``POST   /studies/{sid}/link-budgets/licensing-sync`` the cases' per-station earth-station values
                                                        (uplink transmit power and gain, downlink receive
                                                        gain) into the licensing record's
                                                        ``assignment_overrides``, by assignment id

The cases feed the export collector (``export_context`` section ``links``): the master budget, the
ISED brief and the earth-station documents read them from there.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import link_cases as lc

logger = logging.getLogger(__name__)
router = APIRouter()

TEXT_FIELDS = {"name": 160, "band": 8, "station": 160, "rate_tier": 40, "modulation": 64, "coding": 64,
               "source": 64, "notes": 4000}
NUM_FIELDS = tuple(lc.INPUTS)
MAX_CASES = 100


def _study(study_id: str):
    from .gates import _study_or_404
    return _study_or_404(study_id)


def _altitude(study) -> float | None:
    try:
        return float(study.requirements.orbit.altitude_km)
    except Exception:  # noqa: BLE001
        return None


def _row_dict(r) -> dict[str, Any]:
    out = {"id": r.id, "study_id": r.study_id, "direction": r.direction, "is_design_case": bool(r.is_design_case),
           "margin_db": r.margin_db, "results": r.results_json or {}, "order": r.order,
           "created_at": r.created_at.isoformat() if r.created_at else None,
           "updated_at": r.updated_at.isoformat() if r.updated_at else None}
    for k in TEXT_FIELDS:
        out[k] = getattr(r, k)
    for k in NUM_FIELDS:
        out[k] = getattr(r, k)
    return out


async def list_cases(study_id: str) -> list[dict[str, Any]]:
    """The study's named link cases, in display order; [] when the DB is unavailable."""
    try:
        from sqlalchemy import select

        from ..db.engine import get_session_factory
        from ..db.models_links import LinkBudgetRow
        async with get_session_factory()() as s:
            rows = (await s.execute(select(LinkBudgetRow).where(LinkBudgetRow.study_id == study_id)
                                    .order_by(LinkBudgetRow.order, LinkBudgetRow.created_at))).scalars().all()
            return [_row_dict(r) for r in rows]
    except Exception:  # noqa: BLE001
        logger.debug("link cases unavailable for %s", study_id, exc_info=True)
        return []


class CaseBody(BaseModel):
    name: str = Field("", max_length=160)
    direction: str = "downlink"
    band: str = Field("", max_length=8)
    station: str = Field("", max_length=160)
    rate_tier: str = Field("", max_length=40)
    modulation: str = Field("", max_length=64)
    coding: str = Field("", max_length=64)
    notes: str = Field("", max_length=4000)
    source: str = Field("user", max_length=64)
    order: int | None = None
    # numeric inputs: absent = the band preset's value
    frequency_mhz: float | None = None
    data_rate_bps: float | None = None
    tx_power_w: float | None = None
    tx_antenna_gain_dbi: float | None = None
    tx_losses_db: float | None = None
    elevation_deg: float | None = Field(None, ge=0, le=90)
    slant_range_km: float | None = Field(None, ge=0)
    polarisation_loss_db: float | None = None
    atmospheric_loss_db: float | None = None
    pointing_loss_db: float | None = None
    other_losses_db: float | None = None
    rx_antenna_gain_dbi: float | None = None
    rx_losses_db: float | None = None
    system_noise_temp_k: float | None = None
    required_ebn0_db: float | None = None
    implementation_loss_db: float | None = None


def _resolve(body: dict[str, Any], study, base: dict[str, Any] | None = None) -> dict[str, Any]:
    """A full case: ``base`` (the stored case) or the band preset, overlaid with ``body``."""
    direction = body.get("direction") or (base or {}).get("direction") or "downlink"
    if direction not in lc.DIRECTIONS:
        raise HTTPException(422, f"direction must be one of {', '.join(lc.DIRECTIONS)}")
    link = study.requirements.link.model_dump() if getattr(study.requirements, "link", None) else {}
    band = body.get("band") or (base or {}).get("band") or link.get("band") or \
        lc.band_of(link.get("downlink_frequency_mhz")) or "UHF"
    start = dict(base) if base else lc.preset(band, direction)
    case = {**start, **{k: v for k, v in body.items() if v is not None}}
    case["direction"], case["band"] = direction, (band or "")[:8]
    case.setdefault("elevation_deg", 10.0)
    try:
        case["results"] = lc.compute(case, _altitude(study))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    case["margin_db"] = case["results"]["margin_db"]
    if not case.get("name"):
        case["name"] = f"{direction} {case.get('station') or ''} {case.get('elevation_deg', 10):g} deg".strip()
    return case


@router.get("/link-budgets/presets")
async def presets() -> dict:
    return {"bands": lc.PRESETS, "directions": list(lc.DIRECTIONS)}


@router.get("/studies/{study_id}/link-budgets")
async def get_cases(study_id: str) -> dict:
    study = _study(study_id)
    link = study.requirements.link.model_dump(mode="json")
    return {"study_id": study_id, "design_case": link, "altitude_km": _altitude(study),
            "start": {d: lc.study_preset(link, d) for d in lc.DIRECTIONS},
            "items": await list_cases(study_id)}


@router.post("/studies/{study_id}/link-budgets/compute")
async def compute_case(study_id: str, body: CaseBody) -> dict:
    study = _study(study_id)
    case = _resolve(body.model_dump(exclude_unset=True), study)
    return {"case": {k: v for k, v in case.items() if k != "results"}, "results": case["results"]}


async def _broadcast(study_id: str) -> None:
    from .gates import _broadcast as bc
    await bc(study_id, "study_records_changed", {"kind": "link_budgets"})


@router.post("/studies/{study_id}/link-budgets")
async def create_case(study_id: str, body: CaseBody) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_links import LinkBudgetRow
    study = _study(study_id)
    existing = await list_cases(study_id)
    if len(existing) >= MAX_CASES:
        raise HTTPException(413, "Too many link cases in this study")
    case = _resolve(body.model_dump(exclude_unset=True), study)
    row = LinkBudgetRow(id=uuid4().hex[:16], study_id=study_id,
                        order=case.get("order") if case.get("order") is not None else len(existing),
                        is_design_case=False, results_json=case["results"], margin_db=case["margin_db"],
                        **{k: str(case.get(k) or "")[:n] for k, n in TEXT_FIELDS.items()},
                        **{k: float(case[k]) for k in NUM_FIELDS if case.get(k) is not None},
                        direction=case["direction"])
    async with get_session_factory()() as s:
        s.add(row)
        await s.commit()
        await s.refresh(row)
        out = _row_dict(row)
    await _broadcast(study_id)
    return out


@router.patch("/studies/{study_id}/link-budgets/{case_id}")
async def update_case(study_id: str, case_id: str, body: CaseBody) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_links import LinkBudgetRow
    study = _study(study_id)
    async with get_session_factory()() as s:
        row = await s.get(LinkBudgetRow, case_id)
        if row is None or row.study_id != study_id:
            raise HTTPException(404, f"Link case {case_id} not found")
        case = _resolve(body.model_dump(exclude_unset=True), study, base=_row_dict(row))
        for k, n in TEXT_FIELDS.items():
            setattr(row, k, str(case.get(k) or "")[:n])
        for k in NUM_FIELDS:
            if case.get(k) is not None:
                setattr(row, k, float(case[k]))
        row.direction = case["direction"]
        if case.get("order") is not None:
            row.order = int(case["order"])
        row.results_json, row.margin_db = case["results"], case["margin_db"]
        await s.commit()
        await s.refresh(row)
        out = _row_dict(row)
    await _broadcast(study_id)
    return out


@router.delete("/studies/{study_id}/link-budgets/{case_id}")
async def delete_case(study_id: str, case_id: str) -> dict:
    from ..db.engine import get_session_factory
    from ..db.models_links import LinkBudgetRow
    _study(study_id)
    async with get_session_factory()() as s:
        row = await s.get(LinkBudgetRow, case_id)
        if row is None or row.study_id != study_id:
            raise HTTPException(404, f"Link case {case_id} not found")
        await s.delete(row)
        await s.commit()
    await _broadcast(study_id)
    return {"deleted": case_id}


def design_link_patch(case: dict[str, Any]) -> dict[str, Any]:
    """The ``requirements.link`` fields a case sets (only its own direction's fields)."""
    src = f"link_case:{case.get('name') or case.get('id')}"[:120]
    if case["direction"] == "uplink":
        return {"band": case.get("band") or None, "uplink_frequency_mhz": case["frequency_mhz"],
                "uplink_rate_bps": case["data_rate_bps"], "source": src}
    return {"band": case.get("band") or None, "downlink_frequency_mhz": case["frequency_mhz"],
            "downlink_rate_bps": case["data_rate_bps"], "tx_power_w": case["tx_power_w"],
            "tx_antenna_gain_dbi": case["tx_antenna_gain_dbi"], "tx_losses_db": case["tx_losses_db"],
            "rx_antenna_gain_dbi": case["rx_antenna_gain_dbi"], "system_noise_temp_k": case["system_noise_temp_k"],
            "slant_range_km": (case.get("results") or {}).get("slant_range_km") or case.get("slant_range_km") or None,
            "required_ebn0_db": case["required_ebn0_db"], "margin_db": case.get("margin_db"), "source": src}


#: earth-station fields a link case sets in the licensing record (assignment id -> fields)
LICENSING_FIELDS = ("tx_power_w", "antenna_gain_dbi")


def _station_matches(case_station: str, station_name: str) -> bool:
    """A case's ``station`` names one site ("Ottawa") or all of them ("all four sites", "")."""
    cs = (case_station or "").strip().lower()
    if not cs or cs.startswith("all"):
        return True
    sn = (station_name or "").strip().lower()
    return cs == sn or cs in sn.split() or sn.endswith(" " + cs) or sn.replace("gs ", "", 1) == cs


def licensing_overrides(cases: list[dict[str, Any]], assignments: list[dict[str, Any]]) -> dict[str, dict]:
    """``assignment_overrides`` for the licensing record from the named link cases (W4.04 -> W5.04).

    Per earth station: the uplink transmit assignment (``ES-*-TX-UL``) takes the uplink case's
    ground transmit power and antenna gain; the downlink receive assignment (``ES-*-RX-DL``) takes the
    downlink case's receive antenna gain. A case for that station wins over a case for all stations,
    and the design case over the others; otherwise the first case in display order."""
    def rank(c: dict, station: str) -> tuple:
        specific = (c.get("station") or "").strip().lower() not in ("",) and \
            not (c.get("station") or "").strip().lower().startswith("all")
        return (0 if specific else 1, 0 if c.get("is_design_case") else 1, c.get("order") or 0)

    out: dict[str, dict] = {}
    for a in assignments:
        if a.get("side") != "earth" or a.get("fallback"):
            continue
        direction = a.get("direction")
        mine = [c for c in cases if c.get("direction") == direction and _station_matches(c.get("station"), a.get("station"))]
        if not mine:
            continue
        c = sorted(mine, key=lambda c: rank(c, a.get("station") or ""))[0]
        if direction == "uplink" and a.get("transmits"):
            vals = {"tx_power_w": c.get("tx_power_w"), "antenna_gain_dbi": c.get("tx_antenna_gain_dbi")}
        elif direction == "downlink" and not a.get("transmits"):
            vals = {"antenna_gain_dbi": c.get("rx_antenna_gain_dbi")}
        else:
            continue
        vals = {k: float(v) for k, v in vals.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        if vals:
            out[a["id"]] = {**vals, "source": f"link_case:{c.get('name') or c.get('id')}"[:120]}
    return out


async def sync_licensing(study_id: str) -> dict[str, dict]:
    """Write the link cases' earth-station values into the licensing record (merged: other
    fields of an override, and overrides of other assignments, are kept). Returns what was set."""
    from ..services import licensing as lic
    from .elements import _elements
    study = _study(study_id)
    els = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    cases = await list_cases(study_id)
    if not cases:
        return {}
    ov = licensing_overrides(cases, lic.frequency_assignments(study, els))
    if ov:
        record, _ = await lic.load_record(study_id)
        have = record.get("assignment_overrides") or {}
        patch = {aid: {**(have.get(aid) or {}), **{k: v for k, v in vals.items() if k in LICENSING_FIELDS},
                       "link_case": vals["source"]} for aid, vals in ov.items()}
        if any(have.get(aid) != v for aid, v in patch.items()):   # no new record version when unchanged
            await lic.save_record(study_id, {"assignment_overrides": patch}, actor="link-budget tool")
    return ov


@router.post("/studies/{study_id}/link-budgets/licensing-sync")
async def licensing_sync(study_id: str) -> dict:
    """The named cases' per-station values into the licensing record's assignment overrides."""
    _study(study_id)
    ov = await sync_licensing(study_id)
    await _broadcast(study_id)
    return {"study_id": study_id, "assignment_overrides": ov}


@router.post("/studies/{study_id}/link-budgets/{case_id}/apply")
async def apply_case(study_id: str, case_id: str) -> dict:
    """Make a case the design case of its direction: ``requirements.link`` gets its values
    (through the mission-definition patch, so analyses made with the old link become stale)."""
    from sqlalchemy import select

    from ..db.engine import get_session_factory
    from ..db.models_links import LinkBudgetRow
    from .studies import update_mission
    _study(study_id)
    async with get_session_factory()() as s:
        row = await s.get(LinkBudgetRow, case_id)
        if row is None or row.study_id != study_id:
            raise HTTPException(404, f"Link case {case_id} not found")
        case = _row_dict(row)
        patch = {k: v for k, v in design_link_patch(case).items() if v is not None}
        res = await update_mission(study_id, {"link": patch})
        same = (await s.execute(select(LinkBudgetRow).where(LinkBudgetRow.study_id == study_id,
                                                            LinkBudgetRow.direction == row.direction))).scalars().all()
        for r in same:
            r.is_design_case = r.id == case_id
        await s.commit()
    try:  # W5.04: once a licensing record exists, keep its earth-station values on the cases
        from ..services import licensing as lic
        if (await lic.load_record(study_id))[1]:
            await sync_licensing(study_id)
    except Exception:  # noqa: BLE001 — no licensing table (old DB): the design case is still applied
        logger.warning("link cases: licensing overrides not synced for %s", study_id, exc_info=True)
    await _broadcast(study_id)
    return {"applied": case_id, "direction": case["direction"], "link": res.get("requirements", {}).get("link"),
            "stale_analyses": res.get("stale_analyses", [])}
