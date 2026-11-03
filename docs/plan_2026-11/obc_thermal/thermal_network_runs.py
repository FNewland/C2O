"""Thermal-network runs (OBC_THERMAL_ANALYSIS.md, section "After the thermal network").

Successor of obc_thermal_runs.py (which measured the old fixed-sink zone model
and is kept for the record; its figures are the §1-§4 figures). This script
drives the real SimulationEngine headless on configs/eosat1 with the 2026-11
thermal network and records every network node.

The spacecraft is brought to NOMINAL the way an operator would (the
test_nominal_reachable_e2e sequence: boot the application, AOCS line, wheels,
star trackers, sun acquisition, nadir, mission phase 5 -> 6). Wing deployment,
heater / payload line states and the instructor failures are set directly,
as the instructor console would.

Cases (each run long enough to reach the periodic steady state):
  nominal     heaters under thermostat, payload STANDBY with the cooler
              running (what STANDBY does), nadir hold
  nominal_nocooler  the same with the cooler off (NOM-010 step 3)
  safe        long safe mode: AOCS coarse sun-pointing (+X at the sun, star
              trackers off so it holds), payload and cooler off
  shed        long load shed / survival: only OBC + receiver powered, heater
              lines OFF, AOCS line off (the body drifts)
  shed_htr    the same with the heater lines ON (the OBC heater's job)
  cold        `shed` in the coldest season: aphelion solar flux (1322 W/m2),
              cold-case albedo 0.25 / OLR 218, at the epoch (beta -30)
  soak_<zone> instructor cold_soak on battery / obc / thruster at its default
              depth from nominal: 4 h heater lines OFF, 6 h ON, then clear
  hot         hot-case environment (1414 W/m2, albedo 0.35, OLR 261) on the
              real orbit, payload IMAGING all orbit with the cooler on, nadir
              hold, TX line on

FDIR is disabled in these runs so the load state is the one set up (the
shipped S19 1004/1005 switch the payload off at every eclipse entry).

Run from the repo root (cases may run in parallel processes; TN_CACHE picks
the cache directory, default the system temp dir):
    export PYTHONPATH=$(ls -d sim/packages/*/src | tr '\\n' ':')
    python3 docs/plan_2026-11/obc_thermal/thermal_network_runs.py nominal safe ...
    python3 docs/plan_2026-11/obc_thermal/thermal_network_runs.py --report
(no case names = all cases, then the report). Writes network_summary.json and
network_*.png next to this file.
"""
import json
import logging
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONFIG = REPO / "sim" / "configs" / "eosat1"
os.environ.setdefault("SMO_DUMP_DIR", tempfile.mkdtemp(prefix="tn_runs_"))
logging.disable(logging.WARNING)

from smo_simulator.engine import SimulationEngine  # noqa: E402

DT = 10.0
H = 3600.0
QUICK = "--quick" in sys.argv
NODES = ("structure", "obc", "battery", "payload", "fpa", "ttc", "aocs",
         "prop", "thruster", "panel_px", "panel_mz", "panel_py", "panel_my",
         "wing_py")


# ── engine set-up ─────────────────────────────────────────────────────────

def _config_copy(env=None, raan_shift_deg=0.0):
    """A throw-away copy of configs/eosat1 with a different environment
    and/or RAAN (for the cold and hot cases)."""
    if env is None and not raan_shift_deg:
        return CONFIG
    d = Path(tempfile.mkdtemp(prefix="tn_cfg_")) / "eosat1"
    shutil.copytree(CONFIG, d)
    if env:
        p = d / "simulation.yaml"
        sim = yaml.safe_load(p.read_text())
        sim["tcs"]["environment"].update(env)
        p.write_text(yaml.safe_dump(sim, sort_keys=False))
    if raan_shift_deg:
        p = d / "orbit.yaml"
        txt = p.read_text()
        old = " 120.0000 "
        new = f" {120.0 + raan_shift_deg:8.4f} "
        assert old in txt
        p.write_text(txt.replace(old, new, 1))
    return d


