"""Battery DoD vs cycle life for Li-ion families — design-point trade for LEO."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, SERIES, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

# Approximate cycle life vs DoD: cycles = A * (DoD/100)^(-k)  (illustrative fits)
DoD = np.linspace(5, 100, 200)
A_curves = {
    "Heritage (LiCoO2)":   (1500, 1.3),
    "Aerospace (NCA/NMC)": (4500, 1.5),
    "LFP (high-life)":     (12000, 1.5),
}
for i, (name, (A, k)) in enumerate(A_curves.items()):
    cycles = A * (DoD / 100) ** (-k)
    ax.semilogy(DoD, cycles, lw=2.0, color=SERIES[i], label=name)

# LEO: ~15 eclipses/day → ~5500 cycles per year
cyc_yr = 5500
ax.axhline(cyc_yr, color=COLORS["grey"], lw=1.0, ls=":")
ax.text(95, cyc_yr * 0.85, "1 year LEO (~5500 cycles)",
        fontsize=8.5, color=COLORS["grey"], ha="right", va="top", clip_on=True)
ax.axhline(cyc_yr * 5, color=COLORS["accent_2"], lw=1.4, ls="--",
           label="5-year LEO (27 500 cycles)")
ax.axhline(cyc_yr * 10, color=COLORS["accent_4"], lw=1.4, ls="--",
           label="10-year LEO (55 000 cycles)")

# Design point: NCA/NMC at 30 % DoD meets the 5-year line
A0, k0 = A_curves["Aerospace (NCA/NMC)"]
ypoint = A0 * (30 / 100) ** (-k0)
ax.plot(30, ypoint, "o", color=COLORS["accent_2"], ms=9, zorder=5)
ax.annotate(f"Typical 5-yr LEO design:\nDoD = 30 % → {ypoint/1000:.0f} k cycles",
            xy=(30, ypoint), xytext=(40, ypoint * 5.5),
            fontsize=9, color=COLORS["accent_2"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["accent_2"], lw=1.2),
            annotation_clip=True)

ax.set_xlabel("Depth of discharge (% of full capacity)")
ax.set_ylabel("Cycles to end of life (knee)")
ax.set_title("Battery cycle life vs DoD — Li-ion families (illustrative)")
ax.set_xlim(5, 100)
ax.set_ylim(500, 1e6)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="lower left", fontsize=9)

save(fig, Path(__file__).stem)
