"""Need → MoE → objective → MoP → requirement → TPM chain (Ch 4 §4.3.3).

Vertical flow with the agricultural-monitoring examples of Table 4.3.3 beside
each level, and the owner / lifecycle phase at which each measure is evaluated.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from oer_style import apply_style, COLORS, save

apply_style()

levels = [
    ("Stakeholder need", "operational problem stated by the users",
     "“Timely crop assessments for food security”",
     "", COLORS["ink"]),
    ("MoE · Measure of Effectiveness", "how well the system satisfies the need",
     "“% of crop assessments delivered within\n5 days of acquisition”",
     "users / stakeholders — evaluated in Phase E", COLORS["accent"]),
    ("Mission objective", "specific, measurable goal",
     "“Provide 10 m GSD multispectral imagery,\nrevisit ≤ 5 days, data latency ≤ 24 h”",
     "", COLORS["ink"]),
    ("MoP · Measure of Performance", "technical performance of the system",
     "“GSD ≤ 10 m at nadir”",
     "systems engineer — verified in Phase C/D", COLORS["accent_2"]),
    ("Technical requirement", "verifiable “shall” statement",
     "“The payload shall achieve GSD ≤ 10 m at nadir\nfrom the operational orbit”",
     "", COLORS["ink"]),
    ("TPM · Technical Performance Measure", "design parameter tracked over time",
     "“Current best estimate of imager mass\nversus the 1.5 kg allocation”",
     "design team — tracked in every phase", COLORS["accent_3"]),
]

fig, ax = plt.subplots(figsize=(7.5, 5.4))
ax.set_xlim(0, 15)
ax.set_ylim(0, 11.8)
ax.axis("off")

bw, bh, x0 = 6.0, 1.25, 0.3
pitch = 1.85
for i, (title, sub, example, owner, col) in enumerate(levels):
    y = 11.0 - bh - i * pitch
    filled = col != COLORS["ink"]
    ax.add_patch(FancyBboxPatch((x0, y), bw, bh, boxstyle="round,pad=0.06",
                                facecolor=col if filled else "white",
                                edgecolor=col, linewidth=1.4))
    tc = "white" if filled else COLORS["ink"]
    ax.text(x0 + bw / 2, y + bh * 0.66, title, ha="center", va="center",
            fontsize=8, fontweight="bold", color=tc)
    ax.text(x0 + bw / 2, y + bh * 0.28, sub, ha="center", va="center",
            fontsize=7.5, color=tc, style="italic")
    # example and owner on the right
    ax.text(x0 + bw + 0.4, y + bh * (0.70 if owner else 0.5), example, ha="left",
            va="center", fontsize=8, color=COLORS["ink"], linespacing=1.15)
    if owner:
        ax.text(x0 + bw + 0.4, y + bh * 0.12, owner, ha="left", va="center",
                fontsize=7.5, color=col, style="italic")
    if i < len(levels) - 1:
        ax.add_patch(FancyArrowPatch((x0 + bw / 2, y - 0.02), (x0 + bw / 2, y - pitch + bh + 0.02),
                                     arrowstyle="-|>", mutation_scale=12,
                                     color=COLORS["grey"], linewidth=1.4))
# column headings
ax.text(x0 + bw / 2, 11.7, "Level", ha="center", va="top", fontsize=9, fontweight="bold",
        color=COLORS["grey"])
ax.text(x0 + bw + 0.4, 11.7, "Agricultural-monitoring example  ·  owner and when evaluated",
        ha="left", va="top", fontsize=9, fontweight="bold", color=COLORS["grey"])
save(fig, Path(__file__).stem)
