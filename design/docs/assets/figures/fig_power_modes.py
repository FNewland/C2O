"""Power generation and stacked load profile across one orbit (illustrative)."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from oer_style import apply_style, COLORS, save

apply_style()

T = 96
t = np.linspace(0, T, 960)
ecl_start, ecl_end = 30, 66
sun_in = (t < ecl_start) | (t > ecl_end)

P_bus_base = 6.0
P_comms_load = 8.0
P_payload_imaging = 14.0
P_thermal = 4.0
P_gen = 28.0

fig, axes = plt.subplots(2, 1, figsize=(10.0, 6.2), sharex=True,
                         gridspec_kw={"height_ratios": [1, 1.2]})
fig.subplots_adjust(hspace=0.3)

ax = axes[0]
ax.fill_between(t, 0, np.where(sun_in, P_gen, 0), color=COLORS["accent_5"], alpha=0.9,
                label="Solar-array generation", step=None)
ax.axvspan(ecl_start, ecl_end, color="#d9d9d9", alpha=0.6, lw=0, zorder=0)
ax.set_ylim(0, 32)
ax.set_xlim(0, T)
ax.set_ylabel("Generation (W)")
ax.set_title("Power generation across one orbit — sunlit arc and eclipse")
ax.text((ecl_start + ecl_end) / 2, 16, "eclipse", ha="center", va="center",
        fontsize=10, color=COLORS["grey"], fontweight="bold")
ax.legend(handles=[Patch(facecolor=COLORS["accent_5"], label="Solar-array generation"),
                   Patch(facecolor="#d9d9d9", label="Eclipse")],
          loc="upper right", fontsize=9)

ax = axes[1]
P_bus = np.full_like(t, P_bus_base)
P_th = np.where(~sun_in, P_thermal, P_thermal * 0.5)      # heaters work harder in eclipse
P_pay = np.where(((t > 12) & (t < 18)) | ((t > 72) & (t < 78)), P_payload_imaging, 0)  # sunlit only
P_co = np.where((t > 38) & (t < 46), P_comms_load, 1.5)   # pass falls in eclipse here

ax.stackplot(t, P_bus, P_th, P_pay, P_co,
             colors=[COLORS["grey"], COLORS["accent_3"], COLORS["accent_2"], COLORS["accent"]],
             labels=["Bus / OBC / AOCS", "Thermal heaters", "Payload imaging (sunlit only)",
                     "Comms downlink"], alpha=0.92)
ax.axvspan(ecl_start, ecl_end, color="#d9d9d9", alpha=0.4, lw=0, zorder=0)
ax.set_ylim(0, 32)
ax.set_xlabel("Time in orbit (min)")
ax.set_ylabel("Load (W)")
ax.set_title("Stacked load profile by subsystem (illustrative)")
ax.legend(loc="upper right", fontsize=9, ncol=2)

save(fig, Path(__file__).stem)
