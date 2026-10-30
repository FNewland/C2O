"""Orbital lifetime vs altitude (drag-decay rule of thumb) with FCC 5-yr / IADC 25-yr lines."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, SERIES, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 4.8))

# Very rough rule of thumb: tau ≈ (h − 200)/30 × (m/A)/50 years — illustrative only.
h = np.linspace(200, 1000, 400)
mA_values = [25, 50, 100, 200]

ax.axhspan(0.1, 5, color=COLORS["accent_3"], alpha=0.10, lw=0)
ax.axhspan(5, 25, color=COLORS["accent_5"], alpha=0.10, lw=0)
ax.axhspan(25, 1000, color=COLORS["accent_2"], alpha=0.07, lw=0)

for i, mA in enumerate(mA_values):
    tau = np.clip((h - 200) / 30 * (mA / 50), 0.05, None)
    ax.semilogy(h, tau, lw=2.0, color=SERIES[i], label=f"m/A = {mA} kg/m²")

ax.axhline(5, color=COLORS["accent_3"], lw=1.4, ls="--", label="FCC 5-year rule")
ax.axhline(25, color=COLORS["accent_2"], lw=1.4, ls="--", label="IADC 25-year rule")

ax.text(985, 2.3, "decays within 5 yr — compliant everywhere", fontsize=8.5,
        color=COLORS["accent_3"], ha="right", va="center", fontweight="bold", clip_on=True)
ax.text(985, 7.5, "5–25 yr — IADC-compliant, not FCC", fontsize=8.5,
        color=COLORS["accent_5"], ha="right", va="center", fontweight="bold", clip_on=True)
ax.text(215, 300, "> 25 yr — non-compliant without active de-orbit",
        fontsize=8.5, color=COLORS["accent_2"], ha="left", va="center",
        fontweight="bold", clip_on=True)

ax.set_xlabel("Initial circular altitude (km)")
ax.set_ylabel("Natural orbital lifetime (years, log)")
ax.set_title("Approximate orbital lifetime vs altitude (drag-decay rule of thumb — illustrative)")
ax.set_xlim(200, 1000)
ax.set_ylim(0.1, 1000)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="lower right", fontsize=8.5, ncol=2)

save(fig, Path(__file__).stem)
