"""ConOps timeline — LEOP → Commissioning → Nominal → Disposal."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(11.5, 5.4))
ax.set_xlim(0, 17.5); ax.set_ylim(-1, 9); ax.axis("off")
ax.set_title("Mission Operations Timeline (representative LEO mission)",
             fontsize=12, color=COLORS["charcoal"], pad=8)

phases = [
    ("LEOP",          0.5, 1.7, COLORS["garnet"],    "Days 0–7"),
    ("Commissioning", 2.4, 3.4, COLORS["green"],     "Weeks 1–6"),
    ("Nominal Ops",   6.0, 8.4, COLORS["blue"],      "Years 1–N"),
    ("EOL/Disposal", 14.6, 2.2, COLORS["warm_grey"], "Final 25-yr clock"),
]
# Phase band
y0, h = 5.5, 1.6
for name, x, w, color, dur in phases:
    box = FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.04",
                         linewidth=0, facecolor=color, alpha=0.92)
    ax.add_patch(box)
    ax.text(x + w/2, y0 + h*0.65, name,
            ha="center", va="center", color="white",
            fontweight="bold", fontsize=10)
    ax.text(x + w/2, y0 + h*0.25, dur,
            ha="center", va="center", color="white", fontsize=8.0, style="italic")

# Time arrow (well below the band, above activities)
ax.annotate("", xy=(17.0, 4.6), xytext=(0.3, 4.6),
            arrowprops=dict(arrowstyle="->", color=COLORS["charcoal"], lw=1.0))
ax.text(17.0, 4.85, "time", color=COLORS["warm_grey"], fontsize=8.5)

# Activity rows below the time arrow — connected by leader lines to phase
activities = [
    ("Sequential power-on, antenna deploy,\nfirst contact, detumble",
     0.5, 1.7, COLORS["garnet"], 3.0),
    ("Subsystem checkouts, payload\ncalibration, first light",
     2.4, 3.4, COLORS["green"], 2.0),
    ("Pass planning, imaging, downlink,\nmomentum-mgmt, anomaly response",
     6.0, 8.4, COLORS["blue"], 1.0),
    ("De-orbit burn / passivation;\n25-yr decay clock",
     14.6, 2.2, COLORS["warm_grey"], 0.0),
]

for txt, x, w, color, y in activities:
    cx = x + w/2
    # Leader line from phase band bottom to activity text top
    ax.plot([cx, cx], [y0, y + 0.6], color=color, lw=0.6, alpha=0.5, zorder=0)
    ax.text(cx, y, txt, ha="center", va="top",
            fontsize=7.6, color=color, wrap=True, linespacing=1.25)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_conops_timeline.png")
print("OK conops timeline")
