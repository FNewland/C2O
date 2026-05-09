"""NASA / ECSS lifecycle phases & review gates."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()

# Phases and gates
phases = [
    ("Pre-Phase A", "Concept\nStudies",       COLORS["blue"]),
    ("Phase A",      "Concept &\nTech Dev",    COLORS["blue"]),
    ("Phase B",      "Preliminary\nDesign",    COLORS["green"]),
    ("Phase C",      "Final\nDesign",          COLORS["green"]),
    ("Phase D",      "Assembly,\nIntegration\n& Test", COLORS["warm_grey"]),
    ("Phase E",      "Operations &\nSustainment", COLORS["garnet"]),
    ("Phase F",      "Closeout",               COLORS["charcoal"]),
]
gates_nasa = ["MCR","SRR","SDR","PDR","CDR","SIR","ORR","FRR","DR"]
gates_ecss = ["MDR","PRR","SRR","PDR","CDR","QR","AR","FRR","ELR"]

fig, ax = plt.subplots(figsize=(10.0, 4.6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 6)
ax.axis("off")

# Phase boxes — single horizontal band
x = 0
phase_y = 2.5
phase_h = 1.4
for i, (code, label, color) in enumerate(phases):
    w = [1.7, 1.7, 1.8, 1.8, 1.9, 2.4, 1.4][i]
    box = FancyBboxPatch((x, phase_y), w, phase_h,
                         boxstyle="round,pad=0.04", linewidth=0,
                         facecolor=color, alpha=0.9)
    ax.add_patch(box)
    ax.text(x + w/2, phase_y + phase_h*0.62, label,
            ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    ax.text(x + w/2, phase_y + phase_h*0.18, code,
            ha="center", va="center", fontsize=7.5, color="white", style="italic")
    x += w

# Top track: NASA gates
ax.text(0, 5.3, "NASA gates", fontsize=9, color=COLORS["charcoal"], fontweight="bold")
xpos = [0.7, 1.7, 3.4, 5.2, 7.0, 8.3, 9.4, 11.0, 13.0]
for px, label in zip(xpos, gates_nasa):
    ax.plot([px], [4.5], "v", color=COLORS["garnet"], ms=10)
    ax.text(px, 4.85, label, ha="center", va="bottom", fontsize=7.5,
            color=COLORS["garnet"], fontweight="bold")

# Bottom track: ECSS gates
ax.text(0, 0.6, "ECSS gates", fontsize=9, color=COLORS["charcoal"], fontweight="bold")
for px, label in zip(xpos, gates_ecss):
    ax.plot([px], [1.5], "^", color=COLORS["green"], ms=10)
    ax.text(px, 1.0, label, ha="center", va="top", fontsize=7.5,
            color=COLORS["green"], fontweight="bold")

ax.set_title("Project Lifecycle Phases & Review Gates — NASA vs ECSS",
             fontsize=12, color=COLORS["charcoal"], pad=12)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_lifecycle.png")
print("OK lifecycle")
