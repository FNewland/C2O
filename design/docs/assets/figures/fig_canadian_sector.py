"""Canadian space sector map — categories of actors."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(10.5, 5.6))
ax.set_xlim(0, 14); ax.set_ylim(0, 9); ax.axis("off")

ax.set_title("The Canadian Space Sector — illustrative map of actors",
             fontsize=12, color=COLORS["charcoal"], pad=10)

categories = [
    {
        "name": "Federal", "color": COLORS["garnet"],
        "x": 0.5, "y": 6.5, "w": 4.0, "h": 2.0,
        "items": ["Canadian Space Agency (CSA)",
                  "ISED (spectrum/RSSSA)",
                  "Global Affairs Canada (export)"],
    },
    {
        "name": "Industry primes", "color": COLORS["blue"],
        "x": 5.0, "y": 6.5, "w": 4.0, "h": 2.0,
        "items": ["MDA · Telesat", "Magellan · Maxar Canada", "ABB Canada"],
    },
    {
        "name": "New space", "color": COLORS["green"],
        "x": 9.5, "y": 6.5, "w": 4.0, "h": 2.0,
        "items": ["GHGSat (methane)", "Kepler Communications",
                  "NorthStar (SSA)", "Mission Control · ExoFly"],
    },
    {
        "name": "Universities & labs", "color": COLORS["warm_grey"],
        "x": 0.5, "y": 3.7, "w": 4.0, "h": 2.0,
        "items": ["uOttawa SEDTI",
                  "UTIAS · McGill",
                  "Western · Calgary · UBC",
                  "Concordia · Sherbrooke"],
    },
    {
        "name": "Funding", "color": COLORS["garnet_2"],
        "x": 5.0, "y": 3.7, "w": 4.0, "h": 2.0,
        "items": ["CSA STDP", "CSA FAST",
                  "CSA CSEP",
                  "NSERC / CFI · Provincial"],
    },
    {
        "name": "International ties", "color": COLORS["charcoal"],
        "x": 9.5, "y": 3.7, "w": 4.0, "h": 2.0,
        "items": ["NASA Artemis · ISS",
                  "ESA cooperation",
                  "ITU · COPUOS",
                  "Five Eyes (defence)"],
    },
    {
        "name": "End users", "color": COLORS["green"],
        "x": 0.5, "y": 0.6, "w": 13.0, "h": 2.5,
        "items": ["Climate / GHG monitoring · Arctic surveillance · Maritime traffic",
                  "Remote-area connectivity (broadband / IoT)",
                  "Defence ISR · Disaster response · Forestry & agriculture",
                  "Indigenous community-led monitoring (FN-led)"],
    },
]

for cat in categories:
    box = FancyBboxPatch((cat["x"], cat["y"]), cat["w"], cat["h"],
                         boxstyle="round,pad=0.06", linewidth=0,
                         facecolor=cat["color"], alpha=0.18)
    ax.add_patch(box)
    ax.text(cat["x"] + 0.18, cat["y"] + cat["h"] - 0.32, cat["name"],
            fontsize=10.5, color=cat["color"], fontweight="bold")
    for j, item in enumerate(cat["items"]):
        ax.text(cat["x"] + 0.32, cat["y"] + cat["h"] - 0.78 - j*0.42, "· " + item,
                fontsize=8.7, color=COLORS["charcoal"])

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_canadian_sector.png")
print("OK canadian sector")
