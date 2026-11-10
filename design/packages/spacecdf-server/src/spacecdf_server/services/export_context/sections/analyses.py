"""Section ``analyses``: the last run of each analysis (mission simulation, ground segment,
physics, FMECA, V&V, ...) with its summary and staleness inputs. Owner: X."""
from __future__ import annotations


def empty() -> dict:
    return {"last_runs": {}}


async def collect(ctx) -> dict:
    from ....db import analysis_repo
    runs = await analysis_repo.list_last_runs(ctx.study_id)
    return {"last_runs": {k: runs[k] for k in sorted(runs)}}
