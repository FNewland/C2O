"""Pass log: the passes this console has seen, from ground knowledge only.

The logbook's handover form asks for the "last completed pass" and the
hand-in header wants the session's context. The MCS knows both ends of a
pass without asking the simulator:

* **visibility** from its own ground propagator (the same geometry as the
  contact schedule, ``_compute_orbital_state``: ``in_contact``, station,
  elevation) gives AOS and LOS;
* **telemetry** (the time of the newest TM frame) says whether the pass was
  actually worked: first and last frame received inside it.

A pass is *completed* at LOS. A pass already in progress when the console
started has no AOS of its own (``aos_seen: False``). When sim time jumps
backwards (a breakpoint load, a scenario restart) the open pass is dropped
and the passes that now lie in the future are forgotten: they did not happen
on the new timeline.

All times are SIM epoch seconds (the console's clock base).
"""
from __future__ import annotations

from collections import deque
from typing import Optional

__all__ = ["PassLog"]


class PassLog:
    #: a backwards step larger than this (s) is a time jump, not jitter
    JUMP_S = 5.0

    def __init__(self, keep: int = 24):
        self._done: deque[dict] = deque(maxlen=keep)
        self._cur: Optional[dict] = None
        self._last_now: Optional[float] = None
        self._started = False

    def update(self, now: float, in_contact, station: str = "",
               elevation_deg=None, last_tm_ts: Optional[float] = None) -> None:
        """One sample (each state poll)."""
        if not isinstance(now, (int, float)):
            return
        first = not self._started
        self._started = True
        if self._last_now is not None and now < self._last_now - self.JUMP_S:
            self._cur = None
            kept = [p for p in self._done if p["los"] <= now]
            self._done.clear()
            self._done.extend(kept)
            first = True               # a pass open after the jump has no seen AOS
        self._last_now = now
        if in_contact is not True:
            if self._cur is not None:
                self._cur["los"] = now
                self._done.append(self._cur)
                self._cur = None
            return
        station = str(station or "")
        if self._cur is not None and station and self._cur["station"] and station != self._cur["station"]:
            # handed to another station: the first station's pass ends here
            self._cur["los"] = now
            self._done.append(self._cur)
            self._cur = None
        if self._cur is None:
            self._cur = {"station": station, "aos": now, "aos_seen": not first,
                         "los": None, "max_el_deg": None, "tm_first": None, "tm_last": None}
        if station and not self._cur["station"]:
            self._cur["station"] = station
        if isinstance(elevation_deg, (int, float)):
            m = self._cur["max_el_deg"]
            self._cur["max_el_deg"] = round(float(elevation_deg), 1) if m is None else max(m, round(float(elevation_deg), 1))
        if isinstance(last_tm_ts, (int, float)) and last_tm_ts >= self._cur["aos"]:
            if self._cur["tm_first"] is None:
                self._cur["tm_first"] = float(last_tm_ts)
            self._cur["tm_last"] = float(last_tm_ts)

    @staticmethod
    def _out(p: dict) -> dict:
        return {**p, "tm": p["tm_first"] is not None, "source": "ground"}

    def view(self, n: int = 5) -> dict:
        """``{current, last, passes}``: the open pass, the last completed one
        and up to *n* completed passes, newest first."""
        done = [self._out(p) for p in reversed(self._done)][:n]
        return {"current": self._out(self._cur) if self._cur else None,
                "last": done[0] if done else None,
                "passes": done}
