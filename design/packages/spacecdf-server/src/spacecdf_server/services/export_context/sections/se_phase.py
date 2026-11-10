"""Section ``se_phase``: the systems-engineering phase of the study (the /phase contract of
services/se_protocol.py): entry, deliverables, analysis, coaching. Owner: S (3.S1).

For a gate export (``gate="pdr"``) it is that gate's block; otherwise the gate the study prepares
for. The pack index (X, 3.X2) lists ``deliverables`` with state and owner.
"""
from __future__ import annotations


def empty() -> dict:
    return {"gate": None, "phase": None, "entry": [], "deliverables": [], "analysis": [], "coaching": {}}


async def collect(ctx) -> dict:
    from ...se_protocol import phase
    if ctx.study is None:
        return empty()
    return await phase(ctx.study_id, ctx.study, lang=ctx.lang, gate=ctx.gate)
