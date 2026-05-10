"""Reaction-wheel momentum capacity vs disturbance accumulation."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))

# (a) Momentum accumulation vs orbit number
ax = axes[0]
T_orbit = 5800   # s, ~96 min
N = np.arange(0, 10)
# Disturbance torque (per unit area at LEO 500 km, drag-dominated)
T_drag_typical = 1.0e-5   # N·m
H_per_orbit = T_drag_typical * T_orbit  # N·m·s per orbit
H = N * H_per_orbit
H_avg = H * 0.7   # secular fraction averaged over orbit

ax.plot(N, H_avg * 1000, "o-", color=COLORS["garnet"], lw=2.0, ms=7,
        label="Drag-dominated LEO accumulation")
ax.fill_between(N, H_avg*1000*0.5, H_avg*1000*1.5, alpha=0.15, color=COLORS["garnet"])

# Wheel capacities
ax.axhline(50, color=COLORS["blue"], lw=1.4, ls="--",
           label="Small RW (50 mN·m·s)")
ax.axhline(200, color=COLORS["green"], lw=1.4, ls="--",
           label="Medium RW (200 mN·m·s)")

ax.set_xlabel("Orbits since last desat")
ax.set_ylabel("Accumulated momentum (mN·m·s)")
ax.set_title("Momentum accumulation — typical LEO drag")
ax.grid(True, alpha=0.3)
ax.legend(loc="upper left", frameon=False, fontsize=9)
ax.set_xlim(0, 10)

# (b) Disturbance torque budget
ax = axes[1]
disturbances = [
    ("Aerodynamic drag (300 km)",   3.0e-5),
    ("Aerodynamic drag (500 km)",   1.0e-5),
    ("Aerodynamic drag (700 km)",   3.0e-6),
    ("Gravity gradient (500 km)",   1.5e-6),
    ("Solar radiation pressure",    5.0e-7),
    ("Magnetic dipole residual",    8.0e-7),
]
labels = [d[0] for d in disturbances]
values = [d[1]*1e6 for d in disturbances]   # in µN·m
y = np.arange(len(labels))
ax.barh(y, values, color=SERIES[:len(labels)], alpha=0.85)
for i, v in enumerate(values):
    ax.text(v+1, i, f"{v:.2f} µN·m", va="center", fontsize=8.5)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("Typical disturbance torque (µN·m)")
ax.set_xscale("log")
ax.set_xlim(0.1, 100)
ax.set_title("Disturbance torque sources — order of magnitude")
ax.grid(True, axis="x", alpha=0.3)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_rw_momentum.png")
print("OK rw momentum")
