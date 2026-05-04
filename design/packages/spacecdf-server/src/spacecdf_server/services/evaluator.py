"""SpaceCDF — Candidate evaluator.

Phase 5B prerequisite. Enables snapshotting, diffing, and optimisation
by providing a single entry-point that:

  1. Deep-copies a base DesignState
  2. Applies a dict of {parameter_id: value} overrides
  3. Runs the full reconvergence cascade (Tier 1 + Tier 2)
  4. Returns a compact EvaluationResult with key numeric outputs

Invariant: the base_state is NEVER mutated. Sticky parameters on the base
(source = KB_COMPONENT, POSITION_OVERRIDE, REQUIREMENT) are preserved
through the deep copy but are not locked against the override dict — if the
caller explicitly overrides a sticky param, that's their choice (but the
*original* base_state's sticky values are untouched).

This helper is what the optimiser (5B), validation harness (new), and
trade-study batch runner will all call.
"""
from __future__ import annotations

import copy
import logging
import time
from dataclasses import dataclass, field

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.parameter import ParameterSource, ParameterValue

from .reconvergence import SelectiveReconvergence

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Compact numeric output of a single candidate evaluation."""

    # Core design-point numbers extracted from the converged state
    parameters: dict[str, float] = field(default_factory=dict)
    # Convergence telemetry
    converged: bool = True
    cascade_rounds: int = 0
    total_time_ms: float = 0.0
    # Diagnostic
    warnings: list[str] = field(default_factory=list)
    conflicts_count: int = 0
    critical_conflicts_count: int = 0
    # Overrides actually applied (echoed for traceability)
    applied_overrides: dict[str, float] = field(default_factory=dict)
    # Invariant verification — non-empty means a bug occurred
    integrity_violations: list[str] = field(default_factory=list)


def _make_override_param(param_id: str, value: float) -> ParameterValue:
    """Build a synthetic POSITION_OVERRIDE ParameterValue for the candidate.

    Uses POSITION_OVERRIDE source so the value is sticky within the candidate
    run and won't be overwritten by agents mid-convergence.
    """
    return ParameterValue(
        id=param_id,
        name=param_id,
        value=value,
        unit="",
        domain=param_id.split(".")[0] if "." in param_id else "",
        source=ParameterSource.POSITION_OVERRIDE,
        confidence=0.9,
        margin_percent=0.0,
    )


class CandidateEvaluator:
    """Deep-copy, override, reconverge — repeatable and safe to call in a loop."""

    def __init__(self, reconv: SelectiveReconvergence | None = None):
        self._reconv = reconv or SelectiveReconvergence()
        if not self._reconv._agents:
            self._reconv.initialise()

    async def evaluate(
        self,
        base_state: DesignState,
        overrides: dict[str, float],
        output_params: list[str] | None = None,
    ) -> EvaluationResult:
        """Evaluate a candidate design.

        Args:
            base_state: The baseline DesignState. NOT mutated.
            overrides: {param_id: new_value} to apply before convergence.
            output_params: Optional whitelist of parameter IDs to extract.
                If None, returns a reasonable default set (mass, power, cost,
                link margin, etc.).

        Returns:
            EvaluationResult with the converged numeric outputs.
        """
        start = time.monotonic()

        # Fingerprint the base to verify no mutation afterwards
        base_fingerprint = _fingerprint_sticky(base_state)

        # Deep copy. DesignState holds `_parameters` dict + `_requirements` dict + `_kb` (optional).
        # Copying _parameters and _requirements is sufficient; _kb is shared (read-only).
        new_params = copy.deepcopy(base_state._parameters)  # type: ignore[attr-defined]
        new_requirements = copy.deepcopy(base_state._requirements)  # type: ignore[attr-defined]
        candidate_state = DesignState(
            parameters=new_params,
            requirements=new_requirements,
            knowledge_base=base_state._kb,  # type: ignore[attr-defined]
        )

        # Apply overrides as synthetic POSITION_OVERRIDE params
        applied: dict[str, float] = {}
        for pid, val in overrides.items():
            try:
                fval = float(val)
            except (TypeError, ValueError):
                logger.warning("Evaluator: skipping non-numeric override %s=%r", pid, val)
                continue
            new_params[pid] = _make_override_param(pid, fval)
            applied[pid] = fval

        # Reconverge with the overrides as the seed "changed" set
        changed_seed = set(applied.keys())
        recon_result = await self._reconv.reconverge(candidate_state, changed_seed)

        # Extract outputs
        if output_params is None:
            output_params = _default_output_params()

        out: dict[str, float] = {}
        for pid in output_params:
            p = candidate_state.get_param(pid)
            if p is not None and isinstance(p.value, (int, float)):
                out[pid] = float(p.value)

        # Count conflicts
        conflicts = recon_result.conflicts or []
        crit = sum(1 for c in conflicts if getattr(c, "severity", "") == "critical")

        # Integrity check — has base_state been mutated?
        violations = _verify_unchanged(base_state, base_fingerprint)

        return EvaluationResult(
            parameters=out,
            converged=(recon_result.cascade_rounds < 10),
            cascade_rounds=recon_result.cascade_rounds,
            total_time_ms=(time.monotonic() - start) * 1000,
            warnings=list(recon_result.warnings),
            conflicts_count=len(conflicts),
            critical_conflicts_count=crit,
            applied_overrides=applied,
            integrity_violations=violations,
        )


def _default_output_params() -> list[str]:
    """Canonical output parameters for trade studies / optimisation."""
    return [
        # Tier 1 — core design budgets
        "mass.dry_mass_kg",
        "mass.wet_mass_kg",
        "power.total_sunlight_w",
        "power.sa_power_eol_w",
        "power.battery_capacity_wh",
        "link.downlink_margin_db",
        "cost.total_meur",
        "cost.total_with_margin_meur",
        "orbit.delta_v_total_ms",
        "orbit.delta_v_deorbit_ms",
        "aocs.pointing_accuracy_deg",
        "thermal.max_temp_c",
        "data.generated_per_day_gb",
        "data.downlinked_per_day_gb",
        "propulsion.delta_v_total_ms",
        "propulsion.total_impulse_ns",
        "propulsion.propellant_mass_kg",
        # Tier 2 — analysis outputs
        "conflicts.count",
        "conflicts.critical",
        "conflicts.major",
        "risk.risk_score",
        "risk.high_risks",
        "risk.total_risks",
        "systems.health_score",
        "systems.mass_margin_percent",
        "systems.power_margin_percent",
        "systems.composite_trl",
        "trl.innovation_count",
        # Debris and sustainability
        "debris.lifetime_years",
        "debris.compliance_score",
        "debris.compliant_5yr",
        # Reliability
        "reliability.mission_reliability",
        "reliability.spf_count",
        # Data latency
        "link.data_latency_hours",
    ]


def _fingerprint_sticky(state: DesignState) -> dict[str, tuple]:
    """Capture (value, source) of every sticky parameter for post-run verification."""
    out: dict[str, tuple] = {}
    for pid, p in state._parameters.items():  # type: ignore[attr-defined]
        if p.source.is_sticky:
            out[pid] = (p.value, p.source.value if hasattr(p.source, "value") else str(p.source))
    return out


def _verify_unchanged(state: DesignState, fingerprint: dict[str, tuple]) -> list[str]:
    """Return list of sticky params whose values have drifted on the base state."""
    violations: list[str] = []
    for pid, (orig_val, orig_src) in fingerprint.items():
        p = state._parameters.get(pid)  # type: ignore[attr-defined]
        if p is None:
            violations.append(f"{pid}: sticky param was removed")
            continue
        cur_src = p.source.value if hasattr(p.source, "value") else str(p.source)
        if p.value != orig_val or cur_src != orig_src:
            violations.append(
                f"{pid}: sticky drift ({orig_val}/{orig_src} -> {p.value}/{cur_src})"
            )
    return violations
