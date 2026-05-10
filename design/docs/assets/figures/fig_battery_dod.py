"""Battery DoD vs cycle life for Li-ion — design-point trade for LEO."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

# Approximate cycle-life vs DoD (Li-ion, generic)
# Power-law fit: cycles = A * DoD^(-k), where k ~= 1.6 for typical Li-ion
DoD = np.linspace(5, 100, 200)
A_curves = {
    "Heritage (LiCoO2)":  (1500, 0.85),
    "Aerospace (NCA/NMC)":(3500, 0.80),
    "LFP (high-life)":    (8000, 0.75),
}

for i, (name, (A, k)) in enumerate(A_curves.items()):
    cycles = A * (DoD/100)**(-k)
    ax.semilogy(DoD, cycles, lw=2.0, color=SERIES[i], label=name)

# LEO requirement: 5500 cycles per year for ~96-min orbit
ax.axhline(5500, color=COLORS["garnet_2"], lw=1.0, ls=":")
ax.text(95, 6500, "1 year LEO\n(~5500 cycles)",
        fontsize=8.5, color=COLORS["garnet_2"], ha="right")
ax.axhline(5500*5, color=COLORS["garnet"], lw=1.4, ls="--",
           label="5-year LEO design point")
ax.axhline(5500*10, color=COLORS["green"], lw=1.4, ls="--",
           label="10-year LEO design point")

ax.set_xlabel("Depth of Discharge (% of full capacity)")
ax.set_ylabel("Cycles to end-of-life (knee)")
ax.set_title("Battery cycle life vs DoD — Li-ion families")
ax.set_xlim(5, 100)
ax.set_ylim(100, 1e6)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="lower left", frameon=False, fontsize=9)

# Annotate typical CubeSat design point
A0, k0 = A_curves["Aerospace (NCA/NMC)"]
ypoint = A0 * (30/100)**(-k0)
ax.plot(30, ypoint, "o", color=COLORS["garnet"], ms=9)
ax.annotate(f"Typical 5-yr LEO\ndesign: DoD = 30 %",
            xy=(30, ypoint), xytext=(50, ypoint*4),
            fontsize=9, color=COLORS["garnet"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["garnet"], lw=1.2))
ax.set_ylim(100, 1e6)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_battery_dod.png")
print("OK battery DoD")
