"""Canadian space sector — illustrative map of categories of actors."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(10.5, 5.0))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8.6)
ax.axis("off")
ax.set_title("The Canadian space sector — illustrative map of actors", pad=8)

ROW1, ROW2, H = 6.2, 3.6, 2.3
categories = [
    {"name": "Federal", "color": COLORS["accent"],
     "x": 0.5, "y": ROW1, "w": 4.0, "h": H,
     "items": ["Canadian Space Agency (CSA)", "ISED (spectrum / RSSSA)",
               "Global Affairs Canada (export)"]},
    {"name": "Industry primes", "color": COLORS["accent_2"],
     "x": 5.0, "y": ROW1, "w": 4.0, "h": H,
     "items": ["MDA · Telesat", "Magellan · Maxar Canada", "ABB Canada"]},
    {"name": "New space", "color": COLORS["accent_3"],
     "x": 9.5, "y": ROW1, "w": 4.0, "h": H,
     "items": ["GHGSat (methane)", "Kepler Communications",
               "NorthStar (SSA)", "Mission Control · ExoFly"]},
    {"name": "Universities & labs", "color": COLORS["accent_4"],
     "x": 0.5, "y": ROW2, "w": 4.0, "h": H,
     "items": ["UTIAS · McGill · uOttawa", "Western · Calgary · UBC",
               "Concordia · Sherbrooke", "York · Laval · Dalhousie"]},
    {"name": "Funding", "color": COLORS["accent_5"],
     "x": 5.0, "y": ROW2, "w": 4.0, "h": H,
     "items": ["CSA STDP", "CSA FAST", "CSA CSEP",
               "NSERC / CFI · Provincial"]},
    {"name": "International ties", "color": COLORS["accent_6"],
     "x": 9.5, "y": ROW2, "w": 4.0, "h": H,
     "items": ["NASA Artemis · ISS", "ESA cooperation",
               "ITU · COPUOS", "Five Eyes (defence)"]},
    {"name": "End users", "color": COLORS["grey"],
     "x": 0.5, "y": 0.4, "w": 13.0, "h": 2.7,
     "items": ["Climate / GHG monitoring · Arctic surveillance · Maritime traffic",
               "Remote-area connectivity (broadband / IoT)",
               "Defence ISR · Disaster response · Forestry & agriculture",
               "Indigenous community-led monitoring"]},
]

for cat in categories:
    box = FancyBboxPatch((cat["x"], cat["y"]), cat["w"], cat["h"],
                         boxstyle="round,pad=0.06", linewidth=0,
                         facecolor=cat["color"], alpha=0.16)
    ax.add_patch(box)
    ax.text(cat["x"] + 0.18, cat["y"] + cat["h"] - 0.32, cat["name"],
            fontsize=10.5, color=cat["color"], fontweight="bold", va="center")
    for j, item in enumerate(cat["items"]):
        ax.text(cat["x"] + 0.32, cat["y"] + cat["h"] - 0.85 - j * 0.45, "· " + item,
                fontsize=8.7, color=COLORS["ink"], va="center")

save(fig, Path(__file__).stem)
