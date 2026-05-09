"""Pass-elevation profile — typical Iqaluit S-band pass for 450 km SSO."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()

# Synthesise an elevation profile for a single pass
# (idealised symmetric pass, peak elevation 60 deg, 8.5 min total)
t = np.linspace(0, 8.5, 600)        # minutes
peak = 60.0                          # max elevation deg
duration = 8.5                       # min above 5 deg
elev = peak * np.cos(np.pi * (t - duration/2) / duration)
elev[elev < 0] = 0
mask = elev >= 5.0   # above min elevation

fig, ax = plt.subplots(figsize=(8.4, 4.4))
ax.plot(t[mask], elev[mask], lw=2.4, color=COLORS["garnet"])
ax.fill_between(t[mask], 0, elev[mask], alpha=0.15, color=COLORS["garnet"])

# Min elevation line
ax.axhline(5, color=COLORS["polar"], lw=0.8)
ax.text(8.4, 6, "min elevation 5°", ha="right", fontsize=8.5,
        color=COLORS["warm_grey"])

# Mark AOS, TCA, LOS
def mark(t_val, label, ymax):
    ax.axvline(t_val, color=COLORS["charcoal"], ls=":", lw=0.9)
    ax.text(t_val, ymax+1.5, label, ha="center", fontsize=9,
            color=COLORS["charcoal"], fontweight="bold")

idx_in = np.where(mask)[0]
t_aos, t_los = t[idx_in[0]], t[idx_in[-1]]
t_tca = duration / 2
mark(t_aos, "AOS",  peak)
mark(t_tca, "TCA",  peak)
mark(t_los, "LOS",  peak)

# Annotation: data volume bands
hi_rate = elev > 30
ax.fill_between(t[hi_rate], 0, elev[hi_rate], color=COLORS["green"], alpha=0.25,
                label="≥ 30° elevation: high-rate downlink window")
ax.legend(loc="upper right", frameon=False, fontsize=9)

ax.set_xlabel("Time from AOS (min)")
ax.set_ylabel("Elevation (deg)")
ax.set_xlim(0, 9)
ax.set_ylim(0, peak * 1.2)
ax.set_title("Iqaluit S-band Pass Geometry — 450 km SSO (illustrative)")

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_pass_geometry.png")
print("OK pass geometry")
