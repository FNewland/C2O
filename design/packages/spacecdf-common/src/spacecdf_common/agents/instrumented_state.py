"""InstrumentedDesignState — test-only wrapper that enforces honest declarations.

Per SPINE_SPEC §7. Fails CI if an agent reads a parameter it didn't declare
in input_parameters() or writes one it didn't declare in output_parameters().

Used in tests only; production DesignState is unaffected.
"""
from __future__ import annotations

from typing import Any

from .base import DesignState


class UndeclaredReadError(RuntimeError):
    """Agent read a parameter it didn't declare."""


class UndeclaredWriteError(RuntimeError):
    """Agent wrote a parameter it didn't declare."""


class InstrumentedDesignState(DesignState):
    """Wrapper that tracks which parameters are actually read/written."""

    def __init__(
        self,
        *args: Any,
        agent_name: str = "",
        declared_inputs: set[str] | None = None,
        declared_outputs: set[str] | None = None,
        strict: bool = True,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._agent_name = agent_name
        self._declared_inputs = declared_inputs or set()
        self._declared_outputs = declared_outputs or set()
        self._actually_read: set[str] = set()
        self._strict = strict

    def get(self, param_id: str, default: Any = None) -> Any:
        self._actually_read.add(param_id)
        if self._strict and param_id not in self._declared_inputs:
            # Allow requirement lookups (get_requirement uses different path)
            if not param_id.startswith("_") and "." in param_id:
                raise UndeclaredReadError(
                    f"Agent '{self._agent_name}' read undeclared parameter '{param_id}'. "
                    f"Add it to input_parameters()."
                )
        return super().get(param_id, default)

    def get_param(self, param_id: str) -> Any:
        self._actually_read.add(param_id)
        if self._strict and param_id not in self._declared_inputs:
            if not param_id.startswith("_") and "." in param_id:
                raise UndeclaredReadError(
                    f"Agent '{self._agent_name}' read undeclared parameter '{param_id}' via get_param(). "
                    f"Add it to input_parameters()."
                )
        return super().get_param(param_id)

    @property
    def undeclared_reads(self) -> set[str]:
        """Parameters read but not declared in input_parameters()."""
        return self._actually_read - self._declared_inputs

    @property
    def actually_read(self) -> set[str]:
        return set(self._actually_read)

    def verify_writes(self, written_param_ids: set[str]) -> list[str]:
        """Check that all written params were declared in output_parameters()."""
        undeclared = written_param_ids - self._declared_outputs
        if undeclared and self._strict:
            return [
                f"Agent '{self._agent_name}' wrote undeclared parameter '{p}'. "
                f"Add it to output_parameters()."
                for p in sorted(undeclared)
            ]
        return []
