"""Section ``contacts``: per-station and union contact statistics (min/day, passes/day, mean and
maximum pass, longest gap, data per day) from W4.05. Stub until then. Owner: H."""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return stub("H", "W4.05", stations=[], union={})


async def collect(ctx) -> dict:
    return empty()
