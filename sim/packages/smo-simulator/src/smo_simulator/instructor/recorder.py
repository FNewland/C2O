"""Instructor recorder: one timeline, the ground's view, scheduled injects.

Everything the instructor console shows that is not a raw model value comes
from here (INSTRUCTOR_CONSOLE_DESIGN.md §4). It is built from what the
SIMULATOR itself knows, because in the split deployment nothing about the
trainees crosses the link except their telecommands (LINK_DESIGN.md):

* telecommands received, accepted, rejected and completed (``_dispatch_tc``
  and the S1 reports the spacecraft generates);
* on-board events and alarms, and whether their S5 packet actually reached
  the ground (the TM tap at the radio);
* the ground's picture of housekeeping: the last value of every parameter in
  downlinked S3.25 packets, real-time or played back (``GroundView``);
* the simulator's own state changes (phase, modes, contact, eclipse, faults,
  FDIR recoveries, on-board procedures) and the instructor's own actions.

Ground-side trainee activity (alarm acknowledgements, procedure steps, voice
loops, logbooks) is not visible here; the lanes for it are drawn and marked
"not available on the simulator side" (design §4.3).

Threading: every ``on_*`` hook runs on the tick thread. Readers on the
aiohttp thread only call ``timeline_since`` / ``published`` which copy under
``self._lock``.
"""
from __future__ import annotations

import logging
import math
import struct
import threading
import time
from collections import OrderedDict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from . import divergence as dv
from . import taxonomy as tx

logger = logging.getLogger(__name__)

#: Timeline lanes, top to bottom. "voice" and ground "procedure steps" are
#: ground-side and shown as not available.
LANES = ("phase", "fault", "alarm", "tc", "proc", "link", "instr", "voice")

MAX_ITEMS = 6000
#: A ground-received ALARM with no telecommand after this long (sim s) is a
#: "missed cue" — the simulator's proxy for "not acted on" (it cannot see
#: acknowledgements, which happen on the ground).
MISSED_CUE_S = 300.0
#: Auto snapshots kept (oldest dropped first).
MAX_AUTO_SNAPSHOTS = 6
#: Views bundle rebuilt at most this often (wall seconds).
VIEWS_MIN_INTERVAL_S = 0.9
#: Debrief history sample spacing (sim seconds) and length.
HISTORY_EVERY_S = 10.0
HISTORY_MAX = 4000

TRIGGER_KINDS = ("now", "delay", "at", "aos", "los", "eclipse_entry",
                 "eclipse_exit", "tc")

#: Event-id high byte -> subsystem (fallback when the catalogue has no row).
_EVENT_BANK = {0x01: "eps", 0x02: "aocs", 0x03: "obdh", 0x04: "tcs",
               0x05: "ttc", 0x06: "payload", 0x07: "obdh", 0x08: "prop",
               0x0B: "prop"}
_PARAM_BANK = {0x00: "obdh", 0x01: "eps", 0x02: "aocs", 0x03: "obdh",
               0x04: "tcs", 0x05: "ttc", 0x06: "payload", 0x07: "obdh",
               0x08: "obdh", 0x0A: "obdh", 0x0B: "prop"}
SEV_NAMES = {1: "INFO", 2: "WARNING", 3: "ALARM", 4: "CRITICAL"}
PHASE_NAMES = ["PRE_SEPARATION", "SEPARATION_TIMER", "INITIAL_POWER_ON",
               "BOOTLOADER_OPS", "LEOP", "COMMISSIONING", "NOMINAL"]
AOCS_MODES = {0: "OFF", 1: "SAFE_BOOT", 2: "DETUMBLE", 3: "COARSE_SUN",
              4: "NOMINAL", 5: "FINE_POINT", 6: "SLEW", 7: "DESAT",
              8: "ECLIPSE", 9: "INERTIAL"}


