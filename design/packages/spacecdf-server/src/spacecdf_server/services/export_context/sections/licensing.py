"""Section ``licensing``: applicant, frequency assignments, disposal analysis, filings and their status
(W5.01, W5.02, W5.03, W5.06). The body lives in ``services/licensing.py``. Owner: L."""
from __future__ import annotations


def empty() -> dict:
    return {"status": "empty", "owner": "L", "work_package": "W5.01/W5.03/W5.06", "applicant": {},
            "assignments": [], "filings": [], "stations": [], "disposal": {}, "evidence": []}


async def collect(ctx) -> dict:
    from ...licensing import collect as _collect
    return await _collect(ctx)
