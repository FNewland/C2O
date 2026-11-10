"""Section ``reliability``: the reliability block diagram over the mission-success horizon and the FMEA/FMECA worksheet. Owner: A (3.A5).

STEP 0 STUB (wave 3, PI addendum): returns ``status: not_implemented`` with the owner and the
empty shape below. TODO(A, 3.A5): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"blocks": [], "result": {}, "fmea": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("A", "3.A5", **empty())
