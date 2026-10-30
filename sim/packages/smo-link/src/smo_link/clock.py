"""Clock: NTP-style offset estimator and the STATE re-timing anchor.

LINK_DESIGN §3.5. Each PING/PONG exchange yields one sample::

    t1 = PING sent (local wall)      t2 = PING received (remote wall)
    t3 = PONG sent (remote wall)     t4 = PONG received (local wall)
    offset = ((t2 - t1) + (t3 - t4)) / 2      # remote wall - local wall
    delay  = (t4 - t1) - (t3 - t2)

The estimator keeps the minimum-delay sample of the last 8. At the GSG the
"remote" is the agent, so ``offset`` = agent wall - GSG wall.
"""
from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any

STATE_STALE_S = 5.0
WINDOW = 8


class ClockEstimator:
    def __init__(self, window: int = WINDOW):
        # (delay, offset, local wall - local monotonic at sample time)
        self._samples: deque[tuple[float, float, float]] = deque(maxlen=window)

    def add_sample(self, t1: float, t2: float, t3: float, t4: float) -> None:
        delay = (t4 - t1) - (t3 - t2)
        offset = ((t2 - t1) + (t3 - t4)) / 2.0
        if delay < 0:
            delay = 0.0
        self._samples.append((delay, offset, time.time() - time.monotonic()))

    def _best(self) -> tuple[float, float, float] | None:
        return min(self._samples, key=lambda s: s[0]) if self._samples else None

    @property
    def offset(self) -> float:
        b = self._best()
        return b[1] if b else 0.0

    @property
    def mono_offset(self) -> float | None:
        """Remote wall - local *monotonic*. Unlike ``offset`` this survives a
        step of the local wall clock after the sample was taken (re-review N2):
        remote_now = time.monotonic() + mono_offset."""
        b = self._best()
        return b[1] + b[2] if b else None

    @property
    def rtt(self) -> float | None:
        b = self._best()
        return b[0] if b else None

    @property
    def last_rtt(self) -> float | None:
        return self._samples[-1][0] if self._samples else None

    @property
    def count(self) -> int:
        return len(self._samples)

    def reset(self) -> None:
        self._samples.clear()


def _parse_iso(s: str) -> datetime:
    # Python 3.10 fromisoformat does not accept "Z".
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


class SimClockAnchor:
    """Last STATE from the agent, re-timed to "now" on the GSG clock."""

    def __init__(self, stale_s: float = STATE_STALE_S):
        self.stale_s = stale_s
        self.state: dict | None = None
        self.t_agent_wall: float | None = None
        self.rx_mono: float | None = None

    def update(self, t_agent_wall: float, state: dict, rx_mono: float | None = None) -> None:
        self.state = state
        self.t_agent_wall = float(t_agent_wall)
        self.rx_mono = time.monotonic() if rx_mono is None else rx_mono

    def age_since_rx(self, now_mono: float | None = None) -> float | None:
        if self.rx_mono is None:
            return None
        return (time.monotonic() if now_mono is None else now_mono) - self.rx_mono

    def fresh(self, now_mono: float | None = None) -> bool:
        age = self.age_since_rx(now_mono)
        return age is not None and age <= self.stale_s

    def clear(self) -> None:
        self.state = None
        self.t_agent_wall = None
        self.rx_mono = None

    def retimed(self, offset: float, now_wall: float | None = None,
                now_mono: float | None = None) -> dict | None:
        """The pushed state with time-dependent fields advanced, or None if
        stale. Key order and every other field are unchanged."""
        if self.state is None or not self.fresh(now_mono):
            return None
        now_wall = time.time() if now_wall is None else now_wall
        return retime_state(self.state, self.t_agent_wall, offset, now_wall)


def retime_state(state: dict, t_agent_wall: float, offset: float,
                 now_wall: float) -> dict:
    """age = now - (t_agent_wall - offset); advance sim_time/met_s/eclipse
    countdowns by age x speed (0 when paused)."""
    age = now_wall - (t_agent_wall - offset)
    if age < 0:
        age = 0.0
    try:
        speed = float(state.get("speed") or 0.0)
    except (TypeError, ValueError):
        speed = 0.0
    adv = age * speed if speed > 0 else 0.0
    out = dict(state)
    if adv:
        st = state.get("sim_time")
        if isinstance(st, str):
            try:
                out["sim_time"] = (_parse_iso(st) + timedelta(seconds=adv)).isoformat()
            except ValueError:
                pass
        met = state.get("met_s")
        if isinstance(met, (int, float)) and not isinstance(met, bool):
            out["met_s"] = met + adv
        for k in ("time_to_eclipse_entry_s", "time_to_eclipse_exit_s"):
            v = state.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[k] = max(0.0, v - adv)
    return out


def sim_summary(state: dict | None) -> dict[str, Any]:
    """The ``sim`` block of HELLO."""
    state = state or {}
    return {"speed": state.get("speed"), "sim_time": state.get("sim_time"),
            "tick_hz": state.get("tick_hz")}
