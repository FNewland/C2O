"""OBC thermal analysis runs (docs/plan_2026-11/OBC_THERMAL_ANALYSIS.md §1-§7).

HISTORICAL: this measured the fixed-sink zone model as it was at commit
21af365 (before the 2026-11-03 thermal network). Against the network it no
longer reproduces those numbers (its hand replay assumes the old C/tau/sink).
The current runs are thermal_network_runs.py ("After the thermal network").

Drives the real SimulationEngine headless (the way the tests do: construct the
engine on configs/eosat1 and call _tick_once) and records the OBC node.
Read-only with respect to the model: it sets EPS line states and injects the
instructor `cold_soak` failure exactly as the instructor console would.

Run from the repo root:
    PYTHONPATH=$(ls -d sim/packages/*/src | tr '\\n' ':') \
        python3 docs/plan_2026-11/obc_thermal/obc_thermal_runs.py
Writes summary.json and the PNGs next to this file.
"""
import json
import logging
import math
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONFIG = REPO / "sim" / "configs" / "eosat1"
os.environ.setdefault("SMO_DUMP_DIR", tempfile.mkdtemp(prefix="obc_thermal_"))
logging.disable(logging.WARNING)

from smo_simulator.engine import SimulationEngine  # noqa: E402

DT = 10.0  # s per outer tick; the engine sub-steps physics at dt_max_s = 1 s
H = 3600.0


def new_engine(lines_on: bool):
    eng = SimulationEngine(CONFIG)
    eng._spacecraft_phase = 6
    eng.subsystems["obdh"]._state.sw_image = 1
    eng.subsystems["obdh"]._state.mode = 0
    set_lines(eng, lines_on)
    fired = []
    disp = eng._dispatcher._s19_dispatch

    def spy(ea, fid, data=b""):
        fired.append((eng._elapsed, ea))
        return disp(ea, fid, data)
    eng._dispatcher._s19_dispatch = spy
    eng._fired = fired
    eng._elapsed = 0.0
    return eng


def set_lines(eng, on: bool):
    pl = eng.subsystems["eps"]._state.power_lines
    pl["htr_obc"] = on
    pl["htr_bat"] = on


def run(eng, seconds, rec, t_offset=0.0):
    tcs = eng.subsystems["tcs"]._state
    for _ in range(int(seconds / DT)):
        eng._tick_once(DT)
        eng._elapsed += DT
        rec["t"].append(eng._elapsed - t_offset)
        rec["obc"].append(tcs.temp_obc)
        rec["bat"].append(tcs.temp_battery)
        rec["htr"].append(1 if tcs.htr_obc else 0)
        rec["ecl"].append(1 if eng.params.get(0x0108, 0) else 0)
        rec["obdh_mode"].append(int(eng.subsystems["obdh"]._state.mode))


def blank():
    return {k: [] for k in ("t", "obc", "bat", "htr", "ecl", "obdh_mode")}


def stats(rec, t0, t1):
    idx = [i for i, t in enumerate(rec["t"]) if t0 <= t < t1]
    v = [rec["obc"][i] for i in idx]
    b = [rec["bat"][i] for i in idx]
    h = [rec["htr"][i] for i in idx]
    return {"min": min(v), "max": max(v), "mean": sum(v) / len(v),
            "bat_mean": sum(b) / len(b), "htr_duty": sum(h) / len(h)}


def steady_cases():
    out = {}
    recs = {}
    for name, on in (("nominal_lines_on", True), ("survival_lines_off", False)):
        eng = new_engine(on)
        rec = blank()
        run(eng, 30 * H, rec)
        out[name] = stats(rec, 18 * H, 30 * H)
        out[name]["s19_3003_fired"] = sum(1 for _, ea in eng._fired if ea == 3003)
        orb = eng.orbit.propagate_to(eng._sim_time)
        out[name]["beta_deg"] = orb.solar_beta_deg
        e = rec["ecl"][int(18 * H / DT):]
        out[name]["eclipse_fraction"] = sum(e) / len(e)
        recs[name] = rec
    return out, recs


