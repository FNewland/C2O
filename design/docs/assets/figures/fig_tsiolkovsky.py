"""Tsiolkovsky rocket equation — Δv vs mass ratio for several Isp."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.0, 5.0))

g0 = 9.80665
isps = [70, 220, 320, 1500, 2200]   # cold gas, mono, bipro, Hall, ion
mr = np.linspace(1.0, 4.0, 200)

for i, isp in enumerate(isps):
    ve = isp * g0
    dv = ve * np.log(mr)
    ax.plot(mr, dv,
            color=SERIES[i % len(SERIES)],
            lw=2.0, label=f"Isp = {isp} s")

ax.set_xlabel("Mass ratio m₀ / m_f")
ax.set_ylabel("Δv (m/s)")
ax.set_title("Tsiolkovsky — Δv vs Mass Ratio for Selected Isp")
ax.legend(loc="upper left", frameon=False, fontsize=9)
ax.grid(True, alpha=0.4)

# Annotate typical Δv budgets
levels = [
    (100,    "Station-keeping (LEO sat·yr)"),
    (300,    "Constellation phasing"),
    (1500,   "LEO → GTO injection"),
    (3900,   "LEO → GEO Hohmann"),
]
for v, label in levels:
    ax.axhline(v, color=COLORS["polar"], lw=0.6)
    ax.text(3.95, v+30, label, fontsize=8, color=COLORS["warm_grey"], ha="right")

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_tsiolkovsky.png")
print("OK tsiolkovsky")
