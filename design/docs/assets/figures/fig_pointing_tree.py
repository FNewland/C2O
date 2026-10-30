"""Pointing-error budget tree — root-sum-square waterfall (millidegrees)."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(9.0, 5.0))

# (label, 1σ contribution in millidegrees, group)
rows = [
    ("Star tracker NEA",                   5.0, "knowledge"),
    ("Gyro bias residual",                12.0, "knowledge"),
    ("Time-tag uncertainty",               3.0, "knowledge"),
    ("RW micro-vibration",                20.0, "control"),
    ("Disturbance torque (gravity grad.)", 8.0, "control"),
    ("Disturbance torque (drag)",          5.0, "control"),
    ("Thruster minimum impulse",          10.0, "control"),
    ("Mounting alignment",                30.0, "alignment"),
    ("Thermal distortion",                22.0, "alignment"),
    ("Structural flexure",                12.0, "alignment"),
]
groups = ["knowledge", "control", "alignment"]
group_color = {"knowledge": COLORS["accent"], "control": COLORS["accent_3"],
               "alignment": COLORS["accent_2"]}

group_rss = {g: float(np.sqrt(sum(v**2 for _, v, gg in rows if gg == g))) for g in groups}
total_rss = float(np.sqrt(sum(v**2 for v in group_rss.values())))
required = 60.0   # m°, allocation

y_pos = list(range(len(rows), 0, -1))
values = [r[1] for r in rows]
ax.barh(y_pos, values, color=[group_color[r[2]] for r in rows], alpha=0.9, height=0.7)
for y, v in zip(y_pos, values):
    ax.text(v + 0.8, y, f"{v:.1f} m°", va="center", fontsize=8.5, color=COLORS["ink"])

ax.set_yticks(y_pos)
ax.set_yticklabels([r[0] for r in rows], fontsize=9)
ax.set_xlabel("Contribution (1σ, millidegrees)")
ax.set_title(f"Pointing error budget — total RSS = {total_rss:.1f} m°  ·  allocation ≤ {required:.0f} m°")
ax.axvline(required, color=COLORS["accent_4"], ls="--", lw=1.4)
ax.text(required + 1, len(rows) + 0.45, f"Allocation {required:.0f} m°",
        color=COLORS["accent_4"], fontsize=9, fontweight="bold", va="center", clip_on=True)
ax.axvline(total_rss, color=COLORS["ink"], ls=":", lw=1.2)
ax.text(total_rss - 1, 0.35, f"Total RSS {total_rss:.1f} m°", ha="right",
        color=COLORS["ink"], fontsize=9, fontweight="bold", va="center", clip_on=True)

xpos = required + 4
y_anno = {"knowledge": 9.0, "control": 5.5, "alignment": 2.0}
for g in groups:
    ax.text(xpos, y_anno[g], f"{g.title()} group\nRSS = {group_rss[g]:.1f} m°",
            color=group_color[g], fontsize=9, fontweight="bold", va="center",
            bbox=dict(fc="white", ec="none", pad=1), clip_on=True)

ax.set_xlim(0, 95)
ax.set_ylim(0, len(rows) + 0.9)
ax.grid(axis="y", visible=False)
save(fig, Path(__file__).stem)
