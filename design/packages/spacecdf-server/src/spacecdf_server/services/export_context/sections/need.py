"""Section ``need``: the mission need (problem, context, stakeholders, objectives, alternatives,
selection rationale, ConOps summary, success criteria). Owner: X (export core)."""
from __future__ import annotations

from ._util import dump


def empty() -> dict:
    return {}


async def collect(ctx) -> dict:
    mn = getattr(ctx.study, "mission_need", None) if ctx.study is not None else None
    return dump(mn) or {}
