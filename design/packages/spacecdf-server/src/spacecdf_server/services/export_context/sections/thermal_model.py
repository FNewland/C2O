"""Section ``thermal_model``: the thermal nodal model: nodes, couplings, hot and cold cases, temperatures and margins (design, acceptance, qualification), heater sizing. Owner: A (3.A6).

STEP 0 STUB (wave 3, PI addendum): returns ``status: not_implemented`` with the owner and the
empty shape below. TODO(A, 3.A6): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"nodes": [], "couplings": [], "cases": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("A", "3.A6", **empty())
