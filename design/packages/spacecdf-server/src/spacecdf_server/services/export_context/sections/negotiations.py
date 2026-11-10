"""Section ``negotiations``: the negotiation records: issue, coupled parameters, seats, options with effects, agreed values, sign-offs, reopen trigger. Owner: H (3.H6).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"items": [], "counts": {}``. TODO(H, 3.H6): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("H", "3.H6", **empty())
