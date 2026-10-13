"""System-V model: decomposition (left) and integration & verification (right)."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(11.0, 4.6))
ax.set_xlim(0, 14)
ax.set_ylim(2.6, 10.2)
ax.axis("off")
ax.set_title("System-V model — decomposition · integration and verification", pad=8)

left_levels = [("Mission needs", COLORS["accent"]), ("System requirements", COLORS["accent"]),
               ("Subsystem specs", COLORS["accent_6"]), ("Component specs", COLORS["accent_6"])]
right_levels = [("Mission acceptance", COLORS["accent_2"]), ("System V&V", COLORS["accent_2"]),
                ("Subsystem test", COLORS["accent_3"]), ("Component test", COLORS["accent_3"])]

ys = [8.7, 7.5, 6.3, 5.1]
xs_left = np.linspace(1.5, 4.5, 4)
xs_right = np.linspace(12.5, 9.5, 4)
apex = (7.0, 3.4)

ax.plot([xs_left[0], apex[0]], [ys[0], apex[1]], color=COLORS["grey"], alpha=0.5, lw=1.3, zorder=0)
ax.plot([xs_right[0], apex[0]], [ys[0], apex[1]], color=COLORS["grey"], alpha=0.5, lw=1.3, zorder=0)
for y in ys:
    ax.plot([2.9, 11.1], [y, y], "--", color=COLORS["grey"], alpha=0.5, lw=0.8, zorder=0)
ax.text(7.0, ys[0] + 0.45, "traceability: each requirement ↔ the activity that verifies it",
        ha="center", va="bottom", fontsize=8, color=COLORS["grey"], style="italic")


def label_box(x, y, txt, color, w=2.6, h=0.6):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.04",
                                linewidth=0, facecolor=color, alpha=0.95))
    ax.text(x, y, txt, ha="center", va="center", fontsize=9, color="white", fontweight="bold")


for (lbl, color), x, y in zip(left_levels, xs_left, ys):
    label_box(x, y, lbl, color)
for (lbl, color), x, y in zip(right_levels, xs_right, ys):
    label_box(x, y, lbl, color, w=2.8)

ax.add_patch(FancyBboxPatch((apex[0] - 1.6, apex[1] - 0.45), 3.2, 0.9, boxstyle="round,pad=0.04",
                            linewidth=0, facecolor=COLORS["ink"], alpha=0.95))
ax.text(apex[0], apex[1] + 0.12, "Implementation", ha="center", va="center",
        fontsize=10, color="white", fontweight="bold")
ax.text(apex[0], apex[1] - 0.22, "(build · inspect · unit test)", ha="center", va="center",
        fontsize=8, color="white", style="italic")

ax.text(0.4, 9.75, "DECOMPOSITION", fontsize=10, color=COLORS["accent"], fontweight="bold")
ax.text(13.6, 9.75, "INTEGRATION & VERIFICATION", fontsize=10, color=COLORS["accent_2"],
        fontweight="bold", ha="right")

ax.annotate("", xy=(0.8, 5.1), xytext=(0.8, 8.7),
            arrowprops=dict(arrowstyle="->", color=COLORS["accent"], lw=1.2))
ax.text(0.5, 6.9, "decompose", rotation=90, fontsize=8.5, color=COLORS["accent"],
        ha="center", va="center", fontweight="bold")
ax.annotate("", xy=(13.2, 8.7), xytext=(13.2, 5.1),
            arrowprops=dict(arrowstyle="->", color=COLORS["accent_2"], lw=1.2))
ax.text(13.5, 6.9, "integrate", rotation=90, fontsize=8.5, color=COLORS["accent_2"],
        ha="center", va="center", fontweight="bold")

save(fig, Path(__file__).stem)
