"""SpaceCDF — Design Agent base class.

All engineering domain agents implement this interface. The orchestrator
calls agents in dependency order during each design convergence loop.

Inspired by SMO's SubsystemModel ABC but adapted for design (not simulation):
- execute() replaces tick() — computes steady-state outputs from current inputs
- No time-stepping; agents compute design-point values
- Results include confidence, warnings, and TRL assessments
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..models.parameter import ParameterValue, TRLAssessment


@dataclass
class AgentResult:
    """Result of a design agent execution."""

    domain: str
    parameters: dict[str, ParameterValue] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    trl_assessments: list[TRLAssessment] = field(default_factory=list)
    computation_log: list[str] = field(default_factory=list)
    converged: bool = True
    confidence: float = 0.8

    def add_param(
        self,
        param_id: str,
        name: str,
        value: float | str | bool,
        unit: str = "",
        source: str = "computed",
        confidence: float = 0.8,
        margin_percent: float = 20.0,
        dependencies: list[str] | None = None,
        rationale: str = "",
        trl: int | None = None,
        heritage: str | None = None,
    ) -> None:
        """Convenience method to add a parameter to the result."""
        self.parameters[param_id] = ParameterValue(
            id=param_id,
            name=name,
            value=value,
            unit=unit,
            domain=self.domain,
            source=source,
            confidence=confidence,
            margin_percent=margin_percent,
            dependencies=dependencies or [],
            updated_by=f"agent:{self.domain}",
            rationale=rationale,
            trl=trl,
            heritage=heritage,
        )

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_recommendation(self, msg: str) -> None:
        self.recommendations.append(msg)

    def log(self, msg: str) -> None:
        self.computation_log.append(msg)


class DesignState:
    """Snapshot of the current design state, passed to agents for computation.

    Provides read access to all parameters from all domains, plus
    mission requirements and knowledge base lookups.
    """

    def __init__(
        self,
        parameters: dict[str, ParameterValue] | None = None,
        requirements: dict[str, Any] | None = None,
        knowledge_base: Any = None,
    ):
        self._parameters = parameters or {}
        self._requirements = requirements or {}
        self._kb = knowledge_base

    def get(self, param_id: str, default: float | None = None) -> float | None:
        """Get a parameter value by ID."""
        p = self._parameters.get(param_id)
        if p is not None:
            return p.value if isinstance(p.value, (int, float)) else default
        return default

    def get_param(self, param_id: str) -> ParameterValue | None:
        """Get the full ParameterValue object."""
        return self._parameters.get(param_id)

    def get_requirement(self, key: str, default: Any = None) -> Any:
        """Get a mission requirement by dot-path key."""
        parts = key.split(".")
        obj = self._requirements
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            else:
                return default
            if obj is None:
                return default
        return obj

    @property
    def parameters(self) -> dict[str, ParameterValue]:
        return self._parameters

    @property
    def requirements(self) -> dict[str, Any]:
        return self._requirements

    @property
    def kb(self) -> Any:
        return self._kb

    def update(self, result: AgentResult) -> set[str]:
        """Merge agent results into the design state. Returns set of changed parameter IDs.

        Sticky parameters (source = KB_COMPONENT, POSITION_OVERRIDE, REQUIREMENT)
        are NOT overwritten by agents during re-convergence. This ensures that
        human equipment selections and overrides persist through design iterations.
        """
        changed = set()
        for param_id, param in result.parameters.items():
            existing = self._parameters.get(param_id)
            # Don't overwrite sticky parameters (human selections, requirements)
            if existing is not None and existing.source.is_sticky:
                continue
            if existing is None or existing.value != param.value:
                changed.add(param_id)
            self._parameters[param_id] = param
        return changed


class DesignAgent(ABC):
    """Abstract base class for all SpaceCDF design agents.

    Agents are stateless functions: given a DesignState, they produce
    an AgentResult with updated parameters for their domain.
    """

    @property
    @abstractmethod
    def domain(self) -> str:
        """Engineering domain identifier (e.g. 'orbit', 'power', 'thermal')."""
        ...

    @property
    @abstractmethod
    def tier(self) -> int:
        """Agent tier: 1=compute, 2=analysis, 3=advisory."""
        ...

    @abstractmethod
    def input_parameters(self) -> list[str]:
        """Parameter IDs this agent reads from the design state."""
        ...

    @abstractmethod
    def output_parameters(self) -> list[str]:
        """Parameter IDs this agent writes to the design state."""
        ...

    @abstractmethod
    async def execute(self, state: DesignState) -> AgentResult:
        """Compute outputs from current design state.

        This is the core method. For Tier 1 agents, this runs deterministic
        physics calculations. For Tier 2, it applies rule-based analysis.
        For Tier 3, it generates options for human review.
        """
        ...

    def dependencies(self) -> list[str]:
        """Domain names this agent depends on (for topological sort).

        By default, inferred from input_parameters — any parameter whose
        domain differs from self.domain creates a dependency on that domain.
        """
        deps = set()
        for pid in self.input_parameters():
            parts = pid.split(".")
            if len(parts) >= 2 and parts[1] != self.domain:
                deps.add(parts[1])
        return list(deps)
