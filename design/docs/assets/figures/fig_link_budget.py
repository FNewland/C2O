"""Sample figure: link-budget waterfall (S-band downlink)."""
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()

# Sequence of contributions to received C/No (dB-Hz)
# Positive = gain, negative = loss. Each row = (label, delta_dB)
rows = [
    ("Transmit power (2 W)",                      33.0),
    ("Tx antenna gain (patch)",                    6.0),
    ("Tx line / mismatch loss",                   -1.5),
    ("Free-space path loss (2.2 GHz, 1500 km)",-162.9),
    ("Atmospheric & rain (10° elev.)",            -1.5),
    ("Polarisation & pointing",                   -1.0),
    ("Rx antenna gain (3.7 m dish)",              36.0),
    ("Rx feed loss",                              -0.5),
    ("Boltzmann constant (-10·log k)",           228.6),
    ("System noise temperature (-10·log Ts)",    -22.6),
]

# Cumulative
cum = [0.0]
for _, d in rows:
    cum.append(cum[-1] + d)
final = cum[-1]
required = 50.0  # required C/No (dB-Hz) for chosen modulation+code+rate

fig, ax = plt.subplots(figsize=(8.4, 5.0))
labels = [r[0] for r in rows]
y_pos = list(range(len(rows), 0, -1))   # top -> bottom
for i, (label, d) in enumerate(rows):
    y = len(rows) - i
    start = cum[i]
    end = cum[i + 1]
    color = COLORS["green"] if d >= 0 else COLORS["garnet"]
    ax.barh(y, end - start, left=start, color=color, edgecolor="white", height=0.7)
    ax.text(max(start, end) + 1.5, y, f"{d:+.1f} dB",
            va="center", fontsize=9, color=COLORS["charcoal"])

# Final received C/No
ax.axvline(final, color=COLORS["charcoal"], lw=1.4, ls="--",
           label=f"Received C/N₀ = {final:.1f} dB-Hz")
ax.axvline(required, color=COLORS["blue"], lw=1.4, ls=":",
           label=f"Required C/N₀ = {required:.1f} dB-Hz")

ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xlabel("Cumulative C/N₀ (dB-Hz)")
ax.set_title("S-band Downlink Link Budget — Waterfall")
ax.set_xlim(-180, max(cum) + 60)
ax.legend(loc="lower right", frameon=False)
ax.grid(axis="x")
ax.grid(axis="y", visible=False)

# Margin annotation
margin = final - required
note = f"Link margin: {margin:+.1f} dB"
ax.text(0.99, 0.02, note, transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=10, color=COLORS["garnet"], fontweight="bold")

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_link_budget.png")
print("OK link budget")
