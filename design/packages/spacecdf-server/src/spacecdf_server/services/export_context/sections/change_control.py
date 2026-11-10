"""Section ``change_control``: the change-control flow of each change proposal: affected seats and their decisions, board decision, new baseline. Owner: D (3.D7).

STEP 0 STUB (wave 3, PI addendum): returns ``status: not_implemented`` with the owner and the
empty shape below. TODO(D, 3.D7): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("D", "3.D7", **empty())
