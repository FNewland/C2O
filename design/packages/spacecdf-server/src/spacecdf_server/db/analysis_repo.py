"""Async repository for analysis runs and analysis conflicts (SCDF-170 §1.2).

Dict-in / dict-out like the other arcadia repos (``_arcadia_common``):
``list_*`` / ``get_*`` never raise (log + empty), writers raise ``ValueError``
on not-found so the service layer can decide.

Public API:
    create_run(study_id, analysis, inputs_hash, option_id=None) -> dict
    finish_run(run_id, status, summary=None, series_ref=None, inputs_hash=None) -> dict
    get_run(run_id)                                              -> dict | None
    get_last_run(study_id, analysis, option_id=None)             -> dict | None
    list_last_runs(study_id, option_id=None)                     -> dict[analysis, dict]
    list_runs(study_id, analysis=None, option_id=None, limit=50) -> list[dict]

    replace_conflicts(study_id, analysis, conflicts, option_id=None, run_id=None) -> list[dict]
    list_conflicts(study_id, option_id=None, analysis=None, include_resolved=False) -> list[dict]
    resolve_conflict(conflict_id) -> dict | None
    get_conflict(conflict_id) -> dict | None

Option scoping: ``option_id=None`` means the baseline. ``get_last_run`` /
``list_conflicts`` filter on the exact option id (baseline rows have NULL).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, desc, select

from ._arcadia_common import get_session_factory, new_id, row_to_dict, utcnow
from .models import AnalysisConflictRow, AnalysisRunRow

logger = logging.getLogger(__name__)

RUN_STATUSES = ("running", "ok", "failed")
CONFLICT_SEVERITIES = ("critical", "major", "minor", "warning", "info")

#: API keys -> JSON columns specific to this repo (``_arcadia_common.JSON_KEY_MAP``
#: only knows the shared ones).
_CONFLICT_JSON = {"element_ids": "element_ids_json", "requirement_ids": "requirement_ids_json"}


def _run_dict(row: AnalysisRunRow) -> dict:
    d = row_to_dict(row)
    d["summary"] = d.pop("summary_json", None) or {}
    return d


def _conflict_dict(row: AnalysisConflictRow) -> dict:
    d = row_to_dict(row)
    d["element_ids"] = d.pop("element_ids_json", None) or []
    d["requirement_ids"] = d.pop("requirement_ids_json", None) or []
    d["resolved"] = d.get("resolved_at") is not None
    return d


def _option_filter(model, option_id: str | None):
    return model.option_id.is_(None) if option_id is None else model.option_id == option_id


# ── Runs ────────────────────────────────────────────────────────────────

async def create_run(study_id: str, analysis: str, inputs_hash: str | None,
                     option_id: str | None = None) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        row = AnalysisRunRow(id=new_id("run"), study_id=study_id, option_id=option_id,
                             analysis=analysis, inputs_hash=inputs_hash, status="running")
        session.add(row)
        await session.commit()
        return _run_dict(row)


async def finish_run(run_id: str, status: str, summary: dict | None = None,
                     series_ref: str | None = None, inputs_hash: str | None = None) -> dict:
    if status not in RUN_STATUSES:
        raise ValueError(f"status must be one of {RUN_STATUSES}")
    factory = get_session_factory()
    async with factory() as session:
        row = await session.get(AnalysisRunRow, run_id)
        if row is None:
            raise ValueError(f"analysis run '{run_id}' not found")
        row.status = status
        if row.finished_at is None:
            row.finished_at = utcnow()
        if summary is not None:
            row.summary_json = summary
        if series_ref is not None:
            row.series_ref = series_ref
        if inputs_hash is not None:
            row.inputs_hash = inputs_hash
        await session.commit()
        return _run_dict(row)


async def get_run(run_id: str) -> dict | None:
    try:
        factory = get_session_factory()
        async with factory() as session:
            row = await session.get(AnalysisRunRow, run_id)
            return _run_dict(row) if row else None
    except Exception:
        logger.exception("get_run failed for %s", run_id)
        return None


async def get_last_run(study_id: str, analysis: str, option_id: str | None = None) -> dict | None:
    """Most recent *finished* run (status ok/failed) for the analysis; a run
    still ``running`` is skipped so a crashed run never masks the last result."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = (
                select(AnalysisRunRow)
                .where(AnalysisRunRow.study_id == study_id, AnalysisRunRow.analysis == analysis,
                       _option_filter(AnalysisRunRow, option_id),
                       AnalysisRunRow.status != "running")
                .order_by(desc(AnalysisRunRow.started_at), desc(AnalysisRunRow.id))
                .limit(1)
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _run_dict(row) if row else None
    except Exception:
        logger.exception("get_last_run failed for %s/%s", study_id, analysis)
        return None


