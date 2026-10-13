"""NASA / ECSS lifecycle phases & review gates."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()

phases = [
    ("Pre-Phase A", "Concept\nStudies",                COLORS["accent"]),
    ("Phase A",     "Concept &\nTech Dev",             COLORS["accent"]),
    ("Phase B",     "Preliminary\nDesign",             COLORS["accent_3"]),
    ("Phase C",     "Final\nDesign",                   COLORS["accent_3"]),
    ("Phase D",     "Assembly,\nIntegration\n& Test",  COLORS["accent_5"]),
    ("Phase E",     "Operations &\nSustainment",       COLORS["accent_2"]),
    ("Phase F",     "Closeout",                        COLORS["grey"]),
]
gates_nasa = ["MCR", "SRR", "SDR", "PDR", "CDR", "SIR", "ORR", "FRR", "DR"]
gates_ecss = ["MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR", "ELR"]

fig, ax = plt.subplots(figsize=(10.0, 4.2))
ax.set_xlim(-0.1, 13.9)
ax.set_ylim(0.9, 5.8)
ax.axis("off")

x = 0
phase_y, phase_h = 2.5, 1.4
for i, (code, label, color) in enumerate(phases):
    w = [1.7, 1.7, 1.8, 1.8, 1.9, 2.4, 1.4][i]
    ax.add_patch(FancyBboxPatch((x, phase_y), w, phase_h, boxstyle="round,pad=0.04",
                                linewidth=0, facecolor=color, alpha=0.9))
    ax.text(x + w / 2, phase_y + phase_h * 0.62, label, ha="center", va="center",
            fontsize=8.5, color="white", fontweight="bold")
    ax.text(x + w / 2, phase_y + phase_h * 0.18, code, ha="center", va="center",
            fontsize=7.5, color="white", style="italic")
    x += w

xpos = [0.7, 1.7, 3.4, 5.2, 7.0, 8.3, 9.4, 11.0, 13.0]
ax.text(0, 5.5, "NASA reviews", fontsize=9, color=COLORS["ink"], fontweight="bold", va="center")
for px, label in zip(xpos, gates_nasa):
    ax.plot([px], [4.4], "v", color=COLORS["accent_2"], ms=9)
    ax.text(px, 4.7, label, ha="center", va="bottom", fontsize=7.5,
            color=COLORS["accent_2"], fontweight="bold")

ax.text(0, 1.1, "ECSS reviews", fontsize=9, color=COLORS["ink"], fontweight="bold", va="center")
for px, label in zip(xpos, gates_ecss):
    ax.plot([px], [2.0], "^", color=COLORS["accent_3"], ms=9)
    ax.text(px, 1.7, label, ha="center", va="top", fontsize=7.5,
            color=COLORS["accent_3"], fontweight="bold")

ax.set_title("Project lifecycle phases and review gates — NASA vs ECSS", pad=10)
save(fig, Path(__file__).stem)
