"""FDIR hierarchy (Chapter 18 §18.3.2) as a layered pyramid: Level 0 hardware
watchdog at the base up to Level 4 ground at the apex, with detection means,
response and latency per layer, an "escalate if not cleared" arrow upward and a
"ground override" arrow downward through all layers."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch
from oer_style import apply_style, COLORS, save

apply_style()
fig = plt.figure(figsize=(7.0, 4.6))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_axis_off()
ax.grid(False)

levels = [  # bottom → top
    ("Level 0", "Hardware", "built-in watchdog", "component reset", "milliseconds",
     "processor watchdog timer", COLORS["accent_6"]),
    ("Level 1", "Unit", "unit-level monitoring", "unit reconfiguration", "seconds",
     "EPS over-current trip", COLORS["accent_3"]),
    ("Level 2", "Subsystem", "subsystem health check", "subsystem fallback mode", "seconds to minutes",
     "switch to backup star tracker", COLORS["accent_5"]),
    ("Level 3", "System", "system-level anomaly detection", "mode change: enter Safe", "minutes",
     "transition to safe mode", COLORS["accent_2"]),
    ("Level 4", "Ground", "human-in-the-loop diagnosis", "ground-command recovery", "hours to days",
     "anomaly investigation and patch", COLORS["accent_4"]),
]

# pyramid geometry: apex at (xc, ytop), base half-width hw0 at ybot
xc, ybot, ytop = 30, 8, 90
hw_bot, hw_top = 24, 5
n = len(levels)
hts = (ytop - ybot) / n
for i, (lvl, name, det, resp, lat, ex, c) in enumerate(levels):
    y0, y1 = ybot + i * hts, ybot + (i + 1) * hts
    w0 = hw_bot - (hw_bot - hw_top) * (i / n)
    w1 = hw_bot - (hw_bot - hw_top) * ((i + 1) / n)
    ax.add_patch(Polygon([(xc - w0, y0), (xc + w0, y0), (xc + w1, y1), (xc - w1, y1)], closed=True,
                         facecolor=c, edgecolor="white", lw=1.5, zorder=3, alpha=0.95))
    ax.text(xc, (y0 + y1) / 2 + 2.2, lvl, ha="center", va="center", fontsize=9, fontweight="bold",
            color="white", zorder=4)
    ax.text(xc, (y0 + y1) / 2 - 2.2, name, ha="center", va="center", fontsize=9, color="white", zorder=4)
    # annotation row to the right
    xa = 64
    ax.plot([xc + w1 + 0.5, xa - 1.5], [(y0 + y1) / 2, (y0 + y1) / 2], color=c, lw=0.8, ls=":", zorder=2)
    ax.text(xa, (y0 + y1) / 2 + 4.8, f"Detection: {det}", fontsize=8, va="center", ha="left", color=COLORS["ink"])
    ax.text(xa, (y0 + y1) / 2 + 1.6, f"Response: {resp}", fontsize=8, va="center", ha="left", color=COLORS["ink"])
    ax.text(xa, (y0 + y1) / 2 - 1.6, f"Latency: {lat}", fontsize=8, va="center", ha="left", color=c,
            fontweight="bold")
    ax.text(xa, (y0 + y1) / 2 - 4.8, f"e.g. {ex}", fontsize=8, va="center", ha="left",
            color=COLORS["grey"], style="italic")

# column header
ax.text(64, 96.5, "What each layer does", fontsize=9, fontweight="bold", va="center")
ax.text(xc, 96.5, "FDIR layer", fontsize=9, fontweight="bold", va="center", ha="center")

# escalation arrow (left, upward)
xe = 1.5
ax.add_patch(FancyArrowPatch((xe + 1.5, ybot + 2), (xe + 1.5, ytop - 2),
                             arrowstyle="-|>", mutation_scale=14, color=COLORS["accent_2"], lw=2.0,
                             zorder=2, shrinkA=0, shrinkB=0))
ax.text(xe + 0.7, (ybot + ytop) / 2, "escalate if the fault is not cleared", rotation=90,
        ha="right", va="center", fontsize=8.5, color=COLORS["accent_2"], fontweight="bold")

# ground-override arrow (right of pyramid, downward)
xo = xc + hw_bot + 2.0
ax.add_patch(FancyArrowPatch((xo, ytop - 2), (xo, ybot + 2), arrowstyle="-|>", mutation_scale=14,
                             color=COLORS["accent_4"], lw=2.0, zorder=2, shrinkA=0, shrinkB=0,
                             linestyle="--"))
ax.text(xo + 1.2, (ybot + ytop) / 2, "ground override: every autonomous action is\nvisible in telemetry and reversible by command",
        rotation=90, ha="left", va="center", fontsize=8, color=COLORS["accent_4"], linespacing=1.15)

ax.text(xc, 3, "faults enter at the lowest layer that can detect them; the ground is the top level",
        ha="center", va="center", fontsize=8, style="italic", color=COLORS["grey"])

save(fig, Path(__file__).stem)
