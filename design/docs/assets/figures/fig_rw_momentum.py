"""Reaction-wheel momentum accumulation vs capacity, and disturbance torques — 3U CubeSat scale."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, SERIES, save

apply_style()
fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), gridspec_kw={"width_ratios": [1, 1.25]})
fig.subplots_adjust(wspace=0.75)

# (a) Momentum accumulation — 500 km SSO, T = 5677 s, total disturbance 1.5 µN m (§10.2)
ax = axes[0]
T_orbit = 5677.0
T_dist = 1.5e-6
orbits = np.linspace(0, 5, 200)
H = T_dist * T_orbit * orbits * 1e3            # mN m s, worst-case secular accumulation
ax.plot(orbits, H, color=COLORS["accent_2"], lw=2.0,
        label=f"Worst-case accumulation, {T_dist*1e6:.1f} µN m")
ax.fill_between(orbits, H * 0.5, H * 1.5, alpha=0.15, color=COLORS["accent_2"],
                label="Dipole uncertainty band (0.5–1.5×)")

for cap, name, color in [(1, "Micro wheel 1 mN m s", COLORS["grey"]),
                         (10, "Small wheel 10 mN m s", COLORS["accent"]),
                         (40, "Medium wheel 40 mN m s", COLORS["accent_3"])]:
    ax.axhline(cap, color=color, lw=1.4, ls="--")
    ax.text(0.08, cap * 1.08, name, fontsize=8.5, color=color, va="bottom", clip_on=True)

ax.set_xlabel("Orbits since last desaturation")
ax.set_ylabel("Accumulated momentum (mN m s, log)")
ax.set_yscale("log")
ax.set_ylim(0.3, 100)
ax.set_xlim(0, 5)
ax.set_title("Momentum accumulation — 3U CubeSat, 500 km")
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="lower right", fontsize=8.5)

# (b) Disturbance torque budget — §10.2 worked example values
ax = axes[1]
disturbances = [
    ("Residual dipole (0.05 A m²)",   1.5e-6),
    ("Aerodynamic drag (solar max)",          2.2e-7),
    ("Gravity gradient (500 km)",             5.1e-8),
    ("Aerodynamic drag (solar min)",          2.6e-8),
    ("Solar radiation pressure",              4.6e-9),
]
labels = [d[0] for d in disturbances]
values = [d[1] * 1e6 for d in disturbances]     # µN m
y = np.arange(len(labels))[::-1]
ax.barh(y, values, color=SERIES[:len(labels)], alpha=0.9, height=0.6)
for yi, v in zip(y, values):
    ax.text(v * 1.2, yi, f"{v:.3g} µN m", va="center", fontsize=8.5, clip_on=True)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("Disturbance torque (µN m, log)")
ax.set_xscale("log")
ax.set_xlim(1e-3, 10)
ax.set_title("Disturbance torques — 3U CubeSat at 500 km")
ax.grid(True, which="both", axis="x", alpha=0.3)
ax.grid(False, axis="y")

save(fig, Path(__file__).stem)
