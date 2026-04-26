"""SpaceCDF — Design optimiser (Phase 5B).

Wraps scipy.optimize.differential_evolution around the CandidateEvaluator so
that a design session can run a single-objective trade-space search without
blocking the event loop or mutating sticky parameters on the base state.

Design choices:
  - scipy is called inside asyncio.to_thread — synchronous under the hood,
    but non-blocking from the API's perspective.
  - Progress is emitted via a callback the caller supplies (used by the
    router to broadcast optimize.progress events over the session WS).
  - A per-session lock prevents two runs racing on the same base state.
  - Pareto mode is shipped as "scipy + non-dominated sort" for v1; the plan
    reserves pymoo/NSGA-II behind a feature flag — left for a follow-up.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from spacecdf_common.agents.base import DesignState

from .evaluator import CandidateEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


# -- Objective registry -----------------------------------------------------

@dataclass
class ObjectiveSpec:
    """Declarative mapping from an objective key to a scalar we can minimise."""
    key: str
    description: str
    parameter_id: str
    direction: str  # "min" or "max"


# Canonical objectives exposed to the UI.
OBJECTIVES: dict[str, ObjectiveSpec] = {
    "min_mass": ObjectiveSpec(
        "min_mass", "Minimise wet mass",
        parameter_id="mass.wet_mass_kg", direction="min",
    ),
    "min_dry_mass": ObjectiveSpec(
        "min_dry_mass", "Minimise dry mass",
        parameter_id="mass.dry_mass_kg", direction="min",
    ),
    "min_cost": ObjectiveSpec(
        "min_cost", "Minimise total cost (with margin)",
        parameter_id="cost.total_with_margin_meur", direction="min",
    ),
    "max_link_margin": ObjectiveSpec(
        "max_link_margin", "Maximise downlink margin",
        parameter_id="link.downlink_margin_db", direction="max",
    ),
}

# Canonical design variables with sane default bounds — the UI will offer
# these as checkboxes; the user overrides bounds per run.
DEFAULT_DESIGN_VARIABLES: dict[str, tuple[float, float]] = {
    "orbit.altitude_km":                  (300.0, 900.0),
    "payload.power_w":                    (5.0,  150.0),
    "payload.data_volume_per_day_gb":     (0.1,  50.0),
    "payload.duty_cycle_percent":         (5.0,  100.0),
    "power.sa_margin_percent":            (10.0, 40.0),
    "link.downlink_data_rate_mbps":       (10.0, 1000.0),
}


# -- Run bookkeeping --------------------------------------------------------

@dataclass
class OptimizeConfig:
    variables: list[str]          # param IDs to vary
    bounds: list[tuple[float, float]]  # parallel to variables
    objective: str                # key into OBJECTIVES
    constraints: list[dict[str, Any]] = field(default_factory=list)
    algo: str = "differential_evolution"
    max_evals: int = 200
    seed: int | None = 42


@dataclass
class OptimizeProgress:
    run_id: int
    evaluations: int
    max_evals: int
    best_y: float | None
    best_x: dict[str, float] | None
    fraction: float
    status: str = "running"


@dataclass
class OptimizeRunResult:
    run_id: int
    status: str
    best_x: dict[str, float]
    best_y: float | None
    num_evals: int
    duration_ms: float
    history: list[dict[str, Any]]  # [{eval_n, y, x, feasible}]
    error: str | None = None


# Per-session lock so concurrent runs don't race on the same base state.
_session_locks: dict[str, asyncio.Lock] = {}


def _get_session_lock(session_id: str) -> asyncio.Lock:
    lock = _session_locks.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _session_locks[session_id] = lock
    return lock


# -- Main entry point -------------------------------------------------------

async def run_single_objective(
    *,
    run_id: int,
    session_id: str,
    base_state: DesignState,
    config: OptimizeConfig,
    progress_cb: Callable[[OptimizeProgress], None] | None = None,
) -> OptimizeRunResult:
    """Run a single-objective optimisation.

    scipy.optimize.differential_evolution runs synchronously; we wrap it in
    asyncio.to_thread so the event loop stays responsive.
    """
    from scipy.optimize import differential_evolution

    lock = _get_session_lock(session_id)
    async with lock:
        evaluator = CandidateEvaluator()

        obj_spec = OBJECTIVES.get(config.objective)
        if obj_spec is None:
            return OptimizeRunResult(
                run_id=run_id, status="failed",
                best_x={}, best_y=None, num_evals=0, duration_ms=0.0,
                history=[], error=f"Unknown objective: {config.objective}",
            )

        history: list[dict[str, Any]] = []
        best_y: float | None = None
        best_x: dict[str, float] = {}

        # Progress throttling — one event per 100 ms max
        last_emit: list[float] = [0.0]

        def sync_eval(x: np.ndarray) -> float:
            """Sync wrapper used by scipy — schedule async candidate eval."""
            overrides = {
                var: float(x[i])
                for i, var in enumerate(config.variables)
            }
            # Run the async evaluate in a new loop (we're inside to_thread)
            try:
                result: EvaluationResult = asyncio.run(
                    evaluator.evaluate(base_state, overrides, output_params=None)
                )
            except Exception as e:
                logger.warning("Optimiser eval failed at x=%s: %s", overrides, e)
                return float("inf")

            raw = result.parameters.get(obj_spec.parameter_id)
            if raw is None or not np.isfinite(raw):
                return float("inf")

            # scipy minimises; flip sign for max-direction objectives.
            y = float(raw) if obj_spec.direction == "min" else -float(raw)

            # Apply penalty for critical conflicts (soft constraint)
            if result.critical_conflicts_count > 0:
                y += 1e6 * result.critical_conflicts_count

            nonlocal best_y, best_x
            history.append({
                "eval_n": len(history) + 1,
                "y_objective": y,
                "y_raw": raw,
                "x": overrides,
                "conflicts": result.conflicts_count,
                "critical": result.critical_conflicts_count,
            })
            if best_y is None or y < best_y:
                best_y = y
                best_x = dict(overrides)

            # Progress emit, throttled
            now = time.monotonic()
            if progress_cb is not None and (now - last_emit[0]) > 0.1:
                last_emit[0] = now
                try:
                    progress_cb(OptimizeProgress(
                        run_id=run_id,
                        evaluations=len(history),
                        max_evals=config.max_evals,
                        best_y=best_y if obj_spec.direction == "min" else (-best_y if best_y is not None else None),
                        best_x=dict(best_x),
                        fraction=min(1.0, len(history) / max(config.max_evals, 1)),
                    ))
                except Exception:
                    pass
            return y

        start = time.monotonic()

        def run_scipy() -> tuple[np.ndarray, float, bool]:
            # Bound maxiter to keep function-evals near the target.
            # differential_evolution does popsize * (maxiter+1) evals roughly.
            popsize = 8
            maxiter = max(3, config.max_evals // popsize)
            result = differential_evolution(
                func=sync_eval,
                bounds=config.bounds,
                maxiter=maxiter,
                popsize=popsize,
                tol=1e-3,
                seed=config.seed,
                polish=False,
                updating="deferred",
                workers=1,  # keep it serial; each eval is already a full cascade
                init="sobol",
            )
            return result.x, float(result.fun), bool(result.success)

        try:
            x_best, y_best, success = await asyncio.to_thread(run_scipy)
            duration_ms = (time.monotonic() - start) * 1000.0
            # Reconstruct best_x and report raw (unflipped) best_y
            best_x = {var: float(x_best[i]) for i, var in enumerate(config.variables)}
            raw_best = y_best if obj_spec.direction == "min" else -y_best
            return OptimizeRunResult(
                run_id=run_id,
                status="done" if success else "done",  # scipy "success" is loose; both terminate normally
                best_x=best_x,
                best_y=float(raw_best),
                num_evals=len(history),
                duration_ms=duration_ms,
                history=history,
            )
        except Exception as e:
            logger.exception("Optimiser failed: %s", e)
            return OptimizeRunResult(
                run_id=run_id, status="failed",
                best_x={}, best_y=None,
                num_evals=len(history),
                duration_ms=(time.monotonic() - start) * 1000.0,
                history=history,
                error=str(e),
            )
