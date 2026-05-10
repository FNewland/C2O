"""Solar array sizing nomograph — required area vs orbit-average load."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

# A_SA = (P_sun + P_eclipse * t_e/t_d / eta_dis) / (S_AM0 * eta_cell * cos(beta) * (1 - deg))
# Simplified: A_SA = P_avg * f_eclipse_factor / (S * eta_eff)
S0 = 1361.0     # W/m^2 AM0
eta_cell = 0.30   # GaAs triple-junction
deg = 0.10        # 5-year EOL degradation
beta = np.deg2rad(20)  # representative incidence
eta_eff = eta_cell * np.cos(beta) * (1 - deg)  # ~ 0.226

# Eclipse factor: P_avg orbit-average must be supplied during sun arc
# Sun arc fraction f_s, eclipse f_e = 1 - f_s
# Required generation P_gen = P_avg * (1 + f_e/(f_s * eta_dis))
eta_dis = 0.85
fe_values = [0.0, 0.20, 0.35]   # eclipse fractions
P_avg = np.linspace(5, 50, 100)

for i, fe in enumerate(fe_values):
    fs = 1 - fe
    P_gen = P_avg * (1 + fe / (fs * eta_dis))
    A = P_gen / (S0 * eta_eff)
    ax.plot(P_avg, A * 100*100,  # m^2 → cm^2 doesn't help; use m^2 with fine ticks
            lw=2.0,
            color=SERIES[i],
            label=f"eclipse fraction = {fe:.2f}")
ax.set_xlabel("Orbit-average load $P_{avg}$ (W)")
ax.set_ylabel("Required solar-array area at EOL (cm²)")
ax.set_title("Solar-array nomograph — η = 30 %, EOL deg = 10 %, β = 20°, η_dis = 85 %")
ax.set_xlim(5, 50)
ax.grid(True, alpha=0.3)
ax.legend(loc="upper left", frameon=False, fontsize=9)

# Annotate typical 6U
ax.plot(15, (15 * (1 + 0.35/(0.65*0.85))) / (S0*eta_eff) * 1e4,
        "o", color=COLORS["garnet"], ms=8)
ax.annotate("6U at 15 W avg\n~ 870 cm² needed",
            xy=(15, 870), xytext=(28, 1200),
            fontsize=9, color=COLORS["garnet"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLORS["garnet"], lw=1.2))
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_solar_array.png")
print("OK solar array")
