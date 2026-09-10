"""ResultsSink — the single write-back path of every engineering analysis
(SCDF-170 §1.2).

An analysis (design loop, mission simulation, ground closure, ...) never
writes to the model directly. It hands its outputs to
``ResultsSink.publish`` which:

1. writes each ``ParamWrite`` as a typed element parameter
   (``parameter_repo.upsert_element_parameter`` with ``computed_value`` and
   ``owner_domain=<analysis>``; study-level results attach to the mission
   root element). A ``manual`` / ``reference`` switch is **never** overridden
   — the computed value is stored beside it and reported in
   ``PublishResult.shadowed``; well-known names (``mass_kg`` …) whose element
   column is still empty are written through to the column so budgets see them;
2. replaces the unresolved ``analysis_conflicts`` of (study, option, analysis)
   with the given ``Conflict`` list;
3. re-checks compliance for the written paths (``el:<id>.<name>``,
   ``el:<name>.<name>`` and the flat registry paths they feed) through the
   per-study ``ComplianceTracker`` (``get_tracker``);
4. broadcasts ``analysis_completed`` on the study WebSocket.

Runs are bracketed by ``start_run`` / ``finish_run``; ``finish_run`` stores
the bulky ``series`` as JSON under ``<SPACECDF_DATA_DIR>/analysis/<run_id>.json``
(``SPACECDF_DATA_DIR`` defaults to ``./data``). ``get_last_run`` adds
``stale`` by comparing the stored ``inputs_hash`` with a fresh
``context_hash`` over the keys the analysis declares in ``ANALYSIS_INPUT_KEYS``.

Option scoping: runs, conflicts *and* parameter writes carry ``option_id``
(SCDF-172). Publishing with ``option_id=X`` upserts X override rows (the
baseline rows are untouched) and skips the well-known column write — element
columns are baseline state.

Public API:
    ParamWrite, Conflict, PublishResult
    ResultsSink().publish(study_id, analysis, *, parameters, conflicts, notes, option_id, run_id, ctx)
    start_run(study_id, analysis, inputs_hash, option_id=None) -> run_id
    finish_run(run_id, status, summary=None, series=None, inputs_hash=None) -> dict
    current_hash(study_id, analysis, option_id=None) -> str
    refresh_inputs_hash(run_id) -> str | None      (write-back analyses: call after finish_run)
    get_last_run(study_id, analysis, option_id=None, *, ctx=None) -> dict | None   (+ stale)
    list_analyses(study_id, option_id=None) -> list[dict]                            (+ stale)
    resolve_conflict(conflict_id) -> dict | None
    get_tracker(study_id) -> ComplianceTracker
    on_publish(callback) / off_publish(callback)   post-publish hooks (SCDF-175 V&V auto-closure)
    data_dir() / series_path(run_id) / save_series(run_id, series) / load_series(ref)
    ANALYSIS_INPUT_KEYS
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS

from ..db import analysis_repo, parameter_repo
from .analysis_context import HASH_KEYS, AnalysisContext, build_context, context_hash
from .compliance_tracker import ComplianceDelta, ComplianceTracker
from .element_projection import PROPERTY_TO_PARAM

logger = logging.getLogger(__name__)

#: Context subsets each analysis reads — what its ``inputs_hash`` covers.
#: Unknown analyses hash every subset.
ANALYSIS_INPUT_KEYS: dict[str, tuple[str, ...]] = {
    "design_loop": ("elements", "params", "orbit", "modes", "requirements"),
    "mission_simulation": ("elements", "params", "orbit", "modes", "power", "thermal", "stations"),
    "ground": ("elements", "params", "orbit", "stations"),
    "physics": ("elements", "params", "orbit", "thermal", "requirements"),   # pointing budget vs requirement
    "vv": ("requirements", "elements"),
    "fmeca": ("elements",),
}

SEVERITIES = ("critical", "major", "minor", "warning", "info")


# ── Data classes ────────────────────────────────────────────────────────

@dataclass
class ParamWrite:
    """One parameter an analysis wants to store. ``element_id=None`` → mission root."""
    name: str
    value: float
    element_id: str | None = None
    unit: str = ""
    quantity_kind: str = ""
    description: str = ""


@dataclass
class Conflict:
    """One finding an analysis raises (persisted in ``analysis_conflicts``)."""
    severity: str                     # critical | major | minor | warning | info
    code: str
    title: str
    detail: str = ""
    element_ids: list[str] = field(default_factory=list)
    requirement_ids: list[str] = field(default_factory=list)
    suggested_fix: str | None = None


@dataclass
class PublishResult:
    analysis: str
    run_id: str | None
    written: list[dict] = field(default_factory=list)     # parameter rows written (repo dicts + name)
    shadowed: list[dict] = field(default_factory=list)    # rows whose manual/reference switch hides the new value
    skipped: list[dict] = field(default_factory=list)     # {name, reason}
    paths: list[str] = field(default_factory=list)        # dirty paths handed to the compliance recheck
    conflicts: list[dict] = field(default_factory=list)   # persisted conflict rows
    compliance: ComplianceDelta | None = None
    compliance_results: dict[str, dict] = field(default_factory=dict)  # {req_id: {status, achieved, threshold, margin_pct}}
    notes: list[str] = field(default_factory=list)


# ── Series files ───────────────────────────────────────────────────────

def data_dir() -> Path:
    """``$SPACECDF_DATA_DIR`` (default ``./data``), created on demand."""
    root = Path(os.environ.get("SPACECDF_DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root


def series_path(run_id: str) -> Path:
    d = data_dir() / "analysis"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{run_id}.json"


def save_series(run_id: str, series: Any) -> str:
    """Write ``series`` as JSON; returns the ``series_ref`` stored on the run
    (path relative to the data dir, ``analysis/<run_id>.json``)."""
    path = series_path(run_id)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(series, fh, default=str, separators=(",", ":"))
    return f"analysis/{run_id}.json"


def load_series(series_ref: str | None) -> Any:
    """Inverse of ``save_series``; ``None`` when missing / unreadable."""
    if not series_ref:
        return None
    path = Path(series_ref)
    if not path.is_absolute():
        path = data_dir() / series_ref
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        logger.debug("series %s unreadable", series_ref, exc_info=True)
        return None


# ── Runs ────────────────────────────────────────────────────────────────

def input_keys_for(analysis: str) -> tuple[str, ...]:
    return ANALYSIS_INPUT_KEYS.get(analysis, HASH_KEYS)


async def start_run(study_id: str, analysis: str, inputs_hash: str | None,
                    option_id: str | None = None) -> str:
    """Insert a ``running`` analysis_runs row; returns its id."""
    run = await analysis_repo.create_run(study_id, analysis, inputs_hash, option_id)
    try:
        from ..routers._arcadia_events import broadcast_mutation
        await broadcast_mutation(study_id, "analysis_started", "analysis", analysis,
                                 {"run_id": run["id"], "option_id": option_id})
    except Exception:  # pragma: no cover - defensive
        pass
    return run["id"]


async def finish_run(run_id: str, status: str, summary: dict | None = None,
                     series: Any = None, inputs_hash: str | None = None) -> dict:
    """Close a run (``ok`` | ``failed``), store ``summary`` on the row and
    ``series`` (any JSON-able object) in the series file. Returns the run dict.

    ``inputs_hash`` replaces the hash recorded by ``start_run``. An analysis
    that writes back into the model (the design loop writes element
    parameters) should call ``refresh_inputs_hash(run_id)`` afterwards —
    otherwise its own outputs would flag the run stale.
    """
    series_ref = save_series(run_id, series) if series is not None else None
    return await analysis_repo.finish_run(run_id, status, summary=summary, series_ref=series_ref,
                                          inputs_hash=inputs_hash)


async def current_hash(study_id: str, analysis: str, option_id: str | None = None) -> str:
    """``context_hash`` of a fresh context over ``ANALYSIS_INPUT_KEYS[analysis]``."""
    ctx = await build_context(study_id, option_id=option_id)
    return context_hash(ctx, input_keys_for(analysis))


async def refresh_inputs_hash(run_id: str) -> str | None:
    """Re-stamp a *finished* run's ``inputs_hash`` from the live context.

    Call this after ``finish_run`` for analyses that write back into the
    model (the design loop): the context now includes their own outputs (and,
    for ``design_loop``, ``latest_design`` is the run itself), so the run is
    fresh until the next external change. Returns the new hash.
    """
    run = await analysis_repo.get_run(run_id)
    if run is None:
        return None
    h = await current_hash(run["study_id"], run["analysis"], run.get("option_id"))
    await analysis_repo.finish_run(run_id, run["status"], inputs_hash=h)
    return h


def _with_stale(run: dict, ctx: AnalysisContext) -> dict:
    try:
        current = context_hash(ctx, input_keys_for(run["analysis"]))
    except Exception:  # pragma: no cover - defensive
        current = None
    run = dict(run)
    run["current_hash"] = current
    run["stale"] = bool(run.get("inputs_hash")) and current is not None and run["inputs_hash"] != current
    return run


async def get_last_run(study_id: str, analysis: str, option_id: str | None = None, *,
                       ctx: AnalysisContext | None = None) -> dict | None:
    """Last finished run of ``analysis`` with ``stale`` / ``current_hash`` added
    (``stale`` = the stored ``inputs_hash`` differs from the live context)."""
    run = await analysis_repo.get_last_run(study_id, analysis, option_id)
    if run is None:
        return None
    ctx = ctx or await build_context(study_id, option_id=option_id)
    return _with_stale(run, ctx)


async def list_analyses(study_id: str, option_id: str | None = None, *,
                        ctx: AnalysisContext | None = None) -> list[dict]:
    """Last run per analysis (with ``stale``), ordered by analysis name."""
    runs = await analysis_repo.list_last_runs(study_id, option_id)
    if not runs:
        return []
    ctx = ctx or await build_context(study_id, option_id=option_id)
    return [_with_stale(runs[k], ctx) for k in sorted(runs)]


async def resolve_conflict(conflict_id: str) -> dict | None:
    row = await analysis_repo.resolve_conflict(conflict_id)
    if row is not None:
        try:
            from ..routers._arcadia_events import broadcast_mutation
            await broadcast_mutation(row["study_id"], "conflict_resolved", "conflict", conflict_id, row)
        except Exception:  # pragma: no cover - defensive
            pass
    return row


# ── Compliance trackers (one per study, kept across publishes) ─────────

_trackers: dict[str, ComplianceTracker] = {}


def get_tracker(study_id: str) -> ComplianceTracker:
    tracker = _trackers.get(study_id)
    if tracker is None:
        tracker = _trackers[study_id] = ComplianceTracker()
    return tracker


def reset_trackers() -> None:
    """Tests: forget all compliance history."""
    _trackers.clear()


# ── Post-publish hooks (SCDF-175) ──────────────────────────────────────

#: ``async def cb(study_id, analysis, result: PublishResult) -> None`` — called
#: after every publish once compliance has been rechecked, before the
#: ``analysis_completed`` broadcast. Hooks never break the publish: exceptions
#: are logged and swallowed.
_publish_hooks: list[Callable[..., Awaitable[None]]] = []


def on_publish(callback: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
    """Register ``callback(study_id, analysis, result)`` (idempotent). Returns it."""
    if callback not in _publish_hooks:
        _publish_hooks.append(callback)
    return callback


def off_publish(callback: Callable[..., Awaitable[None]]) -> None:
    if callback in _publish_hooks:
        _publish_hooks.remove(callback)


async def _run_publish_hooks(study_id: str, analysis: str, result: "PublishResult") -> None:
    for cb in list(_publish_hooks):
        try:
            await cb(study_id, analysis, result)
        except Exception:  # pragma: no cover - defensive
            logger.exception("publish hook %r failed for %s/%s", cb, study_id, analysis)


# ── Sink ────────────────────────────────────────────────────────────────

class ResultsSink:
    """Write-back of analysis outputs. Stateless; instantiate freely."""

    async def publish(
        self,
        study_id: str,
        analysis: str,
        *,
        parameters: list[ParamWrite] | tuple[ParamWrite, ...] = (),
        conflicts: list[Conflict] | tuple[Conflict, ...] = (),
        notes: list[str] | tuple[str, ...] = (),
        option_id: str | None = None,
        run_id: str | None = None,
        ctx: AnalysisContext | None = None,
        recheck: bool = True,
        broadcast: bool = True,
    ) -> PublishResult:
        """Persist parameters + conflicts, re-check compliance, broadcast.

        ``ctx`` (if given) must be the context the analysis ran on — it is
        used for the mission root and for the manual/reference check; a fresh
        context is built after the writes for the compliance re-check.
        """
        ctx = ctx or await build_context(study_id, option_id=option_id)
        result = PublishResult(analysis=analysis, run_id=run_id, notes=list(notes))
        root = ctx.mission_root
        by_id = ctx.elements_by_id
        written_keys: list[tuple[str, str]] = []

        for pw in parameters:
            if isinstance(pw.value, bool) or not isinstance(pw.value, (int, float)):
                result.skipped.append({"name": pw.name, "reason": "non-numeric value"})
                continue
            element_id = pw.element_id or (root["id"] if root else None)
            if element_id is None or element_id not in by_id:
                result.skipped.append({"name": pw.name, "reason": f"element {pw.element_id!r} not in study"})
                continue
            existing = ctx.params.get(element_id, {}).get(pw.name)
            payload: dict[str, Any] = {
                "study_id": study_id, "element_id": element_id, "definition_name": pw.name,
                "computed_value": float(pw.value), "owner_domain": analysis, "option_id": option_id,
            }
            if existing is None or existing.switch == "computed":
                payload["value_switch"] = "computed"
            elif option_id is not None and existing.option_id != option_id:
                # A manual/reference *baseline* value must keep shadowing the
                # analysis output inside the option: the new option row copies it.
                payload["value_switch"] = existing.switch
                payload["manual_value" if existing.switch == "manual" else "reference_value"] = existing.value
            try:
                row = await parameter_repo.upsert_element_parameter(payload)
            except Exception as exc:
                logger.exception("publish: parameter %s on %s failed", pw.name, element_id)
                result.skipped.append({"name": pw.name, "reason": str(exc)})
                continue
            if pw.unit or pw.quantity_kind or pw.description:
                await self._fill_definition(row["definition_id"], pw)
            entry = {**row, "name": pw.name, "element_id": element_id, "value": float(pw.value)}
            if existing is not None and existing.switch in ("manual", "reference"):
                result.shadowed.append(entry)
            else:
                result.written.append(entry)
                written_keys.append((element_id, pw.name))
                if option_id is None and pw.name in WELL_KNOWN_PARAMETERS and by_id[element_id].get(pw.name) is None:
                    await self._write_column(study_id, element_id, pw.name, float(pw.value))

        # conflicts
        rows = await analysis_repo.replace_conflicts(
            study_id, analysis, [asdict(c) for c in conflicts], option_id=option_id, run_id=run_id)
        result.conflicts = rows

        # dirty paths + compliance
        result.paths = self._dirty_paths(ctx, written_keys)
        if recheck and (result.paths or result.shadowed):
            fresh = await build_context(study_id, option_id=option_id)
            tracker = get_tracker(study_id)
            tracker.set_requirements(fresh.requirements)
            tracker.set_relations(fresh.relations)
            dirty = set(result.paths) | {p for e in result.shadowed for p in self._dirty_paths(fresh, [(e["element_id"], e["name"])])}
            result.compliance = await tracker.recheck(fresh, dirty or None)
            result.compliance_results = {
                rid: {"status": r.status, "achieved": r.achieved_value, "threshold": r.threshold_value,
                      "margin_pct": r.margin_pct}
                for rid, r in tracker.get_all_results().items()
            }

        await _run_publish_hooks(study_id, analysis, result)

        if broadcast:
            try:
                from ..routers._arcadia_events import broadcast_mutation
                await broadcast_mutation(study_id, "analysis_completed", "analysis", analysis, {
                    "run_id": run_id, "option_id": option_id,
                    "parameters_written": len(result.written), "conflicts": len(result.conflicts),
                    "compliance": asdict(result.compliance) if result.compliance else None,
                })
            except Exception:  # pragma: no cover - defensive
                logger.debug("analysis_completed broadcast failed", exc_info=True)
        return result

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _dirty_paths(ctx: AnalysisContext, keys: list[tuple[str, str]]) -> list[str]:
        """``el:`` forms (id + name) and the flat registry paths each written
        element parameter feeds."""
        if not keys:
            return []
        by_id = ctx.elements_by_id
        paths: list[str] = []
        for eid, name in keys:
            paths.append(f"el:{eid}.{name}")
            el = by_id.get(eid)
            if el is None:
                continue
            if el.get("name"):
                paths.append(f"el:{el['name']}.{name}")
            # every registry path of the element's domain that reads this property
            # (leaf contributions and the subsystem the path writes back to alike)
            for flat_path, (domain, prop, _agg) in PROPERTY_TO_PARAM.items():
                if el.get("subsystem_domain") != domain or flat_path in paths:
                    continue
                if prop == name or prop == f"performance.{name}":
                    paths.append(flat_path)
        return paths

    @staticmethod
    async def _fill_definition(definition_id: str, pw: ParamWrite) -> None:
        try:
            defn = await parameter_repo.get_parameter_definition(definition_id)
            if not defn:
                return
            updates = {}
            if pw.unit and not defn.get("unit"):
                updates["unit"] = pw.unit
            if pw.quantity_kind and not defn.get("quantity_kind"):
                updates["quantity_kind"] = pw.quantity_kind
            if pw.description and not defn.get("description"):
                updates["description"] = pw.description
            if updates:
                await parameter_repo.upsert_parameter_definition({"name": defn["name"], **updates})
        except Exception:
            logger.debug("definition fill for %s failed", definition_id, exc_info=True)

    @staticmethod
    async def _write_column(study_id: str, element_id: str, name: str, value: float) -> None:
        try:
            from .equations import _apply_element_columns
            await _apply_element_columns(study_id, element_id, {name: value})
        except Exception:
            logger.debug("column write-through %s.%s failed", element_id, name, exc_info=True)
