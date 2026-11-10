"""Phase API of the systems-engineering V (SE-01). Owner S (3.S1).

    GET /api/studies/{study_id}/phase              what the phase the study is in asks of it
        ?gate=srr                                  another gate's block (profile gate id)
        &register=learning|plain|practitioner      coaching register (default learning)
        &seat=power_engineer                       only that seat's cards
        &lang=en|fr                                language of the ``evidence`` strings
    GET /api/studies/{study_id}/phase/deliverables the deliverables evaluation alone (gate ``start``
                                                   warnings, the SE-01 criterion and the pack index read it)
    GET /api/se-protocol                           the protocol file as data (validation errors listed)

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