def nominal_engine(cfg=CONFIG):
    eng = SimulationEngine(cfg, speed=1.0)
    d = eng._dispatcher

    def tc(*data, strict=True):
        res = d.dispatch(8, 1, bytes(data), None)
        if strict:
            assert res.error is None, res.error
        elif res.error is not None:
            print("  (TC", data, "refused:", res.error, ")", flush=True)

    def run(seconds):
        for _ in range(int(seconds / DT)):
            eng._tick_once(DT)

    tc(55)                     # boot the application (phase 3 -> 4)
    run(20)
    tc(19, 7)                  # aocs_wheels line
    tc(19, 2)                  # ttc_tx line
    run(10)
    for w in range(4):
        tc(3, w)               # enable wheels
    tc(4, 1)
    tc(5, 1)                   # star trackers
    run(30)
    tc(0, 3)                   # coarse sun
    run(300)
    tc(0, 4)                   # nadir
    run(600)
    tc(120, 5, 0)
    run(10)
    tc(120, 6, 0)
    run(10)
    e = eng.subsystems["eps"]._state
    e.wing_py_deployed = e.wing_my_deployed = True
    set_lines(eng, htr=True, payload=True)
    eng.subsystems["payload"].handle_command({"command": "set_mode", "mode": 1})
    # FDIR off for the thermal cases: the shipped S19 rules 1004/1005 switch
    # the payload off at every eclipse entry (OBC_THERMAL_ANALYSIS §3.3 item
    # 3), which would turn every "nominal" run into a payload-off run. The
    # point here is the thermal response to a KNOWN load state.
    eng._fdir_enabled = False
    eng._tc = tc
    eng._run = run
    return eng


def set_lines(eng, htr=None, payload=None, aocs=None, tx=None):
    pl = eng.subsystems["eps"]._state.power_lines
    if htr is not None:
        pl["htr_obc"] = pl["htr_bat"] = htr
    if payload is not None:
        pl["payload"] = payload
        if not payload:
            pl["fpa_cooler"] = False
    if aocs is not None:
        pl["aocs_wheels"] = aocs
    if tx is not None:
        pl["ttc_tx"] = tx


# ── recording ─────────────────────────────────────────────────────────────

def blank():
    r = {k: [] for k in ("t", "ecl", "htr_obc", "htr_bat", "q_in", "q_rad",
                         "e_net", "p_int", "obdh_mode", "fpa_floor", "aocs_mode")}
    for n in NODES:
        r[n] = []
    return r


def record(eng, seconds, rec, t0=0.0):
    tcs = eng.subsystems["tcs"]
    s = tcs._state
    t = rec["t"][-1] + DT if rec["t"] else t0
    for _ in range(int(seconds / DT)):
        e_rad = 0.0
        e_in = 0.0
        e_p = 0.0
        # integrate the network's own energy flows over the sub-steps
        n_sub = max(1, int(math.ceil(DT / eng._dt_max_s)))
        for _k in range(n_sub):
            eng._tick_once(DT / n_sub)
            li = tcs._last_inputs
            h = DT / n_sub
            e_rad += tcs._last_radiated_j
            e_in += sum(li["q_abs"]) * h
            e_p += sum(li["power"]) * h
        rec["t"].append(t)
        t += DT
        rec["ecl"].append(1 if eng.params.get(0x0108, 0) else 0)
        rec["htr_obc"].append(1 if s.htr_obc else 0)
        rec["htr_bat"].append(1 if s.htr_battery else 0)
        rec["q_in"].append(e_in / DT)
        rec["p_int"].append(e_p / DT)
        rec["q_rad"].append(e_rad / DT)
        rec["e_net"].append(tcs._solver.energy_j() + tcs._CAP["fpa"] * (s.temp_fpa + 273.15))
        rec["obdh_mode"].append(int(eng.subsystems["obdh"]._state.mode))
        rec["aocs_mode"].append(int(eng.params.get(0x020F, -1)))
        rec["fpa_floor"].append(s.fpa_cooler_floor_c)
        for n in NODES:
            rec[n].append(tcs.node_temperature(n))


