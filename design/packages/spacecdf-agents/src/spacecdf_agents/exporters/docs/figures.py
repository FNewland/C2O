"""SpaceCDF — Figure helpers for DOCX exports.

Every helper returns PNG bytes (already styled in uOttawa Horizon palette),
ready for ``theme.add_figure(doc, png_bytes, caption=...)``.

The palette mirrors ``docs/assets/figures/uottawa_brand.py``. We don't import
that file directly to keep the agents package free of a docs/ dependency, but
the constants are kept in sync.

Each helper is defensive: if it receives empty/None data it returns a small
"data not available" placeholder so the document still renders.
"""
from __future__ import annotations

import io
import math
from typing import Any, Iterable, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Wedge
import numpy as np

# ---- Palette (mirrors uottawa_brand.py) ----
GARNET = "#8f001a"
GARNET_2 = "#9c1c30"
GARNET_DARK = "#5a0010"
CHARCOAL = "#2d2d2c"
WARM_GREY = "#80746c"
BLUE = "#636d77"
GREEN = "#67796c"
POLAR = "#f2f2f2"
WHITE = "#ffffff"

SERIES = [GARNET, BLUE, GREEN, WARM_GREY, CHARCOAL, GARNET_2, "#728479", "#6d7983"]

_STYLE_APPLIED = False


def _apply_style() -> None:
    global _STYLE_APPLIED
    if _STYLE_APPLIED:
        return
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Work Sans", "DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 9.5,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "axes.edgecolor": CHARCOAL,
        "axes.labelcolor": CHARCOAL,
        "xtick.color": CHARCOAL,
        "ytick.color": CHARCOAL,
        "text.color": CHARCOAL,
        "axes.titlecolor": GARNET,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": POLAR,
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "lines.linewidth": 2.0,
        "axes.prop_cycle": plt.cycler(color=SERIES),
        "figure.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "savefig.dpi": 180,
        "savefig.bbox": "tight",
    })
    _STYLE_APPLIED = True


