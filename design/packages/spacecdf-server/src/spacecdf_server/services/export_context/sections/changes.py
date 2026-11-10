"""Section ``changes``: the change proposals (ECP / CR): class, impact, affected requirements, source trade, status, decision gate. Owner: L (3.L4).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"items": [], "counts": {}``. TODO(L, 3.L4): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("L", "3.L4", **empty())
