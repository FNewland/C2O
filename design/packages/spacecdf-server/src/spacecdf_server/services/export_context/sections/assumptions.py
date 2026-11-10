"""Section ``assumptions``: the assumption register: statement, what it affects, the evidence that would replace it, owner seat, due gate, status. Owner: S (3.S6).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"items": [], "counts": {}``. TODO(S, 3.S6): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("S", "3.S6", **empty())
