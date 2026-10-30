"""ChangeEventDispatcher — single entry point for all design mutations.

Per SPINE_SPEC §3. Replaces inline logic in routers/ws.py.
All WS messages that mutate the design flow through dispatch().

Phase A (current): accepts events, persists, marks dirty set.
Phase B (SCDF-105): routes through reconverger + compliance + margin.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

from spacecdf_common.models.change_event import ChangeEvent, ChangeKind

from .dirty_set import DirtySet

logger = logging.getLogger(__name__)


@dataclass
class ApplyResult:
    """Result of applying a single ChangeEvent."""
    dirty_param_ids: set[str] = field(default_factory=set)
    dirty_requirement_ids: set[str] = field(default_factory=set)
    domain_invalidations: set[str] = field(default_factory=set)
    error: str | None = None


@dataclass
class DispatchResult:
    """Result of dispatching one or more events."""
    events_processed: int = 0
    dirty_params: set[str] = field(default_factory=set)
    dirty_requirements: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)


class ChangeEventHandler(Protocol):
    """Protocol for per-kind event handlers."""
    async def apply(
        self,
        event: ChangeEvent,
        state: Any,
        session: Any,
    ) -> ApplyResult: ...


# Handler registry — maps ChangeKind to handler
_HANDLERS: dict[ChangeKind, ChangeEventHandler] = {}


def register_handler(kind: ChangeKind, handler: ChangeEventHandler) -> None:
    """Register a handler for a specific ChangeKind."""
    _HANDLERS[kind] = handler


class ChangeEventDispatcher:
    """Routes ChangeEvents to handlers, persists, and marks dirty sets."""

    def __init__(
        self,
        dirty_set: DirtySet,
        persist_fn: Callable[[ChangeEvent], Awaitable[None]] | None = None,
        broadcast_fn: Callable[[str, dict], Awaitable[None]] | None = None,
    ):
        self._dirty_set = dirty_set
        self._persist = persist_fn
        self._broadcast = broadcast_fn

    async def dispatch(
        self,
        event: ChangeEvent,
        state: Any = None,
        session: Any = None,
    ) -> DispatchResult:
        """Process a single ChangeEvent through the pipeline.

        1. Persist (WAL-style: never lose an event)
        2. Apply via handler
        3. Mark DirtySet
        4. Return result (reconvergence triggered externally)
        """
        result = DispatchResult()

        # 1. Persist
        if self._persist:
            try:
                await self._persist(event)
            except Exception as e:
                logger.error("Failed to persist event %s: %s", event.id, e)
                # Continue — design loop must not halt on persistence failure (§5)

        # 2. Apply via handler
        handler = _HANDLERS.get(event.kind)
        if handler and state is not None:
            try:
                apply_result = await handler.apply(event, state, session)
                result.dirty_params.update(apply_result.dirty_param_ids)
                result.dirty_requirements.update(apply_result.dirty_requirement_ids)
                if apply_result.error:
                    result.errors.append(apply_result.error)
            except Exception as e:
                logger.error("Handler error for %s: %s", event.kind, e)
                result.errors.append(str(e))
        else:
            # Default: treat target_id as dirty param
            if event.target_kind == "parameter":
                result.dirty_params.add(event.target_id)

        # 3. Mark DirtySet
        await self._dirty_set.mark(
            param_ids=result.dirty_params,
            requirement_ids=result.dirty_requirements,
        )

        result.events_processed = 1
        return result

    async def dispatch_batch(
        self,
        events: list[ChangeEvent],
        state: Any = None,
        session: Any = None,
    ) -> DispatchResult:
        """Dispatch multiple events (same correlation_id)."""
        combined = DispatchResult()
        for event in events:
            r = await self.dispatch(event, state, session)
            combined.events_processed += r.events_processed
            combined.dirty_params.update(r.dirty_params)
            combined.dirty_requirements.update(r.dirty_requirements)
            combined.errors.extend(r.errors)
        return combined
