"""Power profile across one orbit — by mode (sun/eclipse/comms/payload)."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()

# 6U EOSAT-1-like, 96 min orbit, ~36 min eclipse, mix of payload + comms
T = 96  # min
t = np.linspace(0, T, 480)
sun_in = (t < 30) | (t > 66)        # sun arcs

P_bus_base = 6.0     # always-on (OBC, AOCS housekeeping, htrs idle)
P_comms_load = 8.0   # high-rate downlink during pass
P_payload_imaging = 14.0
P_thermal = 4.0      # heaters

fig, axes = plt.subplots(2, 1, figsize=(10.5, 6.2),
                         gridspec_kw={"height_ratios":[1, 1.2]})

# Top: power generation vs eclipse/sun
ax = axes[0]
gen = np.where(sun_in, 28.0, 0.0)
ax.fill_between(t, 0, gen, color=COLORS["garnet"], alpha=0.9,
                label="Solar array generation")
ax.fill_between(t, 0, np.where(~sun_in, 30, 0),
                color=COLORS["charcoal"], alpha=0.15, label="Eclipse")
ax.set_ylim(0, 32); ax.set_xlim(0, T)
ax.set_ylabel("Generation (W)")
ax.set_title("Power Generation across one orbit (Sun-arc + Eclipse)")
ax.legend(loc="upper right", frameon=False, fontsize=9)

# Bottom: stacked load
ax = axes[1]
P_bus = np.full_like(t, P_bus_base)
P_th  = np.where((t > 0) & (t < T), P_thermal, 0)
# Imaging during day-side, only when over ocean targets (random window)
P_pay = np.where((t > 12) & (t < 18) | (t > 50) & (t < 56),
                 P_payload_imaging, 0)
# Downlink near pass — say t = 35-43 (above Iqaluit)
P_co = np.where((t > 35) & (t < 43), P_comms_load, 1.5)

ax.stackplot(t, P_bus, P_th, P_pay, P_co,
             colors=[COLORS["warm_grey"], COLORS["green"],
                     COLORS["garnet"],   COLORS["blue"]],
             labels=["Bus / OBC / AOCS", "Thermal heaters",
                     "Payload imaging", "Comms downlink"], alpha=0.92)
ax.fill_between(t, 0, np.where(~sun_in, 50, 0),
                color=COLORS["charcoal"], alpha=0.07, zorder=0)

ax.set_ylim(0, 32); ax.set_xlim(0, T)
ax.set_xlabel("Time in orbit (min)")
ax.set_ylabel("Load (W)")
ax.set_title("Stacked load profile by subsystem (illustrative)")
ax.legend(loc="upper right", frameon=False, fontsize=9, ncol=2)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_power_modes.png")
print("OK power modes")
