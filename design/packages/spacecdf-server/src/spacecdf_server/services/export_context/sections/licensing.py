"""Section ``licensing``: applicant, frequency assignments, filings and their status (W5.01,
W5.03, W5.06). Stub until then. Owner: L."""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return stub("L", "W5.01/W5.03/W5.06", applicant={}, assignments=[], filings=[])


async def collect(ctx) -> dict:
    return empty()
