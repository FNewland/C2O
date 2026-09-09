"""Option comparison (SCDF-172 §1.4).

``compare_options(study_id, a, b)`` builds one ``AnalysisContext`` per option
(``build_context(study_id, option_id=...)`` — the baseline option maps to
``option_id=None``) and reports:

* ``parameters`` — every (element, parameter) whose *effective* value differs
  between A and B (either side may be missing), with the numeric delta and the
  unit, plus which side carries an override row;
* ``analyses`` — for every analysis that ran in A or B: the last run's summary
  side by side and the numeric summary fields that differ (nested numbers are
  flattened to dotted keys);
* ``conflicts`` — unresolved analysis conflict counts per side.

Pure read; never raises into the API (context failures are reported as
``warnings``).
"""
from __future__ import annotations

import logging
from typing import Any

from ..db import analysis_repo, option_repo

logger = logging.getLogger(__name__)

_EPS = 1e-12


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _flatten_numbers(d: Any, prefix: str = "", out: dict[str, float] | None = None) -> dict[str, float]:
    out = {} if out is None else out
    if isinstance(d, dict):
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            n = _num(v)
            if n is not None:
                out[key] = n
            elif isinstance(v, dict):
                _flatten_numbers(v, key, out)
    return out


def _differs(a: float | None, b: float | None) -> bool:
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    return abs(a - b) > _EPS * max(1.0, abs(a), abs(b))


async def _context(study_id: str, option_id: str | None):
    from .analysis_context import build_context
    return await build_context(study_id, option_id=option_id)


def _param_rows(ctx_a, ctx_b, option_a: str | None, option_b: str | None) -> list[dict]:
    names = {e.get("id"): e.get("name") for e in (ctx_a.elements or [])}
    keys: set[tuple[str, str]] = set()
    for ctx in (ctx_a, ctx_b):
        for eid, params in (ctx.params or {}).items():
            for name in params:
                keys.add((eid, name))
    rows: list[dict] = []
    for eid, name in sorted(keys, key=lambda k: (names.get(k[0]) or "", k[1])):
        pa = (ctx_a.params or {}).get(eid, {}).get(name)
        pb = (ctx_b.params or {}).get(eid, {}).get(name)
        va = pa.value if pa else None
        vb = pb.value if pb else None
        if not _differs(va, vb):
            continue
        rows.append({
            "element_id": eid, "element": names.get(eid) or eid, "name": name,
            "unit": (pa.unit if pa else None) or (pb.unit if pb else None) or "",
            "a": va, "b": vb,
            "delta": (vb - va) if (va is not None and vb is not None) else None,
            "a_override": bool(pa and option_a is not None and pa.option_id == option_a),
            "b_override": bool(pb and option_b is not None and pb.option_id == option_b),
            "a_provenance": pa.provenance if pa else None,
            "b_provenance": pb.provenance if pb else None,
        })
    return rows


async def _analysis_rows(study_id: str, option_a: str | None, option_b: str | None) -> list[dict]:
    runs_a = await analysis_repo.list_last_runs(study_id, option_a)
    runs_b = await analysis_repo.list_last_runs(study_id, option_b)
    out: list[dict] = []
    for analysis in sorted(set(runs_a) | set(runs_b)):
        ra, rb = runs_a.get(analysis), runs_b.get(analysis)
        sa = (ra or {}).get("summary") or {}
        sb = (rb or {}).get("summary") or {}
        fa, fb = _flatten_numbers(sa), _flatten_numbers(sb)
        deltas = []
        for key in sorted(set(fa) | set(fb)):
            va, vb = fa.get(key), fb.get(key)
            if _differs(va, vb):
                deltas.append({"key": key, "a": va, "b": vb,
                               "delta": (vb - va) if (va is not None and vb is not None) else None})
        out.append({
            "analysis": analysis,
            "a_run_id": (ra or {}).get("id"), "b_run_id": (rb or {}).get("id"),
            "a_finished_at": (ra or {}).get("finished_at"), "b_finished_at": (rb or {}).get("finished_at"),
            "a_status": (ra or {}).get("status"), "b_status": (rb or {}).get("status"),
            "a_summary": sa, "b_summary": sb, "deltas": deltas,
        })
    return out


async def compare_options(study_id: str, a: str | None, b: str | None) -> dict:
    """See module doc. ``a`` / ``b`` are option ids (the baseline option id or
    None/'' both mean the baseline)."""
    option_a = await option_repo.resolve_option_id(a)
    option_b = await option_repo.resolve_option_id(b)
    opt_a = await option_repo.get_option(a) if a else await option_repo.ensure_baseline(study_id)
    opt_b = await option_repo.get_option(b) if b else await option_repo.ensure_baseline(study_id)
    warnings: list[str] = []
    ctx_a = ctx_b = None
    try:
        ctx_a = await _context(study_id, option_a)
        ctx_b = await _context(study_id, option_b)
    except Exception as exc:
        logger.exception("compare_options: context failed for %s", study_id)
        warnings.append(f"context: {exc}")
    parameters = _param_rows(ctx_a, ctx_b, option_a, option_b) if ctx_a and ctx_b else []
    analyses = await _analysis_rows(study_id, option_a, option_b)
    conflicts = {
        "a": len(await analysis_repo.list_conflicts(study_id, option_id=option_a)),
        "b": len(await analysis_repo.list_conflicts(study_id, option_id=option_b)),
    }
    return {
        "study_id": study_id,
        "a": {"id": (opt_a or {}).get("id"), "name": (opt_a or {}).get("name"), "option_id": option_a},
        "b": {"id": (opt_b or {}).get("id"), "name": (opt_b or {}).get("name"), "option_id": option_b},
        "parameters": parameters,
        "analyses": analyses,
        "conflicts": conflicts,
        "warnings": warnings,
    }
