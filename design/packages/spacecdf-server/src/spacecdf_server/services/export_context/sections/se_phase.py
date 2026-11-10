"""Section ``se_phase``: the systems-engineering phase of the study (the /phase contract of services/se_protocol.py): entry, deliverables, analysis, coaching. Owner: S (3.S1).

STEP 0 STUB (wave 3): returns ``status: not_implemented`` with the owner and the empty shape
``"gate": None, "phase": None, "entry": [], "deliverables": [], "analysis": [], "coaching": {}``. TODO(S, 3.S1): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"gate": None, "phase": None, "entry": [], "deliverables": [], "analysis": [], "coaching": {}}


async def collect(ctx) -> dict:
    return stub("S", "3.S1", **empty())
