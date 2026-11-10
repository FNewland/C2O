"""Section ``data_budget``: daily data generated vs downlinked, stores, HK by SID (W3.02
``services/data_budget.py``). Stub until then. Owner: H."""
from __future__ import annotations

from ._util import stub


def empty() -> dict:
    return stub("H", "W3.02/W3.05", daily={}, stores=[], hk={})


async def collect(ctx) -> dict:
    return empty()
