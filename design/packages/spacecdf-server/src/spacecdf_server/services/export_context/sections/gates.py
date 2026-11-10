"""Section ``gates``: the gate profile, each gate's state, readiness and must-pass summary, the
current gate and the stored gate records (history, baselines). Criteria detail per gate and the
RID log come with W4.08. Owner: D."""
from __future__ import annotations

import copy


def empty() -> dict:
    return {"profile": None, "current_gate": None, "gates": [], "records": {}}


async def collect(ctx) -> dict:
    if ctx.study is None:
        return empty()
    from ....routers.gates import study_gates
    res = await study_gates(ctx.study_id)
    return {"profile": res.get("profile"), "current_gate": res.get("current_gate"),
            "gates": res.get("gates") or [],
            "records": copy.deepcopy(dict(getattr(ctx.study, "gate_states", None) or {}))}
