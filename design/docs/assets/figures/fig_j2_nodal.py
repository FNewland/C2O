"""J2 nodal regression rate vs inclination, contoured by altitude — and SSO condition."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
mu = 398_600.4418
RE = 6378.137
J2 = 1.082_626_68e-3

incs_deg = np.linspace(0, 180, 361)
incs = np.deg2rad(incs_deg)
altitudes = [300, 500, 700, 900, 1200]   # km

fig, ax = plt.subplots(figsize=(8.6, 5.2))

# RAAN dot in deg/day
for h in altitudes:
    a = RE + h
    n = np.sqrt(mu / a**3)             # rad/s
    raan_dot = -1.5 * n * J2 * (RE/a)**2 * np.cos(incs)        # rad/s
    raan_dot_dpd = np.rad2deg(raan_dot) * 86400               # deg/day
    ax.plot(incs_deg, raan_dot_dpd, lw=1.8,
            label=f"{h} km")

# SSO line — Earth around Sun ≈ 0.9856 deg/day
ax.axhline(0.9856, color=COLORS["garnet"], lw=2.0, ls="--",
           label="SSO target Ω̇ ≈ 0.9856 °/day")

ax.axhline(0, color=COLORS["polar"], lw=0.6)
ax.set_xlim(0, 180)
ax.set_ylim(-9, 9)
ax.set_xlabel("Inclination (deg)")
ax.set_ylabel("Nodal regression rate Ω̇ (°/day)")
ax.set_title("J₂ Nodal Regression vs Inclination — Sun-synchronous condition shown")
ax.legend(loc="lower right", frameon=False, fontsize=9, ncol=2)

# Annotate SSO crossing for 700 km
a = RE + 700; n = np.sqrt(mu/a**3)
i_sso = np.rad2deg(np.arccos(0.9856 / 86400 / -np.rad2deg(1) / 1)) if False else None
# Compute analytically
target = np.deg2rad(0.9856)/86400 / (-1.5 * n * J2 * (RE/a)**2)
i_sso = np.rad2deg(np.arccos(target))
ax.plot(i_sso, 0.9856, "o", color=COLORS["garnet"], ms=8)
ax.annotate(f"{i_sso:.1f}° at 700 km",
            (i_sso, 0.9856), xytext=(i_sso-30, 4.5),
            fontsize=9, color=COLORS["garnet"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["garnet"], lw=1.0))

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_j2_nodal.png")
print("OK j2 nodal")
