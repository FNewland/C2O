"""Async repository for gate baseline snapshots (``gate_baselines``; WP6, Nov 2026)."""
from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy import select

from .engine import get_session_factory
from .models import GateBaselineRow

logger = logging.getLogger(__name__)


def _row(r: GateBaselineRow, with_snapshot: bool = False) -> dict:
    out = {"id": r.id, "study_id": r.study_id, "gate": r.gate, "profile": r.profile,
           "created_by": r.created_by, "created_at": r.created_at.isoformat() if r.created_at else None,
           "summary": r.summary_json or {}}
    if with_snapshot:
        out["snapshot"] = r.snapshot_json or {}
    return out


async def save_baseline(study_id: str, gate: str, profile: str, created_by: str,
                        summary: dict, snapshot: dict) -> dict:
    row = GateBaselineRow(id=uuid4().hex[:16], study_id=study_id, gate=gate, profile=profile,
                          created_by=created_by[:255], summary_json=summary, snapshot_json=snapshot)
    factory = get_session_factory()
    async with factory() as session:
        session.add(row)
        await session.commit()
    return _row(row)


async def list_baselines(study_id: str, gate: str | None = None) -> list[dict]:
    factory = get_session_factory()
    async with factory() as session:
        q = select(GateBaselineRow).where(GateBaselineRow.study_id == study_id)
        if gate:
            q = q.where(GateBaselineRow.gate == gate)
        rows = (await session.execute(q.order_by(GateBaselineRow.created_at))).scalars().all()
        return [_row(r) for r in rows]


async def get_baseline(baseline_id: str) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        r = await session.get(GateBaselineRow, baseline_id)
        return _row(r, with_snapshot=True) if r else None
