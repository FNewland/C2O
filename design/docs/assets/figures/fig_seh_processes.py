"""NASA SEH 17 processes — three-tier pyramid."""
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
fig, ax = plt.subplots(figsize=(9.5, 5.6))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis("off")
ax.set_title("NASA SEH — 17 Common Technical Processes",
             fontsize=12, color=COLORS["charcoal"], pad=10)

tiers = [
    {
        "name": "System Design",
        "color": COLORS["garnet"],
        "y": (5.7, 7.5),
        "items": [
            "1. Stakeholder Expectations Definition",
            "2. Technical Requirements Definition",
            "3. Logical Decomposition",
            "4. Design Solution Definition",
        ],
    },
    {
        "name": "Product Realisation",
        "color": COLORS["green"],
        "y": (3.4, 5.4),
        "items": [
            "5. Product Implementation",
            "6. Product Integration",
            "7. Product Verification",
            "8. Product Validation",
            "9. Product Transition",
        ],
    },
    {
        "name": "Technical Management",
        "color": COLORS["blue"],
        "y": (0.6, 3.1),
        "items": [
            "10. Technical Planning",
            "11. Requirements Management",
            "12. Interface Management",
            "13. Technical Risk Management",
            "14. Configuration Management",
            "15. Technical Data Management",
            "16. Technical Assessment",
            "17. Decision Analysis",
        ],
    },
]

for tier in tiers:
    y0, y1 = tier["y"]
    box = FancyBboxPatch((0.4, y0), 11.2, y1 - y0, boxstyle="round,pad=0.05",
                        linewidth=0, facecolor=tier["color"], alpha=0.18)
    ax.add_patch(box)
    # Tier label inside top-left of the band, horizontal, in the band colour
    ax.text(0.85, y1 - 0.32, tier["name"].upper(), fontsize=9.0, fontweight="bold",
            color=tier["color"], ha="left", va="center")
    # Items in two columns
    # Two columns for the larger tiers (TM has 8 items)
    cols = 2 if len(tier["items"]) > 4 else 1
    rows = -(-len(tier["items"]) // cols)
    col_w = (11.2 - 0.5) / cols
    # Compute spacing so all items fit between header (y1-0.7) and band bottom (y0+0.2)
    band_inner_h = (y1 - 0.7) - (y0 + 0.2)
    if rows > 1:
        dy = band_inner_h / (rows - 1)
    else:
        dy = 0
    dy = min(dy, 0.42)
    for i, item in enumerate(tier["items"]):
        c = i % cols
        r = i // cols
        cx = 0.85 + c * col_w
        cy = y1 - 0.95 - r * dy
        ax.text(cx, cy, item, fontsize=8.0, color=COLORS["charcoal"],
                ha="left", va="center")

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_seh_processes.png")
print("OK SEH processes")
