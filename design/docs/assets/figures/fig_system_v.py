"""System-V model: decomposition (left) and integration (right)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(10.0, 5.2))
ax.set_xlim(0, 14); ax.set_ylim(0, 9); ax.axis("off")

ax.set_title("System-V Model — Decomposition · Integration", fontsize=12,
             color=COLORS["charcoal"], pad=10)

# Left side (decomposition) — top to bottom
left_levels = [
    ("Mission needs",         8.2, COLORS["blue"]),
    ("System requirements",   7.0, COLORS["blue"]),
    ("Subsystem specs",       5.8, COLORS["green"]),
    ("Component specs",       4.6, COLORS["green"]),
    ("Build / Code",          3.4, COLORS["warm_grey"]),
]
right_levels = [
    ("Mission acceptance",    8.2, COLORS["garnet"]),
    ("System V&V",            7.0, COLORS["garnet"]),
    ("Subsystem test",        5.8, COLORS["green"]),
    ("Component test",        4.6, COLORS["green"]),
    ("Inspection / Unit test",3.4, COLORS["warm_grey"]),
]

# Draw V lines (slanting)
ax.plot([1.6, 7.0], [8.4, 3.0], color=COLORS["polar"], lw=1.3, zorder=0)
ax.plot([7.0, 12.4], [3.0, 8.4], color=COLORS["polar"], lw=1.3, zorder=0)

def label_box(ax, x, y, txt, color, w=2.6, h=0.6):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.04", linewidth=0,
                         facecolor=color, alpha=0.92)
    ax.add_patch(box)
    ax.text(x, y, txt, ha="center", va="center", fontsize=9,
            color="white", fontweight="bold")

# Compute x positions along the V
import numpy as np
xs_left  = np.linspace(1.6, 7.0, 5)
xs_right = np.linspace(12.4, 7.0, 5)
ys = [8.4, 7.0, 5.8, 4.6, 3.0]

for x, (lbl, _y, c) in zip(xs_left, left_levels):
    y_pos = 8.4 - (xs_left.tolist().index(x)) * 1.35
    label_box(ax, x, y_pos, lbl, c)
for x, (lbl, _y, c) in zip(xs_right, right_levels):
    idx = xs_right.tolist().index(x)
    y_pos = 8.4 - idx * 1.35
    label_box(ax, x, y_pos, lbl, c, w=2.7)

# Bottom join annotation
ax.text(7.0, 2.4, "Implementation",
        ha="center", va="center", fontsize=9.5, color=COLORS["charcoal"],
        fontweight="bold")
ax.add_patch(FancyBboxPatch((5.6, 1.9), 2.8, 0.7, boxstyle="round,pad=0.04",
                            linewidth=0, facecolor=COLORS["charcoal"], alpha=0.85))
ax.text(7.0, 2.25, "Implementation", ha="center", va="center",
        fontsize=9, color="white", fontweight="bold")

# Side captions
ax.text(0.6, 8.6, "DECOMPOSITION", fontsize=9, color=COLORS["blue"], fontweight="bold")
ax.text(13.4, 8.6, "INTEGRATION & VERIFICATION", fontsize=9, color=COLORS["garnet"],
        fontweight="bold", ha="right")

# Horizontal dashed traceability lines (decomposition <-> verification)
for y in [8.2, 7.0, 5.8, 4.6]:
    ax.plot([2.9, 11.1], [y, y], "--", color=COLORS["polar"], lw=0.8, zorder=0)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_system_v.png")
print("OK system-V")
