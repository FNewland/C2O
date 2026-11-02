#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADCS Failure-Scenario Viewer  —  tools/adcs_sim_viewer.py

A browser dashboard (default :8097) around the CERISE-style debris-strike ADCS
failure scenario. Set the orbit, the event timing and the fault definition in
the form, click "Run Simulation", and the diagnostic plots, a statistics row and
a colour-coded event timeline are rendered inline. The run's telemetry can be
downloaded as CSV.

The physics is NOT duplicated here: every run calls
``ADCS_failure_sim/cubesat_adcs_sim.py`` — the same module the CLI script uses —
so the viewer and the offline script can never drift apart. All 38 telemetry
channels that module logs are available to the plots and to the CSV.

Usage:  python tools/adcs_sim_viewer.py [--port 8097] [--host 127.0.0.1] [--public]
Or via: ./start.sh  (started automatically with the suite)

Dependencies: aiohttp, numpy (required); matplotlib (required for the plots —
if it is missing the server still starts and reports a clear error per run).
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import io
import json
import os
import sys
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from aiohttp import web

# The shared tool page frame (tools/tool_frame.py) sits next to this file.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── The shared physics module (ADCS_failure_sim/cubesat_adcs_sim.py) ──────────
REPO = Path(__file__).resolve().parents[1]
_SIM_DIR = REPO / "ADCS_failure_sim"
if str(_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(_SIM_DIR))
import cubesat_adcs_sim as adcs  # noqa: E402

# ── matplotlib is optional at import time so a plotting-free install still
#    starts the server and gives a readable error instead of a stack trace. ────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_MATPLOTLIB = True
    MPL_ERROR = ""
except Exception as exc:                # pragma: no cover - environment dependent
    plt = None
    HAVE_MATPLOTLIB = False
    MPL_ERROR = str(exc)

MAX_CACHED_RUNS = 8          # CSVs kept in memory, keyed by run id


# ══════════════════════════════════════════════════════════════════════════════
#  PLOT GENERATION  (base64 PNG, main repo's channel names)
# ══════════════════════════════════════════════════════════════════════════════
def _arr(log, key):
    return np.array([r[key] for r in log], dtype=float)


# ── Plot palette from the design tokens (shared/ui-tokens/c2o.tokens.json) ───
# The plots sit on the page's own surface in the page's own theme: greys for
# axes and resting traces, the categorical series ramp for multi-trace
# panels, and status colours only for what is a status (the debris-strike
# phase and the saturation limits). No hex value is written here.
_TOKENS_JSON = REPO.parent / "shared" / "ui-tokens" / "c2o.tokens.json"
_PALETTES: dict = {}


def palette(theme: str = "dark") -> dict:
    """Matplotlib colours for ``theme`` ("dark" | "light") from the tokens."""
    theme = theme if theme in ("dark", "light") else "dark"
    if theme in _PALETTES:
        return _PALETTES[theme]
    t = json.loads(_TOKENS_JSON.read_text(encoding="utf-8"))["theme"][theme]
    v = lambda path: _tok(t, path)
    pal = {
        "bg": v("surface.1"), "face": v("surface.0"), "grid": v("line.base"),
        "edge": v("line.strong"), "ink": v("text.tertiary"), "text": v("text.secondary"),
        "val": v("text.value"), "warn": v("status.caution"), "alarm": v("status.alarm"),
        "warnWash": v("status.cautionWash"), "alarmWash": v("status.alarmWash"),
        "fill": v("graphic.fill"),
        "cycle": [v(f"category.{i}") for i in range(1, 8)],
    }
    _PALETTES[theme] = pal
    return pal


def _tok(tree: dict, dotted: str) -> str:
    node = tree
    for part in dotted.split("."):
        node = node[part]
    return node["$value"]


def _rc(P: dict) -> dict:
    from cycler import cycler
    return {
        "figure.facecolor": P["bg"], "savefig.facecolor": P["bg"],
        "axes.facecolor": P["face"], "axes.edgecolor": P["edge"],
        "axes.labelcolor": P["text"], "axes.titlecolor": P["text"],
        "axes.prop_cycle": cycler(color=P["cycle"]),
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": P["ink"], "ytick.color": P["ink"],
        "text.color": P["text"], "grid.color": P["grid"], "grid.alpha": 1.0,
        "legend.facecolor": P["bg"], "legend.edgecolor": P["edge"],
        "legend.labelcolor": P["text"], "legend.framealpha": 0.9,
        "font.size": 10, "axes.titlesize": 10, "axes.labelsize": 10,
        "axes.titleweight": "normal", "axes.titlelocation": "left",
    }


_P = None   # palette of the figure being drawn (make_plots sets it)


def _shade(ax, ti, tr, tt):
    """Phases as washes (caution after the strike, alarm after the corrupted
    recovery command) plus the phase names along the top: colour + text."""
    P = _P
    ax.axvspan(ti / 60, tr / 60, color=P["warnWash"], lw=0, zorder=0)
    ax.axvspan(tr / 60, tt / 60, color=P["alarmWash"], lw=0, zorder=0)
    ax.axvline(ti / 60, color=P["warn"], ls="--", lw=1)
    ax.axvline(tr / 60, color=P["alarm"], ls="--", lw=1)


def _b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return data


def make_plots(log, cfg, theme: str = "dark"):
    """Render the four diagnostic figures as base64 PNGs, in the page theme."""
    if not HAVE_MATPLOTLIB:
        raise RuntimeError(
            "matplotlib is not installed, so the plots cannot be rendered "
            f"({MPL_ERROR}). Install it with: pip install matplotlib")
    global _P
    _P = palette(theme)
    with plt.rc_context(_rc(_P)):
        return _make_plots(log, cfg)