def _epoch(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


class GroundView:
    """The ground's picture of housekeeping, from the TM the radio sent.

    ``observe(pkt)`` is called for every packet that leaves the spacecraft
    radio (real-time or S15 playback). S3.25 packets are decoded with the
    engine's own HK structures. A played-back value never overwrites a newer
    real-time one: the MCS keeps live values live (alarm-lifecycle, 2026-11).
    """

    def __init__(self, hk_structures: dict[int, list[tuple]]):
        self._structs = {int(sid): list(params) for sid, params in (hk_structures or {}).items()}
        self._sid_of: dict[int, list[int]] = {}
        for sid, params in self._structs.items():
            for pid, _fmt, _scale in params:
                self._sid_of.setdefault(int(pid), []).append(sid)
        self._last: dict[int, dict[str, Any]] = {}
        self.last_rx_ts: Optional[float] = None
        self.packets = 0
        self.playback_packets = 0
        self._lock = threading.Lock()

    def sids_of(self, pid: int) -> list[int]:
        return list(self._sid_of.get(int(pid), []))

    def observe(self, data_field: bytes, *, sid: int, sample_ts: float,
                rx_ts: float, playback: bool) -> None:
        struct_ = self._structs.get(int(sid))
        if not struct_:
            return
        off = 0
        values: dict[int, float] = {}
        for pid, fmt, scale in struct_:
            try:
                size = struct.calcsize(">" + fmt)
                if off + size > len(data_field):
                    break
                (raw,) = struct.unpack(">" + fmt, data_field[off:off + size])
            except struct.error:
                break
            off += size
            values[int(pid)] = float(raw) / (scale or 1.0)
        with self._lock:
            self.packets += 1
            if playback:
                self.playback_packets += 1
            else:
                self.last_rx_ts = rx_ts
            via = "playback" if playback else "rt"
            for pid, v in values.items():
                cur = self._last.get(pid)
                if cur is not None and cur["ts"] > sample_ts:
                    continue
                self._last[pid] = {"v": v, "ts": sample_ts, "via": via, "sid": int(sid)}

    def values(self) -> dict[int, dict[str, Any]]:
        with self._lock:
            return {k: dict(v) for k, v in self._last.items()}

    def delay_reason(self, pid: int, engine) -> dict:
        """Why the ground might not have the current value of ``pid``.

        ``{"key": English template with {{vars}}, "vars": {...}}`` so the
        console can translate it; ``reason_text()`` renders the English.
        """
        sids = self.sids_of(pid)
        if not sids:
            return {"key": "not in any housekeeping structure", "vars": {}}
        enabled = getattr(engine, "_hk_enabled", {}) or {}
        on = [s for s in sids if enabled.get(s, True)]
        if not on:
            return {"key": "housekeeping SID {{sids}} disabled",
                    "vars": {"sids": ", ".join(str(s) for s in sids)}}
        if int(engine.params.get(0x0311, 1) or 0) == 0 and not any(s in (10, 11) for s in on):
            return {"key": "OBC in the bootloader: only the beacon housekeeping is generated", "vars": {}}
        # Same power gate as SimulationEngine._emit_hk_packets.
        lines = getattr(getattr(engine.subsystems.get("eps"), "_state", None), "power_lines", None) or {}
        owner = {2: "aocs_wheels", 5: "payload"}
        if all(owner.get(s) and not lines.get(owner[s], True) for s in on):
            return {"key": "not generated: power line {{line}} off",
                    "vars": {"line": ", ".join(sorted({owner[s] for s in on}))}}
        try:
            down = bool(engine.downlink_active)
        except Exception:  # noqa: BLE001
            down = False
        if not down:
            return {"key": "no downlink (out of contact or transmitter off)", "vars": {}}
        iv = min(float((getattr(engine, "_hk_intervals", {}) or {}).get(s, 0) or 0) for s in on)
        if iv > 0:
            return {"key": "waiting for the next housekeeping packet (every {{s}} s)", "vars": {"s": f"{iv:g}"}}
        return {"key": "waiting for the next housekeeping packet", "vars": {}}

    @staticmethod
    def reason_text(r: dict) -> str:
        out = r.get("key", "")
        for k, v in (r.get("vars") or {}).items():
            out = out.replace("{{" + k + "}}", str(v))
        return out

    def reset(self) -> None:
        with self._lock:
            self._last.clear()
            self.last_rx_ts = None


class InstructorRecorder:
    """Timeline, ground view, scheduler and views bundle for one engine."""

    def __init__(self, engine):
        self.engine = engine
        self._lock = threading.RLock()
        self._items: deque = deque(maxlen=MAX_ITEMS)
        self._seq = 0
        self.segment = 0
        self.ground = GroundView(getattr(engine, "_hk_structures", {}) or {})
        self._prev: dict[str, Any] = {}
        self._failures: dict[str, dict] = {}       # fault_id -> swimlane record
        self._pending_ev: "OrderedDict[tuple, dict]" = OrderedDict()
        self._tc_names = self._load_tc_names(getattr(engine, "config_dir", None))
        self._event_cat = self._load_event_catalog(getattr(engine, "config_dir", None))
        self._schedule: list[dict] = []
        self._sched_seq = 0
        self._fire_now: list[str] = []
        self._views: Optional[dict] = None
        self._views_wall = 0.0
        self._history: deque = deque(maxlen=HISTORY_MAX)
        self._last_hist_ts: Optional[float] = None
        self._div_state: dict[str, Optional[str]] = {}
        self._grounded_alarms: list[dict] = []
        self._tc_seen_ts: list[float] = []
        self._scenario_name = ""

    # ── catalogues ──────────────────────────────────────────────────────
    @staticmethod
    def _load_tc_names(config_dir) -> dict:
        out: dict = {}
        try:
            import yaml
            path = Path(config_dir or "configs/eosat1") / "commands" / "tc_catalog.yaml"
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            by_ss: dict = {}
            for c in doc.get("commands") or []:
                svc, sub = c.get("service"), c.get("subtype")
                if c.get("func_id") is not None:
                    out[(svc, sub, int(c["func_id"]))] = c.get("name")
                else:
                    by_ss.setdefault((svc, sub), []).append(c.get("name"))
            for k, names in by_ss.items():
                if len(names) == 1:
                    out[k] = names[0]
        except Exception as e:  # noqa: BLE001 — names are a convenience
            logger.debug("TC catalogue not loaded for the timeline: %s", e)
        return out

    @staticmethod
    def _load_event_catalog(config_dir) -> dict:
        out: dict = {}
        try:
            import yaml
            path = Path(config_dir or "configs/eosat1") / "events" / "event_catalog.yaml"
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            rows = doc.get("events") if isinstance(doc, dict) else doc
            for r in rows or []:
                if isinstance(r, dict) and r.get("id") is not None:
                    out[int(r["id"])] = {"name": r.get("name"), "subsystem": r.get("subsystem")}
        except Exception as e:  # noqa: BLE001
            logger.debug("Event catalogue not loaded for the timeline: %s", e)
        return out

    # ── time ────────────────────────────────────────────────────────────
    def now_ts(self) -> float:
        return _epoch(self.engine._sim_time)

    # ── timeline ────────────────────────────────────────────────────────
    def add(self, lane: str, kind: str, text: str, *, sev: int = 1,
            sub: str = "", ref: str = "", data: Optional[dict] = None,
            focus: Optional[dict] = None, ts: Optional[float] = None) -> dict:
        ts = self.now_ts() if ts is None else ts
        with self._lock:
            self._seq += 1
            item = {"seq": self._seq, "seg": self.segment, "ts": round(ts, 3),
                    "t": _iso(ts), "lane": lane, "kind": kind, "sev": int(sev),
                    "text": str(text)[:240], "sub": sub, "ref": ref}
            if data:
                item["data"] = data
            if focus:
                item["focus"] = focus
            self._items.append(item)
        return item

    def timeline_since(self, since: int = 0, limit: int = 2000) -> dict:
        with self._lock:
            items = [dict(i) for i in self._items if i["seq"] > since]
            seq = self._seq
            seg = self.segment
        truncated = len(items) > limit
        if truncated:
            items = items[-limit:]
        return {"seq": seq, "segment": seg, "now_ts": self.now_ts(),
                "now": _iso(self.now_ts()), "speed": self.engine.speed,
                "items": items, "truncated": truncated,
                "pending": self.pending(), "faults": self.fault_lanes(),
                "lanes": list(LANES),
                "unavailable_lanes": {"voice": "ground-side (voice server)",
                                      "proc_ground": "ground-side (MCS procedures)"}}

    # ── scheduled injects ───────────────────────────────────────────────
    def schedule(self, cmd: dict) -> tuple[bool, str]:
        """Accept a ``failure_schedule`` command (already validated)."""
        injects = cmd.get("injects")
        if not isinstance(injects, list) or not injects:
            return False, "failure_schedule needs a non-empty injects list"
        if len(injects) > 8:
            return False, "at most 8 injects fire together"
        trig = cmd.get("trigger") or {"kind": "now"}
        kind = str(trig.get("kind", "now"))
        if kind not in TRIGGER_KINDS:
            return False, f"unknown trigger {kind!r}"
        now = self.now_ts()
        due = None
        if kind == "now":
            due = now
        elif kind == "delay":
            try:
                d = float(trig.get("delay_s"))
            except (TypeError, ValueError):
                return False, "delay trigger needs delay_s"
            if not (0 <= d <= 7 * 86400):
                return False, "delay_s must be 0..604800"
            due = now + d
        elif kind == "at":
            try:
                due = _epoch(datetime.fromisoformat(str(trig.get("at")).replace("Z", "+00:00")))
            except (TypeError, ValueError):
                return False, "at trigger needs an ISO time"
        elif kind == "tc":
            try:
                trig = {"kind": "tc", "service": int(trig["service"]),
                        "subtype": int(trig["subtype"]),
                        **({"func_id": int(trig["func_id"])} if trig.get("func_id") is not None else {})}
            except (KeyError, TypeError, ValueError):
                return False, "tc trigger needs service and subtype"
        with self._lock:
            self._sched_seq += 1
            sid = f"S{self._sched_seq}"
            entry = {
                "id": sid, "label": str(cmd.get("label") or "")[:80],
                "injects": [self._clean_inject(i) for i in injects],
                "trigger": {**trig, "kind": kind}, "due_ts": due,
                "snapshot_before": bool(cmd.get("snapshot_before", True)),
                "created_ts": now, "state": "pending",
            }
            self._schedule.append(entry)
        what = ", ".join(f"{i['subsystem']}/{i['failure']}" for i in entry["injects"])
        if kind != "now":
            self.add("fault", "sched", f"Scheduled {what} ({self._trigger_text(entry['trigger'], due)})",
                     sev=1, ref=sid, data={"schedule_id": sid})
        if kind == "now":
            self._fire(entry)
        return True, ""

    @staticmethod
    def _clean_inject(i: dict) -> dict:
        drop = ("type", "_done", "_outcome", "snapshot_before")
        out = {k: v for k, v in dict(i).items() if k not in drop}
        out["subsystem"] = {"adcs": "aocs", "acs": "aocs"}.get(out.get("subsystem", ""), out.get("subsystem", ""))
        out["failure"] = out.get("failure") or out.get("mode", "")
        out.pop("mode", None)
        return out

    @staticmethod
    def _trigger_text(trig: dict, due) -> str:
        k = trig.get("kind")
        if k in ("delay", "at") and due is not None:
            return "at " + _iso(due)[11:19] + " UTC"
        if k == "tc":
            return f"on the next TC S{trig.get('service')}.{trig.get('subtype')}" + (
                f" func {trig['func_id']}" if trig.get("func_id") is not None else "")
        return {"aos": "at the next AOS", "los": "at the next LOS",
                "eclipse_entry": "at eclipse entry",
                "eclipse_exit": "at eclipse exit"}.get(k, str(k))

    def cancel(self, schedule_id: str) -> tuple[bool, str]:
        with self._lock:
            for e in self._schedule:
                if e["id"] == schedule_id and e["state"] == "pending":
                    e["state"] = "cancelled"
                    break
            else:
                return False, f"no pending schedule {schedule_id!r}"
        self.add("fault", "sched_cancel", f"Cancelled scheduled inject {schedule_id}",
                 ref=schedule_id)
        return True, ""

    def schedule_list(self) -> list[dict]:
        with self._lock:
            return [dict(e) for e in self._schedule if e["state"] == "pending"]

    def _fire(self, entry: dict) -> None:
        entry["state"] = "fired"
        snap = None
        if entry.get("snapshot_before"):
            what = "+".join(i["failure"] for i in entry["injects"])
            snap = self.auto_snapshot(f"before {what}")
        fired, errors = [], []
        for inj in entry["injects"]:
            cmd = {"type": "failure_inject", **inj}
            try:
                self.engine._handle_instructor_cmd(cmd)
                fired.append(f"{inj['subsystem']}/{inj['failure']}")
            except Exception as e:  # noqa: BLE001 — one bad inject never blocks the rest
                errors.append(f"{inj.get('subsystem')}/{inj.get('failure')}: {e}")
        if entry["trigger"].get("kind") != "now" or len(entry["injects"]) > 1:
            self.add("fault", "sched_fire",
                     f"Fired {', '.join(fired) or 'nothing'}"
                     + (f" — errors: {'; '.join(errors)}" if errors else ""),
                     sev=3 if errors else 2, ref=entry["id"],
                     data={"snapshot": snap, "errors": errors})

    def _check_schedule(self, now: float, edges: set[str]) -> None:
        due = []
        with self._lock:
            for e in self._schedule:
                if e["state"] != "pending":
                    continue
                k = e["trigger"]["kind"]
                if (k in ("delay", "at") and e["due_ts"] is not None and now >= e["due_ts"]) \
                        or (k in edges) or (e["id"] in self._fire_now):
                    due.append(e)
            self._fire_now = []
        for e in due:
            self._fire(e)
        if len(self._schedule) > 200:
            with self._lock:
                self._schedule = [e for e in self._schedule if e["state"] == "pending"][-200:]

    def auto_snapshot(self, why: str) -> Optional[str]:
        """Save an in-memory breakpoint before an inject (the "return to
        interrupted scenario" slot). Kept in RAM only, newest six."""
        eng = self.engine
        try:
            from smo_simulator.breakpoints import BreakpointManager
            name = f"auto {self.engine._sim_time.strftime('%H:%M:%S')} {why}"[:80]
            state = BreakpointManager(eng).save(name=name)
            state["auto"] = True
            bps = eng._breakpoints
            bps[state["name"]] = state
            autos = [n for n, s in bps.items() if isinstance(s, dict) and s.get("auto")]
            for old in autos[:-MAX_AUTO_SNAPSHOTS]:
                bps.pop(old, None)
            self.add("instr", "snapshot", f"Auto snapshot \"{state['name']}\"",
                     ref=state["name"])
            return state["name"]
        except Exception as e:  # noqa: BLE001 — never block the inject
            logger.warning("Auto snapshot before inject failed: %s", e)
            self.add("instr", "snapshot_fail", f"Auto snapshot failed: {e}", sev=2)
            return None

    # ── pending (future) items for the timeline ─────────────────────────
    def pending(self) -> list[dict]:
        now = self.now_ts()
        out = []
        for e in self.schedule_list():
            what = ", ".join(f"{i['subsystem']}/{i['failure']}" for i in e["injects"])
            out.append({"source": "instructor", "id": e["id"], "lane": "fault",
                        "ts": e["due_ts"], "gate": None if e["due_ts"] is not None
                        else self._trigger_text(e["trigger"], None),
                        "text": what, "label": e.get("label") or ""})
        se = getattr(self.engine, "_scenario_engine", None)
        try:
            active = se._active if se is not None else None
        except Exception:  # noqa: BLE001
            active = None
        if active is not None:
            elapsed = float(getattr(se, "_elapsed", 0.0))
            for i, ev in enumerate(active.events):
                if ev.fired:
                    continue
                p = ev.params or {}
                text = (f"{p.get('subsystem')}/{p.get('failure')}" if ev.action == "inject"
                        else ev.action)
                if ev.time_offset_s is not None:
                    out.append({"source": "scenario", "id": f"scn{i}", "lane": "fault"
                                if ev.action == "inject" else "phase",
                                "ts": now + max(0.0, float(ev.time_offset_s) - elapsed),
                                "gate": None, "text": text})
                elif ev.condition:
                    out.append({"source": "scenario", "id": f"scn{i}", "lane": "fault",
                                "ts": None, "gate": f"when {ev.condition}", "text": text})
            out.append({"source": "scenario", "id": "scn_end", "lane": "phase",
                        "ts": now + max(0.0, float(active.duration_s) - elapsed),
                        "gate": None, "text": "scenario ends"})
        return out

    # ── TM taps (called from the engine) ────────────────────────────────
    def on_tm_generated(self, pkt: bytes) -> None:
        """A packet the spacecraft generated (whether or not it reaches the
        ground): S1 verification and S5 events go on the timeline."""
        try:
            from smo_common.protocol.ecss_packet import decommutate_packet
            p = decommutate_packet(bytes(pkt))
        except Exception:  # noqa: BLE001
            return
        if p is None or p.secondary is None:
            return
        svc, sub = p.secondary.service, p.secondary.subtype
        if svc == 1:
            self._on_verification(sub, p.data_field or b"")
        elif svc == 5:
            self._on_event_packet(p)

    def on_tm_downlinked(self, pkt: bytes, *, playback: bool = False) -> None:
        """A packet that left the radio towards the ground."""
        try:
            from smo_common.protocol.ecss_packet import decommutate_packet
            p = decommutate_packet(bytes(pkt))
        except Exception:  # noqa: BLE001
            return
        if p is None or p.secondary is None:
            return
        now = self.now_ts()
        svc, sub = p.secondary.service, p.secondary.subtype
        if svc == 3 and sub == 25 and len(p.data_field) >= 2:
            sid = struct.unpack(">H", p.data_field[:2])[0]
            sample = now
            if playback:
                sample = self._cuc_to_sim_ts(getattr(p.secondary, "cuc_seconds", None), now)
            self.ground.observe(p.data_field[2:], sid=sid, sample_ts=sample,
                                rx_ts=now, playback=playback)
        elif svc == 5:
            key = (p.primary.apid, p.primary.sequence_count)
            ev = self._pending_ev.pop(key, None)
            if ev is not None and ev["sev"] >= 2:
                lag = now - ev["ts"]
                item = self.add("alarm", "ev_down",
                                f"{ev['name'] or hex(ev['event_id'])} reached the ground"
                                + (" (played back)" if playback else ""),
                                sev=ev["sev"], sub=ev["sub"], ref=str(ev["seq"]),
                                data={"lag_s": round(lag, 1), "playback": playback})
                self._grounded_alarms.append({"ts": now, "sev": ev["sev"], "sub": ev["sub"],
                                              "name": ev["name"], "seq": item["seq"],
                                              "answered": False, "flagged": False})
                for rec in self._failures.values():
                    if rec.get("ground_ts") is None and rec.get("symptom_seq") == ev["seq"]:
                        rec["ground_ts"] = now

    def _cuc_to_sim_ts(self, cuc, fallback: float) -> float:
        if cuc is None:
            return fallback - 3600.0
        try:
            from smo_common.protocol.ecss_packet import cuc_seconds_to_datetime
            off = (self.engine._build_clock_truth() or {}).get("offset_s") or 0.0
            return _epoch(cuc_seconds_to_datetime(float(cuc))) - float(off)
        except Exception:  # noqa: BLE001
            return fallback - 3600.0

    def _on_verification(self, subtype: int, data: bytes) -> None:
        try:
            from smo_common.protocol.pus_services import VerificationData
            v = VerificationData.parse(data, subtype)
        except Exception:  # noqa: BLE001
            return
        kinds = {1: ("tc_acc", "accepted", 1), 2: ("tc_rej", "rejected at acceptance", 2),
                 3: ("tc_start", "execution started", 1), 4: ("tc_fail", "execution start failed", 2),
                 7: ("tc_done", "completed", 1), 8: ("tc_fail", "execution failed", 2)}
        if subtype not in kinds or subtype == 3:
            return
        kind, word, sev = kinds[subtype]
        ref = f"{v.tc_apid}:{v.tc_seq}"
        text = f"TC {ref} {word}"
        if v.error_code:
            text += f" (0x{v.error_code:04X}{': ' + v.reason if v.reason else ''})"
        self.add("tc", kind, text, sev=sev, ref=ref)

    def _on_event_packet(self, p) -> None:
        df = p.data_field or b""
        if len(df) < 3:
            return
        event_id, severity = struct.unpack(">HB", df[:3])
        aux = ""
        if len(df) >= 8:
            n = df[7]
            aux = df[8:8 + n].decode("ascii", errors="replace")
        cat = self._event_cat.get(int(event_id), {})
        sub = cat.get("subsystem") or ""
        if (event_id & 0xF000) in (0x9000, 0xA000):
            sub = _PARAM_BANK.get((event_id & 0x0FFF) >> 8, "")
        elif not sub:
            sub = _EVENT_BANK.get(event_id >> 8, "")
        name = cat.get("name") or ""
        sev = max(1, min(4, int(severity)))
        focus = None
        if sev >= 3:
            focus = {"view": tx.VIEW_OF_SUBSYSTEM.get(sub, "overview"), "prio": 1,
                     "reason": "on-board alarm"}
        item = self.add("alarm", "event", (name + ": " if name else "") + aux,
                        sev=sev, sub=sub, ref=f"{event_id:#06x}",
                        data={"event_id": int(event_id)}, focus=focus)
        key = (p.primary.apid, p.primary.sequence_count)
        self._pending_ev[key] = {"seq": item["seq"], "ts": item["ts"], "sev": sev,
                                 "sub": sub, "name": name, "event_id": int(event_id)}
        while len(self._pending_ev) > 3000:
            self._pending_ev.popitem(last=False)
        if sev >= 2:
            for rec in self._failures.values():
                if rec.get("symptom_ts") is None and rec.get("cleared_ts") is None \
                        and (sub == rec["subsystem"] or sev >= 3 or not sub):
                    rec["symptom_ts"] = item["ts"]
                    rec["symptom_seq"] = item["seq"]
                    rec["symptom_text"] = item["text"][:120]

    # ── TC hooks ────────────────────────────────────────────────────────
    def on_tc_received(self, svc: int, sub: int, data: bytes, apid: int, seq: int,
                       *, link_refused: bool = False) -> None:
        func = data[0] if (svc == 8 and sub == 1 and data) else None
        name = (self._tc_names.get((svc, sub, func)) if func is not None
                else self._tc_names.get((svc, sub))) or ""
        ident = f"S{svc}.{sub}" + (f" func {func}" if func is not None else "")
        ref = f"{apid}:{seq}"
        if link_refused:
            self.add("tc", "tc_link", f"{name or ident} refused: no uplink", sev=2, ref=ref,
                     data={"service": svc, "subtype": sub, "func_id": func})
            return
        now = self.now_ts()
        self.add("tc", "tc_rx", f"{name or ident}" + (f" ({ident})" if name else ""),
                 sev=1, ref=ref, data={"service": svc, "subtype": sub, "func_id": func,
                                       "name": name})
        self._tc_seen_ts.append(now)
        if len(self._tc_seen_ts) > 500:
            self._tc_seen_ts = self._tc_seen_ts[-500:]
        for a in self._grounded_alarms:
            if not a["answered"] and now >= a["ts"]:
                a["answered"] = True
        for rec in self._failures.values():
            if rec.get("cleared_ts") is None and rec.get("response_ts") is None:
                start = rec.get("ground_ts") or rec.get("symptom_ts")
                if start is not None and now >= start:
                    rec["response_ts"] = now
                    rec["response_text"] = name or ident
        with self._lock:
            for e in self._schedule:
                t = e["trigger"]
                if e["state"] == "pending" and t.get("kind") == "tc" \
                        and t.get("service") == svc and t.get("subtype") == sub \
                        and (t.get("func_id") is None or t.get("func_id") == func):
                    self._fire_now.append(e["id"])

    # ── instructor actions ──────────────────────────────────────────────
    _INSTR_TEXT = {
        "set_speed": lambda c: f"Speed ×{c.get('value')}",
        "freeze": lambda c: "Simulation frozen",
        "resume": lambda c: "Simulation resumed",
        "override_passes": lambda c: "Pass override " + (
            "ON" if c.get("enabled", c.get("on", c.get("value"))) else "OFF/toggle"),
        "set_phase": lambda c: f"Phase set to {c.get('phase')}",
        "set_battery_soc": lambda c: f"Battery SoC override {c.get('soc_pct')} %",
        "start_separation": lambda c: "Separation started",
        "save_breakpoint": lambda c: f"Breakpoint saved \"{c.get('name', '')}\"",
        "load_breakpoint": lambda c: f"Breakpoint loaded \"{c.get('name', '')}\"",
        "start_scenario": lambda c: f"Scenario start \"{c.get('scenario') or c.get('name')}\"",
        "stop_scenario": lambda c: "Scenario stop",
        "set_session_label": lambda c: f"Session label \"{c.get('label', '')}\"",
        "failure_clear": lambda c: f"Clear failure {c.get('failure_id') or '(all)'}",
        "failure_clear_all": lambda c: "Clear all failures",
    }

    def on_instructor_cmd(self, cmd: dict) -> None:
        t = cmd.get("type")
        fn = self._INSTR_TEXT.get(t)
        if fn is None:
            return
        try:
            text = fn(cmd)
        except Exception:  # noqa: BLE001
            text = str(t)
        if t == "load_breakpoint":
            with self._lock:
                self.segment += 1
            self.ground.reset()
            self._prev.clear()
        self.add("instr", t, text, sev=2 if t in ("load_breakpoint", "set_phase",
                                                  "set_battery_soc") else 1)

    def mark(self, cmd: dict) -> tuple[bool, str]:
        kind = str(cmd.get("kind") or "bookmark")
        if kind not in ("bookmark", "anomaly"):
            return False, "mark kind must be bookmark or anomaly"
        text = " ".join(str(cmd.get("text") or "").split())[:160]
        disp = str(cmd.get("disposition") or "")
        if kind == "anomaly" and disp not in ("", "ignore", "restart", "work"):
            return False, "anomaly disposition must be ignore, restart or work"
        label = {"bookmark": "Bookmark", "anomaly": "Sim anomaly"}[kind]
        if disp:
            label += {"ignore": " (ignore)", "restart": " (restart from snapshot)",
                      "work": " (work as real)"}[disp]
        self.add("instr", kind, f"{label}: {text}" if text else label,
                 sev=2 if kind == "anomaly" else 1, data={"disposition": disp} if disp else None)
        return True, ""

    # ── per tick ────────────────────────────────────────────────────────
    def on_tick(self) -> None:
        eng = self.engine
        now = self.now_ts()
        p = eng.params
        o = eng.orbit.state
        cur = {
            "phase": int(getattr(eng, "_spacecraft_phase", 6)),
            "sc_mode": int(getattr(eng, "sc_mode", 0)),
            "obdh_mode": int(p.get(0x0300, 0) or 0),
            "sw_image": int(p.get(0x0311, 1) or 0),
            "aocs_mode": int(p.get(0x020F, 0) or 0),
            "contact": bool(eng.downlink_active),
            "eclipse": bool(o.in_eclipse),
            "fdir_level": int(p.get(0x0700, 0) or 0),
            "override": bool(getattr(eng, "_override_passes", False)),
        }
        prev = self._prev
        edges: set[str] = set()
        if prev:
            if cur["phase"] != prev["phase"]:
                n = PHASE_NAMES[cur["phase"]] if 0 <= cur["phase"] < 7 else cur["phase"]
                self.add("phase", "sc_phase", f"Spacecraft phase → {n}", sev=2,
                         data={"from": prev["phase"], "to": cur["phase"]},
                         focus={"view": "obc", "prio": 2, "reason": "phase change"})
            if cur["sc_mode"] != prev["sc_mode"]:
                why = self._mode_trigger()
                mode = dv.SC_MODE_NAMES.get(cur["sc_mode"], str(cur["sc_mode"]))
                contingency = mode in ("SAFE", "EMERGENCY") and cur["phase"] >= 6
                self.add("phase", "sc_mode", f"Spacecraft mode → {mode}"
                         + (f" ({why})" if why else ""), sev=3 if contingency else 1,
                         data={"from": prev["sc_mode"], "to": cur["sc_mode"], "trigger": why},
                         focus={"view": "obc", "prio": 3 if contingency else 1,
                                "reason": "spacecraft mode change"})
            if cur["obdh_mode"] != prev["obdh_mode"] or cur["sw_image"] != prev["sw_image"]:
                img = "application" if cur["sw_image"] else "bootloader"
                self.add("phase", "obc_mode",
                         f"OBC {dv.OBDH_MODE_NAMES.get(cur['obdh_mode'], cur['obdh_mode'])} · {img}",
                         sev=2, sub="obdh")
            if cur["aocs_mode"] != prev["aocs_mode"]:
                reason = getattr(getattr(eng.subsystems.get("aocs"), "_state", None),
                                 "mode_change_reason", "") or ""
                self.add("phase", "aocs_mode",
                         f"AOCS {AOCS_MODES.get(prev['aocs_mode'], prev['aocs_mode'])} → "
                         f"{AOCS_MODES.get(cur['aocs_mode'], cur['aocs_mode'])}"
                         + (f" ({reason})" if reason else ""), sev=1, sub="aocs")
            if cur["contact"] != prev["contact"]:
                gs = getattr(o, "active_gs", None) or ""
                kind = "aos" if cur["contact"] else "los"
                edges.add(kind)
                self.add("link", kind, ("AOS " + gs if cur["contact"] else "LOS " + (prev.get("gs") or "")).strip()
                         + (" (pass override)" if cur["override"] else ""),
                         focus={"view": "orbit", "prio": 1,
                                "reason": "acquisition of signal" if cur["contact"] else "loss of signal"})
            if cur["eclipse"] != prev["eclipse"]:
                kind = "ecl_in" if cur["eclipse"] else "ecl_out"
                edges.add("eclipse_entry" if cur["eclipse"] else "eclipse_exit")
                self.add("link", kind, "Eclipse entry" if cur["eclipse"] else "Eclipse exit",
                         focus={"view": "power", "prio": 1,
                                "reason": "eclipse entry" if cur["eclipse"] else "eclipse exit"}
                         if cur["eclipse"] else None)
            if cur["fdir_level"] != prev["fdir_level"]:
                self.add("proc", "fdir_level", f"FDIR level {prev['fdir_level']} → {cur['fdir_level']}",
                         sev=2 if cur["fdir_level"] > prev["fdir_level"] else 1, sub="obdh")
        cur["gs"] = getattr(o, "active_gs", None) or ""
        if prev:
            for k, v in prev.items():
                if k.startswith("_"):
                    cur[k] = v
        else:
            cur["_fdir_trig"] = dict(getattr(eng, "_fdir_triggered", {}) or {})
        self._prev = cur
        self._diff_failures(now)
        self._diff_procedures()
        self._diff_scenario()
        self._check_missed_cues(now)
        self._check_schedule(now, edges)

    def _mode_trigger(self) -> str:
        eng = self.engine
        trig = dict(getattr(eng, "_fdir_triggered", {}) or {})
        prev = self._prev.get("_fdir_trig", {})
        new = [k for k in trig if k not in prev]
        self._prev["_fdir_trig"] = trig
        if new:
            return "FDIR " + ", ".join(str(k) for k in new[:3])
        if int(getattr(eng, "_spacecraft_phase", 6)) < 6:
            return "phase < NOMINAL"
        return ""

    def _diff_failures(self, now: float) -> None:
        fm = getattr(self.engine, "_failure_manager", None)
        active = {}
        for af in (getattr(fm, "_failures", {}) or {}).values():
            if getattr(af, "active", False):
                active[af.failure_id] = af
        for fid, af in active.items():
            if fid in self._failures and self._failures[fid].get("cleared_ts") is None:
                continue
            el = tx.element_of(af.subsystem, af.failure)
            cls = tx.inject_class(af.subsystem, af.failure)
            view = tx.view_for(af.subsystem, af.failure)
            fn, obj = tx.function_of(af.subsystem, af.failure)
            extra = {k: v for k, v in (af.extra_params or {}).items()
                     if isinstance(v, (int, float, str, bool, list))}
            self._failures[fid] = {
                "fault_id": fid, "subsystem": af.subsystem, "failure": af.failure,
                "element": el, "inject_class": cls, "function": fn, "objective": obj,
                "element_label": next((e["label"] for e in tx.ELEMENTS if e["id"] == el), el),
                "params": extra, "magnitude": af.target_magnitude, "onset": af.onset,
                "inserted_ts": now, "symptom_ts": None, "ground_ts": None,
                "response_ts": None, "cleared_ts": None, "seg": self.segment,
            }
            detail = " ".join(f"{k}={v}" for k, v in extra.items())
            # A model may raise its first alarm in the same tick the inject
            # lands, before this diff runs: look back over the last seconds.
            rec_new = self._failures[fid]
            with self._lock:
                recent = [i for i in list(self._items)[-80:]
                          if i["lane"] == "alarm" and i["kind"] == "event" and i["sev"] >= 2
                          and i["ts"] >= now - 2.0 and (i["sub"] == af.subsystem or i["sev"] >= 3)]
            if recent:
                rec_new["symptom_ts"] = recent[0]["ts"]
                rec_new["symptom_seq"] = recent[0]["seq"]
                rec_new["symptom_text"] = recent[0]["text"][:120]
                downs = [i for i in list(self._items)[-80:] if i["kind"] == "ev_down"
                         and i["ref"] == str(recent[0]["seq"])]
                if downs:
                    rec_new["ground_ts"] = downs[0]["ts"]
            self.add("fault", "inject", f"Injected {af.subsystem}/{af.failure}"
                     + (f" ({detail})" if detail else ""), sev=3, sub=af.subsystem, ref=fid,
                     data={"element": el, "inject_class": cls},
                     focus={"view": view, "prio": 3, "reason": "inject fired",
                            "subject": f"{af.subsystem}/{af.failure}"})
        for fid, rec in self._failures.items():
            if rec.get("cleared_ts") is None and fid not in active:
                rec["cleared_ts"] = now
                self.add("fault", "clear", f"Cleared {rec['subsystem']}/{rec['failure']}",
                         sev=1, sub=rec["subsystem"], ref=fid)
        if len(self._failures) > 200:
            for k in list(self._failures)[:-200]:
                self._failures.pop(k, None)

    def _diff_procedures(self) -> None:
        eng = self.engine
        try:
            procs = {p["exec_id"]: p for p in eng._procedure_executor.get_active_procedures()}
        except Exception:  # noqa: BLE001
            procs = {}
        try:
            rec = {fid: rs.procedure for fid, rs in eng._fault_propagator.recovery_states().items()}
        except Exception:  # noqa: BLE001
            rec = {}
        prev_p = self._prev.get("_procs", {})
        prev_r = self._prev.get("_recov", {})
        for k, p in procs.items():
            if k not in prev_p:
                self.add("proc", "proc_start", f"On-board procedure {p.get('proc_id')} started",
                         sub="obdh", ref=str(k))
        for k, p in prev_p.items():
            if k not in procs:
                self.add("proc", "proc_end", f"On-board procedure {p.get('proc_id')} ended",
                         sub="obdh", ref=str(k))
        for fid, proc in rec.items():
            if fid not in prev_r:
                self.add("proc", "fdir_recovery", f"FDIR recovery for {fid}"
                         + (f" ({proc})" if proc else ""), sev=2, sub="obdh", ref=str(fid),
                         focus={"view": "obc", "prio": 2, "reason": "FDIR recovery started"})
        self._prev["_procs"] = procs
        self._prev["_recov"] = rec

    def _diff_scenario(self) -> None:
        se = getattr(self.engine, "_scenario_engine", None)
        try:
            name = se.current_name() if se is not None and se.is_active() else ""
        except Exception:  # noqa: BLE001
            name = ""
        if name != self._scenario_name:
            if name:
                self.add("phase", "scn_start", f"Scenario started: {name}", sev=2,
                         ref=name, focus={"view": "overview", "prio": 2,
                                          "reason": "scenario started"})
            else:
                self.add("phase", "scn_end", f"Scenario ended: {self._scenario_name}",
                         sev=2, ref=self._scenario_name,
                         focus={"view": "debrief", "prio": 3, "reason": "scenario ended"})
            self._scenario_name = name

    def _check_missed_cues(self, now: float) -> None:
        for a in self._grounded_alarms:
            if a["answered"] or a["flagged"] or a["sev"] < 3:
                continue
            if now - a["ts"] >= MISSED_CUE_S:
                a["flagged"] = True
                self.add("alarm", "missed_cue",
                         f"No telecommand {int(MISSED_CUE_S // 60)} min after "
                         f"{a['name'] or 'an alarm'} reached the ground", sev=2, sub=a["sub"],
                         ref=str(a["seq"]),
                         focus={"view": tx.VIEW_OF_SUBSYSTEM.get(a["sub"], "overview"),
                                "prio": 2, "reason": "alarm not acted on"})
        if len(self._grounded_alarms) > 300:
            self._grounded_alarms = self._grounded_alarms[-300:]

    # ── fault swimlanes ─────────────────────────────────────────────────
    def fault_lanes(self) -> list[dict]:
        out = []
        for rec in list(self._failures.values()):
            r = dict(rec)
            ins = r["inserted_ts"]

            def gap(a, b):
                return None if a is None or b is None else round(b - a, 1)
            r["latency"] = {
                "to_symptom_s": gap(ins, r.get("symptom_ts")),
                "to_ground_s": gap(r.get("symptom_ts"), r.get("ground_ts")),
                "to_response_s": gap(r.get("ground_ts") or r.get("symptom_ts"), r.get("response_ts")),
                "to_clear_s": gap(ins, r.get("cleared_ts")),
            }
            out.append(r)
        return out

    # ── views bundle (truth + divergence), built on the tick thread ─────
    def maybe_build_views(self, force: bool = False) -> None:
        wall = time.monotonic()
        if not force and wall - self._views_wall < VIEWS_MIN_INTERVAL_S:
            return
        self._views_wall = wall
        try:
            from . import truth
            now = self.now_ts()
            rows = dv.evaluate(self.engine, self.ground, now_ts=now)
            self._note_divergence(rows)
            views = truth.build_views(self.engine, self, rows, now)
            views["divergence"] = {"rows": rows, "summary": dv.summarise(rows),
                                   "ground_last_rx": (None if self.ground.last_rx_ts is None
                                                      else round(now - self.ground.last_rx_ts, 1))}
            views["schedule"] = self.schedule_list()
            views["now_ts"] = now
            views["now"] = _iso(now)
            self._record_history(now, rows, views)
        except Exception as e:  # noqa: BLE001 — never kill the tick
            logger.warning("Instructor views build failed: %s", e, exc_info=True)
            return
        with self._lock:
            self._views = views

    def published(self) -> Optional[dict]:
        with self._lock:
            return self._views

    def _note_divergence(self, rows: list[dict]) -> None:
        for r in rows:
            cause = r.get("cause") if r.get("state") == "diverged" else None
            was = self._div_state.get(r["id"])
            if cause in ("injected", "estimator") and was not in ("injected", "estimator"):
                self.add("fault", "diverge",
                         f"{r['label']}: the spacecraft's value is off the truth ({cause})",
                         sev=2, sub=r["subsystem"], ref=r["id"],
                         focus={"view": "divergence", "prio": 2,
                                "reason": "telemetry diverges from truth"})
            self._div_state[r["id"]] = cause

    def _record_history(self, now: float, rows: list[dict], views: dict) -> None:
        if self._last_hist_ts is not None and 0 <= now - self._last_hist_ts < HISTORY_EVERY_S:
            return
        self._last_hist_ts = now
        sample = {"ts": round(now, 1), "seg": self.segment,
                  "pairs": {r["id"]: [r.get("truth"), r.get("onboard"), r.get("ground"),
                                      r.get("cause") if r.get("state") == "diverged" else None]
                            for r in rows},
                  "tiles": {t["id"]: t.get("state") for t in views.get("overview", {}).get("tiles", [])}}
        with self._lock:
            self._history.append(sample)

    def history(self, seg: Optional[int] = None) -> list[dict]:
        with self._lock:
            return [dict(h) for h in self._history if seg is None or h["seg"] == seg]


def _finite(v) -> bool:
    try:
        return math.isfinite(float(v))
    except (TypeError, ValueError):
        return False
