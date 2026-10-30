"""Pass-elevation profile — illustrative high-latitude S-band pass for a 450 km SSO."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()

t = np.linspace(0, 8.5, 600)
peak = 60.0
duration = 8.5
elev = peak * np.cos(np.pi * (t - duration / 2) / duration)
elev[elev < 0] = 0
mask = elev >= 5.0

fig, ax = plt.subplots(figsize=(8.4, 4.4))
ax.plot(t[mask], elev[mask], lw=2.4, color=COLORS["accent"])
ax.fill_between(t[mask], 0, elev[mask], alpha=0.12, color=COLORS["accent"])

ax.axhline(5, color=COLORS["grey"], lw=0.9, ls=":")
ax.text(4.25, 6.5, "minimum elevation mask 5°", ha="center", va="bottom",
        fontsize=8.5, color=COLORS["grey"], clip_on=True)


def mark(t_val, label, ymax):
    ax.axvline(t_val, color=COLORS["ink"], ls=":", lw=0.9)
    ax.text(t_val, ymax + 3, label, ha="center", va="bottom", fontsize=9,
            color=COLORS["ink"], fontweight="bold",
            bbox=dict(fc="white", ec="none", pad=1.5), clip_on=True)


idx_in = np.where(mask)[0]
t_aos, t_los = t[idx_in[0]], t[idx_in[-1]]
mark(t_aos, "AOS", peak)
mark(duration / 2, "TCA", peak)
mark(t_los, "LOS", peak)

hi = elev > 30
ax.fill_between(t[hi], 0, elev[hi], color=COLORS["accent_3"], alpha=0.25,
                label="≥ 30° elevation: high-rate downlink window")
ax.legend(loc="upper right", fontsize=9)

ax.set_xlabel("Time from AOS (min)")
ax.set_ylabel("Elevation (deg)")
ax.set_xlim(0, 9)
ax.set_ylim(0, peak * 1.25)
ax.set_title("S-band pass geometry — high-latitude station, 450 km SSO (illustrative)")

save(fig, Path(__file__).stem)
