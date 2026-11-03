"""Participant logbook + course worksheets (docs/plan_2026-11/LOGBOOK_SPEC.md).

Self-contained so it can later be replaced by a shared C2O package:

    store.py       JSONL store (identity hash, flock'd append, fold, purge)
    export.py      Markdown / print-ready HTML / JSON export
    worksheets.py  generated worksheet YAML (configs/worksheets/) + context matching
    router.py      FastAPI routes under /api/logbook

The app mounts ``router`` at ``/api/logbook`` and runs ``purge_loop`` for the
retention rules (start-up, then hourly).
"""
from __future__ import annotations

import asyncio
import logging

from .router import router
from .router import store as logbook_store

logger = logging.getLogger(__name__)

PURGE_INTERVAL_S = 3600


async def purge_loop(interval_s: float = PURGE_INTERVAL_S) -> None:
    """Purge at start-up, then every hour. Never raises (logs and carries on)."""
    while True:
        try:
            stats = await asyncio.to_thread(logbook_store.purge)
            if stats.get("deleted") or stats.get("trimmed"):
                logger.info("logbook purge: %s", stats)
        except Exception as e:  # noqa: BLE001 - a purge failure must not stop the server
            logger.warning("logbook purge failed: %s", e)
        await asyncio.sleep(interval_s)


__all__ = ["router", "logbook_store", "purge_loop"]
