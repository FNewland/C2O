"""The shipped example project (plan 3.F2, W10.01): the Northern Fire and Ice study as the dry run
leaves it, as a project file (format v2) under ``configs/examples/nfi/project.json``.

The study is the full seed at S4 (licensing filled, ledger agreed, the four negotiations signed)
plus the team actions of the walkthrough (``test_w3_integration``: cost priced, SEMP issued, debris assessment
accepted, ECP-02 approved, ICDs at Issue A, reliability, FMEA, thermal model, ECP-01 decided) and
the reviews MDR, PRR, SRR and PDR passed. It stays solo (no team preset), so whoever loads it can
edit it at once; the Seats drawer sets a team as usual.

Regenerate after a change to the seed or the walkthrough, from ``design/``::

    python -m tests.fixtures.nfi.example_project            # writes configs/examples/nfi/project.json
    python -m tests.fixtures.nfi.example_project --out /tmp/x.json

``test_w3_close.py`` checks that loading the shipped file and exporting it again gives the
shipped file after id mapping.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parents[2]
EXAMPLE_PATH = DESIGN / "configs" / "examples" / "nfi" / "project.json"
GATES = ("mdr", "prr", "srr", "pdr")


async def finished_study(client, *, recording: bool = False) -> str:
    """Build the study the dry run ends with; returns its id. ``recording=True`` starts from the
    walkthrough's seed and does the on-camera scenes too (Licensing, ledger, negotiations)."""
    from tests.fixtures.nfi import seed_nfi
    from tests.fixtures.nfi.walkthrough import (fill_recording_scenes, mdr_actions, negotiation_scenes,
                                                        pdr_actions, srr_actions)
    seed = await seed_nfi(client, "S4", recording=recording)
    sid = seed.study_id
    if recording:
        await fill_recording_scenes(client, seed)
        await negotiation_scenes(client, sid)
    await mdr_actions(client, sid)
    await srr_actions(client, sid)
    await pdr_actions(client, sid)
    for g in GATES:
        for action in ("start", "pass"):
            r = await client.post(f"/api/studies/{sid}/gates/{g}/review", json={"action": action, "by": "board"})
            if r.status_code != 200:
                raise RuntimeError(f"{g} {action}: {r.status_code} {r.text[:300]}")
    return sid


def dumps(doc: dict) -> str:
    """The shipped file's text: compact JSON, as the export route writes it (the review baselines
    of the four passed gates are about half of the file)."""
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"), default=str) + "\n"


async def build_document() -> dict:
    """Run the app in-process on a throw-away database, build the finished study, export it."""
    from unittest.mock import patch

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    with tempfile.TemporaryDirectory(prefix="nfi-example-") as tmp:
        os.environ.update({"SPACECDF_AUTO_PROPOSE": "0", "SPACECDF_AUTO_IRD": "0",
                           "SPACECDF_DATA_DIR": f"{tmp}/data", "SMO_LOGBOOK_DIR": f"{tmp}/logbook"})
        from spacecdf_server.db import engine as engine_mod
        from spacecdf_server.db.migrate import ensure_schema_upgrades
        from spacecdf_server.db.models import Base
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp}/example.db", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await ensure_schema_upgrades(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        with patch.object(engine_mod, "_engine", engine), patch.object(engine_mod, "_session_factory", factory):
            from spacecdf_server.app import app
            from spacecdf_server.services import project_file as pf
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://example", timeout=600) as c:
                sid = await finished_study(c)
                doc = await pf.export_study(sid, person_id=None)
        await engine.dispose()
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tests.fixtures.nfi.example_project", description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=EXAMPLE_PATH, help=f"output file (default {EXAMPLE_PATH})")
    a = ap.parse_args(argv)
    doc = asyncio.run(build_document())
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(dumps(doc), encoding="utf-8")
    rows = sum(len(v) for v in doc["tables"].values())
    print(f"{a.out}: {rows} rows in {sum(1 for v in doc['tables'].values() if v)} tables, "
          f"{a.out.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
