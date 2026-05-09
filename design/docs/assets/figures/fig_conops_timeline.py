"""ConOps timeline — LEOP → Commissioning → Nominal → Disposal."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(11.0, 4.5))
ax.set_xlim(0, 16); ax.set_ylim(0, 8); ax.axis("off")
ax.set_title("Mission Operations Timeline (representative LEO mission)",
             fontsize=12, color=COLORS["charcoal"], pad=8)

phases = [
    ("LEOP",          0.5, 1.5, COLORS["garnet"],   "Days 0–7"),
    ("Commissioning", 2.0, 3.5, COLORS["green"],    "Weeks 1–6"),
    ("Nominal Ops",   5.5, 8.5, COLORS["blue"],     "Years 1–N"),
    ("EOL / Disposal",14.0, 1.5, COLORS["warm_grey"],"Final 25-yr clock"),
]
y0, h = 4.5, 1.5
for name, x, w, color, dur in phases:
    box = FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.04",
                         linewidth=0, facecolor=color, alpha=0.92)
    ax.add_patch(box)
    ax.text(x + w/2, y0 + h*0.7, name,
            ha="center", va="center", color="white", fontweight="bold", fontsize=10)
    ax.text(x + w/2, y0 + h*0.25, dur,
            ha="center", va="center", color="white", fontsize=8.5, style="italic")

# Activity rows below
activities = [
    ("Sequential power-on, antenna deploy, first contact, detumble",
     0.5, 1.5, COLORS["garnet"], 3.0),
    ("Subsystem checkouts, payload calibration, first light",
     2.0, 3.5, COLORS["green"], 2.4),
    ("Pass planning, imaging, downlink, momentum-mgmt, anomaly response",
     5.5, 8.5, COLORS["blue"], 1.8),
    ("De-orbit burn / passivation; 25-yr decay clock",
     14.0, 1.5, COLORS["warm_grey"], 1.2),
]

for txt, x, w, color, y in activities:
    ax.text(x + w/2, y, txt, ha="center", va="center",
            fontsize=8.0, color=color, wrap=True)

# Bottom timeline arrow
ax.annotate("", xy=(15.7, 3.0), xytext=(0.3, 3.0),
            arrowprops=dict(arrowstyle="->", color=COLORS["charcoal"], lw=1.0))
ax.text(15.7, 3.2, "time", color=COLORS["warm_grey"], fontsize=8.5)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_conops_timeline.png")
print("OK conops timeline")
