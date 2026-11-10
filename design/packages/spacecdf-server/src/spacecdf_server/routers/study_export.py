"""SpaceCDF — read-only views of the shared export seams (W0.2 / W0.3).

* ``GET /api/studies/{study_id}/rollup?gate=``           services/rollup.py (mass, power, form factor)
* ``GET /api/studies/{study_id}/export-context?gate=&lang=&sections=``
                                                          services/export_context.collect, as JSON
* ``GET /api/studies/{study_id}/review-packs``           the review packs the study can export (W4.02)

The second one is what every document generator sees; it is handy for checking a study before
exporting and for tools (textbook number extraction, W10.03).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


def _exists(study_id: str) -> bool:
    from ..services.rollup import study_elements
    from .studies import get_study_store
    return get_study_store().get(study_id) is not None or bool(study_elements(study_id))


@router.get("/studies/{study_id}/rollup")
async def study_rollup(study_id: str, gate: str | None = Query(None, description="mdr, prr, srr, pdr or cdr")) -> dict:
    """Mass (nominal, maturity, system margin, ladder), power (sum of on-powers, orbit average) and
    form factor of the study, from the one roll-up every document uses."""
    if not _exists(study_id):
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    from ..services.rollup import compute
    return (await compute(study_id, gate=(gate or "").lower() or None)).as_dict()


@router.get("/studies/{study_id}/export-context")
async def study_export_context(
    study_id: str,
    gate: str | None = Query(None),
    lang: str = Query("en"),
    sections: str | None = Query(None, description="comma-separated section names; default all"),
) -> dict:
    """The StudyExport every generator receives (all sections; stubs marked not_implemented)."""
    from ..services.export_context import SECTIONS, collect
    wanted = [s.strip() for s in sections.split(",") if s.strip()] if sections else None
    if wanted and set(wanted) - set(SECTIONS):
        raise HTTPException(status_code=422, detail={"unknown_sections": sorted(set(wanted) - set(SECTIONS)),
                                                     "sections": list(SECTIONS)})
    try:
        sx = await collect(study_id, gate=(gate or "").lower() or None, lang=lang, sections=wanted)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return sx.as_dict()


@router.get("/studies/{study_id}/review-packs")
async def study_review_packs(study_id: str) -> dict:
    """The review data packs the study can export (W4.02): the gates of its profile, then QR, AR
    and FRR. ``complete`` is false for the skeleton packs after PDR. Feeds the Export drawer."""
    from .exports.packs import available_packs
    from .studies import get_study_store
    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    from .gates import study_profile
    return {"study_id": study_id, "profile": study_profile(study).get("id"), "packs": available_packs(study)}
