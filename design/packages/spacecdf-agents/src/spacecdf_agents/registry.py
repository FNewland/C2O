"""SpaceCDF — Agent Registry.

Discovers DesignAgent implementations via Python entry points
(group: 'spacecdf.agents'), with fallback to direct imports.
Adapted from SMO's model registry pattern.
"""
from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import Type

from spacecdf_common.agents.base import DesignAgent

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "spacecdf.agents"

_registry: dict[str, Type[DesignAgent]] = {}


def _register_builtins() -> None:
    """Directly import and register built-in agents."""
    builtins = {
        "orbit": "spacecdf_agents.tier1.orbit.OrbitAgent",
        "power": "spacecdf_agents.tier1.power.PowerAgent",
        "mass": "spacecdf_agents.tier1.mass.MassAgent",
        "thermal": "spacecdf_agents.tier1.thermal.ThermalAgent",
        "link": "spacecdf_agents.tier1.link.LinkAgent",
        "data": "spacecdf_agents.tier1.data.DataAgent",
        "aocs": "spacecdf_agents.tier1.aocs.AOCSAgent",
        "propulsion": "spacecdf_agents.tier1.propulsion.PropulsionAgent",
        "structure": "spacecdf_agents.tier1.structure.StructureAgent",
        "systems": "spacecdf_agents.tier2.systems.SystemsAgent",
        "cost": "spacecdf_agents.tier2.cost.CostAgent",
        "risk": "spacecdf_agents.tier2.risk.RiskAgent",
        "trl": "spacecdf_agents.tier2.trl.TRLAgent",
        "conflicts": "spacecdf_agents.tier2.conflicts.ConflictDetectionAgent",
        "debris": "spacecdf_agents.tier2.debris.DebrisComplianceAgent",
        "sustainability": "spacecdf_agents.tier2.sustainability.SustainabilityAgent",
        "radiation": "spacecdf_agents.tier2.radiation.RadiationAgent",
        "volume": "spacecdf_agents.tier2.volume.VolumeAgent",
        "reliability": "spacecdf_agents.tier2.reliability.ReliabilityAgent",
        "community": "spacecdf_agents.tier2.community.CommunityImpactAgent",
    }
    for name, qualname in builtins.items():
        module_path, class_name = qualname.rsplit(".", 1)
        try:
            import importlib
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            if isinstance(cls, type) and issubclass(cls, DesignAgent):
                _registry[name] = cls
                logger.debug("Registered builtin agent: %s -> %s", name, class_name)
        except Exception as e:
            logger.warning("Failed to import builtin agent %s: %s", name, e)


def discover_agents() -> dict[str, Type[DesignAgent]]:
    """Scan entry points and populate the registry."""
    global _registry
    eps = entry_points()
    group = eps.select(group=ENTRY_POINT_GROUP) if hasattr(eps, 'select') else eps.get(ENTRY_POINT_GROUP, [])
    for ep in group:
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, DesignAgent):
                _registry[ep.name] = cls
                logger.debug("Registered agent: %s -> %s", ep.name, cls.__name__)
        except Exception as e:
            logger.warning("Failed to load agent entry point %s: %s", ep.name, e)
    if not _registry:
        logger.info("No entry points found, loading built-in agents")
        _register_builtins()
    return dict(_registry)


def get_agent_class(name: str) -> Type[DesignAgent] | None:
    if not _registry:
        discover_agents()
    return _registry.get(name)


def create_agent(name: str) -> DesignAgent:
    cls = get_agent_class(name)
    if cls is None:
        raise ValueError(f"Unknown agent: {name!r}. Available: {list(_registry.keys())}")
    return cls()


def list_agents() -> list[str]:
    if not _registry:
        discover_agents()
    return list(_registry.keys())
