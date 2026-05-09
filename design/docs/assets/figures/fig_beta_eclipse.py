"""β-angle sweep & eclipse fraction for a 600 km SSO over a year."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()

RE = 6378.137
mu = 398_600.4418

# Two orbits to compare
cases = [
    {"label": "ISS-like (51.6° i, 400 km)", "alt": 400, "i": 51.6},
    {"label": "SSO 10:30 LTAN (98° i, 600 km)", "alt": 600, "i": 98.0},
]

# Sun ecliptic latitude over a year (approx)
days = np.arange(0, 365)
sun_dec = 23.45 * np.sin(2 * np.pi * (days - 80) / 365.25)  # deg

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))

for case in cases:
    a = RE + case["alt"]
    inc = np.deg2rad(case["i"])
    # Approximate β-angle with Sun in equatorial frame, ignoring RAAN drift
    # β = arcsin(sin(δ) cos(i) - cos(δ) sin(i) sin(RAAN_sun - RAAN))
    # For simple sweep across the year, take RAAN_sun - RAAN = 0 then 90 to bound
    beta_min = []
    beta_max = []
    for d in sun_dec:
        d_r = np.deg2rad(d)
        b1 = np.rad2deg(np.arcsin(np.sin(d_r) * np.cos(inc)
                                   - np.cos(d_r) * np.sin(inc) * 0))
        b2 = np.rad2deg(np.arcsin(np.sin(d_r) * np.cos(inc)
                                   - np.cos(d_r) * np.sin(inc) * 1))
        beta_min.append(min(b1, b2))
        beta_max.append(max(b1, b2))
    # Plot envelope
    axes[0].fill_between(days, beta_min, beta_max,
                         color=COLORS["garnet"] if "SSO" in case["label"] else COLORS["blue"],
                         alpha=0.35, label=case["label"])

axes[0].set_xlabel("Day of year")
axes[0].set_ylabel("β-angle envelope (deg)")
axes[0].set_title("β-angle range vs day of year")
axes[0].axhline(0, color=COLORS["polar"], lw=0.6)
axes[0].set_xlim(0, 365)
axes[0].legend(loc="lower left", frameon=False, fontsize=9)

# Eclipse fraction vs β analytically (for circular orbit)
# Φ_eclipse fraction = (1/π) * acos( sqrt(h^2 + 2 R h) / (R + h) / cos(β) )
# (Vallado — for |β| < β*, where β* = asin(R/(R+h)))
beta_grid = np.deg2rad(np.linspace(-90, 90, 900))
for case in cases:
    a = RE + case["alt"]
    R = RE
    h = case["alt"]
    beta_star = np.arcsin(R / (R + h))
    eclipse = np.zeros_like(beta_grid)
    mask = np.abs(beta_grid) < beta_star
    inside = np.sqrt(h**2 + 2*R*h) / (R + h) / np.cos(beta_grid[mask])
    inside = np.clip(inside, -1.0, 1.0)
    eclipse[mask] = np.arccos(inside) / np.pi
    axes[1].plot(np.rad2deg(beta_grid), eclipse * 100,
                 lw=2.0,
                 color=COLORS["garnet"] if "SSO" in case["label"] else COLORS["blue"],
                 label=case["label"])

axes[1].set_xlabel("β-angle (deg)")
axes[1].set_ylabel("Eclipse fraction of orbit (%)")
axes[1].set_title("Eclipse fraction vs β-angle")
axes[1].axhline(0, color=COLORS["polar"], lw=0.6)
axes[1].set_xlim(-90, 90)
axes[1].set_ylim(0, 50)
axes[1].legend(loc="upper right", frameon=False, fontsize=9)

fig.suptitle("β-angle behaviour over a year — and eclipse fraction analytics",
             fontsize=12, color=COLORS["charcoal"], y=1.02)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_beta_eclipse.png")
print("OK beta+eclipse")
