"""Thermal energy-balance schematic for a CubeSat in LEO (Ch 9 §9.4).

A 3U body with the four inputs of §9.4.2 (direct solar, Earth albedo, Earth IR,
internal dissipation) and the single output (radiation to deep space), with
the hot-case and cold-case conditions of §9.4.5 annotated. Flux values are the
§9.4.2 numbers.
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge, Rectangle
from oer_style import apply_style, COLORS, save

apply_style()

fig, ax = plt.subplots(figsize=(7.5, 5.2))
ax.set_xlim(0, 15)
ax.set_ylim(0, 10.4)
ax.set_aspect("equal")
ax.axis("off")

# --- deep space background label ----------------------------------------
ax.text(7.5, 10.3, "deep space  T ≈ 2.7 K (sink)", ha="center", va="top", fontsize=8,
        color=COLORS["grey"], style="italic")

# --- Earth (bottom) --------------------------------------------------------
earth_c = (7.5, -9.5)
ax.add_patch(Wedge(earth_c, 11.0, 0, 180, facecolor="#dbe6f0", edgecolor=COLORS["accent"],
                   linewidth=1.2))
ax.text(7.5, 0.5, "Earth — albedo $\\alpha_E$ ≈ 0.30, IR $q_{IR}$ ≈ 240 W/m²", ha="center", va="bottom",
        fontsize=8, color=COLORS["accent"])

# --- Sun (left) -----------------------------------------------------------
sun = (1.3, 7.6)
ax.add_patch(Circle(sun, 0.55, facecolor=COLORS["accent_5"], edgecolor="none"))
for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
    ax.plot([sun[0] + 0.7 * np.cos(a), sun[0] + 0.95 * np.cos(a)],
            [sun[1] + 0.7 * np.sin(a), sun[1] + 0.95 * np.sin(a)], color=COLORS["accent_5"], lw=1)
ax.text(1.3, 6.65, "Sun\n$S$ = 1361 W/m²", ha="center", va="top", fontsize=8,
        color=COLORS["accent_5"])

# --- CubeSat body (3U, side view) -------------------------------------------
bx, by, bw, bh = 6.3, 3.3, 2.4, 4.0
ax.add_patch(Rectangle((bx, by), bw, bh, facecolor="#f2f2f2", edgecolor=COLORS["ink"],
                       linewidth=1.5, zorder=3))
# internal electronics block
ax.add_patch(FancyBboxPatch((bx + 0.45, by + 1.2), bw - 0.9, 1.6, boxstyle="round,pad=0.04",
                            facecolor=COLORS["accent_2"], edgecolor="none", alpha=0.85, zorder=4))
ax.text(bx + bw / 2, by + 2.0, "$Q_{int}$\nelectronics\ndissipation", ha="center", va="center",
        fontsize=7.5, color="white", zorder=5, linespacing=1.1)
ax.text(bx + bw / 2, by + bh + 0.12, "zenith face (radiator)", ha="center", va="bottom",
        fontsize=7.5, color=COLORS["ink"], style="italic")
ax.text(bx + bw / 2, by - 0.12, "nadir face", ha="center", va="top", fontsize=7.5,
        color=COLORS["ink"], style="italic")
ax.text(bx - 0.12, by + bh - 0.45, "Sun-facing\nside, $\\alpha_s$", ha="right", va="center", fontsize=7.5,
        color=COLORS["ink"], style="italic")
ax.text(bx + bw + 0.12, by + bh / 2, "coatings:\n$\\alpha_s/\\varepsilon$", ha="left", va="center", fontsize=7.5,
        color=COLORS["ink"], style="italic")


def arrow(p, q, color, label=None, lx=0, ly=0, lw=2.2, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=color,
                                 linewidth=lw, zorder=6))
    if label:
        ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, ha=ha, va="center",
                fontsize=8, color=color, zorder=7,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"))


# direct solar (three parallel rays from the Sun)
for dy in (-0.7, 0.0, 0.7):
    arrow((2.4, 6.0 + dy), (bx - 0.05, 5.3 + dy), COLORS["accent_5"], lw=1.8)
ax.text(4.0, 7.3, "direct solar\n$\\alpha_s A_{sun} S$", ha="center", va="center", fontsize=8,
        color=COLORS["accent_5"])

# albedo (reflected sunlight from Earth, angled up-right into the nadir/side faces)
arrow((4.6, 1.6), (bx + 0.3, by - 0.05), COLORS["accent_5"], lw=1.8)
ax.text(3.9, 2.9, "albedo\n$\\alpha_s A_{alb} F_{alb}\\, \\alpha_E S$", ha="center", va="center", fontsize=8,
        color=COLORS["accent_5"])
# Earth IR (straight up into the nadir face)
arrow((bx + bw - 0.5, 1.5), (bx + bw - 0.5, by - 0.05), COLORS["accent_2"], lw=1.8)
ax.text(10.4, 2.3, "Earth IR\n$\\varepsilon A_{IR} F_{IR}\\, q_{IR}$", ha="center", va="center", fontsize=8,
        color=COLORS["accent_2"])

# radiation to space (several outward arrows from the zenith and side faces)
for x in (bx + 0.5, bx + bw / 2, bx + bw - 0.5):
    arrow((x, by + bh + 0.45), (x, by + bh + 1.6), COLORS["accent"], lw=1.8)
arrow((bx + bw + 0.05, by + 3.2), (bx + bw + 1.1, by + 3.9), COLORS["accent"], lw=1.4)
arrow((bx + bw + 0.05, by + 0.8), (bx + bw + 1.1, by + 0.3), COLORS["accent"], lw=1.4)
ax.text(bx + bw / 2, by + bh + 1.75, "radiated to space\n$Q_{out} = \\varepsilon \\sigma A_{rad} T^4$",
        ha="center", va="bottom", fontsize=8, color=COLORS["accent"])

# --- hot / cold case boxes ---------------------------------------------------
def case_box(x, y, w, h, title, lines, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", facecolor="white",
                                edgecolor=col, linewidth=1.4, zorder=8))
    ax.text(x + 0.15, y + h - 0.28, title, ha="left", va="center", fontsize=8.5,
            fontweight="bold", color=col, zorder=9)
    ax.text(x + 0.15, y + (h - 0.5) / 2 - 0.05, lines, ha="left", va="center", fontsize=7.5,
            color=COLORS["ink"], zorder=9, linespacing=1.25)


case_box(10.6, 7.0, 4.3, 3.0, "Hot case",
         "$S$ = 1414 W/m² (perihelion)\nall units on: max $Q_{int}$\nworst Sun angle: max $A_{sun}$\n"
         "EOL coatings: $\\alpha_s$ increased\nalbedo 0.35", COLORS["accent_2"])
case_box(10.6, 3.5, 4.3, 3.0, "Cold case",
         "eclipse: no solar, no albedo\nsafe mode: min $Q_{int}$\nBOL coatings: $\\alpha_s$ lowest\n"
         "Earth IR 200 W/m²\nfull deep-space view", COLORS["accent"])

ax.text(0.2, 9.75, "steady state: $Q_{in} = Q_{out}$\n$T = [(Q_{abs} + Q_{int})/(\\varepsilon\\sigma A_{rad})]^{1/4}$",
        ha="left", va="top", fontsize=8, color=COLORS["ink"])

save(fig, Path(__file__).stem)