def stats(rec, t0, t1, nodes=NODES):
    idx = [i for i, t in enumerate(rec["t"]) if t0 <= t < t1]
    out = {}
    for n in nodes:
        v = [rec[n][i] for i in idx]
        out[n] = {"mean": sum(v) / len(v), "min": min(v), "max": max(v)}
    for h in ("htr_obc", "htr_bat"):
        out[h + "_duty"] = sum(rec[h][i] for i in idx) / len(idx)
    out["p_int_mean_w"] = sum(rec["p_int"][i] for i in idx) / len(idx)
    out["q_in_mean_w"] = sum(rec["q_in"][i] for i in idx) / len(idx)
    out["q_rad_mean_w"] = sum(rec["q_rad"][i] for i in idx) / len(idx)
    out["eclipse_fraction"] = sum(rec["ecl"][i] for i in idx) / len(idx)
    if rec.get("aocs_mode"):
        modes = [rec["aocs_mode"][i] for i in idx]
        out["aocs_modes"] = {m: modes.count(m) / len(modes) for m in sorted(set(modes))}
    return out


C_FPA = 100.0   # tcs.yaml zones: fpa capacitance (J/K)


def energy_check(rec, i0, i1):
    """Network energy bookkeeping over [i0, i1): stored-energy change of the
    network nodes vs the integral of (absorbed + dissipated - radiated). The
    controlled FPA node is outside the network; the heat it exchanges with
    the payload node is part of the dissipation term, so its own stored
    energy is taken out of `e_net` (recorded including it)."""
    def e(i):
        return rec["e_net"][i] - C_FPA * (rec["fpa"][i] + 273.15)
    d_e = e(i1 - 1) - e(i0 - 1)
    flows = sum((rec["q_in"][i] + rec["p_int"][i] - rec["q_rad"][i]) * DT
                for i in range(i0, i1))
    return {"stored_change_kj": d_e / 1e3, "net_flow_kj": flows / 1e3,
            "mismatch_j": d_e - flows}


# ── cases ─────────────────────────────────────────────────────────────────

SETTLE = (6 if QUICK else 10) * H     # bus time constant is ~2 h
WINDOW = 3 * H


def case_steady(name, setup, cfg=CONFIG):
    eng = nominal_engine(cfg)
    setup(eng)
    rec = blank()
    record(eng, SETTLE + WINDOW, rec)
    t_end = rec["t"][-1] + DT
    res = stats(rec, t_end - WINDOW, t_end)
    i0 = next(i for i, t in enumerate(rec["t"]) if t >= t_end - WINDOW)
    res["energy_check"] = energy_check(rec, i0, len(rec["t"]))
    orb = eng.orbit.propagate_to(eng._sim_time)
    res["beta_deg"] = orb.solar_beta_deg
    res["aocs_mode_end"] = int(eng.params.get(0x020F, -1))
    return res, rec


def cooler(eng, on):
    """Line 4 first; TCS refuses the cooler while 0x0114 still reads OFF."""
    eng.subsystems["eps"]._state.power_lines["fpa_cooler"] = on
    eng._run(10)
    r = eng.subsystems["tcs"].handle_command({"command": "fpa_cooler", "on": on})
    assert r.get("success"), r


def setup_nominal(eng):
    """Payload STANDBY with the cooler running — what the payload does in
    STANDBY (manual 03 §3.4) — heater lines ON under thermostat."""
    cooler(eng, True)


def setup_nominal_nocooler(eng):
    """Payload idle with the cooler off (NOM-010 step 3 / the power-budget
    `nominal` profile)."""
    cooler(eng, False)