def _make_plots(log, cfg):
    P = _P

    TI = float(cfg["t_impact"])
    TR = float(cfg["t_recovery"])
    TT = float(cfg["t_total"])
    ts = _arr(log, "t")
    t = ts / 60.0

    BG, PBG = P["bg"], P["face"]
    H_SAT_mNms = adcs.RW_MAX_MOMENTUM * 1e3
    TAU_RATED_mNm = adcs.RW_MAX_TORQUE * 1e3
    ax_name = "XYZ"[int(cfg["corrupted_axis"])]
    ax_key = ax_name.lower()

    # ── Plot 1: Sensors ───────────────────────────────────────────────────────
    fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.patch.set_facecolor(BG)
    for a in ax:
        _shade(a, TI, TR, TT)
        a.set_facecolor(PBG)
    ax[0].plot(t, _arr(log, "mag_x_uT"), lw=.8, label="Bx")
    ax[0].plot(t, _arr(log, "mag_y_uT"), lw=.8, label="By")
    ax[0].plot(t, _arr(log, "mag_z_uT"), lw=.8, label="Bz")
    ax[0].plot(t, _arr(log, "mag_mag_uT"), color=P["val"], lw=1.2, label="|B|")
    ax[0].set_ylabel("Magnetometer [uT]")
    ax[0].legend(ncol=4, fontsize=8)
    ax[0].grid(alpha=.3)
    _phase_labels(ax[0], TI, TR, TT)
    ax[1].plot(t, _arr(log, "sun_x"), lw=.8, label="Sun_x")
    ax[1].plot(t, _arr(log, "sun_y"), lw=.8, label="Sun_y")
    ax[1].plot(t, _arr(log, "sun_z"), lw=.8, label="Sun_z")
    ax[1].set_ylabel("Sun sensor [unit, body]")
    ax[1].legend(ncol=3, fontsize=8)
    ax[1].grid(alpha=.3)
    # Flags panel: main's log adds triad_used (was not available in the fork).
    ax[2].plot(t, _arr(log, "eclipse"), lw=1, color=P["cycle"][0], label="Eclipse")
    ax[2].plot(t, _arr(log, "sun_valid"), lw=1, color=P["cycle"][3], ls=":", label="Sun valid")
    ax[2].plot(t, _arr(log, "triad_used"), lw=1, color=P["cycle"][2], ls="--",
               label="TRIAD fix accepted")
    ax[2].set_ylabel("Flags")
    ax[2].set_xlabel("Time [min]")
    ax[2].legend(ncol=3, fontsize=8)
    ax[2].grid(alpha=.3)
    ax[2].set_ylim(-.1, 1.1)
    fig.tight_layout()
    plots = {"sensors": _b64(fig)}

    # ── Plot 2: Estimator / control state ─────────────────────────────────────
    fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.patch.set_facecolor(BG)
    for a in ax:
        _shade(a, TI, TR, TT)
        a.set_facecolor(PBG)
    # Pointing error (estimate vs nadir target) AND estimator error (estimate vs
    # truth) — the second channel exists only in the main repo's physics module.
    ax[0].plot(t, _arr(log, "att_err_deg"), color=P["val"], lw=1,
               label="Pointing error (est vs nadir)")
    ax[0].plot(t, _arr(log, "est_err_deg"), color=P["cycle"][0], lw=.9,
               label="Estimator error (est vs truth)")
    ax[0].set_ylabel("Angle [deg]")
    ax[0].legend(ncol=2, fontsize=8)
    ax[0].grid(alpha=.3)
    _phase_labels(ax[0], TI, TR, TT)
    ax[1].plot(t, _arr(log, "rate_x_dps"), lw=.8, label="wx")
    ax[1].plot(t, _arr(log, "rate_y_dps"), lw=.8, label="wy")
    ax[1].plot(t, _arr(log, "rate_z_dps"), lw=.8, label="wz")
    ax[1].plot(t, _arr(log, "tumble_rate_dps"), color=P["val"], lw=1.2, label="|rate vs nadir|")
    ax[1].set_ylabel("Body rate [deg/s]")
    ax[1].legend(ncol=4, fontsize=8)
    ax[1].grid(alpha=.3)
    modemap = {"NORMAL": 2, "RECOVERY": 1, "SAFE": 0}
    mn = np.array([modemap[r["mode"]] for r in log])
    ax[2].plot(t, mn, drawstyle="steps-post", color=P["val"], lw=1.4)
    ax[2].set_yticks([0, 1, 2])
    ax[2].set_yticklabels(["SAFE", "RECOVERY", "NORMAL"])
    ax[2].set_ylabel("Control mode")
    ax[2].set_xlabel("Time [min]")
    ax[2].grid(alpha=.3)
    fig.tight_layout()
    plots["estimator"] = _b64(fig)

    # ── Plot 3: Actuators (4 panels — wheel RPM added over the fork's 3) ──────
    fig, ax = plt.subplots(4, 1, figsize=(11, 11), sharex=True)
    fig.patch.set_facecolor(BG)
    for a in ax:
        _shade(a, TI, TR, TT)
        a.set_facecolor(PBG)
    ax[0].plot(t, _arr(log, "tau_wheel_x") * 1e3, lw=.8, label="tau_x")
    ax[0].plot(t, _arr(log, "tau_wheel_y") * 1e3, lw=.8, label="tau_y")
    ax[0].plot(t, _arr(log, "tau_wheel_z") * 1e3, lw=.8, label="tau_z")
    ax[0].axhline(TAU_RATED_mNm, color=P["ink"], ls=":", lw=1, label="rated torque")
    ax[0].axhline(-TAU_RATED_mNm, color=P["ink"], ls=":", lw=1)
    ax[0].set_ylabel("Wheel torque [mN m]")
    ax[0].legend(ncol=4, fontsize=8)
    ax[0].grid(alpha=.3)
    _phase_labels(ax[0], TI, TR, TT)
    ax[1].plot(t, _arr(log, "h_wheel_x") * 1e3, lw=.9, label="hx")
    ax[1].plot(t, _arr(log, "h_wheel_y") * 1e3, lw=.9, label="hy")
    ax[1].plot(t, _arr(log, "h_wheel_z") * 1e3, lw=.9, label="hz")
    ax[1].axhline(H_SAT_mNms, color=P["alarm"], ls=":", lw=1, label="saturation")
    ax[1].axhline(-H_SAT_mNms, color=P["alarm"], ls=":", lw=1)
    ax[1].set_ylabel("Wheel momentum [mN m s]")
    ax[1].legend(ncol=4, fontsize=8)
    ax[1].grid(alpha=.3)
    # wheel_rpm_* is derived by the main repo's module; the fork had no such panel.
    ax[2].plot(t, _arr(log, "wheel_rpm_x"), lw=.9, label="RW-1 (X)")
    ax[2].plot(t, _arr(log, "wheel_rpm_y"), lw=.9, label="RW-2 (Y)")
    ax[2].plot(t, _arr(log, "wheel_rpm_z"), lw=.9, label="RW-3 (Z)")
    ax[2].set_ylabel("Wheel speed [RPM]")
    ax[2].legend(ncol=3, fontsize=8)
    ax[2].grid(alpha=.3)
    ax[3].plot(t, _arr(log, "mtq_x"), lw=.8, label="m_x")
    ax[3].plot(t, _arr(log, "mtq_y"), lw=.8, label="m_y")
    ax[3].plot(t, _arr(log, "mtq_z"), lw=.8, label="m_z")
    ax[3].set_ylabel("MTQ dipole [A m^2]")
    ax[3].set_xlabel("Time [min]")
    ax[3].legend(ncol=3, fontsize=8)
    ax[3].grid(alpha=.3)
    fig.tight_layout()
    plots["actuators"] = _b64(fig)

    # ── Plot 4: Event zoom ────────────────────────────────────────────────────
    def zoom_panel(axcol, t0, t1, title, ev_t):
        m = (ts >= t0) & (ts <= t1)
        tt = ts[m]
        mk = dict(marker=".", ms=3, lw=.8)
        axcol[0].set_title(title, fontsize=9)
        axcol[0].plot(tt, _arr(log, "rate_x_dps")[m], label="wx", **mk)
        axcol[0].plot(tt, _arr(log, "rate_y_dps")[m], label="wy", **mk)
        axcol[0].plot(tt, _arr(log, "rate_z_dps")[m], label="wz", **mk)
        axcol[0].plot(tt, _arr(log, "tumble_rate_dps")[m], color=P["val"], lw=1.2, label="|rate|")
        axcol[0].axvline(ev_t, color=P["ink"], ls="--", lw=1)
        axcol[0].set_ylabel("Body rate [deg/s]")
        axcol[0].grid(alpha=.3)
        axcol[0].legend(fontsize=7, ncol=2)
        axcol[1].plot(tt, _arr(log, f"tau_cmd_{ax_key}")[m] * 1e3,
                      label=f"cmd_{ax_key} (corrupted)", **mk)
        axcol[1].plot(tt, _arr(log, f"tau_wheel_{ax_key}")[m] * 1e3,
                      label=f"delivered_{ax_key}", **mk)
        axcol[1].axhline(TAU_RATED_mNm, color=P["ink"], ls=":", lw=1, label="rated torque")
        axcol[1].axhline(-TAU_RATED_mNm, color=P["ink"], ls=":", lw=1)
        axcol[1].set_ylabel("Torque [mN m]")
        axcol[1].grid(alpha=.3)
        axcol[1].legend(fontsize=7)
        axcol[2].plot(tt, _arr(log, "h_wheel_x")[m] * 1e3, label="hx", **mk)
        axcol[2].plot(tt, _arr(log, "h_wheel_y")[m] * 1e3, label="hy", **mk)
        axcol[2].plot(tt, _arr(log, "h_wheel_z")[m] * 1e3, label="hz", **mk)
        axcol[2].axhline(H_SAT_mNms, color=P["alarm"], ls=":", lw=1)
        axcol[2].axhline(-H_SAT_mNms, color=P["alarm"], ls=":", lw=1)
        axcol[2].set_ylabel("Wheel mom. [mN m s]")
        axcol[2].set_xlabel("Time [s]")
        axcol[2].grid(alpha=.3)
        axcol[2].legend(fontsize=7, ncol=2)

    fig, ax = plt.subplots(3, 2, figsize=(13, 9), sharex="col")
    fig.patch.set_facecolor(BG)
    for a in ax.flat:
        a.set_facecolor(PBG)
    zoom_panel(ax[:, 0], max(TI - 30, 0), min(TI + 90, TT),
               "Debris impact, zoomed", TI)
    zoom_panel(ax[:, 1], max(TR - 20, 0), min(TR + 220, TT),
               f"Recovery attempt, zoomed (axis {ax_name} over-torque)", TR)
    fig.tight_layout()
    plots["zoom"] = _b64(fig)

    return plots


