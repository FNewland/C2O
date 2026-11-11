"""Sensitivity view on the real services (negotiation #4). Owner H (3.H5).

    GET /api/studies/{id}/sensitivity?parameter=science_target|compression_ratio|rate_tier|imaging_share
        [&margin=10][&values=5,10,15]
    GET /api/studies/{id}/sensitivity/altitude[?altitudes=500,550,600]

The service is ``services/sensitivity.py``; disposal figures come from the same physics and mass
basis as L's disposal analysis (``services/licensing.disposal_analysis``).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ._lookup import study_or_404

router = APIRouter()
OWNER, WP = "H", "3.H5"


def _floats(s: str | None) -> list[float] | None:
    if not s:
        return None
    try:
        return [float(x) for x in s.split(",") if x.strip()]
    except ValueError as exc:
        raise HTTPException(422, "values must be comma-separated numbers") from exc


@router.get("/studies/{study_id}/sensitivity")
async def sensitivity(study_id: str, parameter: str = Query("science_target"),
                      margin: float = Query(10.0, ge=0, le=90), values: str | None = Query(None)) -> dict:
    """Margin of the daily data budget against the science target, the compression ratio, the
    rate tier or the imaging share (``points``: x, margin %, status; the baseline; the largest
    science volume with the margin)."""
    from ..services import sensitivity as sv
    study_or_404(study_id)
    if parameter not in sv.PARAMETERS:
        raise HTTPException(422, f"parameter must be one of {', '.join(sv.PARAMETERS)}")
    res = await sv.data(study_id, parameter, margin_pct=margin, values=_floats(values))
    return {**res, "items": res.get("points", []), "owner": OWNER, "work_package": WP}


@router.get("/studies/{study_id}/sensitivity/altitude")
async def altitude_sweep(study_id: str, altitudes: str | None = Query(None)) -> dict:
    """GSD, swath, union contacts, decay with and without the drag device, eclipse and link margin
    over a sweep of the altitude, with the regulatory lines (600 km apogee, 5 years)."""
    from ..services import sensitivity as sv
    study_or_404(study_id)
    res = await sv.altitude(study_id, altitudes=_floats(altitudes))
    return {**res, "items": res["points"], "owner": OWNER, "work_package": WP}
