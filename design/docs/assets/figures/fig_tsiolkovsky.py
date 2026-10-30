"""Tsiolkovsky rocket equation — Δv vs mass ratio for several Isp (log Δv axis)."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, SERIES, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

g0 = 9.80665
isps = [(70, "cold gas"), (220, "monopropellant"), (320, "bipropellant"),
        (1500, "Hall thruster"), (2200, "ion thruster")]
mr = np.linspace(1.005, 4.0, 400)

for i, (isp, kind) in enumerate(isps):
    ax.plot(mr, isp * g0 * np.log(mr), color=SERIES[i], lw=2.0, label=f"Isp = {isp} s ({kind})")

levels = [(100, "CubeSat deorbit / station-keeping (~100 m/s)", 2.3, "center"),
          (300, "constellation phasing (~300 m/s)", 2.3, "center"),
          (1500, "LEO → GTO injection (~1.5 km/s)", 3.97, "right"),
          (3900, "LEO → GEO Hohmann (~3.9 km/s)", 2.3, "center")]
for v, label, x, ha in levels:
    ax.axhline(v, color=COLORS["grey"], lw=0.9, ls=":")
    ax.text(x, v * 1.08, label, fontsize=8, color=COLORS["grey"], ha=ha, va="bottom",
            clip_on=True)

ax.set_xlabel("Mass ratio m₀ / m_f")
ax.set_ylabel("Δv (m/s, log)")
ax.set_yscale("log")
ax.set_ylim(20, 40000)
ax.set_xlim(1.0, 4.0)
ax.set_title("Tsiolkovsky — Δv vs mass ratio for selected Isp")
ax.legend(loc="lower right", fontsize=8.5)
ax.grid(True, which="both", alpha=0.3)

save(fig, Path(__file__).stem)