def soak_case(offset_c):
    """6 h nominal warm-up, then cold_soak(obc, offset) with BOTH heater lines
    OFF (worst case: load shed) for 8 h, heater lines ON for 6 h, soak
    cleared (instructor) for 4 h. Time axis: hours from the injection."""
    eng = new_engine(True)
    rec = blank()
    run(eng, 6 * H, rec)
    t0 = eng._elapsed
    tcs = eng.subsystems["tcs"]
    set_lines(eng, False)
    tcs.inject_failure("cold_soak", zone="obc", offset_c=offset_c)
    run(eng, 8 * H, rec)
    set_lines(eng, True)
    run(eng, 6 * H, rec)
    tcs.clear_failure("cold_soak", zone="obc")
    run(eng, 4 * H, rec)
    rec["t"] = [t - t0 for t in rec["t"]]
    res = {
        "pre": stats(rec, -2 * H, 0),
        "soak_heater_off": stats(rec, 5 * H, 8 * H),
        "soak_heater_on": stats(rec, 11 * H, 14 * H),
        "after_clear": stats(rec, 16 * H, 18 * H),
        "s19_3003_fired_at_h": sorted({round((t - t0) / H, 2)
                                      for t, ea in eng._fired if ea == 3003})[:5],
        "obdh_mode_values": sorted(set(rec["obdh_mode"])),
    }
    # The heater-recovery time constant is checked analytically instead
    # (replay_check: tau_eff = C / (UA + G)); the orbit ripple is as large as
    # the 4 K step, so a 63 % crossing read off the noisy trace is meaningless.
    # time from injection until the node first crosses yellow/red lows
    for name, lim in (("t_to_yellow_5C_s", 5.0), ("t_to_red_0C_s", 0.0),
                      ("t_to_m25C_s", -25.0)):
        res[name] = next((t for t, v in zip(rec["t"], rec["obc"]) if t >= 0 and v <= lim), None)
    return res, rec


def replay_check(rec, offset_c, C=800.0, UA=800.0 / 900.0, G=0.1, P=4.0,
                 sink_ecl=10.0, sink_sun=12.0):
    """Energy-balance sanity check: integrate the OBC node equation by hand,
    C dT/dt = UA (T_sink + soak - T) + G (T_bat - T) + P_htr, driven by the
    RECORDED eclipse flag, battery temperature and heater state, with the
    exact exponential update over each 10 s step (inputs held constant). No
    noise term. Returns RMS and max |sim - hand| over the run."""
    k = UA + G
    T = rec["obc"][0]
    err = []
    for i in range(1, len(rec["t"])):
        t = rec["t"][i]
        soak = offset_c if 0.0 <= rec["t"][i - 1] < 14 * H else 0.0
        ts = (sink_ecl if rec["ecl"][i] else sink_sun) + soak
        t_inf = (UA * ts + G * rec["bat"][i - 1] + P * rec["htr"][i]) / k
        if rec["t"][i - 1] <= 0.0 < t:   # the soak also steps the node itself
            T += offset_c                 # (clearing removes the sink offset only)
        T = t_inf + (T - t_inf) * math.exp(-k * DT / C)
        err.append(rec["obc"][i] - T)
    rms = math.sqrt(sum(e * e for e in err) / len(err))
    return {"rms_k": rms, "max_abs_k": max(abs(e) for e in err),
            "mean_k": sum(err) / len(err), "tau_eff_s": C / k}


