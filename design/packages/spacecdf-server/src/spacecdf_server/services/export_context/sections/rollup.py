"""Section ``rollup``: mass, power and form factor from services/rollup.py (the one roll-up).
Owner: X (export core); the roll-up rules themselves are services/rollup.py."""
from __future__ import annotations


def empty() -> dict:
    return {"mass": {}, "power": {}, "form_factor": None, "form_factor_source": "unknown", "warnings": []}


async def collect(ctx) -> dict:
    from ...rollup import compute
    ru = await compute(ctx.study_id, gate=ctx.gate)
    ctx.cache["rollup"] = ru
    return ru.as_dict()
