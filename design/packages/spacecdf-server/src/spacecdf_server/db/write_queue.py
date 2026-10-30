"""Background write-through queue for parameter edits and snapshots.

Edits are enqueued from the WebSocket hot path; a background worker
drains the queue and writes to the DB in batches. The hot path never
awaits the DB.
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_queue: asyncio.Queue | None = None
_worker_task: asyncio.Task | None = None
_persistence_failures: list[dict] = []  # SCDF-035: surfaced failures


def get_persistence_failures() -> list[dict]:
    """Return and clear any persistence failures since last check."""
    global _persistence_failures
    failures = _persistence_failures[:]
    _persistence_failures = []
    return failures


async def start_worker() -> None:
    global _queue, _worker_task
    _queue = asyncio.Queue(maxsize=10000)
    _worker_task = asyncio.create_task(_drain_worker())
    logger.info("Persistence write-queue worker started")


async def stop_worker() -> None:
    global _worker_task, _queue
    if _worker_task:
        if _queue:
            try:
                await _queue.put(None)
            except Exception:
                pass
        try:
            await _worker_task
        except Exception as e:
            logger.warning("Worker shutdown error: %s", e)
        _worker_task = None
    _queue = None
    logger.info("Persistence write-queue worker stopped")


def _enqueue(item: tuple) -> None:
    """Non-blocking enqueue. Drops on overflow with a warning."""
    if _queue is None:
        return
    try:
        _queue.put_nowait(item)
    except asyncio.QueueFull:
        logger.warning("Write queue full, dropping %s", item[0])


async def enqueue_edit(edit_dict: dict) -> None:
    _enqueue(("edit", edit_dict))


async def enqueue_snapshot(session_id: str, state_dict: dict) -> None:
    _enqueue(("snapshot", session_id, state_dict))


async def enqueue_session(session_dict: dict) -> None:
    _enqueue(("session", session_dict))


async def enqueue_study(study_dict: dict) -> None:
    _enqueue(("study", study_dict))


async def _drain_worker() -> None:
    from . import repo  # noqa: F401 - ensure import
    batch: list = []
    BATCH_SIZE = 50
    BATCH_TIMEOUT = 1.0

    assert _queue is not None

    while True:
        try:
            item = await _queue.get()
            if item is None:
                if batch:
                    await _flush_batch(batch)
                return
            batch.append(item)

            while len(batch) < BATCH_SIZE:
                try:
                    next_item = await asyncio.wait_for(
                        _queue.get(), timeout=BATCH_TIMEOUT
                    )
                    if next_item is None:
                        if batch:
                            await _flush_batch(batch)
                        return
                    batch.append(next_item)
                except asyncio.TimeoutError:
                    break

            await _flush_batch(batch)
            batch = []
        except asyncio.CancelledError:
            if batch:
                try:
                    await _flush_batch(batch)
                except Exception:
                    pass
            return
        except Exception as e:
            logger.error("Write worker error: %s", e)
            batch = []


async def _flush_batch(batch: list) -> None:
    from . import repo

    for item in batch:
        try:
            kind = item[0]
            if kind == "edit":
                await repo.save_edit(item[1])
            elif kind == "snapshot":
                await repo.save_snapshot(item[1], item[2])
            elif kind == "session":
                await repo.save_session(item[1])
            elif kind == "study":
                await repo.save_study(item[1])
        except Exception as e:
            logger.error("Failed to persist %s: %s", item[0], e)
            _persistence_failures.append({
                "type": "persistence_warning",
                "failed_kind": item[0],
                "error": str(e),
                "retry_recommended": True,
            })