# ══════════════════════════════════════════════════════════════════════════════
#  STATISTICS + CSV
# ══════════════════════════════════════════════════════════════════════════════
def _phase_labels(ax, ti, tr, tt):
    """Phase names along the top edge of the first panel of a figure."""
    P = _P
    for x0, x1, name, col in ((0, ti, "NORMAL", P["ink"]), (ti, tr, "SAFE / tumble", P["warn"]),
                              (tr, tt, "RECOVERY", P["alarm"])):
        if x1 - x0 > tt * 0.04:
            ax.text((x0 + 0.01 * tt) / 60, 1.02, name, transform=ax.get_xaxis_transform(),
                    color=col, fontsize=9, va="bottom", ha="left")


def compute_stats(log, cfg):
    """Summary row. Uses main's channel names and its extra channels
    (est_err_deg, triad_used), and looks at all three wheels, not just X."""
    modes = [r["mode"] for r in log]
    dt = float(cfg["dt"])
    h_all = np.abs(np.column_stack([_arr(log, "h_wheel_x"),
                                    _arr(log, "h_wheel_y"),
                                    _arr(log, "h_wheel_z")]))
    peak_axis = int(np.argmax(h_all.max(axis=0)))
    return {
        "max_att_err":   round(float(np.nanmax(_arr(log, "att_err_deg"))), 2),
        "max_est_err":   round(float(np.nanmax(_arr(log, "est_err_deg"))), 2),
        "max_tumble":    round(float(np.nanmax(_arr(log, "tumble_rate_dps"))), 2),
        "max_h_pct":     round(float(h_all.max() / adcs.RW_MAX_MOMENTUM * 100), 1),
        "peak_wheel":    "XYZ"[peak_axis],
        "max_rpm":       round(float(np.nanmax(np.abs(np.column_stack([
            _arr(log, "wheel_rpm_x"), _arr(log, "wheel_rpm_y"),
            _arr(log, "wheel_rpm_z")])))), 0),
        "triad_pct":     round(float(np.mean(_arr(log, "triad_used")) * 100), 1),
        "time_normal":   round(sum(1 for m in modes if m == "NORMAL") * dt / 60, 1),
        "time_safe":     round(sum(1 for m in modes if m == "SAFE") * dt / 60, 1),
        "time_recovery": round(sum(1 for m in modes if m == "RECOVERY") * dt / 60, 1),
        "samples":       len(log),
        "channels":      len(log[0]) if log else 0,
    }


