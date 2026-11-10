"""Seed the Northern Fire and Ice study into a running SpaceCDF server (the dry run, W13).

From ``design/``::

    python -m tests.fixtures.nfi --url http://127.0.0.1:18800 --stage S4
    python -m tests.fixtures.nfi --url http://127.0.0.1:18800 --stage S0 S1 S2 S3 S4   # one study per stage
    python -m tests.fixtures.nfi --url http://127.0.0.1:18800 --stage S4 --recording   # the walkthrough's seed

``--recording`` leaves out what the walkthrough films on camera: the Licensing tab, the allocation
ledger and the negotiation records (PI ruling; ``seed_nfi(..., recording=True)``).

Each stage builds a new study from scratch up to that stage (``seed_nfi``), through the same API calls
the fixture tests make, and prints its id, the seconds per stage and the 403 count. See
``docs/dev/DRY_RUN.md``.
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from .seed import STAGES, SeedError, seed_nfi


async def _main(url: str, stages: list[str], timeout: float, recording: bool = False) -> int:
    import httpx

    rc = 0
    async with httpx.AsyncClient(base_url=url.rstrip("/"), timeout=timeout) as client:
        health = await client.get("/api/health")
        if health.status_code != 200:
            print(f"{url}: /api/health answered {health.status_code}; is the server up?", file=sys.stderr)
            return 2
        for stage in stages:
            try:
                s = await seed_nfi(client, stage, recording=recording)
            except SeedError as exc:
                print(f"{stage}: FAILED: {exc}", file=sys.stderr)
                rc = 1
                continue
            secs = ", ".join(f"{k} {v:.1f} s" for k, v in s.report["seconds"].items())
            mode = " (recording)" if recording else ""
            print(f"{stage}{mode}: study {s.study_id}  ({s.report['calls']} calls, {s.report['forbidden']} x 403; {secs})")
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tests.fixtures.nfi", description=__doc__.splitlines()[0])
    ap.add_argument("--url", default="http://127.0.0.1:18800", help="SpaceCDF server (default: the video stack)")
    ap.add_argument("--stage", nargs="+", default=["S4"], type=str.upper, choices=STAGES,
                    help="stage(s) to build, one new study each (default S4)")
    ap.add_argument("--timeout", type=float, default=600.0, help="seconds per API call (the analyses are slow)")
    ap.add_argument("--recording", action="store_true",
                    help="the walkthrough's seed: leave the Licensing tab, ledger and negotiations empty")
    a = ap.parse_args(argv)
    return asyncio.run(_main(a.url, a.stage, a.timeout, a.recording))


if __name__ == "__main__":
    sys.exit(main())