def plot(recs, soak_recs, summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    blue, orange, aqua, yellow = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
    ink, muted, grid = "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": muted, "axes.labelcolor": ink,
                         "xtick.color": muted, "ytick.color": muted,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "lines.linewidth": 2})

    def limits(ax, x1):
        for y, lab in ((5, "yellow low +5 °C (heater ON setpoint)"),
                       (0, "red low 0 °C"), (-25, "ISIS iOBC min -25 °C"),
                       (-40, "EDDIE OBC min -40 °C")):
            if ax.get_ylim()[0] <= y <= ax.get_ylim()[1]:
                ax.axhline(y, color=muted, lw=0.8, ls="--", zorder=1)
                ax.text(x1, y + 0.4, lab, color=muted, fontsize=7, ha="right", va="bottom")

    def shade(ax, rec):
        t = [x / H for x in rec["t"]]
        ax.fill_between(t, 0, 1, where=[e == 1 for e in rec["ecl"]],
                        transform=ax.get_xaxis_transform(), color="#f0efec", lw=0, zorder=0)

    # 1. Steady state, last 6 h of 30 h
    fig, ax = plt.subplots(figsize=(7, 3.2), dpi=110)
    for name, col, lab in (("nominal_lines_on", blue, "Heater lines ON (nominal / safe)"),
                           ("survival_lines_off", orange, "Heater lines OFF (load shed)")):
        r = recs[name]
        i0 = int(24 * H / DT)
        t = [x / H - 24 for x in r["t"][i0:]]
        ax.plot(t, r["obc"][i0:], color=col, label=lab)
    sub = {k: v[int(24 * H / DT):] for k, v in recs["nominal_lines_on"].items()}
    sub["t"] = [x - 24 * H for x in sub["t"]]
    shade(ax, sub)
    ax.set_ylim(-2, 14)
    ax.set_xlim(0, 6)
    limits(ax, 6)
    ax.set_xlabel("time (h) — shaded = eclipse")
    ax.set_ylabel("OBC node temp (°C)")
    ax.set_title("OBC node, periodic steady state (simulated, 24–30 h)", loc="left", fontsize=10)
    ax.grid(axis="y", color=grid, lw=0.6)
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "obc_steady_state.png")
    plt.close(fig)

    # 2. Cold soak traces
    fig, ax = plt.subplots(figsize=(7, 3.8), dpi=110)
    for off, col in ((-25.0, blue), (-60.0, orange)):
        r = soak_recs[off]
        t = [x / H for x in r["t"]]
        ax.plot(t, r["obc"], color=col, label=f"cold_soak offset {off:.0f} °C")
    for x, lab in ((0, "soak injected,\nheater lines OFF"), (8, "heater lines ON"),
                   (14, "soak cleared")):
        ax.axvline(x, color=ink, lw=0.8, zorder=1)
        ax.text(x + 0.1, 16, lab, fontsize=7, color=ink, va="top")
    ax.set_ylim(-62, 18)
    ax.set_xlim(-2, 18)
    limits(ax, 18)
    ax.set_xlabel("time from injection (h)")
    ax.set_ylabel("OBC node temp (°C)")
    ax.set_title("Instructor cold_soak on the OBC zone (simulated)", loc="left", fontsize=10)
    ax.grid(axis="y", color=grid, lw=0.6)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "obc_cold_soak.png")
    plt.close(fig)

    # 3. Zoom on heater recovery for -25 (with heater state)
    r = soak_recs[-25.0]
    i0 = next(i for i, t in enumerate(r["t"]) if t >= 7 * H)
    i1 = next(i for i, t in enumerate(r["t"]) if t >= 11 * H)
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(7, 3.6), dpi=110, sharex=True,
                                  gridspec_kw={"height_ratios": [4, 1]})
    t = [x / H for x in r["t"][i0:i1]]
    ax.plot(t, r["obc"][i0:i1], color=blue, label="OBC node")
    ax.axvline(8, color=ink, lw=0.8)
    ax.text(8.05, ax.get_ylim()[1], "heater lines ON", fontsize=7, va="top")
    ax.set_ylabel("°C")
    ax.set_title("Heater recovery after a -25 °C soak: +4 K from the OBC heater, +2 K from the battery (simulated)",
                 loc="left", fontsize=10)
    ax.grid(axis="y", color=grid, lw=0.6)
    ax2.step(t, r["htr"][i0:i1], where="post", color=orange)
    ax2.set_yticks([0, 1], ["off", "on"])
    ax2.set_ylabel("heater")
    ax2.set_xlabel("time from injection (h)")
    fig.tight_layout()
    fig.savefig(HERE / "obc_heater_recovery.png")
    plt.close(fig)


def main():
    summary = {}
    steady, recs = steady_cases()
    summary["steady"] = steady
    soak_recs = {}
    for off in (-25.0, -60.0):
        res, rec = soak_case(off)
        summary[f"soak_{int(off)}"] = res
        soak_recs[off] = rec
        summary[f"soak_{int(off)}"]["hand_replay"] = replay_check(rec, off)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print(json.dumps(summary, indent=1, default=float))
    if "--no-plot" not in sys.argv:
        plot(recs, soak_recs, summary)


if __name__ == "__main__":
    main()
