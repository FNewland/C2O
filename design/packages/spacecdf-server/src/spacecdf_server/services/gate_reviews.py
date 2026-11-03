"""SpaceCDF — review gate state machine (WP6, Nov 2026).

States of one profile gate::

    not_ready ──(all must-pass items pass)──▶ ready ──start──▶ under_review ──pass──▶ passed
        ▲                                      ▲                  │                    │
        └──────────────(derived)───────────────┴────cancel────────┘                 reopen
                                                                                       ▼
                                                                    reopened ──start──▶ under_review

``not_ready`` / ``ready`` are derived from the server evaluation every time; the others are
stored in ``Study.gate_states[gate_id]`` with a history. Passing saves a baseline snapshot
(routers/gates.py). Pure functions: no I/O.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

STATES = ("not_ready", "ready", "under_review", "passed", "reopened")
ACTIONS = ("start", "cancel", "pass", "reopen")


class GateTransitionError(ValueError):
    """An action that the gate's state does not allow. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def stored_state(entry: dict[str, Any] | None) -> str | None:
    st = (entry or {}).get("state")
    return st if st in ("under_review", "passed", "reopened") else None


def display_state(entry: dict[str, Any] | None, ready: bool) -> str:
    """The state shown for a gate: the stored one, else derived from readiness."""
    st = stored_state(entry)
    if st in ("under_review", "passed", "reopened"):
        return st
    return "ready" if ready else "not_ready"


def transition(entry: dict[str, Any] | None, action: str, *, ready: bool, by: str = "",
               note: str = "", now: datetime | None = None) -> dict[str, Any]:
    """The gate's new stored entry after ``action``; raises GateTransitionError if not allowed.

    ``ready``: the server evaluation says every must-pass item passes (checked again on
    ``pass``, so a design that broke during the review cannot be passed).
    """
    if action not in ACTIONS:
        raise GateTransitionError("bad_action", f"Unknown action {action!r}")
    entry = {"state": None, "history": [], "baselines": [], **(entry or {})}
    current = display_state(entry, ready)
    new: str | None
    if action == "start":
        if current not in ("ready", "reopened"):
            raise GateTransitionError("not_ready" if current == "not_ready" else "bad_state",
                                      f"Cannot start a review from {current}")
        if not ready:
            raise GateTransitionError("not_ready", "Every must-pass item must pass before the review starts")
        new = "under_review"
    elif action == "cancel":
        if current != "under_review":
            raise GateTransitionError("bad_state", f"No review in progress ({current})")
        new = None
    elif action == "pass":
        if current != "under_review":
            raise GateTransitionError("bad_state", f"Only a gate under review can pass ({current})")
        if not ready:
            raise GateTransitionError("not_ready", "A must-pass item failed during the review")
        new = "passed"
    else:  # reopen
        if current != "passed":
            raise GateTransitionError("bad_state", f"Only a passed gate can be reopened ({current})")
        new = "reopened"
    at = (now or datetime.now(timezone.utc)).isoformat()
    entry["history"] = [*entry.get("history", []),
                        {"action": action, "from": current, "to": new or ("ready" if ready else "not_ready"),
                         "at": at, "by": by, "note": note[:500]}]
    entry["state"] = new
    entry["updated_at"] = at
    return entry
