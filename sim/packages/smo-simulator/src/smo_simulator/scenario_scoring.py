"""SMO Simulator — scenario scoring from the commands the team sends.

INSTRUCTOR_CONSOLE_DESIGN.md §13 item 3 (ruled 2026-11-03): the scenario score
used to be ``recorded responses / expected responses`` and nothing ever
recorded a response, so every debrief said 0 %. The simulator cannot see the
ground (displays watched, voice loops, procedure steps); what it CAN see is
every telecommand the team uplinks, what the spacecraft did with it (S1
acceptance / completion / failure) and the state the spacecraft ends up in.
This module scores from that evidence and nothing else.

Scenario schema (``expected_responses`` items; every key but ``category`` and
``description`` is optional)::

    - category: recover            # detect | isolate | recover | verify | command | ...
      description: "Disable RW1 and desaturate"
      id: disable_rw1              # name for `after:` (default r<index>)
      tc: AOCS_DISABLE_WHEEL(wheel_idx=0)      # or a list: ANY of them counts
      state: "aocs.rw1_enabled == 0"           # or a list: ALL must hold
      within_s: 600                # target, seconds after the reference
      after: [isolate_rw1]         # only counts once these responses are met
      ref: inject                  # inject (default) | start | event:<index>
      weight: 1

    harmful_commands:              # top level, optional
      - tc: AOCS_ENABLE_WHEEL(wheel_idx=0)
        reason: "Re-enables the seized wheel"
        penalty: 10                # percentage points (default 10)

``tc`` uses the procedure notation: a TC catalogue name, optionally with the
arguments that must match (engineering values; ``a=1|2`` accepts either).
``state`` is ``<parameter> <op> <value>``; the parameter is a name from
telemetry/parameters.yaml or a hex/decimal id.

Scoring model (each expected response, against the scenario's reference time —
by default the first injected fault):

=========  ====================================================  ======
status     evidence                                              credit
=========  ====================================================  ======
done       a matching TC the spacecraft did not reject or fail     100 %
           (and, if ``state`` is declared, that state reached
           afterwards), within ``within_s`` of the reference
late       the same, after ``within_s``                             50 %
wrong      a matching TC was sent but rejected / failed, or sent      0 %
           and the declared state never followed, or sent only
           before a prerequisite (``after:``) was met
missed     no matching TC (and no state, for a state-only check)      0 %
observed   no ``tc``/``state`` declared: the simulator cannot see   (not
           it; the instructor judges it in the debrief             scored)
=========  ====================================================  ======

``score = 100 x sum(weight x credit) / sum(weight)`` over the scored
responses, minus the penalty of each harmful-command entry that was sent at
least once after the reference (once per entry), clamped to 0..100. A
scenario with nothing machine-checkable has no score (``None``), not 0 %.

Mean times, from the same evidence (seconds after the reference):

* MTTD — the first satisfied ``detect`` response; otherwise the first
  telecommand that matches ANY expected response (marked *inferred*: the
  team must have detected the fault before acting on it).
* MTTI — the first satisfied ``isolate`` response; otherwise the first
  satisfied ``recover`` response (inferred).
* MTTR — when every scored ``recover`` response has been satisfied (the latest
  of them); ``None`` while any is outstanding.

Everything here is pure: the scenario engine feeds the evidence log
(``observe_*``) and ``evaluate()`` turns it into the debrief, so the result is
reproducible from a saved log and testable without an engine.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

CREDIT = {"done": 1.0, "late": 0.5, "wrong": 0.0, "missed": 0.0}
#: Default target (s after the reference) per category, overridable in
#: simulation.yaml scenario_defaults.response_targets_s and per response.
DEFAULT_TARGETS_S = {"detect": 300.0, "isolate": 600.0, "recover": 900.0,
                     "verify": 1200.0, "command": 600.0, "action": 600.0,
                     "monitor": 600.0, "plan": 1800.0}
FALLBACK_TARGET_S = 900.0
DEFAULT_PENALTY = 10.0
#: S1 fates that mean the spacecraft did not do what was asked.
BAD_FATES = frozenset({"rejected", "failed", "not_uplinked"})
_OPS = ("<=", ">=", "==", "!=", "<", ">")
_TC_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*(?:\((.*)\))?\s*$")
_STATE_RE = re.compile(r"^\s*([A-Za-z0-9_.]+)\s*(<=|>=|==|!=|<|>)\s*(\S+)\s*$")


# ── catalogues ────────────────────────────────────────────────────────────

def _tc_catalog(config_dir):
    from smo_common.commanding.catalog import load_catalog
    return load_catalog(config_dir)


_PARAM_CACHE: dict[str, dict[str, int]] = {}


def _param_ids(config_dir) -> dict[str, int]:
    """telemetry/parameters.yaml name -> id (cached per config dir)."""
    try:
        from smo_common.commanding.catalog import find_config_dir
        cdir = find_config_dir(config_dir)
    except Exception:  # noqa: BLE001
        return {}
    key = str(Path(cdir).resolve())
    if key not in _PARAM_CACHE:
        import yaml
        out: dict[str, int] = {}
        try:
            doc = yaml.safe_load((Path(cdir) / "telemetry" / "parameters.yaml")
                                 .read_text(encoding="utf-8")) or {}
            for p in doc.get("parameters") or []:
                if isinstance(p, dict) and p.get("name") and p.get("id") is not None:
                    out[str(p["name"])] = int(p["id"])
        except Exception as e:  # noqa: BLE001
            logger.debug("parameters.yaml not loaded for scoring: %s", e)
        _PARAM_CACHE[key] = out
    return _PARAM_CACHE[key]


def _scalar(text: str) -> Any:
    t = text.strip().strip('"').strip("'")
    try:
        return int(t, 0)
    except ValueError:
        pass
    try:
        return float(t)
    except ValueError:
        return t


# ── parsing (load time: errors become scenario load issues) ───────────────

def parse_tc(text: str, catalog) -> dict:
    """``NAME(arg=v, arg=v1|v2)`` -> {name, service, subtype, func_id, args}."""
    m = _TC_RE.match(str(text or ""))
    if not m:
        raise ValueError(f"tc {text!r} is not NAME or NAME(arg=value, ...)")
    name, body = m.group(1), (m.group(2) or "").strip()
    try:
        cmd = catalog.get(name)
    except KeyError as e:
        raise ValueError(str(e)) from None
    args: dict[str, list] = {}
    fields = {f.get("name") for f in cmd.get("fields") or []}
    if body:
        for part in body.split(","):
            if "=" not in part:
                raise ValueError(f"tc {text!r}: argument {part.strip()!r} needs name=value")
            k, v = (s.strip() for s in part.split("=", 1))
            if k not in fields:
                raise ValueError(f"tc {text!r}: {cmd['name']} has no argument {k!r} "
                                 f"(has: {', '.join(sorted(f for f in fields if f)) or 'none'})")
            args[k] = [_scalar(x) for x in v.split("|")]
    return {"name": cmd["name"], "text": str(text).strip(),
            "service": int(cmd["service"]), "subtype": int(cmd["subtype"]),
            "func_id": None if cmd.get("func_id") is None else int(cmd["func_id"]),
            "args": args}


def parse_state(text: str, param_ids: dict[str, int]) -> dict:
    m = _STATE_RE.match(str(text or ""))
    if not m:
        raise ValueError(f"state {text!r} is not '<parameter> <op> <value>'")
    pname, op, val = m.group(1), m.group(2), m.group(3)
    try:
        pid = int(pname, 0)
    except ValueError:
        if pname not in param_ids:
            raise ValueError(f"state {text!r}: unknown parameter {pname!r}") from None
        pid = param_ids[pname]
    try:
        value = float(_scalar(val))
    except (TypeError, ValueError):
        raise ValueError(f"state {text!r}: value must be a number") from None
    return {"text": str(text).strip(), "param": pname, "pid": pid, "op": op, "value": value}


def _as_list(v) -> list:
    if v is None or v == "" or v == []:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def parse_ref(v) -> tuple[str, Optional[int]]:
    if v in (None, "", "inject"):
        return "inject", None
    if v == "start":
        return "start", None
    m = re.match(r"^event:(\d+)$", str(v))
    if m:
        return "event", int(m.group(1))
    raise ValueError(f"ref {v!r} must be inject, start or event:<index>")


def compile_rules(expected: list, harmful: list, *, catalog, param_ids: dict,
                  targets: dict, n_events: int) -> tuple[list[dict], list[dict], list[str]]:
    """Validate and compile the scenario's scoring declarations.

    Returns ``(responses, harmful, errors)``; a response or harmful entry with
    an error keeps its text (it is still listed in the debrief) but is not
    machine-checked.
    """
    errors: list[str] = []
    responses: list[dict] = []
    ids: set[str] = set()
    for i, r in enumerate(expected or []):
        r = r if isinstance(r, dict) else {"description": str(r)}
        cat = str(r.get("category") or "recover")
        rid = str(r.get("id") or f"r{i}")
        if rid in ids:
            errors.append(f"expected_responses[{i}]: duplicate id {rid!r}")
        ids.add(rid)
        out = {"i": i, "id": rid, "category": cat,
               "description": str(r.get("description") or "").strip(),
               "tc": [], "state": [], "after": [str(a) for a in _as_list(r.get("after"))],
               "weight": 1.0, "target_s": float(targets.get(cat, FALLBACK_TARGET_S)),
               "ref": ("inject", None), "error": None}
        try:
            out["tc"] = [parse_tc(t, catalog) for t in _as_list(r.get("tc"))]
            out["state"] = [parse_state(s, param_ids) for s in _as_list(r.get("state"))]
            if r.get("within_s") is not None:
                out["target_s"] = float(r["within_s"])
                if out["target_s"] <= 0:
                    raise ValueError("within_s must be > 0")
            if r.get("weight") is not None:
                out["weight"] = float(r["weight"])
                if out["weight"] <= 0:
                    raise ValueError("weight must be > 0")
            out["ref"] = parse_ref(r.get("ref"))
            if out["ref"][0] == "event" and not (0 <= out["ref"][1] < n_events):
                raise ValueError(f"ref event:{out['ref'][1]} — the scenario has "
                                 f"{n_events} event(s)")
        except (ValueError, TypeError) as e:
            out["error"] = str(e)
            out["tc"], out["state"] = [], []
            errors.append(f"expected_responses[{i}]: {e}")
        responses.append(out)
    for r in responses:
        for dep in r["after"]:
            if dep not in ids or dep == r["id"]:
                errors.append(f"expected_responses[{r['i']}]: after {dep!r} is not "
                              f"another response's id")
        r["after"] = [d for d in r["after"] if d in ids and d != r["id"]]
    harm: list[dict] = []
    for i, h in enumerate(harmful or []):
        h = h if isinstance(h, dict) else {}
        out = {"i": i, "reason": str(h.get("reason") or "").strip(), "tc": [],
               "penalty": DEFAULT_PENALTY, "ref": ("inject", None), "error": None}
        try:
            out["tc"] = [parse_tc(t, catalog) for t in _as_list(h.get("tc"))]
            if not out["tc"]:
                raise ValueError("harmful_commands entry needs tc")
            if h.get("penalty") is not None:
                out["penalty"] = float(h["penalty"])
                if not (0 <= out["penalty"] <= 100):
                    raise ValueError("penalty must be 0..100")
            out["ref"] = parse_ref(h.get("ref"))
        except (ValueError, TypeError) as e:
            out["error"] = str(e)
            out["tc"] = []
            errors.append(f"harmful_commands[{i}]: {e}")
        harm.append(out)
    return responses, harm, errors


# ── matching ──────────────────────────────────────────────────────────────

def _decode(spec: dict, data_hex: str, catalog) -> Optional[dict]:
    try:
        from smo_common.commanding.decode import decode
        _name, args = decode(bytes.fromhex(data_hex), service=spec["service"],
                             subtype=spec["subtype"], catalog=catalog, name=spec["name"])
        return args
    except Exception:  # noqa: BLE001 — undecodable bytes simply do not match
        return None


def _eq(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return str(a).strip().lower() == str(b).strip().lower()


def tc_matches(spec: dict, tc: dict, catalog) -> bool:
    if (tc["service"], tc["subtype"]) != (spec["service"], spec["subtype"]):
        return False
    if spec["func_id"] is not None and tc.get("func_id") != spec["func_id"]:
        return False
    if not spec["args"]:
        return True
    args = _decode(spec, tc.get("data", ""), catalog)
    if args is None:
        return False
    return all(k in args and any(_eq(args[k], v) for v in vals)
               for k, vals in spec["args"].items())


def state_holds(check: dict, value) -> bool:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    t, op = check["value"], check["op"]
    return {"==": abs(v - t) < 1e-3, "!=": abs(v - t) >= 1e-3, "<": v < t,
            "<=": v <= t, ">": v > t, ">=": v >= t}[op]


# ── the evidence log ──────────────────────────────────────────────────────

class ScenarioScorer:
    """Evidence log for one scenario run + the pure evaluation.

    Times are scenario-elapsed SIM seconds (``ScenarioEngine.elapsed_s``).
    """

    MAX_TCS = 2000

    def __init__(self, responses: list[dict], harmful: list[dict], *,
                 catalog, has_inject_events: bool = False,
                 has_initial_failures: bool = False):
        self.responses = responses
        self.harmful = harmful
        self._catalog = catalog
        # Reference "inject" for a scenario with no fault at all (first
        # contact, checkout) is the scenario start.
        self._has_inject = bool(has_inject_events)
        self._key_count: dict[tuple, int] = {}
        for c in getattr(catalog, "commands", []) or []:
            k = (int(c["service"]), int(c["subtype"]), c.get("func_id"))
            self._key_count[k] = self._key_count.get(k, 0) + 1
        self.tcs: list[dict] = []
        self.events: dict[int, float] = {}       # event index -> fired at
        self.first_inject: Optional[float] = 0.0 if has_initial_failures else None
        # state check key -> [[t, bool], ...] transitions
        self.states: dict[str, list] = {}
        self.marks: list[dict] = []              # instructor-recorded responses
        self._checks = {c["text"]: c for r in responses for c in r["state"]}

    # -- feeding ------------------------------------------------------
    def _name_of(self, svc: int, sub: int, func) -> str:
        """Catalogue name, or S<svc>.<sub> where several commands share it."""
        if self._key_count.get((svc, sub, func)) == 1:
            cmd = self._catalog.by_func(svc, sub, func)
            if cmd is not None:
                return cmd["name"]
        return f"S{svc}.{sub}" + (f" func {func}" if func is not None else "")

    def observe_tc(self, t: float, svc: int, sub: int, data: bytes, apid: int,
                   seq: int, *, link_refused: bool = False) -> None:
        func = data[0] if (svc == 8 and sub == 1 and data) else None
        self.tcs.append({
            "t": round(float(t), 2), "service": int(svc), "subtype": int(sub),
            "func_id": func, "name": self._name_of(int(svc), int(sub), func),
            "data": bytes(data).hex(), "apid": int(apid), "seq": int(seq),
            "fate": "not_uplinked" if link_refused else "sent", "error": None,
        })
        if len(self.tcs) > self.MAX_TCS:
            del self.tcs[: len(self.tcs) - self.MAX_TCS]

    def observe_verification(self, subtype: int, apid: int, seq: int,
                             error_code: int = 0, reason: str = "") -> None:
        fate = {1: "accepted", 2: "rejected", 4: "failed", 7: "completed",
                8: "failed"}.get(int(subtype))
        if fate is None:
            return
        for tc in reversed(self.tcs):
            if tc["seq"] == seq and (apid == 0 or tc["apid"] == apid) \
                    and tc["fate"] != "not_uplinked":
                if tc["fate"] in BAD_FATES:
                    return                       # a failure is final
                if fate == "accepted" and tc["fate"] == "completed":
                    return
                tc["fate"] = fate
                if fate in BAD_FATES:
                    tc["error"] = (f"0x{int(error_code):04X}" if error_code else "") + \
                        (f" {reason}" if reason else "")
                return

    def observe_event(self, index: int, action: str, t: float) -> None:
        self.events.setdefault(int(index), round(float(t), 2))
        if action == "inject" and self.first_inject is None:
            self.first_inject = round(float(t), 2)

    def observe_params(self, t: float, params: dict) -> None:
        for key, chk in self._checks.items():
            if chk["pid"] not in params:
                continue
            ok = state_holds(chk, params.get(chk["pid"]))
            tr = self.states.setdefault(key, [])
            if not tr or tr[-1][1] != ok:
                tr.append([round(float(t), 2), ok])

    def mark(self, t: float, category: str, description: str = "") -> None:
        self.marks.append({"t": round(float(t), 2), "category": category,
                           "description": description})

    # -- persistence (breakpoints) ------------------------------------
    def get_state(self) -> dict:
        return {"tcs": [dict(x) for x in self.tcs],
                "events": {str(k): v for k, v in self.events.items()},
                "first_inject": self.first_inject,
                "states": {k: [list(x) for x in v] for k, v in self.states.items()},
                "marks": [dict(m) for m in self.marks]}

    def set_state(self, st: dict) -> None:
        self.tcs = [dict(x) for x in st.get("tcs") or []]
        self.events = {int(k): float(v) for k, v in (st.get("events") or {}).items()}
        fi = st.get("first_inject")
        self.first_inject = None if fi is None else float(fi)
        self.states = {k: [list(x) for x in v] for k, v in (st.get("states") or {}).items()}
        self.marks = [dict(m) for m in st.get("marks") or []]

    # -- evaluation ---------------------------------------------------
    def _ref_time(self, ref: tuple) -> Optional[float]:
        kind, idx = ref
        if kind == "start":
            return 0.0
        if kind == "event":
            return self.events.get(idx)
        if self.first_inject is not None:
            return self.first_inject
        # A scenario without any inject (first contact, checkout): the start.
        return None if self._has_inject else 0.0

    def _state_time(self, checks: list[dict], t_from: float, t_end: float) -> Optional[float]:
        """First time >= t_from at which ALL checks hold (None if never)."""
        if not checks:
            return t_from
        cands = {t_from}
        for c in checks:
            for t, _ok in self.states.get(c["text"], []):
                if t_from <= t <= t_end:
                    cands.add(t)
        for t in sorted(cands):
            if all(self._holds_at(c, t) for c in checks):
                return t
        return None

    def _holds_at(self, check: dict, t: float) -> bool:
        cur = None
        for tt, ok in self.states.get(check["text"], []):
            if tt <= t:
                cur = ok
            else:
                break
        return bool(cur)

    def _matching(self, specs: list[dict], t_from: float) -> list[dict]:
        return [tc for tc in self.tcs if tc["t"] >= t_from
                and any(tc_matches(s, tc, self._catalog) for s in specs)]

    def _args_text(self, tc: dict) -> str:
        """Decoded arguments, procedure notation ('wheel_idx=0'), or ''."""
        if "args_text" not in tc:
            text = ""
            try:
                from smo_common.commanding.decode import decode
                if not tc["name"].startswith("S"):   # S<svc>.<sub>: ambiguous, no decode
                    _n, args = decode(bytes.fromhex(tc.get("data", "")), service=tc["service"],
                                      subtype=tc["subtype"], catalog=self._catalog,
                                      name=tc["name"])
                    text = ", ".join(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}"
                                     for k, v in args.items())[:80]
            except Exception:  # noqa: BLE001 — a display nicety only
                text = ""
            tc["args_text"] = text
        return tc["args_text"]

    def _ev(self, tc: dict) -> dict:
        return {"kind": "tc", "name": tc["name"], "args": self._args_text(tc), "t": tc["t"],
                "fate": tc["fate"], "error": tc.get("error"), "seq": tc["seq"]}

    def _evaluate_one(self, r: dict, t_end: float, done_at: dict) -> dict:
        res = {"i": r["i"], "id": r["id"], "category": r["category"],
               "description": r["description"], "weight": r["weight"],
               "target_s": r["target_s"], "status": "observed", "credit": None,
               "scored": False, "time_s": None, "t": None, "evidence": [],
               "note": NO_NOTE, "checks": [c["text"] for c in r["tc"]] + [c["text"] for c in r["state"]]}
        if r.get("error"):
            res["note"] = note("declaration error: {{error}}", error=r["error"])
            return res
        if not r["tc"] and not r["state"]:
            res["note"] = note("not visible to the simulator: judge it in the debrief")
            return res
        ref_t = self._ref_time(r["ref"])
        if ref_t is None:
            res.update(status="not_reached", note=note("its reference event never happened"))
            return res
        res["scored"] = True
        res["ref_t"] = ref_t
        deps = [done_at.get(d) for d in r["after"]]
        order_t = max([d for d in deps if d is not None], default=None)
        lo = ref_t if order_t is None else max(ref_t, order_t)
        sat_t, evidence, status, nt = None, [], "missed", NO_NOTE
        if r["tc"]:
            cands = self._matching(r["tc"], ref_t)
            good = [c for c in cands if c["fate"] not in BAD_FATES]
            good_in_order = [c for c in good if c["t"] >= lo]
            for c in good_in_order:
                st_t = self._state_time(r["state"], c["t"], t_end)
                if st_t is not None:
                    sat_t = st_t
                    evidence = [self._ev(c)] + ([{"kind": "state", "text": "; ".join(
                        s["text"] for s in r["state"]), "t": st_t}] if r["state"] else [])
                    break
            if sat_t is None:
                if good_in_order:
                    status, evidence = "wrong", [self._ev(good_in_order[0])]
                    nt = note("sent, but {{state}} never followed",
                              state="; ".join(s["text"] for s in r["state"]))
                elif good:
                    status, evidence = "wrong", [self._ev(good[0])]
                    nt = note("sent before {{after}} was done", after=", ".join(r["after"]))
                elif cands:
                    status, evidence = "wrong", [self._ev(cands[0])]
                    c0 = cands[0]
                    key = {"rejected": "rejected by the spacecraft",
                           "failed": "failed on board",
                           "not_uplinked": "not uplinked (no command link)"}.get(c0["fate"], "")
                    if c0.get("error"):
                        nt = note(key + " ({{error}})", error=c0["error"].strip())
                    elif key:
                        nt = note(key)
        else:
            st_t = self._state_time(r["state"], lo, t_end)
            if st_t is not None and st_t <= t_end:
                sat_t = st_t
                evidence = [{"kind": "state", "text": "; ".join(s["text"] for s in r["state"]),
                             "t": st_t}]
        if sat_t is not None:
            dt = round(sat_t - ref_t, 1)
            status = "done" if dt <= r["target_s"] else "late"
            res.update(time_s=dt, t=sat_t)
            if order_t is None and any(d is None for d in deps) and r["after"]:
                nt = note("prerequisite {{after}} not seen", after=", ".join(r["after"]))
        res.update(status=status, credit=CREDIT[status], evidence=evidence, note=nt)
        return res

    def evaluate(self, t_end: float) -> dict:
        done_at: dict[str, float] = {}
        results: dict[str, dict] = {}
        # Dependencies first (declaration order is the usual order; resolve
        # in passes so `after:` may point forward too).
        pending = list(self.responses)
        for _ in range(len(pending) + 1):
            nxt = []
            for r in pending:
                if any(d not in results for d in r["after"]):
                    nxt.append(r)
                    continue
                res = self._evaluate_one(r, t_end, done_at)
                results[r["id"]] = res
                if res["t"] is not None and res["status"] in ("done", "late"):
                    done_at[r["id"]] = res["t"]
            if not nxt or len(nxt) == len(pending):
                for r in nxt:                       # a cycle: evaluate unordered
                    results[r["id"]] = self._evaluate_one(dict(r, after=[]), t_end, done_at)
                break
            pending = nxt
        resp = [results[r["id"]] for r in self.responses]

        harm = []
        for h in self.harmful:
            ref_t = self._ref_time(h["ref"])
            hits = [] if (h.get("error") or ref_t is None) else [
                c for c in self._matching(h["tc"], ref_t) if c["fate"] != "not_uplinked"]
            harm.append({"i": h["i"], "reason": h["reason"], "penalty": h["penalty"],
                         "checks": [c["text"] for c in h["tc"]],
                         "applied": bool(hits), "evidence": [self._ev(c) for c in hits[:5]],
                         "note": note("declaration error: {{error}}", error=h["error"])
                         if h.get("error") else NO_NOTE})

        scored = [r for r in resp if r["scored"]]
        possible = sum(r["weight"] for r in scored)
        earned = sum(r["weight"] * (r["credit"] or 0.0) for r in scored)
        penalty = sum(h["penalty"] for h in harm if h["applied"])
        score = None
        if possible > 0:
            score = max(0.0, min(100.0, 100.0 * earned / possible - penalty))
        elif any(h["applied"] for h in harm):
            score = max(0.0, 100.0 - penalty)

        ref0 = self.first_inject if self.first_inject is not None else 0.0
        metrics = self._metrics(resp, ref0)
        return {"score_pct": None if score is None else round(score, 1),
                "earned": round(earned, 2), "possible": round(possible, 2),
                "penalty": round(penalty, 1), "responses": resp, "harmful": harm,
                "metrics": metrics, "ref_s": ref0,
                "commands": [dict(self._ev(c), service=c["service"], subtype=c["subtype"])
                             for c in self.tcs if c["t"] >= 0][:300],
                "marks": [dict(m) for m in self.marks],
                "model": {"credit": dict(CREDIT), "default_penalty": DEFAULT_PENALTY}}

    def _metrics(self, resp: list[dict], ref0: float) -> dict:
        def first(cat):
            got = [r for r in resp if r["category"] == cat and r["status"] in ("done", "late")]
            return min(got, key=lambda r: r["t"]) if got else None

        def rel(t):
            return None if t is None else round(t - ref0, 1)
        out: dict[str, dict] = {}
        d = first("detect")
        if d is not None:
            out["mttd"] = {"s": rel(d["t"]), "inferred": False,
                           "source": note("{{id}}: {{evidence}}", id=d["id"], evidence=_ev_text(d))}
        else:
            specs = [s for r in self.responses for s in r["tc"]]
            hit = next((c for c in self.tcs if c["t"] >= ref0 and c["fate"] != "not_uplinked"
                        and any(tc_matches(s, c, self._catalog) for s in specs)), None)
            mark = next((m for m in self.marks if m["category"] == "detect"), None)
            if hit is not None:
                out["mttd"] = {"s": rel(hit["t"]), "inferred": True,
                               "source": note("first relevant command {{name}}",
                                              name=_ev_text({"evidence": [self._ev(hit)]}))}
            elif mark is not None:
                out["mttd"] = {"s": rel(mark["t"]), "inferred": False,
                               "source": note("instructor mark")}
        i = first("isolate")
        if i is not None:
            out["mtti"] = {"s": rel(i["t"]), "inferred": False,
                           "source": note("{{id}}: {{evidence}}", id=i["id"], evidence=_ev_text(i))}
        else:
            r = first("recover")
            mark = next((m for m in self.marks if m["category"] == "isolate"), None)
            if r is not None:
                out["mtti"] = {"s": rel(r["t"]), "inferred": True,
                               "source": note("first recovery {{id}}: {{evidence}}", id=r["id"],
                                              evidence=_ev_text(r))}
            elif mark is not None:
                out["mtti"] = {"s": rel(mark["t"]), "inferred": False,
                               "source": note("instructor mark")}
        recs = [r for r in resp if r["category"] == "recover" and r["scored"]]
        if recs and all(r["status"] in ("done", "late") for r in recs):
            last = max(recs, key=lambda r: r["t"])
            out["mttr"] = {"s": rel(last["t"]), "inferred": False,
                           "source": note("last recovery {{id}}: {{evidence}}", id=last["id"],
                                          evidence=_ev_text(last))}
        else:
            mark = next((m for m in self.marks if m["category"] == "recover"), None)
            if mark is not None and not recs:
                out["mttr"] = {"s": rel(mark["t"]), "inferred": False,
                               "source": note("instructor mark")}
        return out


def note(key: str, **vars_) -> dict:
    """A translatable note: English template with {{vars}} + its values.

    The console translates ``key`` (it is a catalogue key) and fills ``vars``;
    ``text`` is the English for logs and exports.
    """
    text = key
    for k, v in vars_.items():
        text = text.replace("{{" + k + "}}", str(v))
    return {"key": key, "vars": {k: str(v) for k, v in vars_.items()}, "text": text}


NO_NOTE = {"key": "", "vars": {}, "text": ""}


def _ev_text(r: dict) -> str:
    ev = r.get("evidence") or []
    return ", ".join((e["name"] + (f"({e['args']})" if e.get("args") else ""))
                     if e["kind"] == "tc" else e["text"] for e in ev) or "—"
