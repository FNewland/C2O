"""Section ``debris``: the debris assessment: lifetime with and without the device, casualty risk, collision probability, compliance and acceptance. Owner: L (3.L8).

STEP 0 STUB (wave 3, PI addendum): returns ``status: not_implemented`` with the owner and the
empty shape below. TODO(L, 3.L8): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"assessment": None, "history": []}


async def collect(ctx) -> dict:
    return stub("L", "3.L8", **empty())
