"""GSD vs aperture diameter for visible imagers — diffraction limit + pixel limit."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

# GSD diffraction limit: GSD = 1.22 * lambda * h / D
# GSD pixel-limited: GSD = p * h / f, where f = focal length
# For a baseline visible system: lambda = 550 nm, p = 6 micron, f/D = 5
lam = 550e-9      # m
h_km = [400, 500, 700, 1000]
D = np.linspace(0.05, 0.50, 200)   # 5-50 cm aperture

for i, h in enumerate(h_km):
    h_m = h * 1000
    gsd_diffraction = 1.22 * lam * h_m / D
    ax.plot(D * 100, gsd_diffraction,
            lw=2.0, color=SERIES[i],
            label=f"diff-limited @ {h} km")

# Add pixel-limit curve for one altitude (500 km), p=6e-6, f/D=5
p = 6e-6   # 6 micron
fD = 5
h_m = 500_000
focal = fD * D
gsd_pixel = p * h_m / focal
ax.plot(D * 100, gsd_pixel, lw=1.8, color=COLORS["charcoal"], ls="--",
        label=f"pixel-limited @ 500 km (p=6 µm, f/D=5)")

# Mark common targets
ax.axhline(5.0, color=COLORS["garnet_2"], lw=0.8)
ax.text(48, 5.4, "GSD = 5 m", fontsize=8.5, color=COLORS["garnet_2"], ha="right")
ax.axhline(1.0, color=COLORS["garnet_2"], lw=0.8)
ax.text(48, 1.1, "GSD = 1 m", fontsize=8.5, color=COLORS["garnet_2"], ha="right")

ax.set_xlabel("Aperture diameter (cm)")
ax.set_ylabel("GSD (m)")
ax.set_yscale("log")
ax.set_title("GSD vs aperture — diffraction + pixel limits  (visible band, λ = 550 nm)")
ax.set_xlim(5, 50)
ax.set_ylim(0.2, 30)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_gsd.png")
print("OK gsd")
