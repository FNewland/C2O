"""Cost-estimate accuracy (±1σ) versus lifecycle phase: the band narrows as the
estimating method changes from parametric (Phase 0/A) through analogy (A/B) to
bottom-up (B/C/D); review gates MCR/SRR/PDR/CDR on the phase axis (Chapter 16 §16.1.1)."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(7.3, 4.2))

# phase axis: 0 = start of Phase 0, 4 = end of Phase D
x = np.linspace(0, 4, 400)
# upper edge of the ±1σ band (percent): 50 % at MCR → 10 % at CDR, then flat
sigma = np.interp(x, [0.0, 0.5, 1.5, 2.5, 3.2, 4.0], [50, 45, 30, 18, 10, 10])
ax.fill_between(x, -sigma, sigma, color=COLORS["band"], label="± 1σ accuracy band")
ax.plot(x, sigma, color=COLORS["accent"], lw=1.6)
ax.plot(x, -sigma, color=COLORS["accent"], lw=1.6)
ax.axhline(0, color=COLORS["ink"], lw=1.0)
ax.text(3.95, 1.2, "point estimate", ha="right", va="bottom", fontsize=8.5, color=COLORS["ink"])

# method bands (Table §16.1.1): parametric 0/A, analogy A/B, bottom-up B/C/D
methods = [("Parametric\n± 30–50 %", 0.0, 1.3, COLORS["accent_2"]),
           ("Analogy\n± 20–40 %", 0.9, 2.3, COLORS["accent_4"]),
           ("Bottom-up\n± 10–20 %", 1.9, 4.0, COLORS["accent_3"])]
for k, (name, x0, x1, c) in enumerate(methods):
    y = 60 - 7 * k
    ax.plot([x0, x1], [y, y], color=c, lw=4, solid_capstyle="butt")
    ax.text((x0 + x1) / 2, y + 1.5, name.split("\n")[0] + "  " + name.split("\n")[1],
            ha="center", va="bottom", fontsize=8.5, color=c, fontweight="bold")

# phase boundaries and review gates (Chapter 1 Table 1.3)
for xb in [1, 2, 3]:
    ax.axvline(xb, color=COLORS["grey_light"], lw=0.8, ls="--", zorder=0)
for xc, lab in zip([0.5, 1.5, 2.5, 3.5], ["Phase 0/A", "Phase B", "Phase C", "Phase D"]):
    ax.text(xc, -70, lab, ha="center", va="top", fontsize=9)
gates = [(0.55, "MCR"), (1.0, "SRR"), (2.0, "PDR"), (3.0, "CDR")]
for xg, g in gates:
    ax.plot([xg], [-56], marker="v", color=COLORS["ink"], ms=6, clip_on=False)
    ax.text(xg, -59, g, ha="center", va="top", fontsize=8.5, fontweight="bold")

ax.set_xlim(0, 4)
ax.set_ylim(-78, 68)
ax.set_yticks([-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50])
ax.set_yticklabels(["−50", "−40", "−30", "−20", "−10", "0", "+10", "+20", "+30", "+40", "+50"])
ax.set_xticks([])
ax.set_ylabel("Estimate accuracy, ± 1σ (% of estimate)")
ax.set_xlabel("Lifecycle phase (design maturity)", labelpad=8)
ax.grid(axis="x", visible=False)
ax.spines["bottom"].set_visible(False)
ax.text(0.75, 12, "± 1σ accuracy band", fontsize=8.5, color=COLORS["accent"], va="center", style="italic")

save(fig, Path(__file__).stem)
