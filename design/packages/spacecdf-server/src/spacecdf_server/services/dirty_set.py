"""DirtySet — per-session reactive accounting. SPINE_SPEC §4.

Replaces the fragile 'recent_edits[-20:]' heuristic with explicit tracking
of which parameters, requirements, and domains are dirty since last convergence.

Atomic consume() ensures no edits are lost between mark and convergence.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spacecdf_common.agents.base import DesignAgent


class DirtySet:
    """Thread-safe set tracking dirty parameters, requirements, and domains."""

    def __init__(self) -> None:
        self._params: set[str] = set()
        self._requirements: set[str] = set()
        self._domains: set[str] = set()
        self._lock = asyncio.Lock()

    async def mark(
        self,
        *,
        param_ids: set[str] | list[str] | None = None,
        requirement_ids: set[str] | list[str] | None = None,
        domains: set[str] | list[str] | None = None,
    ) -> None:
        """Mark parameters/requirements/domains as dirty."""
        async with self._lock:
            if param_ids:
                self._params.update(param_ids)
            if requirement_ids:
                self._requirements.update(requirement_ids)
            if domains:
                self._domains.update(domains)

    async def consume(self) -> tuple[set[str], set[str], set[str]]:
        """Atomically read and clear. Returns (params, requirements, domains).

        On reconverger success: consumed set is gone (cleared).
        On reconverger failure: caller must remark() the consumed set.
        """
        async with self._lock:
            params = set(self._params)
            reqs = set(self._requirements)
            domains = set(self._domains)
            self._params.clear()
            self._requirements.clear()
            self._domains.clear()
            return params, reqs, domains

    async def remark(
        self,
        params: set[str],
        requirements: set[str],
        domains: set[str],
    ) -> None:
        """Re-mark a consumed set on convergence failure (no edits lost)."""
        async with self._lock:
            self._params.update(params)
            self._requirements.update(requirements)
            self._domains.update(domains)

    def is_dirty(self, agent: DesignAgent) -> bool:
        """True if any of the agent's input parameters or domain dependencies are dirty."""
        for p in agent.input_parameters():
            if p in self._params:
                return True
        for d in agent.dependencies():
            if d in self._domains:
                return True
        return False

    @property
    def is_empty(self) -> bool:
        return not self._params and not self._requirements and not self._domains

    @property
    def param_count(self) -> int:
        return len(self._params)

    def __repr__(self) -> str:
        return f"DirtySet(params={len(self._params)}, reqs={len(self._requirements)}, domains={len(self._domains)})"