def _save(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


def _placeholder(message: str, *, size=(7, 3.2)) -> bytes:
    _apply_style()
    fig, ax = plt.subplots(figsize=size)
    ax.text(0.5, 0.5, message, ha="center", va="center",
            fontsize=11, style="italic", color=WARM_GREY)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return _save(fig)


# ---------------------------------------------------------------------------
# 1. Budget donut + stacked bar
# ---------------------------------------------------------------------------

def budget_donut(lines: Sequence[dict[str, Any]], *,
                 title: str, unit: str,
                 total_nominal: float | None = None,
                 total_with_margin: float | None = None,
                 allocation: float | None = None) -> bytes:
    """Donut showing nominal contributions by subsystem with central total.

    Each line dict needs: ``subsystem``, ``nominal_value`` (or ``equipment``,
    ``with_margin``).  Lines with zero/negative value are dropped.
    """
    _apply_style()
    items = [(str(l.get("subsystem") or l.get("equipment") or "?"),
              float(l.get("nominal_value", 0) or 0)) for l in lines or []]
    items = [(s, v) for s, v in items if v > 0]
    if not items:
        return _placeholder(f"{title}: no data")
    # Aggregate duplicates by subsystem
    agg: dict[str, float] = {}
    for s, v in items:
        agg[s] = agg.get(s, 0.0) + v
    labels = list(agg.keys())
    values = list(agg.values())

    fig, ax = plt.subplots(figsize=(7, 4.2))
    colors = (SERIES * ((len(values) // len(SERIES)) + 1))[: len(values)]
    wedges, _ = ax.pie(values, labels=None, startangle=90,
                       colors=colors, wedgeprops=dict(width=0.34, edgecolor=WHITE))
    ax.set_title(title, color=GARNET, fontsize=12, weight="bold")

    # Centre total
    centre = total_with_margin if total_with_margin is not None else sum(values)
    ax.text(0, 0.08, f"{centre:.1f}", ha="center", va="center",
            fontsize=18, weight="bold", color=GARNET)
    ax.text(0, -0.18, unit, ha="center", va="center", fontsize=9, color=WARM_GREY)
    if allocation:
        ax.text(0, -0.42, f"alloc: {allocation:.1f} {unit}",
                ha="center", va="center", fontsize=8, color=CHARCOAL)

    # Legend
    legend_labels = [f"{s} — {v:.1f} {unit}" for s, v in zip(labels, values)]
    ax.legend(wedges, legend_labels, loc="center left",
              bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9)
    plt.tight_layout()
    return _save(fig)


def budget_stacked_bar(budgets: dict[str, dict[str, Any]], *, title: str) -> bytes:
    """Side-by-side normalised stacked bar across mass / power / cost / data.

    ``budgets`` keyed by budget type → dict with ``lines``, ``unit``, ``allocation``.
    """
    _apply_style()
    keys = [k for k in ("mass", "power", "data", "cost", "delta_v")
            if k in (budgets or {}) and budgets[k].get("lines")]
    if not keys:
        return _placeholder(f"{title}: no budgets")

    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    # Aggregate per subsystem per budget
    all_subs: list[str] = []
    per_budget: dict[str, dict[str, float]] = {}
    for k in keys:
        per_budget[k] = {}
        for l in budgets[k].get("lines", []):
            sub = str(l.get("subsystem") or "?")
            per_budget[k][sub] = per_budget[k].get(sub, 0.0) + float(l.get("nominal_value", 0) or 0)
            if sub not in all_subs:
                all_subs.append(sub)

    x = np.arange(len(keys))
    width = 0.6
    bottoms = np.zeros(len(keys))
    colors = (SERIES * ((len(all_subs) // len(SERIES)) + 1))[: len(all_subs)]
    for idx, sub in enumerate(all_subs):
        vals = []
        for k in keys:
            total = sum(per_budget[k].values()) or 1
            vals.append(per_budget[k].get(sub, 0) / total * 100)
        ax.bar(x, vals, width, bottom=bottoms, label=sub, color=colors[idx], edgecolor=WHITE)
        bottoms += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels([k.replace("_", " ").upper() for k in keys])
    ax.set_ylabel("Share of budget (%)")
    ax.set_ylim(0, 105)
    ax.set_title(title, color=GARNET)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=8.5)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 2. Orbit & eclipse geometry
# ---------------------------------------------------------------------------

def orbit_geometry(*, altitude_km: float, eclipse_fraction: float,
                   inclination_deg: float | None = None,
                   orbit_type: str = "LEO") -> bytes:
    """Sketch of orbit around Earth with eclipse arc shaded."""
    _apply_style()
    R_E = 6378.0
    a = R_E + max(altitude_km or 400.0, 100.0)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.set_aspect("equal")
    ax.set_xlim(-a * 1.35, a * 1.35); ax.set_ylim(-a * 1.1, a * 1.1)

    # Sun direction (right of figure)
    ax.annotate("", xy=(a * 1.3, 0), xytext=(a * 1.15, 0),
                arrowprops=dict(arrowstyle="-|>", color=GARNET, lw=2))
    ax.text(a * 1.32, 0.05 * a, "Sun", color=GARNET, fontsize=10, weight="bold")

    # Earth
    earth = plt.Circle((0, 0), R_E, color=BLUE, alpha=0.85, ec=CHARCOAL, lw=0.6)
    ax.add_patch(earth)
    ax.text(0, 0, "Earth", ha="center", va="center", color=WHITE, fontsize=9, weight="bold")

    # Shadow cylinder (antisolar)
    sh = mpatches.Rectangle((-a * 1.35, -R_E), a * 1.35, 2 * R_E,
                            color=CHARCOAL, alpha=0.18, lw=0)
    ax.add_patch(sh)
    ax.text(-a * 1.0, R_E * 1.4, "Earth shadow", color=CHARCOAL, fontsize=9, style="italic")

    # Orbit
    theta = np.linspace(0, 2 * np.pi, 400)
    ax.plot(a * np.cos(theta), a * np.sin(theta), color=GARNET, lw=2)

    # Eclipse arc highlight
    frac = max(0.0, min(1.0, eclipse_fraction or 0.0))
    if frac > 0:
        half_angle = math.pi * frac  # angular extent
        theta_e = np.linspace(math.pi - half_angle, math.pi + half_angle, 80)
        ax.plot(a * np.cos(theta_e), a * np.sin(theta_e),
                color=CHARCOAL, lw=4, alpha=0.85)

    # Spacecraft marker
    sc_theta = math.pi / 4
    ax.plot([a * math.cos(sc_theta)], [a * math.sin(sc_theta)], "o",
            color=GARNET_DARK, ms=8, zorder=5)
    ax.annotate("S/C", (a * math.cos(sc_theta), a * math.sin(sc_theta)),
                textcoords="offset points", xytext=(8, 6), color=CHARCOAL, fontsize=9)

    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    title = f"{orbit_type} · {altitude_km:.0f} km"
    if inclination_deg is not None:
        title += f" · i={inclination_deg:.1f}°"
    title += f" · eclipse fraction {frac:.2f}"
    ax.set_title(title, color=GARNET)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 3. Ground-track sketch
# ---------------------------------------------------------------------------

def ground_track(*, altitude_km: float, inclination_deg: float,
                 orbits: int = 3) -> bytes:
    _apply_style()
    R_E = 6378.0
    a = R_E + max(altitude_km or 400.0, 100.0)
    T = 2 * math.pi * math.sqrt(a ** 3 / 398600.4418)  # s
    omega_e = 2 * math.pi / 86164.0
    i = math.radians(inclination_deg or 51.6)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))

    # Continents proxy (just grid)
    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
    for x in range(-180, 181, 30):
        ax.axvline(x, color=POLAR, lw=0.5)
    for y in range(-90, 91, 30):
        ax.axhline(y, color=POLAR, lw=0.5)

    # Sketch ground track over N orbits
    n_pts = 600
    t = np.linspace(0, orbits * T, n_pts)
    # mean anomaly proxy
    M = 2 * math.pi * t / T
    lat = np.degrees(np.arcsin(np.sin(i) * np.sin(M)))
    lon0 = np.degrees(np.arctan2(np.cos(i) * np.sin(M), np.cos(M)))
    lon = lon0 - np.degrees(omega_e * t)
    lon = ((lon + 180) % 360) - 180

    # Break line at lon jumps
    seg_x, seg_y = [lon[0]], [lat[0]]
    for k in range(1, n_pts):
        if abs(lon[k] - lon[k-1]) > 180:
            ax.plot(seg_x, seg_y, color=GARNET, lw=1.5)
            seg_x, seg_y = [], []
        seg_x.append(lon[k]); seg_y.append(lat[k])
    ax.plot(seg_x, seg_y, color=GARNET, lw=1.5)

    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"Indicative ground track — {orbits} orbits, i={inclination_deg:.1f}°",
                 color=GARNET)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 4. Link budget waterfall
# ---------------------------------------------------------------------------

def link_budget_waterfall(items: Sequence[tuple[str, float]], *,
                          title: str = "Link budget waterfall") -> bytes:
    """Each item: (label, dB contribution).  Positive=gain, negative=loss.

    Final bar is the running sum (margin).
    """
    _apply_style()
    if not items:
        return _placeholder("Link budget: no data")
    labels, deltas = zip(*items)
    cumulative = np.cumsum(deltas)
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    base = np.concatenate([[0], cumulative[:-1]])
    colors = [GARNET if d > 0 else BLUE for d in deltas]
    ax.bar(range(len(labels)), deltas, bottom=base, color=colors,
           edgecolor=WHITE, width=0.65)
    # final running line
    ax.plot(range(len(labels)), cumulative, color=CHARCOAL,
            marker="o", ms=4, lw=1.2)
    # annotate values
    for k, (d, c) in enumerate(zip(deltas, cumulative)):
        ax.text(k, c + (0.6 if d >= 0 else -1.2),
                f"{c:+.1f}", ha="center", fontsize=8,
                color=CHARCOAL, weight="bold")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8.5)
    ax.set_ylabel("dB")
    ax.axhline(0, color=CHARCOAL, lw=0.6)
    ax.set_title(title, color=GARNET)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 5. Power-over-orbit timeline
# ---------------------------------------------------------------------------

def power_timeline(*, period_min: float, eclipse_fraction: float,
                   sunlit_load_w: float, eclipse_load_w: float,
                   sa_eol_w: float | None = None,
                   modes: Sequence[dict[str, Any]] | None = None) -> bytes:
    _apply_style()
    period = max(period_min or 95.0, 30.0)
    eclipse_dur = period * (eclipse_fraction or 0.35)
    sunlit_dur = period - eclipse_dur
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    # Two-segment load curve over one orbit
    t = np.linspace(0, period, 400)
    load = np.where(t < sunlit_dur, sunlit_load_w, eclipse_load_w)
    ax.fill_between(t, 0, load, where=(t < sunlit_dur),
                    color=GARNET, alpha=0.7, label="Sunlit load")
    ax.fill_between(t, 0, load, where=(t >= sunlit_dur),
                    color=BLUE, alpha=0.7, label="Eclipse load")
    if sa_eol_w:
        ax.axhline(sa_eol_w, color=CHARCOAL, ls="--", lw=1.2,
                   label=f"SA EoL {sa_eol_w:.1f} W")
    # modes overlay
    if modes:
        for m in modes:
            if "power_w" in m and "start_min" in m and "duration_min" in m:
                ax.axvspan(m["start_min"], m["start_min"] + m["duration_min"],
                           color=POLAR, alpha=0.4)
                ax.text(m["start_min"] + m["duration_min"] / 2,
                        max(sunlit_load_w, eclipse_load_w) * 1.05,
                        m.get("name", ""), fontsize=7, ha="center",
                        rotation=30, color=CHARCOAL)
    ax.set_xlabel("Time over one orbit (min)")
    ax.set_ylabel("Load power (W)")
    ax.set_title("Orbit-averaged power profile", color=GARNET)
    ax.legend(loc="upper right", fontsize=8.5, frameon=False)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 6. Thermal hot/cold case node temperatures
# ---------------------------------------------------------------------------

def thermal_node_bars(nodes: Sequence[dict[str, Any]]) -> bytes:
    """Each node: {name, hot_c, cold_c, limit_hot_c, limit_cold_c}."""
    _apply_style()
    if not nodes:
        return _placeholder("Thermal nodes: no data")
    names = [n.get("name", "?") for n in nodes]
    hot = [float(n.get("hot_c", 0) or 0) for n in nodes]
    cold = [float(n.get("cold_c", 0) or 0) for n in nodes]
    fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(nodes) + 1.4))
    y = np.arange(len(names))
    for k, n in enumerate(nodes):
        ax.plot([cold[k], hot[k]], [y[k], y[k]], color=POLAR, lw=10, solid_capstyle="round")
        if "limit_cold_c" in n and "limit_hot_c" in n:
            ax.plot([n["limit_cold_c"], n["limit_hot_c"]], [y[k], y[k]],
                    color=WARM_GREY, lw=2, alpha=0.6)
    ax.scatter(cold, y, color=BLUE, s=60, zorder=4, label="Cold case")
    ax.scatter(hot, y, color=GARNET, s=60, zorder=4, label="Hot case")
    ax.set_yticks(y); ax.set_yticklabels(names)
    ax.set_xlabel("Temperature (°C)")
    ax.set_title("Thermal node temperatures — hot & cold case", color=GARNET)
    ax.legend(loc="upper right", fontsize=8.5, frameon=False)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 7. Subsystem block diagram