def make_csv(log):
    if not log:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(log[0].keys()))
    w.writeheader()
    w.writerows(log)
    return buf.getvalue()


def run_scenario(params):
    """Run the shared physics module. Returns (log, events, cfg)."""
    cfg = adcs.resolve_params(dict(params or {}, verbose=False))
    events = []
    log, _orbit = adcs.run(cfg, events)
    return log, events, cfg


# ══════════════════════════════════════════════════════════════════════════════
#  SERVER
# ══════════════════════════════════════════════════════════════════════════════
_runs = OrderedDict()                        # run_id -> csv text (bounded)
_executor = ThreadPoolExecutor(max_workers=1)


def _defaults_payload():
    d = adcs.default_params()
    d["epoch"] = d["epoch"].strftime("%Y-%m-%dT%H:%M")
    d.pop("verbose", None)
    return {"defaults": d, "limits": adcs.PARAM_LIMITS,
            "have_matplotlib": HAVE_MATPLOTLIB}


async def handle_index(req):
    from smo_common.web.http import tool_html_response
    import tool_frame          # shared page frame: TOOL_HEAD + title bar
    html = (HTML.replace("__DEFAULTS_JSON__", json.dumps(_defaults_payload()))
            .replace("__FRAME_HEAD__", tool_frame.head())
            .replace("__FRAME_BAR__", tool_frame.bar(
                '<span data-i18n>ADCS failure-scenario viewer</span>'))
            .replace("__FRAME_SCRIPT__", tool_frame.SCRIPT))
    return tool_html_response(html, req.app)


async def handle_defaults(req):
    return web.json_response(_defaults_payload())


def _do_run(params, theme="dark"):
    log, events, cfg = run_scenario(params)
    plots = make_plots(log, cfg, theme)
    return log, events, cfg, plots


async def handle_run(req):
    try:
        params = await req.json()
    except Exception:
        raise web.HTTPBadRequest(text="request body must be JSON")
    if not HAVE_MATPLOTLIB:
        return web.json_response(
            {"error": "matplotlib is not installed, so the plots cannot be "
                      f"rendered ({MPL_ERROR}). Install it with: "
                      "pip install matplotlib"}, status=503)
    loop = asyncio.get_event_loop()
    # Presentation only, not a scenario parameter: the page's theme.
    theme = str(params.pop("theme", "dark")) if isinstance(params, dict) else "dark"
    try:
        log, events, cfg, plots = await loop.run_in_executor(
            _executor, _do_run, params, theme)
    except ValueError as exc:                 # bad/unknown parameter
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:                  # pragma: no cover - defensive
        return web.json_response({"error": f"simulation failed: {exc}"}, status=500)

    run_id = uuid.uuid4().hex[:12]
    _runs[run_id] = make_csv(log)
    while len(_runs) > MAX_CACHED_RUNS:
        _runs.popitem(last=False)

    cfg_out = dict(cfg)
    cfg_out["epoch"] = cfg["epoch"].strftime("%Y-%m-%dT%H:%M:%SZ")
    return web.json_response({"run_id": run_id, "plots": plots,
                              "stats": compute_stats(log, cfg),
                              "events": events, "params": cfg_out})


async def handle_download(req):
    """CSV for a specific run id (falls back to the most recent run)."""
    run_id = req.query.get("id")
    if run_id:
        text = _runs.get(run_id)
        if text is None:
            raise web.HTTPNotFound(text="no such run id (it may have expired)")
    elif _runs:
        run_id, text = next(reversed(_runs.items()))
    else:
        raise web.HTTPNotFound(text="no simulation has been run yet")
    return web.Response(
        text=text, content_type="text/csv",
        headers={"Content-Disposition":
                 f"attachment; filename=adcs_telemetry_{run_id}.csv"})


def create_app():
    # Shared HTTP policy + design system / language runtime (R3 A8, §8).
    _common = Path(__file__).resolve().parents[1] / "packages" / "smo-common" / "src"
    if _common.is_dir() and str(_common) not in sys.path:
        sys.path.insert(0, str(_common))
    from smo_common.web.http import setup_tool_app
    app = setup_tool_app(web.Application())
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/defaults", handle_defaults)
    app.router.add_post("/run", handle_run)
    app.router.add_get("/download", handle_download)
    return app


# ══════════════════════════════════════════════════════════════════════════════
#  HTML DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title data-i18n>ADCS failure-scenario viewer</title>
__FRAME_HEAD__
<style>
/* ADCS viewer. The plots lead; the scenario is a compact rail on the left
   with the run control (and its running state) at the top. Tokens only. */
