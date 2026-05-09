"""Pointing-error budget tree — root-sum-square waterfall."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(9.0, 5.0))

# Budget rows — contributors (1σ, deg)
rows = [
    ("Star tracker NEA",                  0.005,   "knowledge"),
    ("Gyro bias residual",                0.012,   "knowledge"),
    ("Time tag uncertainty",              0.003,   "knowledge"),
    ("RW micro-vibration",                0.020,   "control"),
    ("Disturbance torque (gravity-grad)", 0.008,   "control"),
    ("Disturbance torque (drag)",         0.005,   "control"),
    ("Thruster minimum impulse",          0.010,   "control"),
    ("Mounting alignment",                0.030,   "alignment"),
    ("Thermal distortion",                0.022,   "alignment"),
    ("Structural flexure",                0.012,   "alignment"),
]
groups = ["knowledge", "control", "alignment"]
group_color = {"knowledge": COLORS["blue"],
               "control": COLORS["green"],
               "alignment": COLORS["warm_grey"]}

# RSS within group
group_rss = {}
for g in groups:
    vals = [v for _, v, gg in rows if gg == g]
    group_rss[g] = float(np.sqrt(np.sum(np.array(vals)**2)))

total_rss = float(np.sqrt(sum(v**2 for v in group_rss.values())))
required = 0.06   # deg, allocation for the mission

y_pos = list(range(len(rows), 0, -1))
labels = [r[0] for r in rows]
colors = [group_color[r[2]] for r in rows]
values = [r[1] for r in rows]

bars = ax.barh(y_pos, values, color=colors, alpha=0.9)
for y, v in zip(y_pos, values):
    ax.text(v + 0.001, y, f"{v*1000:.1f} m°", va="center", fontsize=8.5,
            color=COLORS["charcoal"])

ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("Contribution (1σ, deg)")
ax.set_title(f"Pointing Error Budget — total RSS = {total_rss*1000:.1f} m°  ·  required ≤ {required*1000:.0f} m°")
ax.axvline(required, color=COLORS["garnet"], ls="--", lw=1.4)
ax.text(required, len(rows)+0.6, f"  Allocation: {required*1000:.0f} m°",
        color=COLORS["garnet"], fontsize=9, fontweight="bold", va="center")

# Group annotations on right side
xpos = max(values) + 0.025
y_anno = {"knowledge": 9.3, "control": 6.0, "alignment": 2.4}
for g in groups:
    ax.text(xpos, y_anno[g],
            f"{g.title()} group\n RSS = {group_rss[g]*1000:.1f} m°",
            color=group_color[g], fontsize=9, fontweight="bold", va="center")

ax.set_xlim(0, max(values) + 0.06)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_pointing_tree.png")
print("OK pointing tree")
