"""5x5 risk matrix with worked example points (ECSS-M-ST-80C-style)."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(7.6, 6.4))

# Tier colours: 1-2 green, 3-4 amber, 5-9 yellow, 10-15 orange, 16-25 red
def tier_color(score):
    if score <= 2:  return "#7ea668"
    if score <= 4:  return "#a1c47a"
    if score <= 9:  return "#dfca6f"
    if score <= 15: return "#d97a45"
    return "#9c1c30"

for p in range(1, 6):       # severity (column)
    for s in range(1, 6):   # likelihood (row)
        score = p * s
        ax.add_patch(Rectangle((p-1, s-1), 1, 1,
                                facecolor=tier_color(score), edgecolor="white"))
        ax.text(p-0.5, s-0.5, f"{score}", ha="center", va="center",
                color="white", fontsize=11, fontweight="bold")

# Risks plotted
risks = [
    ("R1 RW failure",            4, 3),  # P=4 S=3
    ("R2 Battery degradation",   2, 4),
    ("R3 Star tracker glare",    3, 2),
    ("R4 Ground link outage",    3, 3),
    ("R5 Schedule slip",         4, 4),
    ("R6 Cosmic ray SEU",        5, 1),
]
for name, sev, lik in risks:
    ax.plot(sev-0.5, lik-0.5, "o", color="white", ms=11, mec=COLORS["charcoal"], mew=1.3)
    ax.text(sev-0.5, lik-0.85, name, ha="center", va="top",
            fontsize=8.0, color=COLORS["charcoal"],
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec=COLORS["polar"], alpha=0.92))

ax.set_xlim(0, 5); ax.set_ylim(0, 5)
ax.set_aspect("equal")
ax.set_xticks(np.arange(0.5, 5.5))
ax.set_xticklabels(["1\nNegligible", "2\nMinor", "3\nModerate", "4\nMajor", "5\nCatastrophic"], fontsize=8)
ax.set_yticks(np.arange(0.5, 5.5))
ax.set_yticklabels(["1\nVery low", "2\nLow", "3\nMedium", "4\nHigh", "5\nVery high"], fontsize=8)
ax.set_xlabel("Severity")
ax.set_ylabel("Likelihood")
ax.set_title("Risk Matrix (ECSS-M-ST-80C 5×5) — worked example")
for spine in ax.spines.values(): spine.set_visible(False)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_risk_matrix.png")
print("OK risk matrix")
