"""Section ``icds``: every ICD with its latest issue, state (draft, Issue A, baselined) and the sign-off of both owning seats. Owner: R (3.R6).

STEP 0 STUB (wave 3, PI addendum): returns ``status: not_implemented`` with the owner and the
empty shape below. TODO(R, 3.R6): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("R", "3.R6", **empty())