# ---------------------------------------------------------------------------

def subsystem_block_diagram(connections: Sequence[tuple[str, str, str]] | None = None) -> bytes:
    """A canonical CubeSat-style block diagram.

    ``connections`` overrides default arrows: (from, to, label).
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7)
    ax.axis("off")

    boxes = {
        "Payload": (4, 5.5),
        "OBDH": (4, 3.8),
        "TT&C": (1, 3.8),
        "EPS": (1, 2.0),
        "AOCS": (7, 3.8),
        "Propulsion": (7, 2.0),
        "Thermal": (4, 2.0),
        "Structure": (4, 0.4),
    }
    for label, (x, y) in boxes.items():
        is_payload = label == "Payload"
        col = GARNET if is_payload else GARNET_2 if label in ("OBDH", "TT&C") else BLUE
        box = FancyBboxPatch((x - 0.9, y - 0.4), 1.8, 0.8,
                             boxstyle="round,pad=0.05",
                             facecolor=col, edgecolor=CHARCOAL, alpha=0.9, lw=1)
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center",
                color=WHITE, fontsize=10, weight="bold")

    arrows = connections or [
        ("Payload", "OBDH", "data"),
        ("OBDH", "TT&C", "telem"),
        ("TT&C", "OBDH", "TC"),
        ("EPS", "OBDH", "28V"),
        ("EPS", "Payload", "pwr"),
        ("EPS", "AOCS", "pwr"),
        ("EPS", "TT&C", "pwr"),
        ("OBDH", "AOCS", "cmd"),
        ("AOCS", "Propulsion", "thrust"),
        ("Thermal", "Structure", "cond."),
    ]
    for a, b, lbl in arrows:
        if a not in boxes or b not in boxes:
            continue
        x0, y0 = boxes[a]; x1, y1 = boxes[b]
        arrow = FancyArrowPatch((x0, y0), (x1, y1),
                                arrowstyle="-|>", mutation_scale=12,
                                color=CHARCOAL, alpha=0.7, lw=1)
        ax.add_patch(arrow)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(mx, my + 0.08, lbl, fontsize=7, color=WARM_GREY,
                ha="center", va="bottom")

    ax.set_title("System architecture — subsystem block diagram", color=GARNET, fontsize=12)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 8. Compliance heatmap
# ---------------------------------------------------------------------------

def compliance_heatmap(verifications: Sequence[dict[str, Any]]) -> bytes:
    """Requirement ID × status as a stacked horizontal bar."""
    _apply_style()
    if not verifications:
        return _placeholder("Compliance: no data")

    status_order = ["compliant", "marginal", "non_compliant"]
    counts = {s: 0 for s in status_order}
    for v in verifications:
        s = str(v.get("status", "")).lower()
        if s in counts:
            counts[s] += 1
    total = sum(counts.values()) or 1
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    left = 0
    colors = {"compliant": GREEN, "marginal": "#d4a017", "non_compliant": GARNET}
    for s in status_order:
        pct = counts[s] / total * 100
        ax.barh(0, pct, left=left, height=0.4, color=colors[s],
                edgecolor=WHITE, label=f"{s.replace('_',' ').title()} — {counts[s]}")
        if pct > 3:
            ax.text(left + pct / 2, 0, f"{pct:.0f}%", ha="center", va="center",
                    color=WHITE, fontsize=10, weight="bold")
        left += pct
    ax.set_xlim(0, 100); ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([]); ax.set_xlabel("Share of requirements (%)")
    ax.set_title(f"Compliance status — {total} requirements verified",
                 color=GARNET)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25),
              ncol=3, frameon=False, fontsize=9)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 9. Risk matrix (5×5)
# ---------------------------------------------------------------------------

def risk_matrix(risks: Sequence[dict[str, Any]] | None) -> bytes:
    """Plot risks on a 5×5 likelihood/consequence grid (ECSS-M-ST-80 style)."""
    _apply_style()
    fig, ax = plt.subplots(figsize=(6.5, 5.6))
    score = np.zeros((5, 5))
    for L in range(5):
        for C in range(5):
            s = (L + 1) * (C + 1)
            if s >= 15:
                score[L, C] = 2  # red
            elif s >= 8:
                score[L, C] = 1  # amber
            else:
                score[L, C] = 0  # green
    colors = ["#cfe2c8", "#fce5b3", "#ecb6b3"]
    for L in range(5):
        for C in range(5):
            ax.add_patch(plt.Rectangle((C, L), 1, 1,
                                       color=colors[int(score[L, C])],
                                       ec=WHITE, lw=1))
    ax.set_xlim(0, 5); ax.set_ylim(0, 5)
    ax.set_xticks(np.arange(5) + 0.5); ax.set_xticklabels(["1", "2", "3", "4", "5"])
    ax.set_yticks(np.arange(5) + 0.5); ax.set_yticklabels(["1", "2", "3", "4", "5"])
    ax.set_xlabel("Severity / Consequence")
    ax.set_ylabel("Likelihood")
    ax.set_title("Risk index map (ECSS-M-ST-80C style)", color=GARNET)
    # Plot risks
    if risks:
        xs = []; ys = []; labels = []
        for r in risks:
            L = int(r.get("likelihood", 0) or 0)
            C = int(r.get("severity", 0) or 0)
            if 1 <= L <= 5 and 1 <= C <= 5:
                xs.append(C - 0.5); ys.append(L - 0.5)
                labels.append(str(r.get("id") or r.get("name") or "R"))
        ax.scatter(xs, ys, s=110, color=GARNET, edgecolor=CHARCOAL,
                   linewidth=1.2, zorder=5)
        for x, y, l in zip(xs, ys, labels):
            ax.text(x, y - 0.18, l, ha="center", va="top",
                    fontsize=8, color=CHARCOAL)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 10. Convergence iteration plot
# ---------------------------------------------------------------------------

def convergence_plot(iterations: Sequence[dict[str, Any]] | None,
                     *, parameter: str = "mass.dry_mass_kg",
                     ylabel: str = "Dry mass (kg)") -> bytes:
    _apply_style()
    if not iterations:
        return _placeholder("Convergence: no iterations")
    vals = []
    for it in iterations:
        # Tolerant accessor — iterations may be dicts or pydantic objects
        st = it.get("state") if isinstance(it, dict) else getattr(it, "state", None)
        try:
            if hasattr(st, "get"):
                vals.append(float(st.get(parameter, 0) or 0))
            else:
                vals.append(0.0)
        except Exception:
            vals.append(0.0)
    if not any(vals):
        return _placeholder(f"Convergence: {parameter} not tracked")
    xs = np.arange(1, len(vals) + 1)
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.plot(xs, vals, marker="o", color=GARNET, lw=2)
    ax.set_xlabel("Iteration")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Design loop convergence — {parameter}", color=GARNET)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 11. Cost WBS bar
# ---------------------------------------------------------------------------

def cost_wbs_bar(wbs: Sequence[dict[str, Any]] | None) -> bytes:
    _apply_style()
    if not wbs:
        return _placeholder("Cost WBS: no data")
    names = [w.get("name", w.get("wbs_id", "?")) for w in wbs]
    ddte = [float(w.get("ddte_keur", 0) or 0) / 1000 for w in wbs]
    recurring = [float(w.get("recurring_keur", 0) or 0) / 1000 for w in wbs]
    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.5, 0.5 * len(names) + 1.5))
    ax.barh(y, ddte, color=GARNET, label="DDT&E")
    ax.barh(y, recurring, left=ddte, color=BLUE, label="Recurring")
    ax.set_yticks(y); ax.set_yticklabels(names)
    ax.set_xlabel("Cost (MEUR)")
    ax.invert_yaxis()
    ax.set_title("Cost breakdown by WBS element", color=GARNET)
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    plt.tight_layout()
    return _save(fig)


# ---------------------------------------------------------------------------
# 12. Cost P-curve (probability bars)
# ---------------------------------------------------------------------------

def cost_pcurve(cost: dict[str, Any]) -> bytes:
    _apply_style()
    if not cost:
        return _placeholder("Cost: no estimate")
    labels = ["P50", "P70", "P80", "P90"]
    values = [cost.get(f"{l.lower()}_meur", cost.get(f"{l.lower()}_keur", 0) / 1000)
              for l in labels]
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    bars = ax.bar(labels, values, color=[BLUE, BLUE, GARNET_2, GARNET],
                  edgecolor=WHITE)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
                f"{v:.1f}", ha="center", color=CHARCOAL, fontsize=9, weight="bold")
    ax.set_ylabel("Estimated cost (MEUR)")
    # Keep title brief so it doesn't collide with the bars
    model = cost.get("model_used", "")
    title = f"Cost confidence levels — {model[:36]}" if model else "Cost confidence levels"
    ax.set_title(title, color=GARNET, pad=10)
    ax.margins(y=0.18)
    plt.tight_layout()
    return _save(fig)
