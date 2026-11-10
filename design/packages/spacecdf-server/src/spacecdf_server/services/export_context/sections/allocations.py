"""Section ``allocations``: the allocation ledger: lines per element and budget type with owner, status and sign-off, the Systems reserve and the closure per budget. Owner: A (3.A2).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"items": [], "reserve": {}, "closure": {}, "counts": {}``. TODO(A, 3.A2): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "reserve": {}, "closure": {}, "counts": {}}


async def collect(ctx) -> dict:
    return stub("A", "3.A2", **empty())
