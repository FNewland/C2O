"""NASA SEH 17 common technical processes — three tiers."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(9.5, 4.9))
ax.set_xlim(0, 12)
ax.set_ylim(0.3, 7.9)
ax.axis("off")
ax.set_title("NASA SEH — 17 common technical processes (NPR 7123.1)", pad=8)

tiers = [
    {"name": "System design", "color": COLORS["accent"], "y": (5.9, 7.6),
     "items": ["1. Stakeholder Expectations Definition", "2. Technical Requirements Definition",
               "3. Logical Decomposition", "4. Design Solution Definition"]},
    {"name": "Product realisation", "color": COLORS["accent_3"], "y": (3.6, 5.6),
     "items": ["5. Product Implementation", "6. Product Integration", "7. Product Verification",
               "8. Product Validation", "9. Product Transition"]},
    {"name": "Technical management", "color": COLORS["accent_2"], "y": (0.5, 3.3),
     "items": ["10. Technical Planning", "11. Requirements Management", "12. Interface Management",
               "13. Technical Risk Management", "14. Configuration Management",
               "15. Technical Data Management", "16. Technical Assessment", "17. Decision Analysis"]},
]

for tier in tiers:
    y0, y1 = tier["y"]
    ax.add_patch(FancyBboxPatch((0.4, y0), 11.2, y1 - y0, boxstyle="round,pad=0.05",
                                linewidth=0, facecolor=tier["color"], alpha=0.16))
    ax.text(0.85, y1 - 0.32, tier["name"].upper(), fontsize=9.0, fontweight="bold",
            color=tier["color"], ha="left", va="center")
    cols = 2 if len(tier["items"]) > 3 else 1
    rows = -(-len(tier["items"]) // cols)
    col_w = (11.2 - 0.5) / cols
    dy = 0.42
    for i, item in enumerate(tier["items"]):
        c, r = i % cols, i // cols
        ax.text(0.85 + c * col_w, y1 - 0.85 - r * dy, item, fontsize=8.3,
                color=COLORS["ink"], ha="left", va="center")

save(fig, Path(__file__).stem)
