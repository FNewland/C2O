"""Total ionising dose versus altitude for 1, 2 and 4 mm aluminium shielding (Ch 7 §7.6).

Model (illustrative, not a radiation analysis):
  * The 2 mm Al curve is a quadratic log-log fit through the mid-points of
    the §7.6.1 table LEO/MEO rows (≈ 3 krad/yr at 410 km, 7 at 500 km, 15 at
    800 km, 70 at 2000 km) plus ≈ 1 krad/yr at 300 km, which themselves
    summarise AP-8 trapped-proton / SAA dose behind 2 mm Al (ECSS-E-ST-10-04C;
    SMAD Ch. 8.1). Inclination differences (51.6° vs polar) are within the
    width of the table bands and are not resolved here.
  * Shielding dependence: proton-dominated LEO dose scales roughly as
    D(t) ∝ t^-1.3 for 1–4 mm Al (AP-8 / SHIELDOSE-2 depth-dose trend), giving
    ≈ 2.5× the 2 mm dose at 1 mm and ≈ 0.4× at 4 mm.
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()

# anchor points (altitude km, krad/yr behind 2 mm Al, polar/SSO)
h_anchor = np.array([300, 410, 500, 800, 2000])
d_anchor = np.array([1.0, 3.2, 7.0, 15.0, 70.0])
coef = np.polyfit(np.log(h_anchor), np.log(d_anchor), 2)
h = np.linspace(300, 2200, 400)
d2 = np.exp(np.polyval(coef, np.log(h)))


def dose(t_mm):
    return d2 * (2.0 / t_mm) ** 1.3


fig, ax = plt.subplots(figsize=(7.0, 4.4))
for t, c, ls in [(1, COLORS["accent_2"], "-"), (2, COLORS["accent"], "-"),
                 (4, COLORS["accent_3"], "-")]:
    ax.plot(h, dose(t), color=c, ls=ls, label=f"{t} mm Al shielding")

# Table 7.6.1 bands behind 2 mm Al
rows = [(410, 2, 5, "ISS"), (500, 5, 10, "SSO 500"), (800, 10, 20, "SSO 800"),
        (2000, 50, 100, "MEO 2000")]
for hh, lo, hi, lab in rows:
    ax.plot([hh, hh], [lo, hi], color=COLORS["ink"], lw=4, alpha=0.35, solid_capstyle="butt")
ax.plot([], [], color=COLORS["ink"], lw=4, alpha=0.35, label="§7.6.1 table range (2 mm Al)")

# COTS threshold
ax.axvline(600, color=COLORS["grey"], ls=":", lw=1)
ax.text(610, 0.55, "≈ 600 km: COTS with modest\nshielding below, radiation a\ndesign driver above",
        fontsize=7.5, color=COLORS["grey"], va="bottom", ha="left", style="italic")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(300, 2200)
ax.set_ylim(0.4, 300)
ax.set_xticks([300, 400, 500, 600, 800, 1000, 1500, 2000])
ax.set_xticklabels(["300", "400", "500", "600", "800", "1000", "1500", "2000"])
ax.set_yticks([1, 10, 100])
ax.set_yticklabels(["1", "10", "100"])
ax.set_xlabel("Orbit altitude (km)")
ax.set_ylabel("Total ionising dose (krad(Si) / year)")
ax.legend(loc="upper left", fontsize=8)
ax.grid(True, which="both")
ax.set_title("Trapped-proton dose versus altitude and shielding (LEO–MEO)", pad=8)
save(fig, Path(__file__).stem)
