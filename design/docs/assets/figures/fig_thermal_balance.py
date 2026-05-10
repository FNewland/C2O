"""Radiative thermal equilibrium — surface temp vs alpha/epsilon ratio."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

S0 = 1361     # W/m^2 solar
Earth_IR = 230  # W/m^2 (rough IR emission from Earth at LEO)
albedo = 0.30   # average Earth albedo
sigma = 5.67e-8

# Equilibrium temp T = ((alpha/epsilon * S0_eff) / sigma) ^ (1/4)
# where S0_eff = absorbed solar + IR
ae_ratio = np.linspace(0.05, 4.0, 500)
phi_solar = S0 * 0.25  # average over a flat plate randomly tumbling, roughly
phi_ir = Earth_IR * 0.5

T_sun = ((ae_ratio * phi_solar + phi_ir) / sigma) ** 0.25 - 273.15

ax.plot(ae_ratio, T_sun, lw=2.4, color=COLORS["garnet"],
        label="Sun + Earth IR (LEO orbit-average)")
T_eclipse = ((phi_ir) / sigma)**0.25 - 273.15
ax.axhline(T_eclipse, color=COLORS["blue"], lw=1.6, ls="--",
           label=f"Eclipse only (no Sun): {T_eclipse:.1f} °C")

# Common surfaces (approximate alpha/epsilon)
surfaces = {
    "MLI (gold-coat outer)":   (0.34/0.04, COLORS["green"]),
    "Bare Al (polished)":      (0.20/0.04, COLORS["warm_grey"]),
    "White paint (Z93)":       (0.15/0.92, COLORS["blue"]),
    "Black paint (Chemglaze)": (0.95/0.85, COLORS["charcoal"]),
}
for name, (r, color) in surfaces.items():
    T = ((r * phi_solar + phi_ir) / sigma)**0.25 - 273.15
    ax.plot(r, T, "o", color=color, ms=8)
    ax.text(r*1.04, T+3, f"{name}\nα/ε = {r:.2f}", fontsize=8,
            color=color, fontweight="bold")

ax.set_xlabel("α / ε  (solar absorptance / IR emittance)")
ax.set_ylabel("Equilibrium temperature (°C)")
ax.set_title("Radiative thermal equilibrium — flat plate, LEO orbit-average")
ax.set_xlim(0, 4.0)
ax.set_ylim(-150, 150)
ax.grid(True, alpha=0.3)
ax.legend(loc="lower right", frameon=False, fontsize=9)
ax.axhspan(-40, 60, color=COLORS["polar"], alpha=0.5, zorder=0)
ax.text(0.05, 0, "typical electronics\noperating band",
        fontsize=8.5, color=COLORS["warm_grey"], fontweight="bold")
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_thermal_balance.png")
print("OK thermal balance")
