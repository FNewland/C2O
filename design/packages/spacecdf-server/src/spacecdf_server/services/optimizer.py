"""SpaceCDF — Design optimiser (Phase 5B/5C).

Single-objective via scipy.optimize.differential_evolution and multi-objective
Pareto via a built-in NSGA-II implementation. Both run inside asyncio.to_thread
so the event loop stays responsive.

Design choices:
  - scipy is called inside asyncio.to_thread — synchronous under the hood,
    but non-blocking from the API's perspective.
  - Progress is emitted via a callback the caller supplies (used by the
    router to broadcast optimize.progress events over the session WS).
  - A per-session lock prevents two runs racing on the same base state.
  - Multi-objective uses a lightweight NSGA-II (non-dominated sort + crowding
    distance) with no external dependency beyond numpy.
"""
from __future__ import annotations

import asyncio
import logging
import random
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
    "max_mass_margin": ObjectiveSpec(
        "max_mass_margin", "Maximise mass margin",
        parameter_id="systems.mass_margin_percent", direction="max",
    ),
    "max_power_margin": ObjectiveSpec(
        "max_power_margin", "Maximise power margin",
        parameter_id="systems.power_margin_percent", direction="max",
    ),
    "max_reliability": ObjectiveSpec(
        "max_reliability", "Maximise reliability score",
        parameter_id="reliability.mission_reliability", direction="max",
    ),
    "min_data_latency": ObjectiveSpec(
        "min_data_latency", "Minimise data latency (hours)",
        parameter_id="link.data_latency_hours", direction="min",
    ),
    "max_trl": ObjectiveSpec(
        "max_trl", "Maximise composite TRL",
        parameter_id="systems.composite_trl", direction="max",
    ),
    "max_debris_compliance": ObjectiveSpec(
        "max_debris_compliance", "Maximise debris compliance",
        parameter_id="debris.compliance_score", direction="max",
    ),
}

# Canonical design variables with sane default bounds — the UI will offer
# these as checkboxes; the user overrides bounds per run.
DEFAULT_DESIGN_VARIABLES: dict[str, tuple[float, float]] = {
    "orbit.altitude_km":                  (300.0, 900.0),
    "orbit.inclination_deg":              (0.0,   98.0),
    "payload.power_w":                    (5.0,  150.0),
    "payload.data_volume_per_day_gb":     (0.1,  50.0),
    "payload.duty_cycle_percent":         (5.0,  100.0),
    "power.sa_margin_percent":            (10.0, 40.0),
    "power.battery_dod_percent":          (20.0, 80.0),
    "link.downlink_data_rate_mbps":       (10.0, 1000.0),
    "link.frequency_ghz":                 (2.0,  26.0),
    "thermal.radiator_area_m2":           (0.01, 0.5),
    "aocs.pointing_accuracy_deg":         (0.01, 5.0),
    "propulsion.total_dv_ms":             (0.0,  200.0),
}

# Explicit constraints for feasibility checking
@dataclass
class DesignConstraint:
    """A constraint the optimizer must satisfy."""
    parameter_id: str
    operator: str  # ">=", "<=", "=="
    threshold: float
    name: str
    penalty_weight: float = 1e6  # Penalty per unit of violation

DEFAULT_CONSTRAINTS: list[DesignConstraint] = [
    DesignConstraint("systems.mass_margin_percent", ">=", 0.0, "Positive mass margin"),
    DesignConstraint("systems.power_margin_percent", ">=", 0.0, "Positive power margin"),
    DesignConstraint("debris.compliance_score", ">=", 50.0, "Debris compliance"),
]


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
    pareto_front: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass
class MultiObjectiveConfig:
    """Config for NSGA-II multi-objective runs."""
    variables: list[str]
    bounds: list[tuple[float, float]]
    objectives: list[str]             # keys into OBJECTIVES
    pop_size: int = 40
    n_generations: int = 30
    crossover_prob: float = 0.9
    mutation_prob: float | None = None  # defaults to 1/n_vars
    seed: int | None = 42


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


