"""Orbital lifetime vs altitude (drag-decay rule of thumb), with FCC 5-yr / IADC 25-yr lines."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 4.8))

# Rule of thumb: tau ~ (h - 200)/30 * (m/A)/50 [years]
# This is a *very* rough approximation; treat as illustrative.
h = np.linspace(200, 1000, 200)
mA_values = [25, 50, 100, 200]   # ballistic coefficients (kg/m^2)

for i, mA in enumerate(mA_values):
    tau = (h - 200) / 30 * (mA / 50)
    tau = np.clip(tau, 0, None)
    ax.semilogy(h, np.maximum(tau, 0.05),
                lw=2.0,
                color=SERIES[i],
                label=f"m/A = {mA} kg/m²")

ax.axhline(5,  color=COLORS["garnet"],   lw=1.4, ls="--", label="FCC 5-year rule")
ax.axhline(25, color=COLORS["green"],    lw=1.4, ls="--", label="IADC 25-year rule")

ax.set_xlabel("Initial circular altitude (km)")
ax.set_ylabel("Natural orbital lifetime (years, log)")
ax.set_title("Approximate orbital lifetime vs altitude\n(drag-decay rule of thumb — illustrative)")
ax.set_xlim(200, 1000)
ax.set_ylim(0.1, 1000)
ax.grid(True, which="both", alpha=0.3)
ax.legend(loc="lower right", frameon=False, fontsize=9)

ax.text(880, 30, "compliant\nzone", fontsize=8.5,
        color=COLORS["green"], ha="center", fontweight="bold")
ax.text(880, 0.4, "decay\nfast enough\n— OK",
        fontsize=8.5, color=COLORS["garnet"], ha="center", fontweight="bold")

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_orbital_lifetime.png")
print("OK orbital lifetime")
