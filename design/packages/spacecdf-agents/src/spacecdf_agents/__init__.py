"""SpaceCDF Agents — Design agents and orchestration engine."""

__version__ = "0.1.0"

from .orchestrator import DesignLoopOrchestrator, ConvergenceConfig, DesignLoopResult
from .registry import discover_agents, create_agent, list_agents

__all__ = [
    "DesignLoopOrchestrator", "ConvergenceConfig", "DesignLoopResult",
    "discover_agents", "create_agent", "list_agents",
]
