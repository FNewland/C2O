"""SpaceCDF — Design Loop Orchestrator.

Manages the iterative convergence loop that drives concurrent design.
Runs Tier 1 agents in dependency order, detects convergence, and
triggers Tier 2 analysis when the design stabilises.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.models.parameter import ParameterValue, SystemBudget, BudgetLine
from spacecdf_common.models.study import DesignIteration, MissionRequirements

from .registry import discover_agents, create_agent

logger = logging.getLogger(__name__)


@dataclass
class ConvergenceConfig:
    """Configuration for the design convergence loop."""
    max_iterations: int = 50
    convergence_threshold: float = 0.001  # 0.1% parameter change
    relaxation_factor: float = 0.7  # Under-relaxation for oscillation damping
    oscillation_detection_window: int = 5  # Iterations to detect oscillation
    tier2_on_convergence: bool = True


@dataclass
class DesignLoopResult:
    """Result of a complete design loop execution."""
    iterations: list[DesignIteration] = field(default_factory=list)
    final_state: DesignState | None = None
    converged: bool = False
    total_time_s: float = 0.0
    all_warnings: list[str] = field(default_factory=list)
    all_recommendations: list[str] = field(default_factory=list)
    budgets: dict[str, SystemBudget] = field(default_factory=dict)
    agent_results: dict[str, AgentResult] = field(default_factory=dict)
    conflicts: list = field(default_factory=list)  # list[CrossDomainConflict]


class DesignLoopOrchestrator:
    """Orchestrates the iterative concurrent design loop.

    The loop works as follows:
    1. Initialise design state from mission requirements
    2. Topologically sort agents by dependencies
    3. Execute Tier 1 agents in order
    4. Check for convergence (parameter deltas < threshold)
    5. If oscillation detected, apply under-relaxation
    6. When converged, run Tier 2 analysis agents
    7. Return complete result with budgets and recommendations
    """

    def __init__(self, config: ConvergenceConfig | None = None):
        self.config = config or ConvergenceConfig()
        self._agents: dict[str, DesignAgent] = {}
        self._execution_order: list[str] = []

    def initialise_agents(self, agent_names: list[str] | None = None) -> None:
        """Discover and instantiate design agents."""
        available = discover_agents()
        if agent_names:
            names = [n for n in agent_names if n in available]
        else:
            names = list(available.keys())

        self._agents = {}
        for name in names:
            try:
                self._agents[name] = create_agent(name)
            except Exception as e:
                logger.warning("Failed to create agent %s: %s", name, e)

        self._execution_order = self._topological_sort()
        logger.info("Agent execution order: %s", self._execution_order)

    def _topological_sort(self) -> list[str]:
        """Sort agents by tier then by dependency order within each tier."""
        # Separate by tier
        tier1 = {n: a for n, a in self._agents.items() if a.tier == 1}
        tier2 = {n: a for n, a in self._agents.items() if a.tier == 2}
        tier3 = {n: a for n, a in self._agents.items() if a.tier == 3}

        # Topological sort within tier 1 (Kahn's algorithm)
        sorted_t1 = self._kahn_sort(tier1)
        sorted_t2 = list(tier2.keys())
        sorted_t3 = list(tier3.keys())

        return sorted_t1 + sorted_t2 + sorted_t3

    def _kahn_sort(self, agents: dict[str, DesignAgent]) -> list[str]:
        """Kahn's algorithm for topological sorting of agents by dependencies."""
        in_degree: dict[str, int] = {name: 0 for name in agents}
        graph: dict[str, list[str]] = {name: [] for name in agents}

        for name, agent in agents.items():
            for dep in agent.dependencies():
                if dep in agents:
                    graph[dep].append(name)
                    in_degree[name] += 1

        queue = [n for n, d in in_degree.items() if d == 0]
        result = []
        while queue:
            queue.sort()  # Deterministic ordering
            node = queue.pop(0)
            result.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Handle cycles (shouldn't happen but be safe)
        remaining = [n for n in agents if n not in result]
        if remaining:
            logger.warning("Circular dependencies detected among agents: %s", remaining)
            result.extend(remaining)

        return result

    async def run(
        self,
        requirements: MissionRequirements,
        initial_state: DesignState | None = None,
        knowledge_base: object | None = None,
    ) -> DesignLoopResult:
        """Execute the full design convergence loop.

        Args:
            requirements: Mission requirements driving the design.
            initial_state: Optional pre-populated design state.
            knowledge_base: Knowledge base for component lookups.

        Returns:
            DesignLoopResult with converged design and budgets.
        """
        start_time = time.monotonic()
        result = DesignLoopResult()

        # Initialise agents if not done
        if not self._agents:
            self.initialise_agents()

        # Initialise design state
        state = initial_state or DesignState(
            requirements=requirements.model_dump(),
            knowledge_base=knowledge_base,
        )

        # Seed state from requirements
        self._seed_from_requirements(state, requirements)

        # Parameter history for oscillation detection
        param_history: list[dict[str, float]] = []

        # Track unique warnings to avoid duplicates across iterations
        seen_warnings: set[str] = set()

        # --- Convergence loop ---
        for iteration in range(1, self.config.max_iterations + 1):
            max_delta = 0.0
            iter_warnings: list[str] = []
            prev_values = {
                pid: p.value for pid, p in state.parameters.items()
                if isinstance(p.value, (int, float))
            }

            # Execute Tier 1 agents in order
            tier1_names = [n for n in self._execution_order if self._agents[n].tier == 1]
            for agent_name in tier1_names:
                agent = self._agents[agent_name]
                try:
                    agent_result = await agent.execute(state)
                    result.agent_results[agent_name] = agent_result

                    # Apply under-relaxation if oscillation detected
                    if iteration > self.config.oscillation_detection_window:
                        self._apply_relaxation(agent_result, state)

                    changed = state.update(agent_result)
                    iter_warnings.extend(agent_result.warnings)

                    # Track max parameter delta
                    for pid in changed:
                        p = state.get_param(pid)
                        if p and isinstance(p.value, (int, float)):
                            old_val = prev_values.get(pid, 0)
                            if old_val != 0:
                                delta = abs((p.value - old_val) / old_val)
                            else:
                                delta = abs(p.value) if p.value != 0 else 0
                            max_delta = max(max_delta, delta)

                except Exception as e:
                    logger.error("Agent %s failed: %s", agent_name, e)
                    iter_warnings.append(f"Agent {agent_name} failed: {e}")

            # Record iteration
            param_snapshot = {
                pid: p.value for pid, p in state.parameters.items()
                if isinstance(p.value, (int, float))
            }
            param_history.append(param_snapshot)

            iteration_record = DesignIteration(
                iteration=iteration,
                max_parameter_delta=max_delta,
                converged=max_delta < self.config.convergence_threshold,
                budgets_closed=False,  # Will check after convergence
                warnings=iter_warnings,
                parameter_snapshot=param_snapshot,
            )
            result.iterations.append(iteration_record)
            for w in iter_warnings:
                if w not in seen_warnings:
                    result.all_warnings.append(w)
                    seen_warnings.add(w)

            logger.info(
                "Iteration %d: max_delta=%.6f, warnings=%d",
                iteration, max_delta, len(iter_warnings)
            )

            # Check convergence
            if max_delta < self.config.convergence_threshold and iteration > 1:
                result.converged = True
                logger.info("Design converged after %d iterations", iteration)
                break

        # --- Post-convergence: Tier 2 agents ---
        if result.converged and self.config.tier2_on_convergence:
            tier2_names = [n for n in self._execution_order if self._agents[n].tier == 2]
            for agent_name in tier2_names:
                agent = self._agents[agent_name]
                try:
                    agent_result = await agent.execute(state)
                    result.agent_results[agent_name] = agent_result
                    state.update(agent_result)
                    result.all_warnings.extend(agent_result.warnings)
                    result.all_recommendations.extend(agent_result.recommendations)
                    # Extract conflicts from the conflict detection agent
                    if agent_name == "conflicts" and hasattr(agent_result, '_conflicts'):
                        result.conflicts = agent_result._conflicts
                except Exception as e:
                    logger.error("Tier 2 agent %s failed: %s", agent_name, e)

        # Build system budgets
        result.budgets = self._build_budgets(state, requirements)

        # Check budget closure
        budgets_closed = all(
            b.status.value in ("green", "amber")
            for b in result.budgets.values()
        )
        if result.iterations:
            result.iterations[-1].budgets_closed = budgets_closed

        result.final_state = state
        result.total_time_s = time.monotonic() - start_time

        return result

    def _seed_from_requirements(self, state: DesignState, req: MissionRequirements) -> None:
        """Populate initial design state parameters from mission requirements."""
        # Orbit
        state._parameters["orbit.altitude_km"] = ParameterValue(
            id="orbit.altitude_km", name="Orbital Altitude", value=req.orbit.altitude_km,
            unit="km", domain="orbit", source="requirement", confidence=1.0, margin_percent=0,
        )
        state._parameters["orbit.inclination_deg"] = ParameterValue(
            id="orbit.inclination_deg", name="Inclination", value=req.orbit.inclination_deg,
            unit="deg", domain="orbit", source="requirement", confidence=1.0, margin_percent=0,
        )
        state._parameters["mission.duration_years"] = ParameterValue(
            id="mission.duration_years", name="Mission Duration", value=req.design_lifetime_years,
            unit="years", domain="mission", source="requirement", confidence=1.0, margin_percent=0,
        )
        state._parameters["mission.spacecraft_class"] = ParameterValue(
            id="mission.spacecraft_class", name="Spacecraft Class", value=req.spacecraft_class,
            unit="", domain="mission", source="requirement", confidence=1.0, margin_percent=0,
        )

        # Payload requirements
        for i, payload in enumerate(req.payloads):
            prefix = f"payload.{i}"
            state._parameters[f"{prefix}.mass_kg"] = ParameterValue(
                id=f"{prefix}.mass_kg", name=f"Payload {payload.name} Mass", value=payload.mass_kg,
                unit="kg", domain="payload", source="requirement", confidence=1.0, margin_percent=10,
            )
            state._parameters[f"{prefix}.power_w"] = ParameterValue(
                id=f"{prefix}.power_w", name=f"Payload {payload.name} Power", value=payload.power_w,
                unit="W", domain="payload", source="requirement", confidence=1.0, margin_percent=10,
            )
            state._parameters[f"{prefix}.data_rate_mbps"] = ParameterValue(
                id=f"{prefix}.data_rate_mbps", name=f"Payload {payload.name} Data Rate",
                value=payload.data_rate_mbps, unit="Mbps", domain="payload",
                source="requirement", confidence=1.0, margin_percent=0,
            )
            state._parameters[f"{prefix}.pointing_deg"] = ParameterValue(
                id=f"{prefix}.pointing_deg", name=f"Payload {payload.name} Pointing",
                value=payload.pointing_accuracy_deg, unit="deg", domain="payload",
                source="requirement", confidence=1.0, margin_percent=0,
            )
            state._parameters[f"{prefix}.duty_cycle"] = ParameterValue(
                id=f"{prefix}.duty_cycle", name=f"Payload {payload.name} Duty Cycle",
                value=payload.duty_cycle_percent / 100.0, unit="", domain="payload",
                source="requirement", confidence=1.0, margin_percent=0,
            )
            state._parameters[f"{prefix}.data_volume_per_day_gb"] = ParameterValue(
                id=f"{prefix}.data_volume_per_day_gb",
                name=f"Payload {payload.name} Daily Data Volume",
                value=payload.data_volume_per_day_gb, unit="GB",
                domain="payload", source="requirement", confidence=1.0, margin_percent=0,
            )

    def _apply_relaxation(self, agent_result: AgentResult, state: DesignState) -> None:
        """Apply under-relaxation to dampen oscillations."""
        alpha = self.config.relaxation_factor
        for pid, param in agent_result.parameters.items():
            existing = state.get_param(pid)
            if existing and isinstance(param.value, (int, float)) and isinstance(existing.value, (int, float)):
                param.value = alpha * param.value + (1 - alpha) * existing.value

    def _build_budgets(self, state: DesignState, req: MissionRequirements) -> dict[str, SystemBudget]:
        """Build system-level budgets from current design state."""
        budgets = {}

        # Mass budget
        mass_lines = []
        for pid, param in state.parameters.items():
            if pid.endswith(".mass_kg") and isinstance(param.value, (int, float)):
                subsystem = pid.split(".")[0]
                mass_lines.append(BudgetLine(
                    subsystem=subsystem,
                    equipment=param.name,
                    nominal_value=param.value,
                    margin_percent=param.margin_percent,
                    unit="kg",
                    trl=param.trl,
                ))

        if mass_lines:
            # Determine mass allocation from LV capacity or target
            allocation = req.target_mass_kg or 500.0  # Default 500 kg if not specified
            budgets["mass"] = SystemBudget(
                budget_type="mass", lines=mass_lines, allocation=allocation, unit="kg"
            )

        # Power budget
        power_lines = []
        for pid, param in state.parameters.items():
            if pid.endswith(".power_w") and isinstance(param.value, (int, float)):
                subsystem = pid.split(".")[0]
                power_lines.append(BudgetLine(
                    subsystem=subsystem,
                    equipment=param.name,
                    nominal_value=param.value,
                    margin_percent=param.margin_percent,
                    unit="W",
                ))

        if power_lines:
            sa_power = state.get("power.sa_power_eol_w", 100.0) or 100.0
            budgets["power"] = SystemBudget(
                budget_type="power", lines=power_lines, allocation=sa_power, unit="W"
            )

        # Cost budget
        cost_lines = []
        for pid, param in state.parameters.items():
            if pid.endswith(".cost_keur") and isinstance(param.value, (int, float)):
                subsystem = pid.split(".")[0]
                cost_lines.append(BudgetLine(
                    subsystem=subsystem,
                    equipment=param.name,
                    nominal_value=param.value,
                    margin_percent=10.0,
                    unit="kEUR",
                ))

        if cost_lines:
            allocation = (req.target_cost_meur or 50.0) * 1000  # Convert MEUR to kEUR
            budgets["cost"] = SystemBudget(
                budget_type="cost", lines=cost_lines, allocation=allocation, unit="kEUR"
            )

        return budgets
