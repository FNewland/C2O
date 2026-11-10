"""Section ``debris``: the debris assessment: lifetime with and without the device, casualty risk,
collision probability, compliance and acceptance. Owner: L (3.L8).

``assessment`` is the latest stored run (``services/debris_assessment.py``) with its acceptance,
``history`` the earlier runs (version, status, headline figures), ``evidence`` the gate evidence
(accepted at which gate, compliant, stale). ``assessment`` is None until the team runs it.
"""
from __future__ import annotations


def empty() -> dict:
    return {"assessment": None, "history": []}


async def collect(ctx) -> dict:
    from ...debris_assessment import history, srr_evidence
    items = await history(ctx.study_id)
    head = ("version", "status", "lifetime_y", "lifetime_without_device_y", "casualty_risk", "collision_probability",
            "compliant", "accepted_by", "accepted_gate", "accepted_at", "created_at")
    return {"status": "ok", "owner": "L", "work_package": "3.L8",
            "assessment": items[0] if items else None,
            "history": [{k: it.get(k) for k in head} for it in items[1:]],
            "evidence": await srr_evidence(ctx.study_id) if items else None}
