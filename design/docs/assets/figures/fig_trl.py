"""Technology readiness level ladder with the evidence environment for each band."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(10.0, 5.4))
ax.set_xlim(0, 13.5)
ax.set_ylim(0, 10)
ax.axis("off")
ax.set_title("Technology readiness level (TRL) ladder", pad=8)

trls = [
    (1, "Basic principles observed",               COLORS["grey"]),
    (2, "Technology concept formulated",           COLORS["grey"]),
    (3, "Analytical / experimental proof of concept", COLORS["grey"]),
    (4, "Component validation in laboratory",      COLORS["accent_3"]),
    (5, "Component validation in relevant environment", COLORS["accent_3"]),
    (6, "System/subsystem demo in relevant environment", COLORS["accent_3"]),
    (7, "System prototype demo in space",          COLORS["accent"]),
    (8, "System qualified through test and demo",  COLORS["accent"]),
    (9, "Flight-proven in successful mission",     COLORS["accent_2"]),
]
for idx, (trl, label, color) in enumerate(trls):
    y = idx + 0.4
    ax.add_patch(FancyBboxPatch((0.6, y), 7.9, 0.8, boxstyle="round,pad=0.04",
                                linewidth=0, facecolor=color, alpha=0.85))
    ax.text(0.9, y + 0.4, f"TRL {trl}", color="white", fontsize=10, fontweight="bold", va="center")
    ax.text(2.2, y + 0.4, label, color="white", fontsize=9.5, va="center")

notes = [
    ("TRL 1–3", "Research and internal R&D —\nnot selectable for flight", 1.6),
    ("TRL 4–6", "Ground evidence; CubeSat buses\ntypically buy COTS at TRL ≥ 6", 4.9),
    ("TRL 7",   "First in-orbit demonstration —\nthe costliest gap to cross (6 → 7)", 6.8),
    ("TRL 8–9", "Operational missions —\nflight heritage drives selection", 8.5),
]
for k, v, yc in notes:
    ax.text(9.0, yc + 0.32, k, fontsize=9.5, fontweight="bold", color=COLORS["ink"], va="bottom")
    ax.text(9.0, yc + 0.22, v, fontsize=8.5, color=COLORS["ink"], va="top", linespacing=1.25)

save(fig, Path(__file__).stem)
