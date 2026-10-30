"""Async repository for Study persistence.

Write-through cache: the in-memory _studies dict in studies.py is the
primary read path; this module ensures durability by mirroring every
mutation to the database. On startup, existing rows are loaded back
into memory.

All DB errors are logged and swallowed so the hot path never crashes.
"""
from __future__ import annotations

import json
import logging

from sqlalchemy import select, delete as sa_delete

from .engine import get_session_factory
from .models import StudyRow

logger = logging.getLogger(__name__)


async def db_save_study(study) -> None:
    """Save or update a study in the database.

    Serializes the full Study Pydantic model into meta_json for
    complete round-trip fidelity.
    """
    try:
        # Serialize — try model_dump first, fall back to json round-trip
        try:
            meta = study.model_dump(mode="json")
        except Exception:
            meta = json.loads(study.model_dump_json())

        factory = get_session_factory()
        async with factory() as session:
            existing = await session.get(StudyRow, study.id)
            if existing:
                existing.name = study.name
                existing.meta_json = meta
            else:
                row = StudyRow(
                    id=study.id,
                    name=study.name,
                    meta_json=meta,
                )
                session.add(row)
            await session.commit()
        logger.info("Saved study %s (%s) to DB", study.id, study.name)
    except Exception:
        logger.exception("db_save_study failed for %s", study.id)


async def db_load_all_studies() -> dict:
    """Load all studies from DB, returning {id: Study} dict.

    Returns an empty dict on any DB error so the server can still
    start with an empty in-memory cache.
    """
    from spacecdf_common.models.study import Study

    studies: dict = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(StudyRow))
            for row in result.scalars():
                try:
                    study = Study(**row.meta_json)
                    studies[study.id] = study
                except Exception as e:
                    logger.warning(
                        "Failed to deserialize study %s: %s", row.id, e
                    )
        logger.info("Loaded %d studies from DB", len(studies))
    except Exception:
        logger.exception(
            "Failed to load studies from DB — starting with empty cache"
        )
    return studies


async def db_delete_study(study_id: str) -> None:
    """Delete a study row from the database."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = sa_delete(StudyRow).where(StudyRow.id == study_id)
            await session.execute(stmt)
            await session.commit()
        logger.info("Deleted study %s from DB", study_id)
    except Exception:
        logger.exception("db_delete_study failed for %s", study_id)
