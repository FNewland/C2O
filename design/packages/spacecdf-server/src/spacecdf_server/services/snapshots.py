"""SpaceCDF — Named snapshot service (Phase 5B).

Named, labelled snapshots of a session's DesignState, with diff support so
engineers can compare two named baselines parameter-by-parameter. Underpins
the DesignComparison UI and feeds the optimiser's "apply best" flow.

Uses the existing DesignStateSnapshotRow (extended in 5B with name, label,
parent_snapshot_id, tags_json). Writes are immediate (not via the async
write queue) so the API response can return a real DB id.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from ..db.engine import get_session_factory
from ..db.models import DesignStateSnapshotRow
from .session_manager import get_session_manager

logger = logging.getLogger(__name__)


@dataclass
class SnapshotInfo:
    id: int
    session_id: str
    name: str | None
    label: str
    version: int
    parent_snapshot_id: int | None
    tags: list[str]
    created_at: str

    @classmethod
    def from_row(cls, row: DesignStateSnapshotRow) -> "SnapshotInfo":
        return cls(
            id=row.id,
            session_id=row.session_id,
            name=row.name,
            label=row.label or "auto",
            version=row.version or 0,
            parent_snapshot_id=row.parent_snapshot_id,
            tags=list(row.tags_json or []),
            created_at=(row.created_at or datetime.now(timezone.utc)).isoformat(),
        )


async def create_named_snapshot(
    session_id: str,
    name: str,
    label: str = "manual",
    tags: list[str] | None = None,
    parent_snapshot_id: int | None = None,
) -> SnapshotInfo:
    """Snapshot the live session state under a human-meaningful name."""
    sm = get_session_manager()
    state = sm.get_session_state(session_id)
    if state is None:
        raise ValueError(f"No live state for session {session_id}")

    # Reuse the same serialisation the auto-snapshot path uses
    state_dict = sm._serialise_state(state)  # noqa: SLF001 — intentional reuse
    payload = json.dumps(state_dict, default=str)

    factory = get_session_factory()
    async with factory() as db:
        row = DesignStateSnapshotRow(
            session_id=session_id,
            version=state_dict.get("_version", 0),
            state_json=payload,
            name=name,
            label=label,
            parent_snapshot_id=parent_snapshot_id,
            tags_json=list(tags or []),
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return SnapshotInfo.from_row(row)


async def list_snapshots(session_id: str) -> list[SnapshotInfo]:
    """All snapshots for a session, newest first."""
    factory = get_session_factory()
    async with factory() as db:
        stmt = (
            select(DesignStateSnapshotRow)
            .where(DesignStateSnapshotRow.session_id == session_id)
            .order_by(DesignStateSnapshotRow.created_at.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [SnapshotInfo.from_row(r) for r in rows]


async def get_snapshot(snapshot_id: int) -> tuple[SnapshotInfo, dict[str, Any]] | None:
    """Return (info, state_dict) for a single snapshot."""
    factory = get_session_factory()
    async with factory() as db:
        row = await db.get(DesignStateSnapshotRow, snapshot_id)
        if not row:
            return None
        try:
            state = json.loads(row.state_json)
        except Exception:
            state = {}
        return SnapshotInfo.from_row(row), state


@dataclass
class ParamDelta:
    param_id: str
    value_a: Any | None
    value_b: Any | None
    unit: str
    source_a: str | None
    source_b: str | None
    change_type: str  # 'added' | 'removed' | 'changed' | 'unchanged'
    delta: float | None = None
    delta_percent: float | None = None


def diff_states(state_a: dict, state_b: dict, changes_only: bool = True) -> list[ParamDelta]:
    """Parameter-by-parameter diff of two serialised states.

    Numeric params get delta + delta_percent. Non-numeric params report the
    string change. Stable ordering: sorted by param_id.
    """
    params_a = state_a.get("parameters", {})
    params_b = state_b.get("parameters", {})
    all_ids = sorted(set(params_a.keys()) | set(params_b.keys()))

    out: list[ParamDelta] = []
    for pid in all_ids:
        a = params_a.get(pid)
        b = params_b.get(pid)

        va = a.get("value") if a else None
        vb = b.get("value") if b else None
        sa = a.get("source") if a else None
        sb = b.get("source") if b else None
        unit = (b or a or {}).get("unit", "")

        if a is None:
            ctype = "added"
        elif b is None:
            ctype = "removed"
        elif va != vb or sa != sb:
            ctype = "changed"
        else:
            ctype = "unchanged"

        if changes_only and ctype == "unchanged":
            continue

        delta: float | None = None
        delta_pct: float | None = None
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            delta = float(vb) - float(va)
            if va not in (0, 0.0):
                delta_pct = 100.0 * delta / float(va)

        out.append(
            ParamDelta(
                param_id=pid,
                value_a=va,
                value_b=vb,
                unit=unit,
                source_a=sa,
                source_b=sb,
                change_type=ctype,
                delta=delta,
                delta_percent=delta_pct,
            )
        )
    return out


async def diff_snapshots(a_id: int, b_id: int) -> dict[str, Any]:
    """Load both snapshots and return a structured diff payload."""
    a = await get_snapshot(a_id)
    b = await get_snapshot(b_id)
    if a is None or b is None:
        missing = [sid for sid, x in [(a_id, a), (b_id, b)] if x is None]
        raise ValueError(f"Snapshot(s) not found: {missing}")

    a_info, a_state = a
    b_info, b_state = b
    deltas = diff_states(a_state, b_state, changes_only=True)

    # Category summaries
    changed = sum(1 for d in deltas if d.change_type == "changed")
    added = sum(1 for d in deltas if d.change_type == "added")
    removed = sum(1 for d in deltas if d.change_type == "removed")

    return {
        "a": a_info.__dict__,
        "b": b_info.__dict__,
        "summary": {
            "total_diffs": len(deltas),
            "changed": changed,
            "added": added,
            "removed": removed,
        },
        "deltas": [d.__dict__ for d in deltas],
    }
