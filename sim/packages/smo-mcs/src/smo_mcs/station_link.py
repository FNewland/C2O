"""Ground-station link monitoring data for the MCS (walkthrough finding M1).

RSSI 0x0502, link margin 0x0503, BER 0x050C, Eb/N0 0x0519 and AGC 0x051A are
``visibility: ground_derived``: the STATION's receiver measures them, the
spacecraft never downlinks them. The operator parameter catalogue refuses
ground-derived parameters as spacecraft telemetry, and nothing else fed them,
so the TT&C page's "Key parameters" read "no data" for the whole session and
25 GO/NO-GO steps on 13 cards could not be judged (2026-11-02 walkthrough).

A real control centre receives the station's monitoring data next to the
telemetry (in SLE terms, the return-link status reports; in a station M&C
feed, the receiver's level, Eb/N0, lock and frame-error figures). This module
is that feed. It is deliberately NOT spacecraft TM:

* it never enters the TM parameter cache, the TM archive or HK staleness;
* every value carries its source, and the console labels the cells
  "station-measured";
* only the five receiver readings pass — no channel-model truth (injected
  impairments, ground-penalty figures, Eb/N0 setpoints) ever does.

Two sources, best first:

1. ``radio`` — the RF bridge's own receiver status (``GET /api/status`` on the
   radio page, FRAME or RF mode), when ``SMO_RADIO_STATUS_URL`` points at a
   running bridge. Values count only while the bridge's carrier is locked:
   an unlocked receiver measures nothing.
2. ``link_model`` — the simulator's ground-receiver block (``ttc.station`` in
   its ``/api/state``), computed from the same link budget that drives the
   model. Used when there is no RF bridge (the default deployment). In the
   split deployment it arrives through the GSG's local ``/api/state``,
   exactly as the clock anchor does. It carries no numbers and a reason when
   the station has no signal.

A value older than ``MAX_AGE_S`` (wall seconds) is dropped rather than shown
as current: the feeds refresh every 1-1.5 s, so a silent source is a dead one.
"""
from __future__ import annotations

import time
from typing import Any, Optional

#: param id -> field name in both feeds (the radio's RadioStatus fields and
#: the simulator's ``ttc.station`` block use the same names on purpose).
STATION_PARAMS: dict[int, str] = {
    0x0502: "rssi_dbm",
    0x0503: "link_margin_db",
    0x050C: "ber_log10",
    0x0519: "eb_n0_db",
    0x051A: "agc_db",
}

SOURCE_LABELS = {
    "radio": "station receiver (RF bridge)",
    "link_model": "station receiver (simulated from the link budget; no RF bridge)",
}

MAX_AGE_S = 5.0


def _locked(v: Any) -> bool:
    """The bridge serialises LockState as its value or its name."""
    if isinstance(v, bool):
        return v
    s = str(v).upper()
    return s.endswith("LOCKED") and not s.endswith("UNLOCKED")


class StationLink:
    """Holds the newest station monitoring data from each source."""

    def __init__(self) -> None:
        self._radio: Optional[dict] = None
        self._model: Optional[dict] = None

    # ── ingest ────────────────────────────────────────────────────────
    def ingest_sim_state(self, payload: Any, now: Optional[float] = None) -> None:
        """Absorb ``ttc.station`` from a simulator / GSG ``/api/state``."""
        if not isinstance(payload, dict):
            return
        ttc = payload.get("ttc")
        st = ttc.get("station") if isinstance(ttc, dict) else None
        if not isinstance(st, dict):
            return
        signal = bool(st.get("signal"))
        values = {}
        if signal:
            for pid, key in STATION_PARAMS.items():
                v = st.get(key)
                if v is not None:
                    try:
                        values[pid] = float(v)
                    except (TypeError, ValueError):
                        pass
        self._model = {
            "source": "link_model", "signal": signal and bool(values),
            "band": st.get("band"), "reason": st.get("reason"),
            "values": values, "wall": time.time() if now is None else now,
        }

    def ingest_radio_status(self, status: Any, now: Optional[float] = None) -> None:
        """Absorb an RF bridge ``/api/status`` snapshot."""
        if not isinstance(status, dict):
            return
        locked = _locked(status.get("carrier_lock"))
        values = {}
        if locked:
            for pid, key in STATION_PARAMS.items():
                v = status.get(key)
                if v is not None:
                    try:
                        values[pid] = float(v)
                    except (TypeError, ValueError):
                        pass
        self._radio = {
            "source": "radio", "signal": locked and bool(values),
            "band": None, "mode": status.get("mode"),
            "reason": None if locked else "no signal: station receiver not locked",
            "values": values, "wall": time.time() if now is None else now,
        }

    # ── read ──────────────────────────────────────────────────────────
    def view(self, now: Optional[float] = None) -> dict:
        """The block the MCS publishes as ``station_link``.

        ``{source, label, signal, band, reason, age_s, values: {"0x0502": v}}``
        — ``values`` is empty when there is no signal or no fresh source.
        """
        now = time.time() if now is None else now
        for cand in (self._radio, self._model):
            if cand is None:
                continue
            age = now - cand["wall"]
            if age > MAX_AGE_S:
                continue
            label = SOURCE_LABELS[cand["source"]]
            if cand.get("mode"):
                label = f"{label}, {cand['mode']} mode"
            return {
                "source": cand["source"], "label": label,
                "signal": cand["signal"], "band": cand.get("band"),
                "reason": cand.get("reason"),
                "age_s": round(max(0.0, age), 1),
                "values": {f"0x{pid:04X}": v
                           for pid, v in cand["values"].items()},
            }
        return {"source": None, "label": None, "signal": False, "band": None,
                "reason": "no station monitoring data (no RF bridge and no "
                          "simulator state feed)",
                "age_s": None, "values": {}}

    def value(self, pid: int, now: Optional[float] = None) -> Optional[float]:
        v = self.view(now)["values"].get(f"0x{int(pid):04X}")
        return None if v is None else float(v)
