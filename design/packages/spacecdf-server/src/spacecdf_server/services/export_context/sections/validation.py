"""Section ``validation``: the validation activities (V1 …) with performer and stage, the need-validation rows and the coverage of the objectives. Owner: S (3.S5).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"items": [], "need_validation": [], "coverage": {}, "counts": {}``. TODO(S, 3.S5): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "need_validation": [], "coverage": {}, "counts": {}}


async def collect(ctx) -> dict:
    return stub("S", "3.S5", **empty())
