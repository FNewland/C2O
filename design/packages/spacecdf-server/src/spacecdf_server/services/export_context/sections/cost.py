"""Section ``cost``: the priced cost model: labour, test campaigns, hardware, reserve, launch (zero when provided), total. Owner: A (3.A7).

STEP 0 STUB (wave 3, PI addendum): returns ``status: not_implemented`` with the owner and the
empty shape below. TODO(A, 3.A7): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "by_category": {}, "total_keur": None}


async def collect(ctx) -> dict:
    return stub("A", "3.A7", **empty())
