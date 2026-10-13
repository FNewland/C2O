"""End-to-end data pipeline, instrument → user, as a horizontal flow (Ch 4 §4.8.5).

Seven stages grouped by segment (space / ground / user), with the key sizing
parameter of each stage from the §4.8.5 table written beneath it, and the
daily-balance condition (downlink capacity ≥ data generated) noted.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from oer_style import apply_style, COLORS, save

apply_style()

stages = [
    ("Instrument", "GB/day =\nrate × duty\ncycle", COLORS["accent"]),
    ("On-board\nstorage", "GB ≥ 1 day\nof data\n(2× margin)", COLORS["accent"]),
    ("Downlink", "GB/pass =\nrate × contact\ntime", COLORS["accent"]),
    ("Ground\nreception", "passes/day,\nstation\nnetwork", COLORS["accent_3"]),
    ("Processing\nL0→L1→L2", "latency (h):\nalgorithms,\ncompute", COLORS["accent_3"]),
    ("Archive", "catalogue,\nAPI, long-term\nstorage", COLORS["accent_3"]),
    ("User\ndelivery", "latency (h):\nnetwork\nbandwidth", COLORS["accent_2"]),
]
groups = [("Space segment", 0, 2), ("Ground segment", 3, 5), ("User segment", 6, 6)]

fig, ax = plt.subplots(figsize=(7.5, 3.4))
n = len(stages)
bw, gap = 1.5, 0.6
pitch = bw + gap
ax.set_xlim(-0.15, n * pitch - gap + 0.15)
ax.set_ylim(-2.2, 2.75)
ax.axis("off")

y0, bh = 0.0, 1.1
for i, (name, param, col) in enumerate(stages):
    x = i * pitch
    ax.add_patch(FancyBboxPatch((x, y0), bw, bh, boxstyle="round,pad=0.05",
                                facecolor=col, edgecolor=col, linewidth=1))
    ax.text(x + bw / 2, y0 + bh / 2, name, ha="center", va="center", fontsize=7.5,
            fontweight="bold", color="white", linespacing=1.1)
    ax.text(x + bw / 2, y0 - 0.2, param, ha="center", va="top", fontsize=7.5,
            color=COLORS["ink"], linespacing=1.2)
    if i < n - 1:
        ax.add_patch(FancyArrowPatch((x + bw + 0.03, y0 + bh / 2), (x + pitch - 0.03, y0 + bh / 2),
                                     arrowstyle="-|>", mutation_scale=11,
                                     color=COLORS["grey"], linewidth=1.3))

# segment brackets above the boxes
for name, a, b in groups:
    xa, xb = a * pitch - 0.1, b * pitch + bw + 0.1
    ax.plot([xa, xa, xb, xb], [1.75, 1.95, 1.95, 1.75], color=COLORS["grey"], lw=1)
    ax.text((xa + xb) / 2, 2.05, name, ha="center", va="bottom", fontsize=8.5,
            fontweight="bold", color=COLORS["grey"])

# link type labels on the arrows that cross a segment boundary
ax.text(2 * pitch + bw + gap / 2, y0 + bh + 0.08, "RF link\n(S/X-band)", ha="center",
        va="bottom", fontsize=7, color=COLORS["grey"], style="italic")
ax.text(5 * pitch + bw + gap / 2, y0 + bh + 0.08, "terrestrial\nnetwork", ha="center",
        va="bottom", fontsize=7, color=COLORS["grey"], style="italic")

ax.text((n * pitch - gap) / 2, -1.6,
        "Sustainability condition: daily downlink capacity ≥ daily data generated,\n"
        "otherwise on-board storage fills.",
        ha="center", va="top", fontsize=8, style="italic", color=COLORS["accent_2"])

save(fig, Path(__file__).stem)
