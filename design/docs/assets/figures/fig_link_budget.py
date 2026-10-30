"""Link-budget waterfall — the §11.8.1 S-band downlink (2.25 GHz, 1695 km, 3 m dish)."""
from pathlib import Path

import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()

# (label, contribution in dB). Positive = gain, negative = loss.
rows = [
    ("Transmit power (2 W)",                      3.0),
    ("Tx antenna gain (patch)",                   6.0),
    ("Tx line losses",                           -1.5),
    ("Free-space path loss (2.25 GHz, 1695 km)", -164.1),
    ("Atmospheric loss (10° elevation)",         -0.5),
    ("Pointing loss",                            -1.0),
    ("Polarisation loss",                        -0.3),
    ("Rx antenna gain (3 m dish)",               35.0),
    ("System noise temperature (150 K)",        -21.8),
    ("Boltzmann constant (−10·log k)",          228.6),
]
cum = [0.0]
for _, d in rows:
    cum.append(cum[-1] + d)
final = cum[-1]                 # 83.4 dBHz
rate_dB = 67.0                  # 5 Mbit/s
required = rate_dB + 4.0 + 2.0  # Eb/N0 req (QPSK + LDPC 3/4) + implementation loss = 73.0
margin = final - required

fig, ax = plt.subplots(figsize=(8.8, 5.2))
n = len(rows)
for i, (label, d) in enumerate(rows):
    y = n - i
    start, end = cum[i], cum[i + 1]
    color = COLORS["accent_3"] if d >= 0 else COLORS["accent_2"]
    width = max(abs(d), 1.2)                 # keep tiny bars visible
    left = min(start, end) if abs(d) >= 1.2 else (start - 1.2 if d < 0 else start)
    ax.barh(y, width, left=left, color=color, edgecolor="white", height=0.7)
    ax.text(max(start, end) + 2.5, y, f"{d:+.1f} dB", va="center", fontsize=9,
            color=COLORS["ink"], clip_on=True)

# EIRP after row 3 (cum[3] = 7.5 dBW)
ax.text(cum[3] + 2.5, n - 2.45, f"→ EIRP = {cum[3]:+.1f} dBW", fontsize=8,
        color=COLORS["grey"], va="center", style="italic", clip_on=True)

ax.axvline(final, color=COLORS["ink"], lw=1.4, ls="--",
           label=f"Received C/N₀ = {final:.1f} dBHz")
ax.axvline(required, color=COLORS["accent"], lw=1.4, ls=":",
           label=f"Required C/N₀ = {required:.1f} dBHz (5 Mbit/s)")

ax.set_yticks(list(range(n, 0, -1)))
ax.set_yticklabels([r[0] for r in rows], fontsize=9)
ax.set_xlabel("Cumulative C/N₀ (dBHz)")
ax.set_title("S-band downlink link budget — waterfall (500 km SSO, 10° elevation)")
ax.set_xlim(-175, 120)
ax.set_ylim(0.3, n + 2.3)
ax.legend(loc="upper left", fontsize=8.5)
ax.grid(axis="x")
ax.grid(axis="y", visible=False)

ax.text(0.99, 0.975, f"Link margin = {final:.1f} − {required:.1f} = {margin:+.1f} dB",
        transform=ax.transAxes, ha="right", va="top", fontsize=10, zorder=10,
        color=COLORS["accent_2"], fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=COLORS["accent_2"], lw=0.8))

save(fig, Path(__file__).stem)
