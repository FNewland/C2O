"""Daily data volume vs ground-station contact time — closure check."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, SERIES, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

# Capacity: # passes/day × pass duration × downlink rate
# 1 day on a polar SSO: 4-6 contacts to a single polar station, 8-12 min each
# Downlink rates depending on band
configs = [
    ("UHF 9.6 kbps × 4 passes × 8 min",   9_600, 4, 8),
    ("S-band 1 Mbps × 4 passes × 8 min",  1_000_000, 4, 8),
    ("S-band 4 Mbps × 4 passes × 8 min",  4_000_000, 4, 8),
    ("X-band 50 Mbps × 4 passes × 8 min", 50_000_000, 4, 8),
    ("X-band 200 Mbps × 4 passes × 8 min",200_000_000, 4, 8),
]
labels = []
volumes_GB = []
for name, R, n, t_min in configs:
    V_bits = R * (n * t_min * 60)
    V_GB = V_bits / 8 / 1e9
    labels.append(name)
    volumes_GB.append(V_GB)

y = np.arange(len(labels))
ax.barh(y, volumes_GB, color=SERIES[:len(labels)], alpha=0.9)
for i, v in enumerate(volumes_GB):
    ax.text(v*1.04, i, f"{v:.2f} GB/day", va="center", fontsize=9)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xscale("log")
ax.set_xlabel("Daily downlink capacity (GB/day, log)")
ax.set_xlim(0.001, 1000)
ax.grid(True, which="both", axis="x", alpha=0.3)
ax.set_title("Daily downlink capacity by band  (single polar GS, ~4 passes/day)")

# Production estimates
sources = [
    ("CubeSat HK only",               0.005),
    ("Multispectral imager (1 band)", 0.5),
    ("Ocean colour 4-band imager",    2.5),
    ("SAR (compressed)",              30),
    ("Hyperspectral",                 60),
]
for name, vol in sources:
    ax.axvline(vol, color=COLORS["garnet_2"], lw=0.8)

ax.text(0.005, len(labels)+0.4, "HK only",
        rotation=90, fontsize=8, color=COLORS["garnet_2"], va="bottom")
ax.text(0.5, len(labels)+0.4, "Imager",
        rotation=90, fontsize=8, color=COLORS["garnet_2"], va="bottom")
ax.text(30, len(labels)+0.4, "SAR (compressed)",
        rotation=90, fontsize=8, color=COLORS["garnet_2"], va="bottom")

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_data_volume.png")
print("OK data volume")
