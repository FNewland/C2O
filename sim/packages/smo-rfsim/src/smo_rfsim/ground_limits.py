"""Ground-receiver limit checking for the RF bridge (plan decision 2026-11-01).

BER (0x050C ``ttc.ber``) and AGC (0x051A ``ttc.agc_level``) are measured by
the GROUND demodulator, not by the spacecraft (``visibility: ground_derived``
in parameters.yaml). They used to be banded in ``mcs/limits.yaml`` — the
spacecraft-telemetry limit set — where no sample ever arrived, so the bands
could never alarm. The author's ruling moves the limits to the equipment
that makes the measurement: the RF bridge evaluates them on every radio tick
and the radio page (and, through ``GET /api/ground-limits``, the MCS TT&C
page) shows them labelled "ground".

Conventions are the MCS ones (PRINCIPLES P3/P7, ``smo_mcs.tm_processor``):

* bands are ``yellow_low / yellow_high / red_low / red_high`` (any may be
  ``None``); red is tested before yellow, comparisons are strict;
* states are ``nominal``, ``yellow_low``, ``yellow_high``, ``red_low``,
  ``red_high``;
* only TRANSITIONS are journalled (entering a band, changing band, returning
  to nominal), never the steady state.

One addition, suppression by design (P7.3): with no carrier lock there is no
signal to measure, so the check is not evaluated and the state is
``no_signal``. Losing the carrier at LOS is not a BER alarm.

The radio page is purely observational (no POST), so acknowledgement is not
done here: P7.5 keeps ONE alarm authority, the MCS alarm journal, which can
ingest the transitions below by their monotonically increasing ``seq``.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

NO_SIGNAL = "no_signal"


@dataclass(frozen=True)
class GroundLimit:
    key: str                 # RadioStatus field the value comes from
    param_id: int            # the catalogued ground-derived parameter
    name: str
    units: str
    description: str
    yellow_low: Optional[float] = None
    yellow_high: Optional[float] = None
    red_low: Optional[float] = None
    red_high: Optional[float] = None

    def band(self) -> dict:
        return {"yellow_low": self.yellow_low, "yellow_high": self.yellow_high,
                "red_low": self.red_low, "red_high": self.red_high}

    def classify(self, value: float) -> str:
        """Same order and strictness as the MCS TMProcessor.classify."""
        if self.red_low is not None and value < self.red_low:
            return "red_low"
        if self.red_high is not None and value > self.red_high:
            return "red_high"
        if self.yellow_low is not None and value < self.yellow_low:
            return "yellow_low"
        if self.yellow_high is not None and value > self.yellow_high:
            return "yellow_high"
        return "nominal"


def build_limits(cfg) -> tuple[GroundLimit, ...]:
    """The two ground limits, from rfsim.yaml ``ground_limits``."""
    return (
        GroundLimit(
            key="ber_log10", param_id=0x050C, name="ttc.ber", units="log10",
            description="Bit error rate at the ground demodulator "
                        "(log10; -5 = 1e-5, the Eb/N0 9.6 dB design point)",
            yellow_high=cfg.ber_yellow_high, red_high=cfg.ber_red_high),
        GroundLimit(
            key="agc_db", param_id=0x051A, name="ttc.agc_level", units="dB",
            description="Ground receiver AGC level tracking the downlink "
                        "(RSSI + offset)",
            yellow_low=cfg.agc_yellow_low, yellow_high=cfg.agc_yellow_high,
            red_low=cfg.agc_red_low, red_high=cfg.agc_red_high),
    )


class GroundLimitChecker:
    """Evaluates the ground limits against a RadioStatus and journals
    transitions."""

    JOURNAL_DEPTH = 200

    def __init__(self, limits: tuple[GroundLimit, ...]):
        self.limits = tuple(limits)
        self.state: dict[int, str] = {l.param_id: NO_SIGNAL for l in self.limits}
        self.values: dict[int, Optional[float]] = {
            l.param_id: None for l in self.limits}
        self.journal: deque = deque(maxlen=self.JOURNAL_DEPTH)
        self._seq = 0

    def evaluate(self, status, now: Optional[float] = None) -> dict[int, str]:
        """Check every limit against ``status``; returns the state map.

        Not evaluated (``no_signal``) unless the carrier is LOCKED.
        """
        now = time.time() if now is None else now
        lock = getattr(status, "carrier_lock", None)
        mode = getattr(getattr(status, "mode", None), "value",
                       getattr(status, "mode", None))
        # PACKET mode has no RF receiver chain at all: nothing is measured.
        locked = (getattr(lock, "value", lock) == "LOCKED"
                  and str(mode).upper() != "PACKET")
        for lim in self.limits:
            value = getattr(status, lim.key, None)
            if not locked or value is None:
                new = NO_SIGNAL
                self.values[lim.param_id] = None
            else:
                value = float(value)
                self.values[lim.param_id] = value
                new = lim.classify(value)
            prev = self.state.get(lim.param_id, NO_SIGNAL)
            self.state[lim.param_id] = new
            if new == prev:
                continue
            # Entering or leaving no-signal is not a limit transition, except
            # that an out-of-limits value which loses its signal must be
            # closed, so the alarm does not hang open across LOS.
            if new == NO_SIGNAL and prev == "nominal":
                continue
            if prev == NO_SIGNAL and new == "nominal":
                continue
            self._seq += 1
            self.journal.append({
                "seq": self._seq,
                "timestamp": now,
                "param_id": f"0x{lim.param_id:04X}",
                "name": lim.name,
                "value": self.values[lim.param_id],
                "status": new,
                "previous": prev,
                "cleared": new in ("nominal", NO_SIGNAL),
                "band": lim.band(),
                "source": "ground",
            })
        return dict(self.state)

    def summary(self) -> str:
        """Worst current state: 'red' > 'yellow' > 'nominal' > 'no_signal'."""
        states = self.state.values()
        if any(s.startswith("red") for s in states):
            return "red"
        if any(s.startswith("yellow") for s in states):
            return "yellow"
        if any(s == "nominal" for s in states):
            return "nominal"
        return NO_SIGNAL

    def to_api(self, since: int = 0) -> dict:
        """Body of GET /api/ground-limits."""
        return {
            "source": "ground",
            "summary": self.summary(),
            "limits": {
                f"0x{l.param_id:04X}": {
                    **l.band(), "name": l.name, "units": l.units,
                    "description": l.description, "source": "ground",
                } for l in self.limits},
            "state": {f"0x{pid:04X}": s for pid, s in self.state.items()},
            "value": {f"0x{pid:04X}": v for pid, v in self.values.items()},
            "transitions": [t for t in self.journal if t["seq"] > since],
            "seq": self._seq,
        }
