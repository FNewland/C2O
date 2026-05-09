"""Sample figure: Hohmann transfer schematic with ΔV annotations."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()

MU = 398_600.4418
RE = 6378.137
r1 = RE + 400      # initial circular (ISS-like)
r2 = RE + 35_786   # GEO

a_t = (r1 + r2) / 2
v1 = np.sqrt(MU / r1)
v2 = np.sqrt(MU / r2)
vp = np.sqrt(MU * (2 / r1 - 1 / a_t))
va = np.sqrt(MU * (2 / r2 - 1 / a_t))
dV1 = vp - v1
dV2 = v2 - va
dV_total = dV1 + dV2

theta = np.linspace(0, 2 * np.pi, 720)
# Initial orbit
x1, y1 = r1 * np.cos(theta), r1 * np.sin(theta)
# Final orbit
x2, y2 = r2 * np.cos(theta), r2 * np.sin(theta)
# Transfer ellipse: focus at origin, periapsis at +x, half-pi for sweep
e_t = (r2 - r1) / (r2 + r1)
nu = np.linspace(0, np.pi, 360)
r_t = a_t * (1 - e_t**2) / (1 + e_t * np.cos(nu))
xt, yt = r_t * np.cos(nu), r_t * np.sin(nu)

fig, ax = plt.subplots(figsize=(7.0, 7.0))
# Earth
earth = plt.Circle((0, 0), RE, color=COLORS["blue"], alpha=0.35, zorder=1)
ax.add_patch(earth)
ax.plot([0], [0], "o", color=COLORS["charcoal"], ms=4)

# Orbits
ax.plot(x1, y1, color=COLORS["green"], lw=1.6, label=f"Initial circular (r₁ = {r1-RE:.0f} km alt)")
ax.plot(x2, y2, color=COLORS["blue"], lw=1.6, label=f"Final circular (r₂ = {r2-RE:.0f} km alt)")
ax.plot(xt, yt, color=COLORS["garnet"], lw=2.0, label="Hohmann transfer (half-ellipse)")

# Burn 1 marker
ax.plot([r1], [0], "o", color=COLORS["garnet"], ms=8, zorder=5)
ax.annotate(f"ΔV₁ = {dV1*1000:.0f} m/s",
            (r1, 0), xytext=(r1 * 0.3, r1 * 1.6),
            fontsize=10, color=COLORS["garnet"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["garnet"], lw=1.2))

# Burn 2 marker
ax.plot([-r2], [0], "o", color=COLORS["garnet"], ms=8, zorder=5)
ax.annotate(f"ΔV₂ = {dV2*1000:.0f} m/s",
            (-r2, 0), xytext=(-r2 * 0.95, -r2 * 0.45),
            fontsize=10, color=COLORS["garnet"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["garnet"], lw=1.2))

# Total
ax.text(0.02, 0.02,
        f"Total ΔV = {dV_total*1000:.0f} m/s\nTransfer time = {np.pi*np.sqrt(a_t**3/MU)/3600:.2f} h",
        transform=ax.transAxes, fontsize=10, color=COLORS["charcoal"],
        bbox=dict(boxstyle="round,pad=0.4", fc=COLORS["polar"], ec="none"))

R_max = r2 * 1.15
ax.set_xlim(-R_max, R_max)
ax.set_ylim(-R_max, R_max)
ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("Hohmann Transfer — LEO (400 km) → GEO")
ax.legend(loc="upper right", frameon=False, fontsize=9)

# Hide spines (already off via style)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_hohmann.png")
print("OK hohmann")