def setup_safe(eng):
    set_lines(eng, payload=False)
    eng.subsystems["payload"].handle_command({"command": "set_mode", "mode": 0})
    # Star trackers off: COARSE_SUN is a hold, and with a valid tracker the
    # AOCS promotes itself back to the commanded mode after 60 s.
    eng._tc(4, 0, strict=False)
    eng._tc(5, 0, strict=False)
    eng._tc(0, 3, strict=False)     # AOCS COARSE_SUN: +X at the sun
    eng._tc(50, 1, strict=False)    # OBC SAFE


def setup_shed(eng, htr=False):
    set_lines(eng, htr=htr, payload=False, aocs=False, tx=False)
    eng.subsystems["payload"].handle_command({"command": "set_mode", "mode": 0})
    # stop the auto-TX hold re-energising the transmitter
    eng._auto_tx_hold_s = 0.0


def setup_hot(eng):
    """Imaging all orbit with the cooler on, nadir hold, TX line on."""
    set_lines(eng, payload=True, tx=True)
    cooler(eng, True)
    eng.subsystems["payload"].handle_command({"command": "set_mode", "mode": 2})


def case_soak(zone):
    eng = nominal_engine()
    tcs = eng.subsystems["tcs"]
    if zone == "thruster":
        eng.subsystems["eps"]._state.power_lines["prop"] = True
    rec = blank()
    record(eng, (6 if QUICK else 8) * H, rec)
    t_inj = rec["t"][-1] + DT
    off = tcs._soak_default[zone]
    set_lines(eng, htr=False)
    tcs.inject_failure("cold_soak", zone=zone)
    record(eng, 4 * H, rec)
    set_lines(eng, htr=True)
    if zone == "thruster":
        tcs.handle_command({"command": "auto_mode", "circuit": 2})
    record(eng, 6 * H, rec)
    tcs.clear_failure("cold_soak", zone=zone)
    record(eng, 4 * H, rec)
    rec["t"] = [t - t_inj for t in rec["t"]]
    node = zone
    res = {"offset_c": off,
           "pre": stats(rec, -2 * H, 0, (node, "structure")),
           "soak_heater_off": stats(rec, 2 * H, 4 * H, (node, "structure")),
           "soak_heater_on": stats(rec, 7 * H, 10 * H, (node, "structure")),
           "after_clear": stats(rec, 12 * H, 14 * H, (node, "structure"))}
    return res, rec


# ── plots ─────────────────────────────────────────────────────────────────

