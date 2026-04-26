"""SpaceCDF — Selective Re-convergence Service.

When a parameter changes (e.g. engineer selects equipment), only the
affected downstream agents need to re-run, not the entire loop.

This service builds a reverse dependency index from agent declarations,
identifies affected agents, topologically sorts them, and executes only
the minimum set needed to propagate the change.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.models.parameter import ParameterValue

from spacecdf_agents.registry import discover_agents, create_agent

logger = logging.getLogger(__name__)

MAX_CASCADE_ROUNDS = 10
CONVERGENCE_THRESHOLD = 0.001


@dataclass
class ReconvergenceResult:
    """Result of a selective re-convergence."""
    changed_params: set[str] = field(default_factory=set)
    agents_executed: list[str] = field(default_factory=list)
    cascade_rounds: int = 0
    total_time_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)
    conflicts: list = field(default_factory=list)


class SelectiveReconvergence:
    """Runs only the agents affected by a parameter change."""

    def __init__(self):
        self._agents: dict[str, DesignAgent] = {}
        self._param_to_agents: dict[str, set[str]] = {}  # param_id -> agent names that read it
        self._domain_to_agents: dict[str, set[str]] = {}  # domain -> agent names that depend on it

    def initialise(self) -> None:
        """Build the reverse dependency index from agent declarations."""
        available = discover_agents()
        self._agents = {}
        for name, cls in available.items():
            self._agents[name] = cls()

        # Build reverse indices
        self._param_to_agents = {}
        self._domain_to_agents = {}

        for name, agent in self._agents.items():
            for param_id in agent.input_parameters():
                if param_id not in self._param_to_agents:
                    self._param_to_agents[param_id] = set()
                self._param_to_agents[param_id].add(name)

            for dep_domain in agent.dependencies():
                if dep_domain not in self._domain_to_agents:
                    self._domain_to_agents[dep_domain] = set()
                self._domain_to_agents[dep_domain].add(name)

    def _find_affected_agents(self, changed_param_ids: set[str]) -> set[str]:
        """Find all agents that need to re-run due to parameter changes."""
        affected = set()

        for param_id in changed_param_ids:
            # Direct parameter dependency
            if param_id in self._param_to_agents:
                affected.update(self._param_to_agents[param_id])

            # Domain-level dependency
            domain = param_id.split(".")[0]
            if domain in self._domain_to_agents:
                affected.update(self._domain_to_agents[domain])

        # Only include Tier 1 agents in cascade; Tier 2 run once at end
        return {name for name in affected if self._agents[name].tier == 1}

    def _topological_sort(self, agent_names: set[str]) -> list[str]:
        """Sort a subset of agents by dependency order."""
        in_degree: dict[str, int] = {n: 0 for n in agent_names}
        graph: dict[str, list[str]] = {n: [] for n in agent_names}

        for name in agent_names:
            agent = self._agents[name]
            for dep in agent.dependencies():
                # Find agents in our subset that provide this dependency
                for other in agent_names:
                    if self._agents[other].domain == dep:
                        graph[other].append(name)
                        in_degree[name] += 1

        queue = sorted([n for n, d in in_degree.items() if d == 0])
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    queue.sort()

        remaining = [n for n in agent_names if n not in result]
        result.extend(sorted(remaining))
        return result

    async def reconverge(
        self,
        state: DesignState,
        changed_param_ids: set[str],
    ) -> ReconvergenceResult:
        """Run selective re-convergence for the given parameter changes.

        Only agents affected by the changed parameters are executed.
        Cascades propagate until no more changes occur or max rounds reached.
        Tier 2 agents (conflicts, cost, risk, trl) run once at the end.
        """
        if not self._agents:
            self.initialise()

        start = time.monotonic()
        result = ReconvergenceResult()
        all_changed = set(changed_param_ids)

        # Cascade loop
        current_changes = set(changed_param_ids)
        for round_num in range(1, MAX_CASCADE_ROUNDS + 1):
            affected = self._find_affected_agents(current_changes)
            if not affected:
                break

            execution_order = self._topological_sort(affected)
            round_changes: set[str] = set()

            for agent_name in execution_order:
                agent = self._agents[agent_name]
                try:
                    agent_result = await agent.execute(state)
                    new_changes = state.update(agent_result)
                    round_changes.update(new_changes)
                    result.agents_executed.append(agent_name)
                    result.warnings.extend(agent_result.warnings)
                except Exception as e:
                    logger.error("Reconvergence: agent %s failed: %s", agent_name, e)

            all_changed.update(round_changes)
            result.cascade_rounds = round_num

            if not round_changes:
                break  # Converged
            current_changes = round_changes

        # Run Tier 2 agents once at end
        tier2_names = sorted(n for n, a in self._agents.items() if a.tier == 2)
        for agent_name in tier2_names:
            agent = self._agents[agent_name]
            try:
                agent_result = await agent.execute(state)
                state.update(agent_result)
                result.agents_executed.append(agent_name)
                result.warnings.extend(agent_result.warnings)
                # Extract conflicts
                if hasattr(agent_result, '_conflicts'):
                    result.conflicts = agent_result._conflicts
            except Exception as e:
                logger.error("Reconvergence Tier 2: agent %s failed: %s", agent_name, e)

        result.changed_params = all_changed
        result.total_time_ms = (time.monotonic() - start) * 1000
        return result
