"""Free-space path loss vs slant range, multiple bands."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 4.6))

# FSPL = 20 log10(4 pi d / lambda) [dB]
c = 3e8
bands = {
    "VHF (150 MHz)":   0.150e9,
    "UHF (435 MHz)":   0.435e9,
    "S-band (2.2 GHz)":2.2e9,
    "X-band (8.0 GHz)":8.0e9,
    "Ka-band (26 GHz)":26.0e9,
}
d = np.linspace(100, 36000, 600) * 1e3   # km → m

for i, (name, f) in enumerate(bands.items()):
    lam = c / f
    FSPL = 20 * np.log10(4 * np.pi * d / lam)
    ax.plot(d/1e3, FSPL, lw=2.0, color=SERIES[i], label=name)

# Mark common slant ranges
for ds, label in [(1000, "1000 km LEO"), (2200, "polar pass slant"),
                   (35786, "GEO direct")]:
    ax.axvline(ds, color=COLORS["polar"], lw=0.6)
    ax.text(ds, 90, label, rotation=90, fontsize=8, va="bottom",
            color=COLORS["warm_grey"])

ax.set_xlabel("Slant range (km, log)")
ax.set_ylabel("Free-space path loss (dB)")
ax.set_xscale("log")
ax.set_xlim(100, 40000)
ax.set_ylim(85, 220)
ax.grid(True, which="both", alpha=0.3)
ax.set_title("Free-space path loss vs slant range across frequency bands")
ax.legend(loc="upper left", frameon=False, fontsize=9)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_fspl.png")
print("OK fspl")
