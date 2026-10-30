"""Solar-array sizing nomograph (Ch 9 §9.2 sizing chain).

Left:  P_SA,BOL vs orbit-average load for three eclipse fractions
       (Step 2 with P_sun = P_ecl = P_avg, η_sun = 0.90, η_ecl = 0.786; Step 3 L_d·L_T = 0.862).
Right: A_SA = P_BOL / (η_cell · S · cosθ · f_pack · f_cover) for three Sun angles,
       with the EOSat-3U point 16.0 W BOL → 0.053 m² at θ = 23°.
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, SERIES, save

apply_style()

S = 1361.0
eta_cell = 0.295
f_pack, f_cover = 0.85, 0.97
eta_sun, eta_ecl = 0.90, 0.786
Ld_LT = 0.9269 * 0.930          # 3-yr degradation × 65 °C derating

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
fig.subplots_adjust(wspace=0.32)

# Left: orbit-average load → BOL array power
ax = axes[0]
P_avg = np.linspace(2, 30, 200)
for i, fe in enumerate([0.0, 0.20, 0.38]):
    fs = 1 - fe
    P_eol = P_avg * (1 / eta_sun + fe / (fs * eta_ecl))
    P_bol = P_eol / Ld_LT
    ax.plot(P_avg, P_bol, lw=2.0, color=SERIES[i], label=f"eclipse fraction = {fe:.2f}")
ax.set_xlabel("Orbit-average load (W)")
ax.set_ylabel("Required array power, BOL (W)")
ax.set_title("Load → BOL power (Steps 2–3)", fontsize=11)
ax.set_xlim(2, 30)
ax.set_ylim(0, 70)
ax.legend(loc="upper left", fontsize=8.5)
ax.text(0.98, 0.03, "η_sun = 0.90, η_ecl = 0.79\nL_d·L_T = 0.86 (3 yr, 65 °C)",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=COLORS["grey"])

# Right: BOL power → array area
ax = axes[1]
P_bol = np.linspace(2, 60, 200)
for i, theta in enumerate([0, 23, 45]):
    A = P_bol / (eta_cell * S * np.cos(np.deg2rad(theta)) * f_pack * f_cover)
    ax.plot(P_bol, A, lw=2.0, color=SERIES[i], label=f"Sun angle θ = {theta}°")

P_e, th_e = 16.0, 23
A_e = P_e / (eta_cell * S * np.cos(np.deg2rad(th_e)) * f_pack * f_cover)
ax.plot(P_e, A_e, "o", color=COLORS["accent_2"], ms=9, zorder=5)
ax.annotate(f"EOSat-3U: {P_e:.1f} W BOL\n→ {A_e:.3f} m² at θ = {th_e}°",
            xy=(P_e, A_e), xytext=(26, 0.03), fontsize=9, color=COLORS["accent_2"],
            fontweight="bold", arrowprops=dict(arrowstyle="->", color=COLORS["accent_2"], lw=1.2),
            annotation_clip=True)
ax.set_xlabel("Required array power, BOL (W)")
ax.set_ylabel("Array area A$_{SA}$ (m²)")
ax.set_title("BOL power → array area (Step 4)", fontsize=11)
ax.set_xlim(2, 60)
ax.set_ylim(0, 0.3)
ax.legend(loc="upper left", fontsize=8.5)
ax.text(0.98, 0.97, "η_cell = 0.295, S = 1361 W/m²\nf_pack = 0.85, f_cover = 0.97",
        transform=ax.transAxes, ha="right", va="top", fontsize=8, color=COLORS["grey"])

fig.suptitle("Solar-array sizing nomograph — A = P_BOL / (η_cell · S · cos θ · f_pack · f_cover)",
             fontsize=12, fontweight="bold", y=1.02)
save(fig, Path(__file__).stem)
