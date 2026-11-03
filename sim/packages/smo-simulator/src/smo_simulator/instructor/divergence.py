"""Truth versus what the trainees see, with the cause of every gap.

Each *pair* is one quantity the instructor may need to compare:

* **truth** — the simulator's own state (model internals: the true attitude,
  the true zone temperature, sim time);
* **onboard** — what the spacecraft itself measures or estimates (the value
  it puts in telemetry: a drifting thermistor, the MEKF attitude, the OBC
  clock);
* **ground** — the last value the ground actually received in downlinked
  housekeeping, with its age (``GroundView``). This is the trainees' view;
  it is computed from the simulator's own TM output, never from a console.

The gap is classified by cause (research report, "Truth versus indication"):

``injected``   an instructor-injected indication fault makes the spacecraft
               measure or estimate wrong (drawn in the inject colour; the
               only cause that is the instructor's doing);
``estimator``  the on-board estimate or clock is off for a natural reason
               (MEKF error, clock drift, sensor noise beyond threshold);
``delay``      the spacecraft knows the right value but the ground does not
               have it yet: no contact, HK disabled, not in any HK SID, or the
               packet store has not been dumped. Legitimate operations delay.

Precedence when several apply: injected > estimator > delay. All flags are
returned, so the console can say "estimate wrong AND 4 min old".

``classify`` is pure (unit-tested); ``PAIRS`` / ``evaluate`` read engine
state on the tick thread only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

CAUSES = ("injected", "estimator", "delay")

#: Ground value older than this (sim s) is "late" even if it agrees.
STALE_AFTER_S = 60.0


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def classify(truth: Any, onboard: Any, ground: Any, *, threshold: float,
             ground_age_s: Optional[float] = None, injected: bool = False,
             estimate: bool = False, delay_reason: str = "",
             enum: bool = False, stale_after_s: float = STALE_AFTER_S,
             angular: bool = False) -> dict[str, Any]:
    """Classify the truth / onboard / ground triple of one quantity.

    ``threshold`` is the absolute difference that counts as divergence (for
    ``enum`` pairs any difference counts). ``angular`` wraps differences to
    ±180°. Returns ``{state, cause, causes, onboard_err, ground_err,
    ground_lag, late, reason}`` where ``state`` is ``ok`` | ``diverged`` |
    ``nodata``.
    """
    def diff(a, b):
        if enum:
            return None if a is None or b is None else (0.0 if a == b else 1.0)
        fa, fb = _num(a), _num(b)
        if fa is None or fb is None:
            return None
        d = fa - fb
        if angular:
            d = (d + 180.0) % 360.0 - 180.0
        return d

    thr = 0.5 if enum else max(float(threshold), 0.0)
    out: dict[str, Any] = {
        "state": "ok", "cause": None, "causes": [], "reason": "",
        "onboard_err": diff(onboard, truth), "ground_err": diff(ground, truth),
        "ground_lag": diff(ground, onboard), "late": False,
    }
    if truth is None:
        out["state"] = "nodata"
        out["reason"] = "no truth for this quantity"
        return out
    causes: list[str] = []
    ob = out["onboard_err"]
    if ob is not None and abs(ob) > thr:
        causes.append("injected" if injected else "estimator")
    elif ob is not None and injected and abs(ob) > thr / 4.0:
        # an injected lie below the divergence threshold is still worth a
        # flag: it is the instructor's doing and it will grow (gradual onset)
        causes.append("injected")
    if ground is None:
        causes.append("delay")
        out["reason"] = delay_reason or "never received on the ground"
    else:
        lag = out["ground_lag"]
        late = ground_age_s is not None and ground_age_s > stale_after_s
        out["late"] = bool(late)
        if lag is not None and abs(lag) > thr:
            causes.append("delay")
            out["reason"] = delay_reason or "the ground has an older value"
        elif late and delay_reason:
            out["reason"] = delay_reason
    # one entry per cause, in precedence order
    causes = [c for c in CAUSES if c in causes]
    out["causes"] = causes
    if causes:
        out["cause"] = causes[0]
        # "diverged" means the ground's picture is off from the truth, or the
        # spacecraft's own knowledge is: either way the instructor must know.
        ge = out["ground_err"]
        if (ge is None or abs(ge) > thr or (ob is not None and abs(ob) > thr)
                or "injected" in causes):
            out["state"] = "diverged"
    return out


# ─────────────────────────────────────────────────────────────────────────
# Pair registry
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class Pair:
    """One compared quantity. ``truth`` reads the engine (tick thread);
    ``param`` is the telemetry parameter that carries the on-board value;
    ``injected_by`` lists (subsystem, failure, predicate(extra_params))."""
    id: str
    label: str
    subsystem: str
    unit: str
    threshold: float
    truth: Callable[[Any], Any]
    param: Optional[int] = None
    onboard: Optional[Callable[[Any], Any]] = None
    kind: str = "measured"          # measured | estimate | direct | enum
    digits: int = 1
    injected_by: list[tuple[str, str, Callable[[dict], bool]]] = field(default_factory=list)
    enum_names: Optional[dict[int, str]] = None
    angular: bool = False
    #: when set, the ground value is derived from these params (e.g. an
    #: angle computed from a downlinked quaternion) instead of `param`
    ground_fn: Optional[Callable[[dict], Any]] = None
    note: str = ""


def _model(engine, name):
    return engine.subsystems.get(name)


def _st(engine, name):
    m = _model(engine, name)
    return getattr(m, "_state", None) if m is not None else None


def _attr(engine, sub, field_name):
    s = _st(engine, sub)
    v = getattr(s, field_name, None) if s is not None else None
    return v


def _quat_angle_deg(a, b) -> Optional[float]:
    try:
        from smo_common import attitude as att
        return float(att.quat_angle_deg(a, b))
    except Exception:  # noqa: BLE001
        return None


def _q_true(engine):
    v = _attr(engine, "aocs", "q_true")
    return list(v) if v else None


def _q_est(engine):
    m = _model(engine, "aocs")
    if m is None or not hasattr(m, "_est_quat"):
        return None
    try:
        return [float(x) for x in m._est_quat()]
    except Exception:  # noqa: BLE001
        return None


def _true_point_err(engine):
    qt, qr = _q_true(engine), _attr(engine, "aocs", "q_ref")
    return _quat_angle_deg(qt, list(qr)) if qt and qr else None


def _omega_true_dps(engine, axis):
    w = _attr(engine, "aocs", "omega_true")
    return math.degrees(float(w[axis])) if w else None


def _zone_pred(zone):
    return lambda p: str(p.get("zone", "battery")) == zone


def _axis_pred(axis):
    return lambda p: str(p.get("axis", 0)) in (str(axis), "all")


_ATT_SENSORS = [("aocs", f, lambda p: True) for f in
                ("gyro_bias", "st_blind", "st_failure", "css_failure",
                 "css_head_fail", "mag_failure")]

_TCS_ZONES = (
    ("panel_px", 0x0400, "+X panel"), ("panel_mx", 0x0401, "−X panel"),
    ("panel_py", 0x0402, "+Y panel"), ("panel_my", 0x0403, "−Y panel"),
    ("panel_pz", 0x0404, "+Z panel"), ("panel_mz", 0x0405, "−Z panel (radiator)"),
    ("obc", 0x0406, "OBC"), ("battery", 0x0407, "Battery"),
    ("fpa", 0x0408, "FPA"), ("thruster", 0x0409, "Catalyst bed"),
)

SC_MODE_NAMES = {0: "SAFE", 1: "NOMINAL", 2: "SCIENCE", 3: "EMERGENCY"}
OBDH_MODE_NAMES = {0: "NOMINAL", 1: "SAFE", 2: "EMERGENCY"}


def _ground_quat_err(g: dict) -> Optional[float]:
    """Pointing error the ground can compute: q_ref vs q_est as downlinked."""
    est = [g.get(0x02A0), g.get(0x02A1), g.get(0x02A2), g.get(0x02A3)]
    ref = [g.get(0x02AB), g.get(0x02AC), g.get(0x02AD), g.get(0x02AE)]
    if any(v is None for v in est + ref):
        return None
    return _quat_angle_deg(est, ref)


def build_pairs() -> list[Pair]:
    pairs: list[Pair] = []
    # ── AOCS: attitude knowledge is the classic truth-vs-estimate gap ──
    pairs.append(Pair(
        id="aocs.point_err", label="Pointing error", subsystem="aocs", unit="°",
        threshold=0.1, digits=3, kind="estimate", param=0x02A8,
        truth=_true_point_err, injected_by=list(_ATT_SENSORS),
        note="truth: true attitude vs commanded; on board (aocs.control_err "
             "0x02A8): the estimate vs commanded"))
    pairs.append(Pair(
        id="aocs.knowledge", label="Attitude knowledge error", subsystem="aocs",
        unit="°", threshold=0.05, digits=3, kind="estimate",
        truth=lambda e: 0.0,
        onboard=lambda e: (_quat_angle_deg(_q_est(e), _q_true(e))
                           if _q_est(e) and _q_true(e) else None),
        ground_fn=None, injected_by=list(_ATT_SENSORS),
        note="angle between the on-board estimate and the true attitude; "
             "the ground cannot measure this"))
    for i, (axis, pid) in enumerate((("roll", 0x0204), ("pitch", 0x0205), ("yaw", 0x0206))):
        pairs.append(Pair(
            id=f"aocs.rate_{axis}", label=f"Body rate {axis}", subsystem="aocs",
            unit="°/s", threshold=0.01, digits=4, kind="estimate", param=pid,
            truth=(lambda e, i=i: _omega_true_dps(e, i)),
            injected_by=[("aocs", "gyro_bias", _axis_pred(i))]))
    # ── TCS: reported zone temperatures vs node truth ──
    for zone, pid, label in _TCS_ZONES:
        pairs.append(Pair(
            id=f"tcs.{zone}", label=f"{label} temperature", subsystem="tcs",
            unit="°C", threshold=1.0, digits=1, kind="measured", param=pid,
            truth=(lambda e, z=zone: _attr(e, "tcs", f"temp_{z}")),
            injected_by=[("tcs", "sensor_drift", _zone_pred(zone))]))
    # ── EPS: direct values (only the downlink can make them diverge) ──
    pairs.append(Pair(
        id="eps.soc", label="Battery state of charge", subsystem="eps", unit="%",
        threshold=1.0, digits=1, kind="direct", param=0x0101,
        truth=lambda e: _attr(e, "eps", "bat_soc_pct")))
    pairs.append(Pair(
        id="eps.bus_v", label="Bus voltage", subsystem="eps", unit="V",
        threshold=0.2, digits=2, kind="direct", param=0x0105,
        truth=lambda e: _attr(e, "eps", "bus_voltage")))
    pairs.append(Pair(
        id="eps.p_gen", label="Power generated", subsystem="eps", unit="W",
        threshold=2.0, digits=1, kind="direct", param=0x0107,
        truth=lambda e: _attr(e, "eps", "power_gen_w")))
    # ── OBDH: the two modes, and the clock ──
    pairs.append(Pair(
        id="sys.sc_mode", label="Spacecraft mode (sat.mode)", subsystem="obdh",
        unit="", threshold=0, kind="enum", param=0x0001,
        truth=lambda e: int(getattr(e, "sc_mode", 0)), enum_names=SC_MODE_NAMES,
        note="derived system mode: SAFE until commissioned (phase < NOMINAL) "
             "or while an FDIR safe contingency is latched"))
    pairs.append(Pair(
        id="obdh.mode", label="OBC software mode (obdh.mode)", subsystem="obdh",
        unit="", threshold=0, kind="enum", param=0x0300,
        truth=lambda e: _attr(e, "obdh", "mode"), enum_names=OBDH_MODE_NAMES,
        note="the OBC application's own mode; not the same quantity as sat.mode"))
    pairs.append(Pair(
        id="obdh.clock", label="On-board clock offset", subsystem="obdh",
        unit="s", threshold=1.0, digits=3, kind="estimate",
        truth=lambda e: 0.0,
        onboard=lambda e: ((e._build_clock_truth() or {}).get("offset_s")),
        injected_by=[("obdh", "clock_drift", lambda p: True)],
        note="OBC time minus true time; never downlinked — the trainees "
             "measure it from the time correlation"))
    # ── Payload storage ──
    pairs.append(Pair(
        id="payload.store", label="Payload store used", subsystem="payload",
        unit="%", threshold=1.0, digits=1, kind="direct", param=0x0604,
        truth=lambda e: _attr(e, "payload", "store_used_pct")))
    return pairs


PAIRS: list[Pair] = build_pairs()


def _active_injects(engine) -> list[tuple[str, str, dict]]:
    fm = getattr(engine, "_failure_manager", None)
    out = []
    for af in (getattr(fm, "_failures", {}) or {}).values():
        if getattr(af, "active", False):
            out.append((af.subsystem, af.failure, dict(af.extra_params or {})))
    return out


def evaluate(engine, ground, *, now_ts: float) -> list[dict[str, Any]]:
    """Evaluate every pair against the engine (tick thread) and the ground view.

    ``ground`` is a ``GroundView``. Returns JSON-safe rows.
    """
    injects = _active_injects(engine)
    gvals = ground.values()
    rows = []
    for p in PAIRS:
        try:
            truth = p.truth(engine)
        except Exception:  # noqa: BLE001 — a missing model never breaks the view
            truth = None
        if p.onboard is not None:
            try:
                onboard = p.onboard(engine)
            except Exception:  # noqa: BLE001
                onboard = None
        elif p.param is not None:
            onboard = engine.params.get(p.param)
        else:
            onboard = None
        if p.kind == "enum":
            truth = None if truth is None else int(round(float(truth)))
            onboard = None if onboard is None else int(round(float(onboard)))
        injected = any(sub == s and fail == f and pred(extra)
                       for s, f, pred in p.injected_by
                       for sub, fail, extra in injects)
        ground_val, age, via = None, None, None
        reason = ""
        reason_t = None
        ground_kind = "tm"
        if p.param is not None:
            g = gvals.get(p.param)
            if g is not None:
                ground_val, age, via = g["v"], now_ts - g["ts"], g["via"]
                if p.kind == "enum":
                    ground_val = int(round(float(ground_val)))
            reason_t = ground.delay_reason(p.param, engine)
            reason = ground.reason_text(reason_t)
        elif p.ground_fn is not None:
            ground_val = p.ground_fn({k: v["v"] for k, v in gvals.items()})
        else:
            ground_kind = "none"
        if ground_kind == "none":
            # The ground cannot observe this quantity at all (knowledge
            # error, clock offset): compare truth with onboard only.
            c = classify(truth, onboard, onboard, threshold=p.threshold,
                         injected=injected, estimate=p.kind == "estimate",
                         enum=p.kind == "enum", angular=p.angular)
        else:
            c = classify(truth, onboard, ground_val, threshold=p.threshold,
                         ground_age_s=age, injected=injected,
                         estimate=p.kind == "estimate", delay_reason=reason,
                         enum=p.kind == "enum", angular=p.angular)

        def jnum(v, d=p.digits):
            f = _num(v)
            return None if f is None else round(f, max(d, 0) + 2)

        rows.append({
            "id": p.id, "label": p.label, "subsystem": p.subsystem,
            "unit": p.unit, "kind": p.kind, "digits": p.digits,
            "param": (f"0x{p.param:04X}" if p.param is not None else None),
            "truth": truth if p.kind == "enum" else jnum(truth),
            "onboard": onboard if p.kind == "enum" else jnum(onboard),
            "ground": ground_val if p.kind == "enum" else jnum(ground_val),
            "ground_age_s": None if age is None else round(age, 1),
            "ground_via": via, "ground_kind": ground_kind,
            "enum_names": ({str(k): v for k, v in p.enum_names.items()}
                           if p.enum_names else None),
            "injected": injected, "note": p.note,
            "reason_t": reason_t if c.get("reason") == reason and reason else None,
            **{k: (jnum(v) if k.endswith(("_err", "_lag")) else v)
               for k, v in c.items()},
        })
    return rows


def summarise(rows: list[dict]) -> dict[str, Any]:
    """Counts per cause and per subsystem (for the overview strip)."""
    by_cause = {c: 0 for c in CAUSES}
    by_sub: dict[str, dict[str, int]] = {}
    for r in rows:
        if r.get("state") != "diverged":
            continue
        c = r.get("cause")
        if c in by_cause:
            by_cause[c] += 1
        d = by_sub.setdefault(r["subsystem"], {k: 0 for k in CAUSES})
        if c in d:
            d[c] += 1
    return {"by_cause": by_cause, "by_subsystem": by_sub,
            "diverged": sum(by_cause.values())}
