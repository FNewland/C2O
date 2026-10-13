"""Radiative thermal equilibrium — flat-plate orbit-average temperature vs α/ε."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

S0 = 1361
Earth_IR = 230
sigma = 5.67e-8
phi_solar = S0 * 0.25      # orbit/attitude-averaged solar flux on a tumbling plate
phi_ir = Earth_IR * 0.5    # one face sees Earth on average


def T_eq(r):
    return ((r * phi_solar + phi_ir) / sigma) ** 0.25 - 273.15


ae = np.linspace(0.05, 4.0, 500)
ax.plot(ae, T_eq(ae), lw=2.4, color=COLORS["accent_2"], label="Sun + Earth IR (LEO orbit-average)")
T_ecl = (phi_ir / sigma) ** 0.25 - 273.15
ax.axhline(T_ecl, color=COLORS["accent"], lw=1.6, ls="--",
           label=f"Eclipse only (no Sun): {T_ecl:.0f} °C")

ax.axhspan(-40, 60, color=COLORS["band"], alpha=0.9, zorder=0)
ax.text(3.95, 57, "typical electronics operating band (−40 … +60 °C)", fontsize=8.5,
        color=COLORS["grey"], ha="right", va="top", clip_on=True)

# (name, alpha, epsilon, label offset in data units)
surfaces = [
    ("White paint (Z93)",       0.15, 0.92, (0.12, 14),  COLORS["accent"]),
    ("Black paint (Chemglaze)", 0.95, 0.85, (0.12, -12), COLORS["ink"]),
    ("Aluminised Kapton",       0.40, 0.63, (-0.12, 42), COLORS["accent_4"]),
    ("Machined Al 6061",        0.35, 0.10, (-0.10, 10), COLORS["grey"]),
]
for name, a, e, (dx, dy), color in surfaces:
    r = a / e
    ax.plot(r, T_eq(r), "o", color=color, ms=8, zorder=5)
    ax.text(r + dx, T_eq(r) + dy, f"{name}\nα/ε = {a:.2f}/{e:.2f} = {r:.2f}", fontsize=8,
            color=color, fontweight="bold", ha="left" if dx > 0 or r < 1 else "right",
            va="bottom" if dy > 0 else "top", clip_on=True)

ax.set_xlabel("α / ε  (solar absorptance / IR emittance)")
ax.set_ylabel("Equilibrium temperature (°C)")
ax.set_title("Radiative thermal equilibrium — flat plate, LEO orbit-average")
ax.set_xlim(0, 4.0)
ax.set_ylim(-150, 150)
ax.grid(True, alpha=0.3)
ax.legend(loc="lower right", fontsize=9)
ax.text(0.02, 0.02, "Polished Al and MLI outer layers (α/ε ≈ 5–9) lie off-scale to the right.",
        transform=ax.transAxes, fontsize=8, style="italic", color=COLORS["grey"])
save(fig, Path(__file__).stem)
