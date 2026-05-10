"""System-V model: decomposition (left) and integration (right)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from uottawa_brand import apply_style, COLORS, add_footer
import numpy as np

apply_style()
fig, ax = plt.subplots(figsize=(11.0, 5.6))
ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis("off")

ax.set_title("System-V Model — Decomposition · Integration",
             fontsize=12, color=COLORS["charcoal"], pad=10)

# 4 levels per side, converging to a single "Implementation" box at the apex
left_levels = [
    ("Mission needs",         COLORS["blue"]),
    ("System requirements",   COLORS["blue"]),
    ("Subsystem specs",       COLORS["green"]),
    ("Component specs",       COLORS["green"]),
]
right_levels = [
    ("Mission acceptance",    COLORS["garnet"]),
    ("System V&V",            COLORS["garnet"]),
    ("Subsystem test",        COLORS["green"]),
    ("Component test",        COLORS["green"]),
]

# Y rows for the 4 levels (top → bottom)
ys = [8.7, 7.5, 6.3, 5.1]
# X positions on each side (top is widest, bottom is narrower as the V converges)
xs_left  = np.linspace(1.5, 4.5, 4)
xs_right = np.linspace(12.5, 9.5, 4)

# V lines (apex at x=7.0, y=3.4)
apex = (7.0, 3.4)
ax.plot([xs_left[0], apex[0]],  [ys[0], apex[1]], color=COLORS["polar"], lw=1.3, zorder=0)
ax.plot([xs_right[0], apex[0]], [ys[0], apex[1]], color=COLORS["polar"], lw=1.3, zorder=0)

def label_box(ax, x, y, txt, color, w=2.6, h=0.6):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.04", linewidth=0,
                         facecolor=color, alpha=0.92)
    ax.add_patch(box)
    ax.text(x, y, txt, ha="center", va="center", fontsize=9,
            color="white", fontweight="bold")

for (lbl, color), x, y in zip(left_levels, xs_left, ys):
    label_box(ax, x, y, lbl, color)
for (lbl, color), x, y in zip(right_levels, xs_right, ys):
    label_box(ax, x, y, lbl, color, w=2.8)

# Apex / Implementation block — single, centred
ax.add_patch(FancyBboxPatch((apex[0] - 1.6, apex[1] - 0.45), 3.2, 0.9,
                            boxstyle="round,pad=0.04", linewidth=0,
                            facecolor=COLORS["charcoal"], alpha=0.95))
ax.text(apex[0], apex[1] + 0.1, "Implementation",
        ha="center", va="center", fontsize=10, color="white", fontweight="bold")
ax.text(apex[0], apex[1] - 0.22, "(build • inspect • unit test)",
        ha="center", va="center", fontsize=8, color="white", style="italic")

# Side captions — placed clear of the top-row boxes
ax.text(0.4, 9.6, "DECOMPOSITION", fontsize=10,
        color=COLORS["blue"], fontweight="bold")
ax.text(13.6, 9.6, "INTEGRATION & VERIFICATION", fontsize=10,
        color=COLORS["garnet"], fontweight="bold", ha="right")

# Horizontal dashed traceability lines linking matched levels
for y in ys:
    ax.plot([2.9, 11.1], [y, y], "--", color=COLORS["polar"], lw=0.8, zorder=0)

# Down arrow on left, up arrow on right
ax.annotate("", xy=(0.8, 5.1), xytext=(0.8, 8.7),
            arrowprops=dict(arrowstyle="->", color=COLORS["blue"], lw=1.2))
ax.text(0.55, 6.9, "decompose", rotation=90, fontsize=8.5,
        color=COLORS["blue"], ha="center", va="center", fontweight="bold")
ax.annotate("", xy=(13.2, 8.7), xytext=(13.2, 5.1),
            arrowprops=dict(arrowstyle="->", color=COLORS["garnet"], lw=1.2))
ax.text(13.45, 6.9, "integrate", rotation=90, fontsize=8.5,
        color=COLORS["garnet"], ha="center", va="center", fontweight="bold")

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_system_v.png")
print("OK system-V")
