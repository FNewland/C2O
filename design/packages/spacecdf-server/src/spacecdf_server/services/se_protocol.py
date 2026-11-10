"""Systems-engineering protocol: what the current phase asks of the team (SE-01). Owner S (3.S1).

STEP 0 STUB (wave 3). The contract below is fixed; agent S replaces the body with the loader of
``configs/se_protocol.yaml`` (3.S1) and the deliverables service (``se_deliverables.py``, 3.S2).

``GET /api/studies/{study_id}/phase`` (``routers/se_phase.py``) returns :func:`phase` as is::

    {"study_id": "...", "gate": "mdr",            # the profile gate the study prepares for
     "phase": "0",                                # lifecycle phase that gate closes
     "entry": [],          # [{id, label{en,fr}, state: ok|warn|missing, evidence, fix}] "Before you start"
     "deliverables": [],   # [{id, kind: product|diagram|trade|document|criteria|object, label{en,fr},
                           #   owner_seat, state: ok|warn|missing, evidence, fix, draft}]
     "analysis": [],       # [{id, label{en,fr}, state, evidence}] "Analysis standard" (open assumptions …)
     "coaching": {},       # {phase: [card], seats: {seat: [card]}} card = {id, title{en,fr}, body{en,fr}, source}
     "status": "not_implemented", "owner": "S"}   # dropped once 3.S1 lands

Readers: the Phase panel (D, 3.D2), the gate ``start`` warnings (D, 3.D1), the
``<GATE>-SE-01`` criterion (R, 3.R4), the pack index (X, 3.X2), the Guide drawer (S, 3.S4).
"""
from __future__ import annotations

from typing import Any

#: lifecycle phase each gate closes (ECSS-M-ST-10C): the stub's answer for "phase"
GATE_PHASE = {"mdr": "0", "prr": "A", "srr": "B", "pdr": "B", "cdr": "C", "qr": "D", "ar": "D", "frr": "D"}


def empty_phase(gate: str | None = None) -> dict[str, Any]:
    """The phase shape with nothing in it."""
    g = (gate or "").lower() or None
    return {"gate": g, "phase": GATE_PHASE.get(g or "", None), "entry": [], "deliverables": [], "analysis": [],
            "coaching": {}}


def current_gate_id(study: Any) -> str | None:
    """The id of the first gate of the study's profile that has not passed (lower case)."""
    from ..routers.gates import current_gate, study_profile
    from . import gate_profiles as gp
    g = current_gate(study_profile(study), study)
    if g is None:
        return None
    return gp.legacy_gate_id(g.get("id")) or str(g.get("id") or "").lower() or None


async def phase(study_id: str, study: Any, *, lang: str = "en") -> dict[str, Any]:
    """What the phase the study is in asks of it. TODO(S, 3.S1/3.S2): the real protocol."""
    gate = current_gate_id(study) if study is not None else None
    return {"study_id": study_id, **empty_phase(gate), "status": "not_implemented", "owner": "S",
            "work_package": "3.S1"}


__all__ = ["GATE_PHASE", "current_gate_id", "empty_phase", "phase"]
