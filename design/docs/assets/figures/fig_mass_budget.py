"""Sample figure: mass budget pie + margin stack."""
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, SERIES, COLORS, add_footer

apply_style()

# 6U CubeSat illustrative mass breakdown (kg)
labels = [
    "Payload",
    "Structure",
    "Power (solar + battery)",
    "AOCS",
    "Comms",
    "OBC / Harness",
    "Propulsion",
    "Thermal",
]
values = [2.4, 1.8, 1.6, 1.0, 0.6, 0.5, 0.4, 0.2]
total = sum(values)

fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.5),
                         gridspec_kw={"width_ratios": [1.2, 1.0]})

# Pie
ax = axes[0]
wedges, txts, atxts = ax.pie(
    values, labels=labels, colors=SERIES,
    autopct=lambda p: f"{p:.0f}%",
    startangle=90, counterclock=False,
    wedgeprops=dict(edgecolor="white", linewidth=1.2),
    textprops=dict(fontsize=9, color=COLORS["charcoal"]),
    pctdistance=0.72,
)
for t in atxts:
    t.set_color("white")
    t.set_fontweight("bold")
ax.set_title(f"Mass distribution — {total:.1f} kg dry")

# Margin stack — Phase A through D (ECSS margin policy)
ax = axes[1]
phases = ["Phase A", "Phase B", "Phase C", "Phase D"]
margins = [44, 24, 13, 5]      # ECSS-M-ST-10C representative values
dry = [total] * 4

ax.bar(phases, dry, color=COLORS["blue"], label="Dry mass")
ax.bar(phases, [d * m / 100 for d, m in zip(dry, margins)],
       bottom=dry, color=COLORS["garnet"], label="Margin")
for x, m in enumerate(margins):
    ax.text(x, dry[x] + dry[x] * m / 100 + 0.15,
            f"+{m}%", ha="center", fontsize=9, color=COLORS["charcoal"])

ax.set_ylim(0, max(dry) * 1.6)
ax.set_ylabel("Mass (kg)")
ax.set_title("ECSS margin policy by phase")
ax.legend(frameon=False, loc="upper right")
ax.grid(axis="x", visible=False)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_mass_budget.png")
print("OK mass budget")
