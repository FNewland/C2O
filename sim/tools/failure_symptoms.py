#!/usr/bin/env python3
"""Inject every catalogued failure headless and find its first symptom.

Companion of ``configs/eosat1/instructor/expected_symptoms.yaml`` (Franz's
ruling of 2026-11-03, docs/plan_2026-11/REDESIGN_DECISIONS.md): the
instructor console's "first symptom" (time from inject to the first on-board
symptom) is the first of the failure's EXPECTED symptoms, not the first
warning of any kind. This tool is how those expectations are derived and
kept honest.

For each (subsystem, failure) in the failure catalogue it:

1. restores a prepared spacecraft state (the failure's ``context`` in the
   YAML: ``nominal`` = NOMINAL nadir pointing, payload STANDBY, heater lines
   and transmitter on; ``imaging`` = the same with the FPA cooled, FINE
   pointing, IMAGING and a capture every 60 s; ``contact`` = nominal with the
   pass override on), flown there by telecommand from the default start;
2. runs the same state WITHOUT the failure (control) and WITH it, for the
   failure's ``window_s``, recording every S5 event (S12 reports arrive as
   0x9xxx), and every parameter that leaves its mcs/limits.yaml band (with
   its ``valid_when`` honoured);
3. reports the first observation that the control run does not also show,
   and when each EXPECTED symptom was first met.

Modes::

    python3 tools/failure_symptoms.py --report [--only eps.bus_short ...]
    python3 tools/failure_symptoms.py --check        # exit 1 on a mismatch
    python3 tools/failure_symptoms.py --json out.json

``--check`` passes when every failure has at least one expected symptom and,
unless the entry is marked ``checkable: false`` (with a reason: the symptom
needs a ground-station pass, a burn or another team action), one of its
expected symptoms is met inside the window in the injected run and not in the
control run.

Symptom kinds (YAML ``symptoms:`` list, any of):

* ``{event: 0x0105}``           an S5 event id (any severity);
* ``{s12: 0x0101}``             the S12 monitor on that parameter reports a
                                violation (S5 0x9000 | id & 0x0FFF);
* ``{param: 0x0105, limit: true}``  the parameter leaves its mcs/limits.yaml
                                nominal band (yellow or red);
* ``{param: 0x0105, below: 27.0}`` / ``{param: ..., above: x}``;
* ``{param: 0x0302, change: 1.0}``  moves by at least this much from its
                                value at the inject;
  any ``param`` symptom may carry ``when: {param: id, value: v}``: judged
  only while that parameter equals v (e.g. sunlit: eclipse flag 0x0108 = 0),
  and ``for_s: n``: the condition must hold n seconds without a break;
* ``{clock_offset_s: 1.0}``     the on-board clock moves this far from true
                                time, relative to its offset at the inject
                                (what the ground sees in the packet time
                                stamps against reception time).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
for pkg in ("smo-common", "smo-simulator"):
    p = REPO / "packages" / pkg / "src"
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("SMO_DUMP_DIR", tempfile.mkdtemp(prefix="symptoms_"))
logging.disable(logging.WARNING)

import yaml  # noqa: E402

CONFIG = REPO / "configs" / "eosat1"
SYMPTOMS_FILE = CONFIG / "instructor" / "expected_symptoms.yaml"


# ── spacecraft states ────────────────────────────────────────────────

def _engine():
    from smo_simulator.engine import SimulationEngine
    return SimulationEngine(CONFIG, speed=1.0)


def _tc(eng, *data):
    res = eng._dispatcher.dispatch(8, 1, bytes(data), None)
    if res.error is not None:
        raise RuntimeError(f"TC {data} refused: {res.error}")


def _run(eng, seconds, dt=5.0):
    for _ in range(int(seconds / dt)):
        eng._tick_once(dt)


def build_contexts() -> dict[str, dict]:
    """Fly the default start to the prepared states; returns breakpoints."""
    from smo_simulator.breakpoints import BreakpointManager
    eng = _engine()
    _tc(eng, 55)                       # boot the application
    _run(eng, 20)
    _tc(eng, 19, 7)                    # wheels line
    _tc(eng, 19, 2)                    # transmitter line
    _run(eng, 10)
    for w in range(4):
        _tc(eng, 3, w)
    _tc(eng, 4, 1)
    _tc(eng, 5, 1)                     # star trackers
    _run(eng, 30)
    _tc(eng, 0, 3)                     # coarse sun
    _run(eng, 300)
    _tc(eng, 0, 4)                     # nadir
    _run(eng, 600)
    _tc(eng, 120, 5, 0)
    _run(eng, 10)
    _tc(eng, 120, 6, 0)                # mission phase NOMINAL
    _run(eng, 10)
    e = eng.subsystems["eps"]._state
    e.wing_py_deployed = e.wing_my_deployed = True
    for line in (3, 5, 6):             # payload, battery and OBC heater lines
        _tc(eng, 19, line)
    _run(eng, 5)
    _tc(eng, 26, 1)                    # payload STANDBY (cooler off)
    _run(eng, 1800)
    states = {"nominal": BreakpointManager(eng).save("nominal")}

    eng._override_passes = True
    _run(eng, 20)
    states["contact"] = BreakpointManager(eng).save("contact")
    eng._override_passes = False

    _tc(eng, 43, 1)                    # FPA cooler: imaging preparation
    _run(eng, 600)
    for _ in range(240):               # FINE needs aocs.fine_ready == 0
        if int(eng.params.get(0x02C5, 1) or 0) == 0:
            break
        _run(eng, 5)
    try:
        _tc(eng, 0, 5)                 # FINE_POINT
    except RuntimeError as e:          # the captures will be refused
        print(f"imaging context without FINE_POINT: {e}", flush=True)
    _run(eng, 120)
    _tc(eng, 26, 2)                    # IMAGING
    _tc(eng, 119, 1)                   # shutter open
    _run(eng, 10)
    states["imaging"] = BreakpointManager(eng).save("imaging")
    return states


# ── observation ──────────────────────────────────────────────────────

def _load_limits():
    rows = yaml.safe_load((CONFIG / "mcs" / "limits.yaml").read_text())["limits"]
    return {int(r["param_id"]): r for r in rows}


def _limit_state(lim, params) -> str:
    vw = lim.get("valid_when")
    if vw:
        raw = params.get(int(vw["param_id"]))
        if raw is None or (int(round(float(raw))) & int(vw.get("mask", 0xFFFFFFFF))) \
                != int(vw.get("value", 1)):
            return "unchecked"
    v = params.get(int(lim["param_id"]))
    if v is None:
        return "unknown"
    v = float(v)
    for key, cmp in (("red_low", v.__lt__), ("red_high", v.__gt__),
                     ("yellow_low", v.__lt__), ("yellow_high", v.__gt__)):
        b = lim.get(key)
        if b is not None and cmp(float(b)):
            return key
    return "nominal"


class Recorder:
    """Every event and every ground-limit departure, with sim seconds."""

    def __init__(self, eng, limits):
        from smo_simulator.engine import _SEVERITY_NAME_TO_INT
        self.eng, self.limits, self.t = eng, limits, 0.0
        self.events: list[tuple[float, int, int]] = []
        self.limit_hits: list[tuple[float, int, str]] = []
        self._limit_prev = {pid: _limit_state(l, eng.params) for pid, l in limits.items()}
        orig = eng._emit_event
        self._orig = orig

        def spy(ev, _orig=orig):
            sev = ev.get("severity", 1)
            if isinstance(sev, str):
                sev = _SEVERITY_NAME_TO_INT.get(sev.strip().upper(), 1)
            self.events.append((self.t, int(ev.get("event_id", 0)), int(sev)))
            return _orig(ev)
        eng._emit_event = spy

    def close(self):
        self.eng._emit_event = self._orig

    def step(self, dt):
        self.eng._tick_once(dt)
        self.t += dt
        for pid, lim in self.limits.items():
            st = _limit_state(lim, self.eng.params)
            prev = self._limit_prev.get(pid)
            if st != prev and st.startswith(("yellow", "red")):
                self.limit_hits.append((self.t, pid, st))
            self._limit_prev[pid] = st


def observations(rec: Recorder) -> list[tuple[float, str]]:
    """Alarm-class observations in time order, as symptom labels."""
    out = []
    for t, eid, sev in rec.events:
        if (eid & 0xF000) == 0x9000:
            out.append((t, f"s12:0x{eid & 0x0FFF:04X}"))
        elif (eid & 0xF000) == 0xA000:
            continue
        elif sev >= 2:
            out.append((t, f"event:0x{eid:04X}"))
    for t, pid, st in rec.limit_hits:
        out.append((t, f"limit:0x{pid:04X}"))
    out.sort(key=lambda x: x[0])
    return out


def symptom_label(s: dict) -> str:
    if "event" in s:
        return f"event:0x{int(s['event']):04X}"
    if "s12" in s:
        return f"s12:0x{int(s['s12']) & 0x0FFF:04X}"
    if "clock_offset_s" in s:
        return f"clock_offset_s:{s['clock_offset_s']}"
    pid = int(s["param"])
    if s.get("limit"):
        return f"limit:0x{pid:04X}"
    for k in ("below", "above", "change"):
        if k in s:
            return f"param:0x{pid:04X}:{k}:{s[k]}"
    return f"param:0x{pid:04X}"


def first_met(sym: dict, rec: Recorder, trace: list[tuple[float, dict]],
              base: dict) -> float | None:
    """Sim seconds after the inject at which `sym` is first met, or None."""
    if "event" in sym:
        eid = int(sym["event"])
        return next((t for t, e, _ in rec.events if e == eid), None)
    if "s12" in sym:
        eid = 0x9000 | (int(sym["s12"]) & 0x0FFF)
        return next((t for t, e, _ in rec.events if e == eid), None)
    if "clock_offset_s" in sym:
        b = base.get("clock_offset_s") or 0.0
        return next((t for t, params in trace
                     if params.get("clock_offset_s") is not None
                     and abs(params["clock_offset_s"] - b)
                     >= float(sym["clock_offset_s"])), None)
    pid = int(sym["param"])
    if sym.get("limit"):
        return next((t for t, p, _ in rec.limit_hits if p == pid), None)
    when = sym.get("when")
    hold = float(sym.get("for_s", 0.0) or 0.0)
    since = None
    for t, params in trace:
        v = params.get(pid)
        hit = False
        if v is not None and not (when and params.get(int(when["param"])) != when["value"]):
            v = float(v)
            hit = (("below" in sym and v < float(sym["below"]))
                   or ("above" in sym and v > float(sym["above"]))
                   or ("change" in sym and base.get(pid) is not None
                       and abs(v - float(base[pid])) >= float(sym["change"])))
        if not hit:
            since = None
            continue
        since = t if since is None else since
        if t - since >= hold:
            return t
    return None


def run_one(eng, state, sub, fail, spec_entry, limits, inject: bool) -> dict:
    from smo_simulator import failure_catalog as fc
    from smo_simulator.breakpoints import BreakpointManager
    BreakpointManager(eng).load(json.loads(json.dumps(state, default=str)))
    eng._fdir_enabled = True
    window = float(spec_entry.get("window_s", 1800))
    capture = spec_entry.get("context") == "imaging"
    for _ in range(5):                 # settle: restored parameters refresh
        eng._tick_once(1.0)
    base = dict(eng.params)
    try:
        base["clock_offset_s"] = (eng._build_clock_truth() or {}).get("offset_s")
    except Exception:  # noqa: BLE001
        base["clock_offset_s"] = None
    rec = Recorder(eng, limits)
    if inject:
        spec = fc.get_spec(sub, fail)
        eng._failure_manager.inject(sub, fail, magnitude=spec.default_magnitude(),
                                    onset="step", **spec.defaults())
    trace = []
    next_capture = 5.0
    while rec.t < window:
        dt = 1.0 if rec.t < 120 else 5.0
        if capture and rec.t >= next_capture:
            try:
                _tc(eng, 28, 0, 0, 0x08, 0x00)
            except RuntimeError:
                pass
            next_capture += 60.0
        rec.step(dt)
        snap = dict(eng.params)          # every parameter (cached control)
        try:
            snap["clock_offset_s"] = (eng._build_clock_truth() or {}).get("offset_s")
        except Exception:  # noqa: BLE001
            snap["clock_offset_s"] = None
        trace.append((rec.t, snap))
    final = dict(eng.params)
    eng._failure_manager.clear_all()
    rec.close()
    return {"rec": rec, "trace": trace, "base": base, "final": final}


def analyse(sub, fail, entry, states, limits, eng, cache) -> dict:
    ctx = entry.get("context", "nominal")
    key = (ctx, float(entry.get("window_s", 1800)))
    if key not in cache:
        cache[key] = run_one(eng, states[ctx], sub, fail, entry, limits, False)
    control = cache[key]
    run = run_one(eng, states[ctx], sub, fail, entry, limits, True)
    ctrl_obs = {lab for _, lab in observations(control["rec"])}
    obs = [(t, lab) for t, lab in observations(run["rec"]) if lab not in ctrl_obs]
    met = {}
    for s in entry.get("symptoms", []):
        t = first_met(s, run["rec"], run["trace"], run["base"])
        tc_ = first_met(s, control["rec"], control["trace"], control["base"])
        # Met in the control run too, and not earlier with the failure: the
        # symptom is background, not the failure's.
        met[symptom_label(s)] = {"t": t, "in_control": tc_ is not None
                                 and (t is None or tc_ <= t)}
    # Low-severity events the control run does not show, and the parameters
    # that end furthest from the control (relative), for populating params.
    ctrl_ev = {e for _, e, _ in control["rec"].events}
    info = []
    for t, e, sev in run["rec"].events:
        if sev < 2 and e not in ctrl_ev and (e & 0xF000) not in (0x9000, 0xA000):
            info.append((t, f"event:0x{e:04X}"))
    diffs = []
    for pid, v in run["final"].items():
        c = control["final"].get(pid)
        if not isinstance(v, (int, float)) or not isinstance(c, (int, float)):
            continue
        d = abs(float(v) - float(c))
        rel = d / max(abs(float(c)), 1.0)
        if rel > 0.05:
            diffs.append((rel, f"0x{pid:04X}", round(float(c), 3), round(float(v), 3)))
    diffs.sort(reverse=True)
    return {"failure": f"{sub}.{fail}", "context": ctx,
            "first_observed": obs[:5], "info_events": info[:5],
            "param_diffs": [d[1:] for d in diffs[:8]], "expected": met}


def load_expected() -> dict:
    return (yaml.safe_load(SYMPTOMS_FILE.read_text(encoding="utf-8"))
            or {}).get("expected_symptoms", {}) if SYMPTOMS_FILE.exists() else {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args(argv)
    from smo_simulator import failure_catalog as fc

    expected = load_expected()
    pairs = sorted(fc.all_failure_names())
    if args.only:
        pairs = [p for p in pairs if f"{p[0]}.{p[1]}" in set(args.only)]
    missing = [f"{s}.{f}" for s, f in pairs
               if not (expected.get(f"{s}.{f}") or {}).get("symptoms")]
    states = build_contexts()
    limits = _load_limits()
    eng = _engine()
    cache: dict = {}
    results, failures = [], []
    for sub, fail in pairs:
        entry = expected.get(f"{sub}.{fail}") or {}
        r = analyse(sub, fail, entry, states, limits, eng, cache)
        results.append(r)
        ok = True
        if entry.get("symptoms") and entry.get("checkable", True):
            hits = [v for v in r["expected"].values()
                    if v["t"] is not None and not v["in_control"]]
            ok = bool(hits)
        if args.report or not ok:
            exp = ", ".join(f"{k}@{v['t']:.0f}s" if v["t"] is not None else f"{k}@-"
                            for k, v in r["expected"].items())
            obs = ", ".join(f"{lab}@{t:.0f}s" for t, lab in r["first_observed"])
            if args.report and not r["first_observed"]:
                obs = ("info " + ", ".join(f"{lab}@{t:.0f}s" for t, lab in r["info_events"])
                       + " | params " + ", ".join(f"{p}:{c}->{v}" for p, c, v in r["param_diffs"][:5]))
            print(f"{'ok ' if ok else 'BAD'} {r['failure']:34s} [{r['context']}] "
                  f"observed: {obs or '-'} | expected: {exp or '-'}", flush=True)
        if not ok:
            failures.append(r["failure"])
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1, default=str))
    if missing:
        print(f"no expected symptoms: {missing}")
    if args.check:
        if missing or failures:
            print(f"CHECK FAILED: {len(missing)} without symptoms, "
                  f"{len(failures)} not met: {failures}")
            return 1
        print(f"check passed: {len(pairs)} failures, every expected symptom set met "
              f"(or declared not checkable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
