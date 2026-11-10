"""Section ``stakeholders``: the stakeholder register (category, authority, engagement), the needs, the MOEs (placeholders flagged) and the need validation. Owner: S (3.S3).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"items": [], "needs": [], "moes": [], "counts": {}``. TODO(S, 3.S3): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"items": [], "needs": [], "moes": [], "counts": {}}


async def collect(ctx) -> dict:
    return stub("S", "3.S3", **empty())
