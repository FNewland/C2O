"""Daily downlink capacity by band vs payload data production — closure check."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, SERIES, save

apply_style()
fig, ax = plt.subplots(figsize=(8.4, 5.0))

# Capacity = rate × passes/day × pass duration (no protocol overhead)
configs = [
    ("UHF 9.6 kbit/s",     9_600),
    ("S-band 1 Mbit/s",    1_000_000),
    ("S-band 4 Mbit/s",    4_000_000),
    ("X-band 50 Mbit/s",   50_000_000),
    ("X-band 200 Mbit/s",  200_000_000),
]
n_pass, t_min = 4, 8
labels = [c[0] for c in configs]
volumes_GB = [R * n_pass * t_min * 60 / 8 / 1e9 for _, R in configs]

y = np.arange(len(labels))
ax.barh(y, volumes_GB, color=SERIES[:len(labels)], alpha=0.9, height=0.6, zorder=3)
for i, v in enumerate(volumes_GB):
    ax.text(v * 1.15, i, f"{v:.3g} GB/day", va="center", fontsize=9, clip_on=True)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xscale("log")
ax.set_xlabel("Daily downlink capacity (GB/day, log)")
ax.set_xlim(0.001, 1000)
ax.set_ylim(-1.6, len(labels) - 0.4)
ax.grid(True, which="both", axis="x", alpha=0.3)
ax.grid(False, axis="y")
ax.set_title(f"Daily downlink capacity by band  ({n_pass} × {t_min}-min passes, single polar station)")

# Payload production estimates (GB/day) — vertical lines, labelled inside the axes
sources = [
    ("HK only (5 MB)", 0.005),
    ("Imager, 1 band (0.5 GB)", 0.5),
    ("4-band imager (2.5 GB)", 2.5),
    ("SAR, compressed (30 GB)", 30),
    ("Hyperspectral (60 GB)", 60),
]
for k, (name, vol) in enumerate(sources):
    ax.axvline(vol, color=COLORS["accent_2"], lw=0.9, ls="--", zorder=2)
    # alternate label rows for the close pairs
    ytxt = -0.65 if k % 2 == 0 else -1.15
    ax.text(vol * 1.1, ytxt, name, fontsize=7.5, color=COLORS["accent_2"],
            ha="left", va="center", clip_on=True)
ax.text(0.0011, -0.65, "payload\nproduction:", fontsize=7.5,
        color=COLORS["accent_2"], ha="left", va="center", style="italic")

save(fig, Path(__file__).stem)
