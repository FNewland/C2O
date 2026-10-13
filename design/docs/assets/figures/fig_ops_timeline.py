"""Gantt-style operations timeline for the first year of a CubeSat mission
(Chapter 17 §17.4): LEOP (72 h), commissioning (weeks 1–4), early operations
(to month 3), nominal operations thereafter; staffing bands 24/7 → 16/7 → 8/5."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from oer_style import apply_style, COLORS, save

apply_style()
fig, (ax, axs) = plt.subplots(2, 1, figsize=(7.2, 4.2), sharex=True,
                              gridspec_kw={"height_ratios": [3.3, 1.6], "hspace": 0.12})

WK = 52
leop_end = 3 / 7          # 72 h in weeks
comm_end = 4
early_end = 13            # ≈ month 3
# ---- activity bars (broken_barh)
phases = [
    ("LEOP", [(0, leop_end)], COLORS["accent_2"]),
    ("Commissioning", [(leop_end, comm_end - leop_end)], COLORS["accent_4"]),
    ("Early operations", [(comm_end, early_end - comm_end)], COLORS["accent_5"]),
    ("Nominal operations", [(early_end, WK - early_end)], COLORS["accent"]),
]
for i, (name, spans, c) in enumerate(phases):
    y = len(phases) - 1 - i
    ax.broken_barh(spans, (y - 0.35, 0.7), facecolors=c, edgecolors="none")
ax.set_yticks(range(len(phases)))
ax.set_yticklabels([p[0] for p in reversed(phases)], fontsize=9)
ax.set_ylim(-0.6, len(phases) - 0.4)
ax.grid(axis="y", visible=False)

# annotations on the bars
ax.annotate("72 h: separation, beacon,\ndeployments, health check", xy=(leop_end, 3), xytext=(2.2, 3.0),
            fontsize=8, va="center", ha="left",
            arrowprops=dict(arrowstyle="-|>", color=COLORS["ink"], lw=0.8))
ax.text(comm_end + 0.6, 2, "weeks 1–4: subsystem checkout, AOCS calibration, payload first light",
        fontsize=8, va="center", ha="left")
ax.text(early_end + 0.6, 1, "to month 3: performance characterisation, procedure refinement",
        fontsize=8, va="center", ha="left")
ax.text(early_end + (WK - early_end) / 2, 0, "routine science or service; orbit maintenance; automated passes",
        fontsize=8, va="center", ha="center", color="white")

# ---- staffing bands
bands = [("24/7  (3 shifts)", 0, leop_end, 3, COLORS["accent_2"]),
         ("16/7  (2 shifts)", leop_end, comm_end, 2, COLORS["accent_4"]),
         ("8/5  (1 shift, or automated)", comm_end, WK, 1, COLORS["accent"])]
x = np.array([0, leop_end, leop_end, comm_end, comm_end, WK])
y = np.array([3, 3, 2, 2, 1, 1])
axs.fill_between(x, 0, y, step=None, color=COLORS["band"], edgecolor="none")
axs.plot(x, y, color=COLORS["ink"], lw=1.5)
for name, x0, x1, lvl, c in bands:
    axs.text(x1 + 0.6 if lvl > 1 else early_end + 0.6, lvl + 0.15, name, fontsize=8.5, va="bottom",
             ha="left", color=c, fontweight="bold")
axs.set_ylim(0, 3.7)
axs.set_yticks([1, 2, 3])
axs.set_yticklabels(["8/5", "16/7", "24/7"], fontsize=9)
axs.set_ylabel("Staffing", fontsize=9)
axs.grid(axis="y", visible=False)

# ---- time axis: weeks with month marks
axs.set_xlim(0, WK)
axs.set_xticks([0, 4, 8, 13, 17, 22, 26, 30, 35, 39, 43, 48, 52])
axs.set_xticklabels(["0", "4", "8", "13", "17", "22", "26", "30", "35", "39", "43", "48", "52"])
axs.set_xlabel("Weeks after launch")
for m, wk in [("month 1", 4.35), ("month 3", 13), ("month 6", 26), ("month 12", 52)]:
    for a in (ax, axs):
        a.axvline(wk, color=COLORS["grey_light"], lw=0.8, ls="--", zorder=0)
    ax.text(wk, len(phases) - 0.45, m, fontsize=8, ha="center", va="bottom", color=COLORS["grey"])

save(fig, Path(__file__).stem)