.ad-wrap{ display:grid; grid-template-columns:300px minmax(0,1fr); gap:var(--sp-4); align-items:start; }
.ad-rail{ position:sticky; top:64px; max-height:calc(100vh - 80px); overflow:auto; }
.ad-run{ display:flex; flex-direction:column; gap:var(--sp-2); padding:var(--sp-3) var(--sp-4);
  border-bottom:1px solid var(--line); position:sticky; top:0; background:var(--s1); z-index:1; }
.ad-run .ds-btn{ width:100%; min-height:32px; }
.ad-run .ds-row .ds-btn{ width:auto; flex:1; }
.ad-run .ds-meta{ min-height:16px; }
.ad-f{ display:grid; grid-template-columns:1fr 1fr; gap:var(--sp-2) var(--sp-3); align-items:end; }
.ad-f .full{ grid-column:1 / -1; }
.ad-main{ display:flex; flex-direction:column; gap:var(--sp-4); min-width:0; }
.ad-ph{ padding:var(--sp-2) var(--sp-4) var(--sp-3); }
.ad-ph .p1{ fill:var(--s3); } .ad-ph .p2{ fill:var(--warn-wash); stroke:var(--warn); }
.ad-ph .p3{ fill:var(--alarm-wash); stroke:var(--alarm); }
.ad-ph .pl{ font-family:var(--sans) !important; font-size:12px !important; fill:var(--tx) !important; }
.ad-ph .ev{ stroke:var(--val); stroke-width:1.5; }
.ad-ph .evl{ fill:var(--val) !important; }
.ad-plots .ds-panel-b{ padding:0; }
.ad-plot{ display:block; width:100%; height:auto; }
.ad-plot[hidden]{ display:none; }
.ad-busy{ opacity:.45; transition:opacity var(--motion) var(--ease); }
.ad-stats{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); }
.ad-stats>div{ padding:var(--sp-2) var(--sp-4) var(--sp-3); border-right:1px solid var(--line);
  border-bottom:1px solid var(--line); display:flex; flex-direction:column; gap:2px; }
.ad-stats .k{ font-size:var(--fs-label); color:var(--tx3); }
.ad-ev td{ vertical-align:baseline; }
#events-wrap{ overflow-x:auto; position:relative; }
.ad-ev td:last-child{ min-width:24ch; }
.ad-empty[hidden]{ display:none; }
.ad-empty{ display:grid; place-items:center; min-height:360px; text-align:center; }
.ad-empty p{ max-width:56ch; color:var(--tx2); }
.ad-empty .ds-meta{ margin-top:var(--sp-2); }
@media (max-width:980px){
  .ad-wrap{ grid-template-columns:minmax(0,1fr); }
  .ad-rail{ position:static; max-height:none; }
  .ad-stats{ grid-template-columns:repeat(2,minmax(0,1fr)); }
}
</style>
</head>
<body>
<a class="ds-skip" href="#main" data-i18n>Skip to content</a>
__FRAME_BAR__
<main id="main" class="tf-main ad-wrap">
  <form class="ds-panel ad-rail" id="form" novalidate aria-label="Scenario parameters" data-i18n-aria-label>
    <div class="ad-run">
      <button type="submit" class="ds-btn primary" id="run-btn" data-i18n>Run simulation</button>
      <div class="ds-row">
        <button type="button" class="ds-btn sm" id="dl-btn" data-i18n>Download CSV</button>
        <button type="button" class="ds-btn ghost sm" id="reset-btn" data-i18n>Reset to defaults</button>
      </div>
      <span class="ds-meta" id="run-meta" role="status" aria-live="polite"></span>
    </div>
    <details class="ds-disclosure" open>
      <summary><span data-i18n data-i18n-context="sim">Timing</span><span class="r" id="sum-timing"></span></summary>
      <div class="bd ad-f" style="padding-left:var(--sp-4)">
        <div class="ds-field full"><label for="t_total" data-i18n>Total Duration (s)</label><input class="ds-input" id="t_total" inputmode="decimal"><span class="hint" data-i18n>16000 s ~ 4.4 h ~ 2.8 orbits</span></div>
        <div class="ds-field"><label for="t_impact" data-i18n>Debris Impact Time (s)</label><input class="ds-input" id="t_impact" inputmode="decimal"></div>
        <div class="ds-field"><label for="t_recovery" data-i18n>Recovery Command Time (s)</label><input class="ds-input" id="t_recovery" inputmode="decimal"></div>
        <div class="ds-field full"><label for="dt" data-i18n>Time Step (s)</label><input class="ds-input" id="dt" inputmode="decimal"><span class="hint" data-i18n>1 s = telemetry rate of the CSV</span></div>
      </div>
    </details>
    <details class="ds-disclosure" open>
      <summary><span data-i18n>Debris Strike</span><span class="r" id="sum-strike"></span></summary>
      <div class="bd ad-f" style="padding-left:var(--sp-4)">
        <div class="ds-field"><label for="corrupted_axis" data-i18n>Corrupted Axis</label>
          <select class="ds-select" id="corrupted_axis"><option value="0">X (RW-1)</option><option value="1">Y (RW-2)</option><option value="2">Z (RW-3)</option></select></div>
        <div class="ds-field"><label for="corruption_factor" data-i18n>Gain Corruption Factor (x)</label><input class="ds-input" id="corruption_factor" inputmode="decimal"></div>
        <div class="ds-field"><label for="dw_x" data-i18n>d-omega X (rad/s)</label><input class="ds-input" id="dw_x" inputmode="decimal"></div>
        <div class="ds-field"><label for="dw_y" data-i18n>d-omega Y (rad/s)</label><input class="ds-input" id="dw_y" inputmode="decimal"></div>
        <div class="ds-field"><label for="dw_z" data-i18n>d-omega Z (rad/s)</label><input class="ds-input" id="dw_z" inputmode="decimal"></div>
        <div class="ds-field"><label for="seed" data-i18n>Noise Seed</label><input class="ds-input" id="seed" inputmode="numeric"></div>
        <span class="hint full ds-meta" data-i18n>same seed -> identical telemetry</span>
      </div>
    </details>
    <details class="ds-disclosure">
      <summary><span data-i18n>Orbit</span><span class="r" id="sum-orbit"></span></summary>
      <div class="bd ad-f" style="padding-left:var(--sp-4)">
        <div class="ds-field"><label for="alt_km" data-i18n>Altitude (km)</label><input class="ds-input" id="alt_km" inputmode="decimal"></div>
        <div class="ds-field"><label for="inc_deg" data-i18n>Inclination (deg)</label><input class="ds-input" id="inc_deg" inputmode="decimal"></div>
        <div class="ds-field"><label for="ecc" data-i18n>Eccentricity</label><input class="ds-input" id="ecc" inputmode="decimal"></div>
        <div class="ds-field"><label for="raan_deg" data-i18n>RAAN (deg)</label><input class="ds-input" id="raan_deg" inputmode="decimal"></div>
        <div class="ds-field"><label for="argp_deg" data-i18n>Arg. of Perigee (deg)</label><input class="ds-input" id="argp_deg" inputmode="decimal"></div>
        <div class="ds-field"><label for="nu_deg" data-i18n>True Anomaly (deg)</label><input class="ds-input" id="nu_deg" inputmode="decimal"></div>
        <div class="ds-field full"><label for="epoch" data-i18n>Epoch (UTC)</label><input class="ds-input" id="epoch" type="datetime-local" step="60"><span class="hint" data-i18n>Sets Sun position &amp; magnetic field</span></div>
      </div>
    </details>
  </form>

  <div class="ad-main">
    <section class="ds-panel" aria-labelledby="ph-h">
      <div class="ds-panel-h"><span id="ph-h" data-i18n>Scenario</span><span class="r" id="ph-meta"></span></div>
      <div class="ad-ph" id="phases"></div>
    </section>
    <div id="run-banner"></div>
    <section class="ds-panel ad-plots" aria-labelledby="pl-h">
      <h2 class="ds-sr" id="pl-h" data-i18n>Diagnostic plots</h2>
      <div id="plot-tabs" style="padding:0 var(--sp-3)"></div>
      <div class="ds-panel-b" id="plot-body" role="tabpanel" aria-labelledby="pl-h">
        <div class="ad-empty" id="placeholder"><div>
          <p data-i18n>Set the scenario on the left, then run the simulation. The four diagnostic plots, the statistics and the event timeline appear here.</p>
          <p class="ds-meta" data-i18n>Typical run time: 4 to 8 s for a 3-hour scenario at 1 s steps.</p>
        </div></div>
        <img class="ad-plot" id="img-sensors" alt="" hidden>
        <img class="ad-plot" id="img-estimator" alt="" hidden>
        <img class="ad-plot" id="img-actuators" alt="" hidden>
        <img class="ad-plot" id="img-zoom" alt="" hidden>
      </div>
    </section>
    <section class="ds-panel" aria-labelledby="st-h" id="stats-panel" hidden>
      <div class="ds-panel-h"><span id="st-h" data-i18n>Run statistics</span><span class="r" id="st-meta"></span></div>
      <div class="ad-stats" id="stats-grid"></div>
      <div id="events-wrap"></div>
    </section>
  </div>
