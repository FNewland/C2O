"""Mass budget pie + compound ECSS margin envelope by phase (Table 8.3)."""
from pathlib import Path

import matplotlib.pyplot as plt
from oer_style import apply_style, SERIES, COLORS, save

apply_style()

labels = ["Payload", "Structure", "Power (SA + battery)", "AOCS",
          "Comms", "OBC / harness", "Propulsion", "Thermal"]
values = [2.4, 1.8, 1.6, 1.0, 0.6, 0.5, 0.4, 0.2]
total = sum(values)

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6),
                         gridspec_kw={"width_ratios": [1.45, 1.0]})

ax = axes[0]
colors = SERIES + [COLORS["grey_light"]]
wedges, _, atxts = ax.pie(
    values, colors=colors[:len(values)],
    autopct=lambda p: f"{p:.0f} %" if p >= 4 else "",
    startangle=90, counterclock=False,
    wedgeprops=dict(edgecolor="white", linewidth=1.2),
    textprops=dict(fontsize=9), pctdistance=0.72, radius=1.0,
)
for t in atxts:
    t.set_color("white")
    t.set_fontweight("bold")
ax.legend(wedges, [f"{l} — {v:.1f} kg" for l, v in zip(labels, values)],
          loc="center right", bbox_to_anchor=(0.02, 0.5), fontsize=8.5)
ax.set_title(f"Dry-mass distribution — {total:.1f} kg CBE")

# Compound margin = (1 + equipment maturity) × (1 + system margin) − 1   (Table 8.3)
ax = axes[1]
phases = ["Phase A", "Phase B", "Phase C", "Phase D"]
equip = [0.20, 0.10, 0.05, 0.00]      # new design → OTS modified → OTS unmodified → measured
system = [0.20, 0.15, 0.10, 0.05]
compound = [(1 + e) * (1 + s) - 1 for e, s in zip(equip, system)]
ticklabels = [f"{p}\n{e*100:.0f}%×{s*100:.0f}%" for p, e, s in zip(phases, equip, system)]

ax.bar(phases, [total] * 4, color=COLORS["accent"], label="Dry mass (CBE)")
ax.bar(phases, [total * m for m in compound], bottom=[total] * 4,
       color=COLORS["accent_2"], label="Margin: equipment + system (compound)")
for x, m in enumerate(compound):
    ax.text(x, total * (1 + m) + 0.12, f"+{m*100 + 1e-6:.0f} %", ha="center",
            fontsize=9.5, fontweight="bold", color=COLORS["ink"])

ax.set_xticks(range(4))
ax.set_xticklabels(ticklabels, fontsize=8)
ax.text(0.5, -0.19, "(equipment maturity × system margin, Table 8.3)", transform=ax.transAxes,
        ha="center", va="top", fontsize=7.5, color=COLORS["grey"], style="italic")
ax.set_ylim(0, total * 1.6)
ax.set_ylabel("Mass (kg)")
ax.set_title("ECSS margin envelope by phase")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), fontsize=8.5, ncol=1)
ax.grid(axis="x", visible=False)

fig.subplots_adjust(wspace=0.3, left=0.16, bottom=0.22)
save(fig, Path(__file__).stem)
