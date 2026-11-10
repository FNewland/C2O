"""Section ``open_items``: the open-item register (RIDs, actions, conditional decisions, PI and seat decisions, change proposals) by the gate each blocks. Owner: D (3.D4).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"items": [], "by_gate": {}, "counts": {}``. TODO(D, 3.D4): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "by_gate": {}, "counts": {}}


async def collect(ctx) -> dict:
    return stub("D", "3.D4", **empty())