</main>
__FRAME_SCRIPT__
<script type="module">
import { renderValue, renderNoData, renderTabs, mountTabs, renderBanner, setDisabled, setEnabled, glyph, esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
const T = (s, v) => I18n.tText(s, v);
const BOOT = __DEFAULTS_JSON__;
const FIELDS = ['alt_km','inc_deg','ecc','raan_deg','argp_deg','nu_deg','epoch',
                't_total','dt','t_impact','t_recovery','corrupted_axis',
                'corruption_factor','dw_x','dw_y','dw_z','seed'];
const g = (id) => document.getElementById(id);
let LAST = null, running = false, dirty = false, tab = "sensors", t0 = 0, tick = null;

/* ── form state and validation (limits from the physics module) ── */
function applyDefaults() {
  FIELDS.forEach((k) => { if (g(k) && BOOT.defaults[k] !== undefined) g(k).value = BOOT.defaults[k]; });
  FIELDS.forEach((k) => setErr(k, ""));
  dirty = !!LAST; validate();
}
function setErr(id, msg) {
  const inp = g(id), f = inp && inp.closest(".ds-field");
  if (!f) return;
  f.classList.toggle("is-invalid", !!msg);
  let e = f.querySelector(".err");
  if (msg) {
    if (!e) { e = document.createElement("span"); e.className = "err"; e.id = id + "-err"; f.appendChild(e); }
    e.innerHTML = glyph("alarm-up") + esc(msg);
    inp.setAttribute("aria-invalid", "true"); inp.setAttribute("aria-describedby", id + "-err");
  } else { if (e) e.remove(); inp.removeAttribute("aria-invalid"); inp.removeAttribute("aria-describedby"); }
}
function validate() {
  const errs = {};
  for (const k of FIELDS) {
    if (k === "epoch" || k === "corrupted_axis") continue;
    const raw = g(k).value.trim(), v = Number(raw);
    if (raw === "" || !Number.isFinite(v)) { errs[k] = T("Enter a number."); continue; }
    const lim = BOOT.limits[k];
    if (lim && (v < lim[0] || v > lim[1])) errs[k] = T("Between {{a}} and {{b}}.", { a: lim[0], b: lim[1] });
    if (k === "seed" && !Number.isInteger(v)) errs[k] = T("A whole number.");
  }
  const n = (k) => Number(g(k).value);
  if (!errs.t_impact && !errs.t_total && n("t_impact") >= n("t_total")) errs.t_impact = T("Before the end of the run ({{t}} s).", { t: n("t_total") });
  if (!errs.t_recovery && !errs.t_impact && n("t_recovery") <= n("t_impact")) errs.t_recovery = T("After the impact ({{t}} s).", { t: n("t_impact") });
  if (!g("epoch").value) errs.epoch = T("Set the epoch.");
  for (const k of FIELDS) if (k !== "corrupted_axis") setErr(k, errs[k] || "");
  const first = Object.keys(errs)[0];
  const lbl = first ? (document.querySelector(`label[for="${first}"]`) || {}).textContent : "";
  const btn = g("run-btn");
  if (!running) {
    if (first) setDisabled(btn, T("Fix {{field}}: {{msg}}", { field: lbl, msg: errs[first] }));
    else if (!BOOT.have_matplotlib) setDisabled(btn, T("matplotlib is not installed, so plots cannot be rendered."));
    else setEnabled(btn);
  }
  summaries();
  drawPhases();
  return !first;
}
function summaries() {
  g("sum-timing").textContent = `${g("t_total").value} s`;
  g("sum-strike").textContent = `${["X", "Y", "Z"][+g("corrupted_axis").value]} ×${g("corruption_factor").value}`;
  g("sum-orbit").textContent = `${g("alt_km").value} km · ${g("inc_deg").value}°`;
}

/* ── the scenario strip: phases and events on the run's time axis ── */
function drawPhases() {
  const host = g("phases");
  const tt = Number(g("t_total").value), ti = Number(g("t_impact").value), tr = Number(g("t_recovery").value);
  if (!(tt > 0) || !(ti >= 0) || !(tr > ti) || ti >= tt) { host.innerHTML = `<p class="ds-meta">${esc(T("Fix the timing fields to see the scenario."))}</p>`; return; }
  const W = Math.max(300, host.clientWidth - 32), H = 64, L = 0, R = 8;
  const X = (t) => L + (Math.min(t, tt) / tt) * (W - L - R);
  const m = (t) => `${(t / 60).toFixed(0)} min`;
  let s = `<svg class="tf-plot" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-labelledby="ph-h ph-desc">` +
    `<desc id="ph-desc">${esc(T("Normal pointing until the debris strike at {{a}}, safe mode and tumble until the recovery command at {{b}}, recovery until the end at {{c}}.", { a: m(ti), b: m(tr), c: m(tt) }))}</desc>`;
  const seg = (a, b, cls, name) => { const w = X(b) - X(a);
    s += `<rect class="${cls}" x="${X(a).toFixed(1)}" y="8" width="${w.toFixed(1)}" height="22" rx="1"/>`;
    if (w > 70) s += `<text class="pl" x="${(X(a) + 10).toFixed(1)}" y="23">${esc(name)}</text>`; };
  seg(0, ti, "p1", "NORMAL"); seg(ti, tr, "p2", "SAFE / tumble"); seg(tr, tt, "p3", "RECOVERY");
  const evs = LAST && !dirty ? LAST.events : [{ t: ti, type: "impact" }, { t: tr, type: "recovery" }];
  for (const e of evs) {
    const x = X(e.t).toFixed(1);
    s += `<line class="ev" x1="${x}" y1="4" x2="${x}" y2="34"/>`;
  }
  const step = tt > 7200 ? 1800 : tt > 1800 ? 600 : 300;
  for (let t = 0; t <= tt; t += step) s += `<text x="${X(t).toFixed(1)}" y="${H - 6}" text-anchor="${t === 0 ? "start" : "middle"}">${(t / 60).toFixed(0)}</text>`;
  s += `<text x="${W - R}" y="${H - 6}" text-anchor="end">min</text></svg>`;
  host.innerHTML = s;
  g("ph-meta").textContent = LAST && !dirty ? T("last run · {{n}} events", { n: LAST.events.length })
    : LAST ? T("changed since the last run") : T("not run yet");
}

/* ── running state ── */
function setRunning(on) {
  running = on;
  const btn = g("run-btn");
  clearInterval(tick);
  if (on) {
    t0 = Date.now();
    btn.classList.add("is-active");
    const paint = () => { btn.innerHTML = `<span class="ds-run" aria-hidden="true"></span>${esc(T("Running · {{s}} s", { s: Math.round((Date.now() - t0) / 1000) }))}`; };
    paint(); tick = setInterval(paint, 1000);
    btn.setAttribute("aria-busy", "true");
    setDisabled(g("reset-btn"), T("A run is in progress."));
    document.querySelectorAll(".ad-plot").forEach((im) => im.classList.add("ad-busy"));
  } else {
    btn.classList.remove("is-active"); btn.removeAttribute("aria-busy");
    btn.textContent = T("Run simulation");
    setEnabled(g("reset-btn"));
    document.querySelectorAll(".ad-plot").forEach((im) => im.classList.remove("ad-busy"));
  }
  paintDownload();
}
function paintDownload() {
  const b = g("dl-btn");
  if (!LAST) setDisabled(b, T("Run a simulation first."));
  else if (running) setDisabled(b, T("A run is in progress."));
  else setEnabled(b);
}

async function runSim() {
  if (running || !validate()) return;
  const params = { epoch: g("epoch").value, corrupted_axis: +g("corrupted_axis").value,
                   theme: document.documentElement.getAttribute("data-theme") || "dark" };
  FIELDS.forEach((k) => { if (k !== "epoch" && k !== "corrupted_axis") params[k] = +g(k).value; });
  setRunning(true);
  g("run-banner").innerHTML = renderBanner("info", T("Integrating {{n}} time steps", { n: Math.round(params.t_total / params.dt).toLocaleString(I18n.getLang() === "fr" ? "fr-FR" : "en-GB") }), { role: "status" });
  try {
    const res = await fetch("run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(params) });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(d.error || T("Server error {{status}}", { status: res.status }));
    LAST = d; dirty = false; LAST.theme = params.theme;
    ["sensors", "estimator", "actuators", "zoom"].forEach((k) => { g("img-" + k).src = "data:image/png;base64," + d.plots[k]; });
    g("run-banner").innerHTML = "";
    g("run-meta").textContent = T("Last run took {{s}} s", { s: ((Date.now() - t0) / 1000).toFixed(1) });
    showResults();
  } catch (err) {
    g("run-banner").innerHTML = renderBanner("alarm", T("Error: {{msg}}", { msg: err.message }), { role: "alert" });
  }
  setRunning(false);
  drawPhases();
}

/* ── results ── */
const PLOTS = [["sensors", () => T("Sensors")], ["estimator", () => T("Estimator")], ["actuators", () => T("Actuators")], ["zoom", () => T("Event zoom")]];
const ALT = { sensors: () => T("Sensor plots"), estimator: () => T("Estimator plots"), actuators: () => T("Actuator plots"), zoom: () => T("Event zoom plots") };
function drawPlotTabs() {
  g("plot-tabs").innerHTML = renderTabs(PLOTS.map(([id, l]) => ({ id, label: l(), reason: LAST ? "" : T("Run a simulation first.") })), tab, { label: T("Diagnostic plots"), panel: "plot-body" });
  mountTabs(g("plot-tabs"), (id) => { tab = id; drawPlotTabs(); showPlot(); });
}
function showPlot() {
  g("placeholder").hidden = !!LAST;
  PLOTS.forEach(([k]) => { const im = g("img-" + k); im.hidden = !LAST || k !== tab; im.alt = ALT[k](); });
}
function showResults() {
  drawPlotTabs(); showPlot();
  const s = LAST.stats;
  const cell = (k, v, u, d) => `<div><span class="k">${esc(k)}</span>${renderValue(v, { units: u, digits: d })}</div>`;
  g("stats-grid").innerHTML = [
    cell(T("Max pointing error"), s.max_att_err, "°", 2), cell(T("Max estimator error"), s.max_est_err, "°", 2),
    cell(T("Peak tumble rate"), s.max_tumble, "°/s", 2),
    cell(T("Peak wheel momentum ({{wheel}})", { wheel: s.peak_wheel }), s.max_h_pct, "%", 1),
    cell(T("Peak wheel speed"), s.max_rpm, "rpm", 0),
    cell(T("Time in NORMAL"), s.time_normal, "min", 1), cell(T("Time in SAFE"), s.time_safe, "min", 1),
    cell(T("Time in RECOVERY"), s.time_recovery, "min", 1), cell(T("Samples with TRIAD fix"), s.triad_pct, "%", 1),
    cell(T("Samples × {{n}} channels", { n: s.channels }), s.samples, "", 0),
  ].join("");
  g("st-meta").textContent = T("epoch {{e}}", { e: LAST.params.epoch });
  const fmt = (t) => `T+${String(Math.floor(t / 60)).padStart(2, "0")}:${String(Math.floor(t % 60)).padStart(2, "0")}`;
  const kind = (k) => k === "autosafe" ? `<span class="ds-chip is-alarm">${glyph("alarm-up")}${esc(T("Auto safe mode"))}</span>`
    : k === "impact" ? `<span class="ds-chip is-caution">${glyph("warn-up")}${esc(T("Impact"))}</span>`
    : `<span class="ds-chip">${esc(T("Recovery command"))}</span>`;
  g("events-wrap").setAttribute("tabindex", "0");
  g("events-wrap").setAttribute("aria-label", T("Event"));
  g("events-wrap").innerHTML = `<table class="ds-table ad-ev"><thead><tr><th>${esc(T("Time"))}</th><th>${esc(T("Event"))}</th><th>${esc(T("Message"))}</th></tr></thead><tbody>` +
    (LAST.events.length ? LAST.events.map((e) => `<tr><td class="num">${fmt(e.t)}</td><td>${kind(e.type)}</td><td>${esc(e.msg)}</td></tr>`).join("")
      : `<tr><td colspan="3">${esc(T("No events in this run."))}</td></tr>`) + `</tbody></table>`;
  g("stats-panel").hidden = false;
}

function downloadCSV() {
  if (!LAST) return;
  fetch("download?id=" + LAST.run_id).then((r) => r.blob()).then((b) => {
    const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "adcs_telemetry.csv"; a.click();
  });
}

g("form").addEventListener("submit", (ev) => { ev.preventDefault(); runSim(); });
g("form").addEventListener("input", () => { if (LAST) dirty = true; validate(); });
g("reset-btn").addEventListener("click", applyDefaults);
g("dl-btn").addEventListener("click", downloadCSV);
window.addEventListener("c2o:themechange", (e) => {
  if (LAST && LAST.theme !== e.detail.theme) g("run-meta").textContent = T("Plots were drawn in the other theme: run again to redraw them.");
});
const rerender = () => { document.getElementById("tf-meta").innerHTML = `${esc(T("Physics:"))} <code>ADCS_failure_sim/cubesat_adcs_sim.py</code>`; validate(); drawPlotTabs(); showPlot(); paintDownload(); if (LAST) showResults(); if (!running) g("run-btn").textContent = T("Run simulation"); };
window.addEventListener("smo:i18nready", rerender);
window.addEventListener("smo:langchange", rerender);
new ResizeObserver(drawPhases).observe(g("phases"));
applyDefaults(); drawPlotTabs(); showPlot(); paintDownload();
document.getElementById("tf-meta").innerHTML = `${esc(T("Physics:"))} <code>ADCS_failure_sim/cubesat_adcs_sim.py</code>`;
if (!BOOT.have_matplotlib) g("run-banner").innerHTML = renderBanner("alarm", T("matplotlib is not installed, so plots cannot be rendered."));
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="ADCS Failure-Scenario Viewer")
    ap.add_argument("--port", type=int, default=8097)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--public", action="store_true",
                    help="bind 0.0.0.0 so the viewer is reachable from the LAN")
    args = ap.parse_args()

    host = "0.0.0.0" if (args.public or os.environ.get("SMO_PUBLIC") == "1") else args.host
    if not HAVE_MATPLOTLIB:
        print(f"==> WARNING: matplotlib unavailable ({MPL_ERROR}) - plots disabled")
    print(f"==> ADCS Failure-Scenario Viewer on http://localhost:{args.port}")
    web.run_app(create_app(), host=host, port=args.port, print=None)


if __name__ == "__main__":
    main()