def plots(recs, soak_recs, limits):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pal = {"nominal": "#2a78d6", "nominal_nocooler": "#6cb4f0", "safe": "#1baf7a", "shed": "#eb6834",
           "shed_htr": "#eda100", "cold": "#7a5af5", "hot": "#d6336c"}
    ink, muted, grid = "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": muted,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "lines.linewidth": 1.6})

    def last(rec, key, hours):
        t_end = rec["t"][-1] + DT
        idx = [i for i, t in enumerate(rec["t"]) if t >= t_end - hours * H]
        return [(rec["t"][i] - rec["t"][idx[0]]) / H for i in idx], [rec[key][i] for i in idx], idx

    def shade(ax, rec, idx):
        t = [(rec["t"][i] - rec["t"][idx[0]]) / H for i in idx]
        ax.fill_between(t, 0, 1, where=[rec["ecl"][i] == 1 for i in idx],
                        transform=ax.get_xaxis_transform(), color="#f0efec", lw=0, zorder=0)

    def hlines(ax, items, x1):
        lo, hi = ax.get_ylim()
        for y, lab in items:
            if lo <= y <= hi:
                ax.axhline(y, color=muted, lw=0.8, ls="--", zorder=1)
                ax.text(x1, y + 0.3, lab, color=muted, fontsize=7, ha="right", va="bottom")

    obc_lims = [(limits["obc_yellow_low"], "OBC yellow low"),
                (limits["obc_red_low"], "OBC red low"),
                (-25.0, "ISIS iOBC min -25")]

    # 1. OBC per case, last 3 h
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=110)
    for name in ("hot", "nominal", "nominal_nocooler", "safe", "shed_htr", "shed", "cold"):
        if name not in recs:
            continue
        t, v, idx = last(recs[name], "obc", 3)
        ax.plot(t, v, color=pal[name], label=name)
    t, v, idx = last(recs["nominal"], "obc", 3)
    shade(ax, recs["nominal"], idx)
    ax.set_xlim(0, 3)
    hlines(ax, obc_lims, 3)
    ax.set_xlabel("time (h), periodic steady state — shaded = eclipse (nominal run)")
    ax.set_ylabel("OBC node (°C)")
    ax.set_title("OBC node by operating case (simulated, thermal network)", loc="left", fontsize=10)
    ax.grid(axis="y", color=grid, lw=0.6)
    ax.legend(frameon=False, fontsize=7, ncol=7, loc="upper center",
              bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout()
    fig.savefig(HERE / "network_obc_cases.png")
    plt.close(fig)

    # 2. Key nodes in the nominal case
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=110)
    cols = {"panel_px": "#9aa0a6", "structure": ink, "obc": "#2a78d6",
            "battery": "#1baf7a", "payload": "#eb6834", "fpa": "#7a5af5"}
    for n, c in cols.items():
        t, v, idx = last(recs["nominal"], n, 3)
        ax.plot(t, v, color=c, label=n)
    shade(ax, recs["nominal"], idx)
    ax.set_xlim(0, 3)
    ax.set_xlabel("time (h) — shaded = eclipse")
    ax.set_ylabel("°C")
    ax.set_title("Nominal operations: network nodes (simulated)", loc="left", fontsize=10)
    ax.grid(axis="y", color=grid, lw=0.6)
    ax.legend(frameon=False, fontsize=7, ncol=6, loc="upper center",
              bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout()
    fig.savefig(HERE / "network_nominal_nodes.png")
    plt.close(fig)

    # 3. Cold soak per zone
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 7.0), dpi=110, sharex=True)
    for ax, zone in zip(axes, ("obc", "battery", "thruster")):
        r = soak_recs[zone]
        t = [x / H for x in r["t"]]
        ax.plot(t, r[zone], color="#2a78d6", label=f"{zone} node")
        ax.plot(t, r["structure"], color=muted, lw=1.0, label="structure")
        for x, lab in ((0, "soak, heater lines OFF"), (4, "lines ON"), (10, "soak cleared")):
            ax.axvline(x, color=ink, lw=0.8)
            ax.text(x + 0.05, 0.97, lab, fontsize=7, va="top", transform=ax.get_xaxis_transform())
        ax.set_ylabel("°C")
        ax.grid(axis="y", color=grid, lw=0.6)
        ax.legend(frameon=False, fontsize=7, loc="lower right")
        if zone == "obc":
            hlines(ax, obc_lims, 14)
        ax.set_title(f"cold_soak on {zone} (default {r['_offset']:.0f} K)", loc="left", fontsize=9)
    axes[-1].set_xlabel("time from injection (h)")
    axes[-1].set_xlim(-2, 14)
    fig.tight_layout()
    fig.savefig(HERE / "network_cold_soak.png")
    plt.close(fig)

    # 4. Hot case: payload node, FPA and its cooler floor
    if "hot" in recs:
        fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=110)
        for key, c, lab in (("payload", "#eb6834", "payload node (FPA sink)"),
                            ("fpa", "#7a5af5", "FPA node"),
                            ("fpa_floor", muted, "cooler floor (coldest holdable)"),
                            ("obc", "#2a78d6", "OBC")):
            t, v, idx = last(recs["hot"], key, 3)
            ax.plot(t, v, color=c, label=lab)
        ax.axhline(-15, color=ink, lw=0.8, ls=":")
        ax.text(3, -14.6, "FPA setpoint -15 °C", fontsize=7, ha="right")
        ax.set_xlim(0, 3)
        ax.set_xlabel("time (h) — shaded = eclipse")
        ax.set_ylabel("°C")
        t, v, idx = last(recs["hot"], "payload", 3)
        shade(ax, recs["hot"], idx)
        ax.set_title("Hot case: hot environment, imaging all orbit + cooler (simulated)",
                     loc="left", fontsize=10)
        ax.grid(axis="y", color=grid, lw=0.6)
        ax.legend(frameon=False, fontsize=7, ncol=4, loc="upper center",
                  bbox_to_anchor=(0.5, -0.2))
        fig.tight_layout()
        fig.savefig(HERE / "network_hot_case.png")
        plt.close(fig)