async def list_runs(study_id: str, analysis: str | None = None, option_id: str | None = None,
                    limit: int = 50) -> list[dict]:
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(AnalysisRunRow).where(AnalysisRunRow.study_id == study_id,
                                                _option_filter(AnalysisRunRow, option_id))
            if analysis:
                stmt = stmt.where(AnalysisRunRow.analysis == analysis)
            stmt = stmt.order_by(desc(AnalysisRunRow.started_at)).limit(limit)
            return [_run_dict(r) for r in (await session.execute(stmt)).scalars()]
    except Exception:
        logger.exception("list_runs failed for %s", study_id)
        return []


async def list_last_runs(study_id: str, option_id: str | None = None) -> dict[str, dict]:
    """``{analysis: last finished run}`` for every analysis that has run."""
    out: dict[str, dict] = {}
    for run in await list_runs(study_id, option_id=option_id, limit=500):
        if run["status"] == "running" or run["analysis"] in out:
            continue
        out[run["analysis"]] = run
    return out


# ── Conflicts ──────────────────────────────────────────────────────────

def _conflict_kwargs(study_id: str, analysis: str, c: dict[str, Any], option_id: str | None,
                     run_id: str | None) -> dict:
    severity = c.get("severity") or "major"
    if hasattr(severity, "value"):
        severity = severity.value
    if severity not in CONFLICT_SEVERITIES:
        severity = "major"
    return {
        "id": c.get("id") or new_id("cf"), "study_id": study_id, "option_id": option_id, "run_id": run_id,
        "analysis": analysis, "severity": severity, "code": str(c.get("code") or ""),
        "title": str(c.get("title") or ""), "detail": str(c.get("detail") or c.get("description") or ""),
        "element_ids_json": list(c.get("element_ids") or []),
        "requirement_ids_json": list(c.get("requirement_ids") or []),
        "suggested_fix": c.get("suggested_fix"),
    }


async def replace_conflicts(study_id: str, analysis: str, conflicts: list[dict],
                            option_id: str | None = None, run_id: str | None = None) -> list[dict]:
    """Replace the *unresolved* conflicts of (study, option, analysis) with ``conflicts``.

    Resolved rows are left in place. Returns the newly created rows.
    """
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(
            delete(AnalysisConflictRow).where(
                AnalysisConflictRow.study_id == study_id, AnalysisConflictRow.analysis == analysis,
                _option_filter(AnalysisConflictRow, option_id), AnalysisConflictRow.resolved_at.is_(None),
            )
        )
        rows = [AnalysisConflictRow(**_conflict_kwargs(study_id, analysis, c, option_id, run_id))
                for c in conflicts]
        session.add_all(rows)
        await session.commit()
        return [_conflict_dict(r) for r in rows]


async def list_conflicts(study_id: str, option_id: str | None = None, analysis: str | None = None,
                         include_resolved: bool = False) -> list[dict]:
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(AnalysisConflictRow).where(AnalysisConflictRow.study_id == study_id,
                                                     _option_filter(AnalysisConflictRow, option_id))
            if analysis:
                stmt = stmt.where(AnalysisConflictRow.analysis == analysis)
            if not include_resolved:
                stmt = stmt.where(AnalysisConflictRow.resolved_at.is_(None))
            stmt = stmt.order_by(AnalysisConflictRow.created_at, AnalysisConflictRow.id)
            return [_conflict_dict(r) for r in (await session.execute(stmt)).scalars()]
    except Exception:
        logger.exception("list_conflicts failed for %s", study_id)
        return []


async def get_conflict(conflict_id: str) -> dict | None:
    try:
        factory = get_session_factory()
        async with factory() as session:
            row = await session.get(AnalysisConflictRow, conflict_id)
            return _conflict_dict(row) if row else None
    except Exception:
        logger.exception("get_conflict failed for %s", conflict_id)
        return None


async def resolve_conflict(conflict_id: str) -> dict | None:
    """Mark a conflict resolved (idempotent). Returns the row or ``None`` if unknown."""
    factory = get_session_factory()
    async with factory() as session:
        row = await session.get(AnalysisConflictRow, conflict_id)
        if row is None:
            return None
        if row.resolved_at is None:
            row.resolved_at = utcnow()
            await session.commit()
        return _conflict_dict(row)
