"""Section ``schedule``: milestones per gate, WBS, long-lead items, cost (W11a). Stub until then.
Owner: A."""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return stub("A", "W11a", milestones=[], work_packages=[], long_lead=[])


async def collect(ctx) -> dict:
    return empty()
