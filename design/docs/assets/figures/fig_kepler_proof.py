"""Kepler's third law verification — period vs altitude for known orbits."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

mu = 398_600.4418
RE = 6378.137

h = np.logspace(np.log10(150), np.log10(50000), 600)
a = RE + h
T = 2 * np.pi * np.sqrt(a**3 / mu) / 60

ax.plot(h, T, lw=2.4, color=COLORS["accent"], label="T = 2π√(a³/μ)")

points = [
    ("ISS (400 km)",         400,   92.7, (8, -12)),
    ("Sentinel-2 (786 km)",  786,  100.4, (8, 4)),
    ("GPS (20 184 km)",    20184,  718,   (-8, 6)),
    ("GEO (35 786 km)",    35786, 1436,   (-10, 8)),
]
for name, alt, T_known, off in points:
    ax.plot(alt, T_known, "o", ms=8, color=COLORS["accent_2"], zorder=5)
    ax.annotate(name, (alt, T_known), xytext=off, textcoords="offset points",
                fontsize=8.5, color=COLORS["ink"],
                ha="left" if off[0] > 0 else "right", annotation_clip=True)

ax.set_xlabel("Altitude (km, log)")
ax.set_ylabel("Orbital period (min, log)")
ax.set_title("Kepler's third law — circular-orbit period vs altitude, checked against known orbits")
ax.set_xscale("log")
ax.set_yscale("log")
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="upper left", fontsize=10)
ax.set_xlim(150, 50000)
ax.set_ylim(80, 2000)
save(fig, Path(__file__).stem)