# ===================================================================
# Multi-objective NSGA-II
# ===================================================================

def _non_dominated_sort(fitnesses: np.ndarray) -> list[list[int]]:
    """Fast non-dominated sort (Deb et al. 2002).

    Args:
        fitnesses: (N, M) array — N individuals, M objectives (all minimised).

    Returns:
        List of fronts, each a list of individual indices.
    """
    n = len(fitnesses)
    domination_count = np.zeros(n, dtype=int)
    dominated_set: list[list[int]] = [[] for _ in range(n)]
    fronts: list[list[int]] = [[]]

    for p in range(n):
        for q in range(p + 1, n):
            diff = fitnesses[p] - fitnesses[q]
            if np.all(diff <= 0) and np.any(diff < 0):
                # p dominates q
                dominated_set[p].append(q)
                domination_count[q] += 1
            elif np.all(diff >= 0) and np.any(diff > 0):
                # q dominates p
                dominated_set[q].append(p)
                domination_count[p] += 1

    for i in range(n):
        if domination_count[i] == 0:
            fronts[0].append(i)

    i = 0
    while fronts[i]:
        next_front: list[int] = []
        for p in fronts[i]:
            for q in dominated_set[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    return [f for f in fronts if f]


def _crowding_distance(fitnesses: np.ndarray, front: list[int]) -> np.ndarray:
    """Compute crowding distance for individuals in a front."""
    n = len(front)
    if n <= 2:
        return np.full(n, float("inf"))

    dists = np.zeros(n)
    f_front = fitnesses[front]
    m = f_front.shape[1]

    for obj in range(m):
        order = np.argsort(f_front[:, obj])
        dists[order[0]] = float("inf")
        dists[order[-1]] = float("inf")
        obj_range = f_front[order[-1], obj] - f_front[order[0], obj]
        if obj_range < 1e-12:
            continue
        for k in range(1, n - 1):
            dists[order[k]] += (f_front[order[k + 1], obj] - f_front[order[k - 1], obj]) / obj_range

    return dists


def _sbx_crossover(
    p1: np.ndarray, p2: np.ndarray, bounds: np.ndarray, eta: float = 20.0
) -> tuple[np.ndarray, np.ndarray]:
    """Simulated Binary Crossover (SBX)."""
    c1, c2 = p1.copy(), p2.copy()
    for i in range(len(p1)):
        if abs(p1[i] - p2[i]) < 1e-14:
            continue
        u = random.random()
        if u <= 0.5:
            beta = (2.0 * u) ** (1.0 / (eta + 1.0))
        else:
            beta = (1.0 / (2.0 * (1.0 - u))) ** (1.0 / (eta + 1.0))
        c1[i] = 0.5 * ((1 + beta) * p1[i] + (1 - beta) * p2[i])
        c2[i] = 0.5 * ((1 - beta) * p1[i] + (1 + beta) * p2[i])
        c1[i] = np.clip(c1[i], bounds[i, 0], bounds[i, 1])
        c2[i] = np.clip(c2[i], bounds[i, 0], bounds[i, 1])
    return c1, c2


def _polynomial_mutation(
    x: np.ndarray, bounds: np.ndarray, prob: float, eta: float = 20.0
) -> np.ndarray:
    """Polynomial mutation."""
    y = x.copy()
    for i in range(len(x)):
        if random.random() > prob:
            continue
        delta_max = bounds[i, 1] - bounds[i, 0]
        if delta_max < 1e-14:
            continue
        delta = (x[i] - bounds[i, 0]) / delta_max
        u = random.random()
        if u < 0.5:
            deltaq = (2.0 * u + (1.0 - 2.0 * u) * (1.0 - delta) ** (eta + 1.0)) ** (1.0 / (eta + 1.0)) - 1.0
        else:
            deltaq = 1.0 - (2.0 * (1.0 - u) + 2.0 * (u - 0.5) * delta ** (eta + 1.0)) ** (1.0 / (eta + 1.0))
        y[i] = x[i] + deltaq * delta_max
        y[i] = np.clip(y[i], bounds[i, 0], bounds[i, 1])
    return y


async def run_multi_objective(
    *,
    run_id: int,
    session_id: str,
    base_state: DesignState,
    config: MultiObjectiveConfig,
    progress_cb: Callable[[OptimizeProgress], None] | None = None,
) -> OptimizeRunResult:
    """Run NSGA-II multi-objective optimisation.

    Returns the Pareto front as a list of {x: {...}, objectives: {...}} dicts.
    """
    lock = _get_session_lock(session_id)
    async with lock:
        evaluator = CandidateEvaluator()

        obj_specs = []
        for key in config.objectives:
            spec = OBJECTIVES.get(key)
            if spec is None:
                return OptimizeRunResult(
                    run_id=run_id, status="failed",
                    best_x={}, best_y=None, num_evals=0, duration_ms=0.0,
                    history=[], error=f"Unknown objective: {key}",
                )
            obj_specs.append(spec)

        n_vars = len(config.variables)
        n_obj = len(obj_specs)
        bounds_arr = np.array(config.bounds)
        mutation_prob = config.mutation_prob or (1.0 / n_vars)

        history: list[dict[str, Any]] = []
        eval_count = [0]

        def sync_evaluate(x: np.ndarray) -> np.ndarray:
            """Evaluate one individual, return objective vector (all minimised)."""
            overrides = {var: float(x[i]) for i, var in enumerate(config.variables)}
            try:
                result: EvaluationResult = asyncio.run(
                    evaluator.evaluate(base_state, overrides, output_params=None)
                )
            except Exception as e:
                logger.warning("NSGA-II eval failed at x=%s: %s", overrides, e)
                return np.full(n_obj, 1e18)

            obj_vals = np.zeros(n_obj)
            for j, spec in enumerate(obj_specs):
                raw = result.parameters.get(spec.parameter_id)
                if raw is None or not np.isfinite(raw):
                    obj_vals[j] = 1e18
                elif spec.direction == "max":
                    obj_vals[j] = -float(raw)
                else:
                    obj_vals[j] = float(raw)
                # Penalty for critical conflicts
                if result.critical_conflicts_count > 0:
                    obj_vals[j] += 1e6 * result.critical_conflicts_count

            eval_count[0] += 1
            history.append({
                "eval_n": eval_count[0],
                "objectives": {spec.key: float(obj_vals[j]) for j, spec in enumerate(obj_specs)},
                "x": overrides,
                "conflicts": result.conflicts_count,
            })
            return obj_vals

        start = time.monotonic()
        last_emit = [0.0]

        def run_nsga2() -> tuple[np.ndarray, np.ndarray]:
            """Synchronous NSGA-II main loop."""
            rng = random.Random(config.seed)
            random.seed(config.seed)

            # Initialise population (Latin hypercube-ish)
            pop = np.zeros((config.pop_size, n_vars))
            for i in range(config.pop_size):
                for j in range(n_vars):
                    pop[i, j] = bounds_arr[j, 0] + rng.random() * (bounds_arr[j, 1] - bounds_arr[j, 0])

            # Evaluate initial population
            fit = np.array([sync_evaluate(pop[i]) for i in range(config.pop_size)])

            for gen in range(config.n_generations):
                # Generate offspring
                offspring_x = []
                for _ in range(config.pop_size // 2):
                    # Tournament selection
                    i1, i2 = rng.sample(range(config.pop_size), 2)
                    i3, i4 = rng.sample(range(config.pop_size), 2)
                    p1 = pop[i1] if rng.random() < 0.5 else pop[i2]
                    p2 = pop[i3] if rng.random() < 0.5 else pop[i4]

                    if rng.random() < config.crossover_prob:
                        c1, c2 = _sbx_crossover(p1, p2, bounds_arr)
                    else:
                        c1, c2 = p1.copy(), p2.copy()

                    c1 = _polynomial_mutation(c1, bounds_arr, mutation_prob)
                    c2 = _polynomial_mutation(c2, bounds_arr, mutation_prob)
                    offspring_x.extend([c1, c2])

                offspring_x = offspring_x[:config.pop_size]
                offspring_fit = np.array([sync_evaluate(x) for x in offspring_x])

                # Combine parent + offspring
                combined_x = np.vstack([pop, np.array(offspring_x)])
                combined_fit = np.vstack([fit, offspring_fit])

                # Non-dominated sort + crowding to select next generation
                fronts = _non_dominated_sort(combined_fit)
                new_pop = []
                new_fit = []
                for front in fronts:
                    if len(new_pop) + len(front) <= config.pop_size:
                        for idx in front:
                            new_pop.append(combined_x[idx])
                            new_fit.append(combined_fit[idx])
                    else:
                        remaining = config.pop_size - len(new_pop)
                        cd = _crowding_distance(combined_fit, front)
                        sorted_by_cd = sorted(range(len(front)), key=lambda k: cd[k], reverse=True)
                        for k in sorted_by_cd[:remaining]:
                            new_pop.append(combined_x[front[k]])
                            new_fit.append(combined_fit[front[k]])
                        break

                pop = np.array(new_pop)
                fit = np.array(new_fit)

                # Progress callback
                now = time.monotonic()
                if progress_cb and (now - last_emit[0]) > 0.2:
                    last_emit[0] = now
                    try:
                        progress_cb(OptimizeProgress(
                            run_id=run_id,
                            evaluations=eval_count[0],
                            max_evals=config.pop_size * config.n_generations * 2,
                            best_y=None,
                            best_x=None,
                            fraction=(gen + 1) / config.n_generations,
                            status="running",
                        ))
                    except Exception:
                        pass

            return pop, fit

        try:
            final_pop, final_fit = await asyncio.to_thread(run_nsga2)
            duration_ms = (time.monotonic() - start) * 1000.0

            # Extract Pareto front (first front from final population)
            fronts = _non_dominated_sort(final_fit)
            pareto_indices = fronts[0] if fronts else []

            pareto_front: list[dict[str, Any]] = []
            for idx in pareto_indices:
                x_dict = {var: float(final_pop[idx, i]) for i, var in enumerate(config.variables)}
                obj_dict = {}
                for j, spec in enumerate(obj_specs):
                    raw = final_fit[idx, j]
                    # Un-flip max objectives for display
                    obj_dict[spec.key] = float(-raw) if spec.direction == "max" else float(raw)
                pareto_front.append({"x": x_dict, "objectives": obj_dict})

            # Sort pareto front by first objective for consistency
            pareto_front.sort(key=lambda p: list(p["objectives"].values())[0])

            # Pick the "best" as the knee point (min sum of normalised objectives)
            best_x: dict[str, float] = {}
            best_y: float | None = None
            if pareto_front:
                obj_matrix = np.array([[p["objectives"][s.key] for s in obj_specs] for p in pareto_front])
                ranges = obj_matrix.max(axis=0) - obj_matrix.min(axis=0)
                ranges[ranges < 1e-12] = 1.0
                normalised = (obj_matrix - obj_matrix.min(axis=0)) / ranges
                knee_idx = int(np.argmin(normalised.sum(axis=1)))
                best_x = pareto_front[knee_idx]["x"]
                best_y = list(pareto_front[knee_idx]["objectives"].values())[0]

            return OptimizeRunResult(
                run_id=run_id,
                status="done",
                best_x=best_x,
                best_y=best_y,
                num_evals=eval_count[0],
                duration_ms=duration_ms,
                history=history,
                pareto_front=pareto_front,
            )

        except Exception as e:
            logger.exception("NSGA-II failed: %s", e)
            return OptimizeRunResult(
                run_id=run_id, status="failed",
                best_x={}, best_y=None,
                num_evals=eval_count[0],
                duration_ms=(time.monotonic() - start) * 1000.0,
                history=history,
                error=str(e),
            )