CACHE = Path(os.environ.get("TN_CACHE", tempfile.gettempdir())) / "tn_runs_cache"


def main():
    """`thermal_network_runs.py [CASE ...] [--quick]` runs the named cases
    (default: all) and caches each; `--report` builds the summary and the
    figures from the cache. Cases can therefore run in parallel processes."""
    import pickle
    CACHE.mkdir(parents=True, exist_ok=True)
    lim = yaml.safe_load((CONFIG / "mcs" / "limits.yaml").read_text())
    row = next(r for r in lim["limits"] if r["param_id"] == 0x0406)
    limits = {"obc_yellow_low": row["yellow_low"], "obc_red_low": row["red_low"]}
    cold_env = {"solar_flux_w_m2": 1322.0, "scale_solar_with_distance": False,
                "albedo": 0.25, "earth_ir_w_m2": 218.0}
    hot_env = {"solar_flux_w_m2": 1414.0, "scale_solar_with_distance": False,
               "albedo": 0.35, "earth_ir_w_m2": 261.0}
    plan = {"nominal": (setup_nominal, lambda: CONFIG),
            "nominal_nocooler": (setup_nominal_nocooler, lambda: CONFIG),
            "safe": (setup_safe, lambda: CONFIG),
            "shed": (setup_shed, lambda: CONFIG),
            "shed_htr": (lambda e: setup_shed(e, htr=True), lambda: CONFIG),
            "cold": (setup_shed, lambda: _config_copy(env=cold_env)),
            "cold_htr": (lambda e: setup_shed(e, htr=True),
                         lambda: _config_copy(env=cold_env)),
            # Hot case on the REAL orbit (beta -30, the short-eclipse end of
            # the year): a dawn-dusk copy puts the Sun along the SADA axis, the
            # wings stop generating and the bus load-sheds the AOCS — not a
            # thermal hot case.
            "hot": (setup_hot, lambda: _config_copy(env=hot_env))}
    soaks = ("soak_obc", "soak_battery", "soak_thruster")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--report" not in sys.argv:
        for name in (args or list(plan) + list(soaks)):
            print("case", name, flush=True)
            if name in plan:
                setup, cfg = plan[name]
                res, rec = case_steady(name, setup, cfg())
            else:
                res, rec = case_soak(name[len("soak_"):])
                rec["_offset"] = res["offset_c"]
            with open(CACHE / f"{name}.pkl", "wb") as f:
                pickle.dump((res, rec), f)
            print(json.dumps(res, indent=1, default=float), flush=True)
        if args:
            return
    summary, recs, soak_recs = {}, {}, {}
    for name in list(plan) + list(soaks):
        f = CACHE / f"{name}.pkl"
        if not f.exists():
            continue
        res, rec = pickle.load(open(f, "rb"))
        summary[name] = res
        if name in plan:
            t_end = rec["t"][-1] + DT
            i0 = next(i for i, t in enumerate(rec["t"]) if t >= t_end - WINDOW)
            res["energy_check"] = energy_check(rec, i0, len(rec["t"]))
            res["energy_check"]["throughput_kj"] = sum(
                (rec["q_in"][i] + rec["p_int"][i]) * DT
                for i in range(i0, len(rec["t"]))) / 1e3
            recs[name] = rec
        else:
            soak_recs[name[len("soak_"):]] = rec
    out = HERE / ("network_summary_quick.json" if QUICK else "network_summary.json")
    out.write_text(json.dumps(summary, indent=1, default=float))
    if "--no-plot" not in sys.argv:
        plots(recs, soak_recs, limits)


if __name__ == "__main__":
    main()
