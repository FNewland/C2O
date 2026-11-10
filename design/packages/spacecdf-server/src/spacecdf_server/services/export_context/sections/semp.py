"""Section ``semp``: the SEMP content the study does not hold elsewhere: organisation and seats, lifecycle and gates, technical processes, tailoring, configuration management (the generator, services/docx/semp.py, also reads the other sections). Owner: X (3.X3).

STEP 0 STUB (wave 3, PI addendum): returns ``status: not_implemented`` with the owner and the
empty shape below. TODO(X, 3.X3): read the model and return the real shape (keep these keys).
"""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return {"organisation": [], "lifecycle": [], "processes": [], "tailoring": [], "configuration_management": {}}


async def collect(ctx) -> dict:
    return stub("X", "3.X3", **empty())
