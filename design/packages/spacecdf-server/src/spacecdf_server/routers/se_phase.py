"""Phase API of the systems-engineering V (SE-01). Owner S (3.S1).

``GET /studies/{study_id}/phase`` — what the phase the study is in asks of it: entry checks,
deliverables, analysis standard and coaching (shape: ``services/se_protocol.py``). Step 0 serves
the stub contract; 3.S1 makes it real.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from ..services import se_protocol
from ._wave3_stub import study_or_404

router = APIRouter()


@router.get("/studies/{study_id}/phase")
async def get_phase(study_id: str, lang: str = Query("en")) -> dict:
    study = study_or_404(study_id)
    return await se_protocol.phase(study_id, study, lang=lang)
