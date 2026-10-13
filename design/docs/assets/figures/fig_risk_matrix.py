"""5x5 risk matrix with worked-example risks (ECSS-M-ST-80C style)."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(7.4, 7.0))


def tier_color(score):
    if score <= 2:
        return "#7ea668"
    if score <= 4:
        return "#a1c47a"
    if score <= 9:
        return "#dfca6f"
    if score <= 15:
        return "#d97a45"
    return "#b03a2e"


for p in range(1, 6):
    for s in range(1, 6):
        score = p * s
        ax.add_patch(Rectangle((p - 1, s - 1), 1, 1, facecolor=tier_color(score), edgecolor="white"))
        ax.text(p - 0.5, s - 0.5, f"{score}", ha="center", va="center",
                color="white", fontsize=11, fontweight="bold")

risks = [
    ("R1", "Reaction-wheel failure",   4, 3),
    ("R2", "Battery degradation",      2, 4),
    ("R3", "Star-tracker glare",       3, 2),
    ("R4", "Ground-link outage",       3, 3),
    ("R5", "Schedule slip",            4, 4),
    ("R6", "Cosmic-ray SEU",           5, 1),
]
for rid, _, sev, lik in risks:
    bx, by = sev - 1 + 0.2, lik - 1 + 0.78
    ax.add_patch(plt.Circle((bx, by), 0.14, color=COLORS["ink"], zorder=3))
    ax.text(bx, by, rid, ha="center", va="center", color="white", fontsize=8,
            fontweight="bold", zorder=4)

ax.set_xlim(-0.05, 5.05)
ax.set_ylim(-0.05, 5.05)
ax.set_aspect("equal")
ax.set_xticks(np.arange(0.5, 5.5))
ax.set_xticklabels(["1\nNegligible", "2\nMinor", "3\nModerate", "4\nMajor", "5\nCatastrophic"], fontsize=8.5)
ax.set_yticks(np.arange(0.5, 5.5))
ax.set_yticklabels(["1\nVery low", "2\nLow", "3\nMedium", "4\nHigh", "5\nVery high"], fontsize=8.5)
ax.set_xlabel("Severity (consequence)")
ax.set_ylabel("Likelihood")
ax.set_title("Risk matrix (ECSS-M-ST-80C 5×5) — worked example")
ax.grid(False)
for spine in ax.spines.values():
    spine.set_visible(False)

key = "   ".join(f"{rid} {name}" for rid, name, _, _ in risks[:3]) + "\n" + \
      "   ".join(f"{rid} {name}" for rid, name, _, _ in risks[3:])
fig.text(0.5, 0.015, key, ha="center", va="bottom", fontsize=8.5, color=COLORS["ink"])
fig.subplots_adjust(bottom=0.2)

save(fig, Path(__file__).stem)
