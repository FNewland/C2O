"""GSD vs aperture diameter for visible imagers — diffraction limit + pixel limit."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, SERIES, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

lam = 550e-9
h_km = [400, 500, 700, 1000]
D = np.linspace(0.05, 0.50, 200)

for i, h in enumerate(h_km):
    gsd_diff = 1.22 * lam * (h * 1000) / D
    ax.plot(D * 100, gsd_diff, lw=2.0, color=SERIES[i], label=f"diffraction-limited @ {h} km")

p = 6e-6
fD = 5
gsd_pixel = p * 500_000 / (fD * D)
ax.plot(D * 100, gsd_pixel, lw=1.8, color=COLORS["ink"], ls="--",
        label="pixel-limited @ 500 km (p = 6 µm, f/D = 5)")

ax.axhline(5.0, color=COLORS["grey"], lw=0.9, ls=":")
ax.text(48, 5.4, "GSD = 5 m", fontsize=8.5, color=COLORS["grey"], ha="right", clip_on=True)
ax.axhline(1.0, color=COLORS["grey"], lw=0.9, ls=":")
ax.text(6, 0.9, "GSD = 1 m", fontsize=8.5, color=COLORS["grey"], ha="left",
        va="top", clip_on=True)

ax.set_xlabel("Aperture diameter (cm)")
ax.set_ylabel("GSD (m)")
ax.set_yscale("log")
ax.set_title("GSD vs aperture — diffraction and pixel limits  (visible band, λ = 550 nm)")
ax.set_xlim(5, 50)
ax.set_ylim(0.2, 30)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="upper right", fontsize=8.5)
save(fig, Path(__file__).stem)
