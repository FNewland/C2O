"""J2 nodal regression rate vs inclination for several altitudes — SSO condition."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()
mu = 398_600.4418
RE = 6378.137
J2 = 1.082_626_68e-3

incs_deg = np.linspace(0, 180, 361)
incs = np.deg2rad(incs_deg)
altitudes = [300, 500, 700, 900, 1200]

fig, ax = plt.subplots(figsize=(8.6, 5.2))
for h in altitudes:
    a = RE + h
    n = np.sqrt(mu / a**3)
    raan_dot = -1.5 * n * J2 * (RE / a) ** 2 * np.cos(incs)
    ax.plot(incs_deg, np.rad2deg(raan_dot) * 86400, lw=1.8, label=f"{h} km")

SSO = 0.9856
ax.axhline(SSO, color=COLORS["accent_2"], lw=2.0, ls="--",
           label=f"SSO target Ω̇ = +{SSO} °/day")
ax.axhline(0, color=COLORS["grey_light"], lw=0.8)
ax.set_xlim(0, 180)
ax.set_ylim(-9, 9)
ax.set_xlabel("Inclination (deg)")
ax.set_ylabel("Nodal regression rate Ω̇ (°/day)")
ax.set_title("J₂ nodal regression vs inclination — Sun-synchronous condition shown")
ax.legend(loc="lower right", fontsize=9, ncol=2)

a = RE + 700
n = np.sqrt(mu / a**3)
target = np.deg2rad(SSO) / 86400 / (-1.5 * n * J2 * (RE / a) ** 2)
i_sso = np.rad2deg(np.arccos(target))
ax.plot(i_sso, SSO, "o", color=COLORS["accent_2"], ms=8)
ax.annotate(f"i = {i_sso:.1f}° at 700 km",
            (i_sso, SSO), xytext=(i_sso - 35, 4.5),
            fontsize=9, color=COLORS["accent_2"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["accent_2"], lw=1.0),
            annotation_clip=True)

save(fig, Path(__file__).stem)
