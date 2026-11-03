"""SMO MCS — alarm lifecycle (ISA-18.2 / IEC 62682 alarm states).

An alarm in the MCS journal is the record of one *condition*, and it has two
independent facts about it: is the condition still present (ACTIVE / returned
to normal, RTN) and has an operator seen it (UNACK / ACK). The four
combinations are the standard alarm states:

=============  ==========  =============  ==================================
state          condition   operator       live alarm list
=============  ==========  =============  ==================================
UNACK_ACTIVE   present     not yet acked  shown, annunciated
ACK_ACTIVE     present     acked          shown (standing alarm)
UNACK_RTN      gone        not yet acked  shown, marked "returned to normal"
ACK_RTN        gone        acked          REMOVED (kept in journal/archive)
=============  ==========  =============  ==================================

So an alarm leaves the live list only when the condition has gone AND an
operator has acknowledged it, in either order: a transient the operator did
not see is never silently erased, and an acknowledged condition does not sit
on the console after it has cleared.

What makes an alarm return to normal depends on its source:

* ``LIMIT`` (ground limit check) — the parameter's ground limit state goes
  back to nominal (TMProcessor transition, with hysteresis), or a later limit
  transition on the same parameter supersedes it (yellow -> red, red ->
  yellow: the old band is no longer the condition).
* ``S12`` (on-board monitor) — TM(12,10) back-to-limits for the same monitor,
  the monitor is disabled or deleted (TM(12,13) definition table), or — after
  a TM reconnect, a new pass (a TM(12,10) sent during LOS sits in the on-board
  store and stored TM never clears a live alarm) or a simulator reset /
  scenario restart / breakpoint load — fresh real-time telemetry puts the
  value back inside the monitor's band.
* ``S5`` (on-board event) — an event is a point in time, it has no condition
  that can return to normal. It is annunciated UNACK_ACTIVE and acknowledging
  it closes it (straight to ACK_RTN).

Played-back (S15 dump, VC1) telemetry never raises, updates or clears an
alarm: it describes the past and is analysed offline in the delayed-TM
viewer.

This module holds only the pure state logic so it can be tested without a
server; :mod:`smo_mcs.server` owns the journal, the archive and the WebSocket
broadcasts.
"""
from __future__ import annotations

from typing import Optional

UNACK_ACTIVE = "UNACK_ACTIVE"
ACK_ACTIVE = "ACK_ACTIVE"
UNACK_RTN = "UNACK_RTN"
ACK_RTN = "ACK_RTN"

STATES = (UNACK_ACTIVE, ACK_ACTIVE, UNACK_RTN, ACK_RTN)

#: Sources whose alarms are point events (no return-to-normal condition).
POINT_EVENT_SOURCES = frozenset({"S5"})


def state_of(alarm: dict) -> str:
    """The ISA-18.2 state of *alarm* from its ``active``/``acknowledged``."""
    active = bool(alarm.get("active", True))
    acked = bool(alarm.get("acknowledged", False))
    if active:
        return ACK_ACTIVE if acked else UNACK_ACTIVE
    return ACK_RTN if acked else UNACK_RTN


def is_live(alarm: dict) -> bool:
    """True while the alarm belongs on the live alarm list."""
    return state_of(alarm) != ACK_RTN


def _sync(alarm: dict) -> dict:
    """Recompute the derived fields every consumer reads."""
    st = state_of(alarm)
    alarm["state"] = st
    # `rtn` is what the console renders ("returned to normal"); `cleared`
    # is the historical name the system overview and older clients read.
    alarm["rtn"] = not alarm.get("active", True)
    alarm["cleared"] = alarm["rtn"]
    alarm["live"] = st != ACK_RTN
    return alarm


def init(alarm: dict, *, ts: float) -> dict:
    """Fill the lifecycle fields of a newly raised alarm (UNACK_ACTIVE)."""
    alarm["active"] = True
    alarm.setdefault("acknowledged", False)
    alarm["point_event"] = alarm.get("source") in POINT_EVENT_SOURCES
    alarm.setdefault("raised_ts", ts)
    alarm.pop("rtn_ts", None)
    alarm.pop("rtn_reason", None)
    return _sync(alarm)


def acknowledge(alarm: dict, *, ts: float) -> bool:
    """Operator acknowledgement. Returns True if the state changed.

    A point event (S5) has nothing left to wait for once seen, so
    acknowledging it also closes it (ACK_RTN).
    """
    before = state_of(alarm)
    alarm["acknowledged"] = True
    alarm.setdefault("ack_ts", ts)
    if alarm.get("point_event") and alarm.get("active", True):
        alarm["active"] = False
        alarm["rtn_ts"] = ts
        alarm["rtn_reason"] = "point event acknowledged"
    _sync(alarm)
    return state_of(alarm) != before


def return_to_normal(alarm: dict, *, ts: float, reason: str,
                     value: Optional[object] = None) -> bool:
    """The alarm's condition has gone. Returns True if the state changed.

    Acknowledgement is NOT implied: an unacknowledged alarm becomes
    UNACK_RTN and stays on the live list until an operator acknowledges it.
    """
    if not alarm.get("active", True):
        return False
    alarm["active"] = False
    alarm["rtn_ts"] = ts
    alarm["cleared_ts"] = ts        # historical name of rtn_ts
    alarm["rtn_reason"] = reason
    if value is not None:
        alarm["rtn_value"] = value
    _sync(alarm)
    return True


def is_active(alarm: dict) -> bool:
    return bool(alarm.get("active", True))
