"""TRL ladder annotated with course touchpoints."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(9.0, 5.4))
ax.set_xlim(0, 12); ax.set_ylim(0, 10); ax.axis("off")
ax.set_title("Technology Readiness Level (TRL) Ladder",
             fontsize=12, color=COLORS["charcoal"], pad=10)

trls = [
    (1,  "Basic principles",                 COLORS["warm_grey"]),
    (2,  "Concept formulated",               COLORS["warm_grey"]),
    (3,  "Proof of concept",                 COLORS["warm_grey"]),
    (4,  "Lab validation",                   COLORS["green"]),
    (5,  "Relevant-environment validation",  COLORS["green"]),
    (6,  "Relevant-environment demo",        COLORS["green"]),
    (7,  "Operational demo",                 COLORS["blue"]),
    (8,  "Qualified system",                 COLORS["blue"]),
    (9,  "Flight-proven",                    COLORS["garnet"]),
]

for idx, (trl, label, color) in enumerate(trls):
    y = idx + 0.4
    box = FancyBboxPatch((1, y), 8, 0.8, boxstyle="round,pad=0.04",
                         linewidth=0, facecolor=color, alpha=0.82)
    ax.add_patch(box)
    ax.text(1.3, y + 0.4, f"TRL {trl}",
            color="white", fontsize=10, fontweight="bold", va="center")
    ax.text(2.7, y + 0.4, label, color="white", fontsize=10, va="center")

# Right-side ladder annotations: course touchpoints
touch = {
    "TRL 1–3": "Discussed in Course Plan §2 — research / IRAD context",
    "TRL 4–6": "CubeSat platforms typically buy at TRL ≥ 6 (commercial COTS)",
    "TRL 7":   "First in-orbit demonstration — relevant for new instruments",
    "TRL 8–9": "Operational missions — flight heritage drives selection in CDF Day 3",
}
for j, (k, v) in enumerate(touch.items()):
    y = 8 - j*1.6
    ax.text(9.5, y + 0.45, k, fontsize=9.5, fontweight="bold", color=COLORS["charcoal"])
    ax.text(9.5, y - 0.05, v, fontsize=8.5, color=COLORS["charcoal"], wrap=True)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_trl.png")
print("OK trl ladder")
