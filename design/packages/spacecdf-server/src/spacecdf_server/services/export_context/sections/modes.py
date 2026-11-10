"""Section ``modes``: the mode machine (modes, transitions, mode x unit matrix) and the energy
balance (per-mode power with margins, energy per orbit, operational orbit). Owner: H."""
from __future__ import annotations


def empty() -> dict:
    return {"modes": [], "transitions": [], "members": [], "energy": None}


async def collect(ctx) -> dict:
    from ....routers.modes import get_modes, mode_energy
    m = await get_modes(ctx.study_id)
    try:
        energy = await mode_energy(ctx.study_id, gate=ctx.gate)
    except Exception:  # noqa: BLE001 — no modes yet / rule config problem
        energy = None
    return {"modes": m.get("modes") or [], "transitions": m.get("transitions") or [],
            "members": m.get("members") or [], "findings": m.get("findings") or [], "energy": energy}
