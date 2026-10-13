"""Hohmann transfer schematic (400 km LEO → GEO) with ΔV annotations."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()

MU = 398_600.4418
RE = 6378.137
r1 = RE + 400
r2 = RE + 35_786

a_t = (r1 + r2) / 2
v1 = np.sqrt(MU / r1)
v2 = np.sqrt(MU / r2)
vp = np.sqrt(MU * (2 / r1 - 1 / a_t))
va = np.sqrt(MU * (2 / r2 - 1 / a_t))
dV1 = vp - v1
dV2 = v2 - va
dV_total = dV1 + dV2
t_transfer_h = np.pi * np.sqrt(a_t**3 / MU) / 3600

theta = np.linspace(0, 2 * np.pi, 720)
x1, y1 = r1 * np.cos(theta), r1 * np.sin(theta)
x2, y2 = r2 * np.cos(theta), r2 * np.sin(theta)
e_t = (r2 - r1) / (r2 + r1)
nu = np.linspace(0, np.pi, 360)
r_t = a_t * (1 - e_t**2) / (1 + e_t * np.cos(nu))
xt, yt = r_t * np.cos(nu), r_t * np.sin(nu)

fig, ax = plt.subplots(figsize=(7.0, 7.4))
ax.add_patch(plt.Circle((0, 0), RE, color=COLORS["accent"], alpha=0.3, zorder=1))
ax.plot([0], [0], "o", color=COLORS["ink"], ms=3)

ax.plot(x1, y1, color=COLORS["accent_3"], lw=1.6, label=f"Initial circular orbit ({r1-RE:.0f} km altitude)")
ax.plot(x2, y2, color=COLORS["accent"], lw=1.6, label=f"Final circular orbit (GEO, {r2-RE:.0f} km)")
ax.plot(xt, yt, color=COLORS["accent_2"], lw=2.0, label="Hohmann transfer ellipse (half)")

ax.plot([r1], [0], "o", color=COLORS["accent_2"], ms=8, zorder=5)
ax.annotate(f"ΔV₁ = {dV1*1000:.0f} m/s (perigee burn)",
            (r1, 0), xytext=(r2 * 0.30, r2 * 0.32), ha="center",
            fontsize=10, color=COLORS["accent_2"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["accent_2"], lw=1.2),
            annotation_clip=True)
ax.plot([-r2], [0], "o", color=COLORS["accent_2"], ms=8, zorder=5)
ax.annotate(f"ΔV₂ = {dV2*1000:.0f} m/s (apogee burn)",
            (-r2, 0), xytext=(-r2 * 0.95, -r2 * 0.30),
            fontsize=10, color=COLORS["accent_2"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["accent_2"], lw=1.2),
            annotation_clip=True)

ax.text(0.98, 0.02,
        f"Total ΔV = {dV_total*1000:.0f} m/s\nTransfer time = {t_transfer_h:.2f} h",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=10, color=COLORS["ink"],
        bbox=dict(boxstyle="round,pad=0.4", fc=COLORS["band"], ec="none"))

R_max = r2 * 1.12
ax.set_xlim(-R_max, R_max)
ax.set_ylim(-R_max, R_max)
ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("Hohmann transfer — LEO (400 km) → GEO")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=1, fontsize=9)

save(fig, Path(__file__).stem)
