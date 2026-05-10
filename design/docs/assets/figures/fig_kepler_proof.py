"""Kepler's third law verification — period vs semi-major axis."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

mu = 398_600.4418   # km^3/s^2 Earth
RE = 6378.137

# Compute period for circular orbits across altitude range
h = np.linspace(0, 36000, 600)
a = RE + h
T = 2 * np.pi * np.sqrt(a**3 / mu) / 60   # min

ax.plot(h, T, lw=2.6, color=COLORS["garnet"], label="T = 2π√(a³/μ)")

# Reference points
points = [
    ("ISS-class (400 km)", 400, 92.7),
    ("EOSAT-1 (450 km)",   450, 93.6),
    ("Sentinel-2 (786 km)",786, 100.4),
    ("Iridium (780 km)",   780, 100.3),
    ("GPS (20 184 km)",    20184, 718),
    ("GEO (35 786 km)",    35786, 1436),
]
for name, alt, T_known in points:
    ax.plot(alt, T_known, "o", ms=8, color=COLORS["charcoal"])
    ax.annotate(name, (alt, T_known),
                xytext=(8, 4), textcoords="offset points",
                fontsize=8.5, color=COLORS["charcoal"])

ax.set_xlabel("Altitude (km)")
ax.set_ylabel("Orbital period (min)")
ax.set_title("Kepler's Third Law — verified against known orbits")
ax.grid(True, alpha=0.3)
ax.set_yscale("log")
ax.legend(loc="lower right", frameon=False, fontsize=10)
ax.set_xlim(0, 36000)
ax.set_ylim(80, 2000)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_kepler_proof.png")
print("OK kepler proof")
