"""3U CubeSat envelope per the CubeSat Design Specification Rev 14 (Ch 12 §12.1.1).

Left: side view (X–Z) of the 100 × 100 × 340.5 mm body with the four
hard-anodised rails, the rail-end contact pads (stand-offs), the two
deployment switches on the −Z rail ends, the remove-before-flight (RBF) pin
access, the 6.5 mm protrusion envelope on the ±X/±Y faces between the rails,
and the CG limit (within 2 cm of the geometric centre). Right: end view (X–Y)
with the 8.5 × 8.5 mm rail cross-sections. Dimensions in mm, drawn to scale.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
from oer_style import apply_style, COLORS, save

apply_style()

W, L, RAIL, PROT = 100.0, 340.5, 8.5, 6.5
RAIL_COL = "#8d8d8d"
BODY_COL = "#eef2f6"

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.1, 5.0), gridspec_kw={"width_ratios": [1.0, 1.0]})
for a in (ax, ax2):
    a.set_aspect("equal")
    a.axis("off")


def dim(a, p, q, text, offset=0, fs=7.5, color=COLORS["ink"], rot=0):
    """Dimension line between p and q with the text at its midpoint."""
    a.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>", mutation_scale=8, color=color, lw=0.8,
                                shrinkA=0, shrinkB=0))
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    if rot == 90:
        a.text(mx + offset, my, text, ha="center", va="center", fontsize=fs, color=color,
               rotation=90, bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none"))
    else:
        a.text(mx, my + offset, text, ha="center", va="center", fontsize=fs, color=color,
               bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none"))


# ------------------------------------------------------------------ side view
ax.add_patch(Rectangle((0, 0), W, L, facecolor=BODY_COL, edgecolor=COLORS["ink"], lw=1.2))
# rails (two visible edges in this view)
for x in (0, W - RAIL):
    ax.add_patch(Rectangle((x, 0), RAIL, L, facecolor=RAIL_COL, edgecolor=COLORS["ink"], lw=0.8))
# rail-end contact pads (stand-offs) at ±Z
for x in (0, W - RAIL):
    for y in (-7, L):
        ax.add_patch(Rectangle((x, y), RAIL, 7, facecolor=COLORS["ink"], edgecolor="none"))
# deployment switches on the −Z rail ends
for x in (RAIL / 2, W - RAIL / 2):
    ax.add_patch(Circle((x, -12), 3.2, facecolor=COLORS["accent_2"], edgecolor="none"))
ax.annotate("deployment switches\n(−Z rail ends, ≥ 1 per\naccessible rail face)", xy=(W - RAIL / 2, -14),
            xytext=(W + 30, -40), fontsize=7.5, color=COLORS["accent_2"], ha="left", va="center",
            arrowprops=dict(arrowstyle="-|>", color=COLORS["accent_2"], lw=0.9, mutation_scale=9))
ax.annotate("", xy=(RAIL / 2, -14), xytext=(W + 30, -40),
            arrowprops=dict(arrowstyle="-|>", color=COLORS["accent_2"], lw=0.9, mutation_scale=9,
                            shrinkB=0, connectionstyle="arc3,rad=0.25"))
# protrusion envelope on the ±X faces (6.5 mm beyond the face, between the rails)
for x0, sgn in ((W, +1), (0, -1)):
    ax.add_patch(Rectangle((x0 if sgn > 0 else x0 - PROT, RAIL), PROT, L - 2 * RAIL,
                           facecolor=COLORS["band_2"], edgecolor=COLORS["accent_2"], lw=0.8, ls="--"))
ax.annotate("6.5 mm protrusion\nenvelope on ±X/±Y faces\n(between rails, stowed)", xy=(W + PROT, 260),
            xytext=(W + 30, 300), fontsize=7.5, color=COLORS["accent_2"], ha="left", va="center",
            arrowprops=dict(arrowstyle="-|>", color=COLORS["accent_2"], lw=0.9, mutation_scale=9))
# RBF pin access (on a side face, near the +Z end)
ax.add_patch(Rectangle((W - RAIL - 14, 300), 8, 8, facecolor="white", edgecolor=COLORS["accent_4"], lw=1.2))
ax.annotate("RBF pin access\n(accessible in the deployer)", xy=(W - RAIL - 6, 304), xytext=(W + 30, 225),
            fontsize=7.5, color=COLORS["accent_4"], ha="left", va="center",
            arrowprops=dict(arrowstyle="-|>", color=COLORS["accent_4"], lw=0.9, mutation_scale=9))
# CG limit box about the geometric centre
cx, cz = W / 2, L / 2
ax.add_patch(Rectangle((cx - 20, cz - 20), 40, 40, facecolor="none", edgecolor=COLORS["accent_3"],
                       lw=1.2, ls="--"))
ax.plot(cx, cz, marker="+", ms=9, color=COLORS["accent_3"], mew=1.2)
ax.annotate("CG within 2 cm of the\ngeometric centre", xy=(cx + 20, cz + 10), xytext=(W + 30, 140),
            fontsize=7.5, color=COLORS["accent_3"], ha="left", va="center",
            arrowprops=dict(arrowstyle="-|>", color=COLORS["accent_3"], lw=0.9, mutation_scale=9))
# rails label
ax.annotate("hard-anodised Al rails\n(4 ×, 8.5 × 8.5 mm)", xy=(RAIL / 2, 60), xytext=(-72, 60),
            fontsize=7.5, color=COLORS["ink"], ha="center", va="center",
            arrowprops=dict(arrowstyle="-|>", color=COLORS["ink"], lw=0.9, mutation_scale=9))
ax.annotate("rail-end contact pads\n(stand-offs)", xy=(RAIL / 2, L + 3), xytext=(-72, L + 20),
            fontsize=7.5, color=COLORS["ink"], ha="center", va="center",
            arrowprops=dict(arrowstyle="-|>", color=COLORS["ink"], lw=0.9, mutation_scale=9))
# dimensions
dim(ax, (-14, 0), (-14, L), "340.5", rot=90, offset=-6)
dim(ax, (0, L + 22), (W, L + 22), "100", offset=6)
# body axes
ax.add_patch(FancyArrowPatch((W + 30, 20), (W + 30, 70), arrowstyle="-|>", mutation_scale=10,
                             color=COLORS["grey"], lw=1))
ax.add_patch(FancyArrowPatch((W + 30, 20), (W + 80, 20), arrowstyle="-|>", mutation_scale=10,
                             color=COLORS["grey"], lw=1))
ax.text(W + 30, 76, "+Z", fontsize=8, color=COLORS["grey"], ha="center", va="bottom")
ax.text(W + 86, 20, "+X", fontsize=8, color=COLORS["grey"], ha="left", va="center")
ax.set_xlim(-112, W + 130)
ax.set_ylim(-60, L + 45)
ax.set_title("Side view (X–Z)", fontsize=9, pad=2)

# ------------------------------------------------------------------- end view
ax2.add_patch(Rectangle((0, 0), W, W, facecolor=BODY_COL, edgecolor=COLORS["ink"], lw=1.2))
for x in (0, W - RAIL):
    for y in (0, W - RAIL):
        ax2.add_patch(Rectangle((x, y), RAIL, RAIL, facecolor=RAIL_COL, edgecolor=COLORS["ink"], lw=0.8))
# protrusion envelopes on all four faces between the rails
ax2.add_patch(Rectangle((W, RAIL), PROT, W - 2 * RAIL, facecolor=COLORS["band_2"],
                        edgecolor=COLORS["accent_2"], lw=0.8, ls="--"))
ax2.add_patch(Rectangle((-PROT, RAIL), PROT, W - 2 * RAIL, facecolor=COLORS["band_2"],
                        edgecolor=COLORS["accent_2"], lw=0.8, ls="--"))
ax2.add_patch(Rectangle((RAIL, W), W - 2 * RAIL, PROT, facecolor=COLORS["band_2"],
                        edgecolor=COLORS["accent_2"], lw=0.8, ls="--"))
ax2.add_patch(Rectangle((RAIL, -PROT), W - 2 * RAIL, PROT, facecolor=COLORS["band_2"],
                        edgecolor=COLORS["accent_2"], lw=0.8, ls="--"))
# CG box (±X/±Y)
ax2.add_patch(Rectangle((W / 2 - 20, W / 2 - 20), 40, 40, facecolor="none",
                        edgecolor=COLORS["accent_3"], lw=1.2, ls="--"))
ax2.plot(W / 2, W / 2, marker="+", ms=9, color=COLORS["accent_3"], mew=1.2)
ax2.text(W / 2, W / 2 - 24, "CG box\n±20 mm", fontsize=7.5, color=COLORS["accent_3"],
         ha="center", va="top")
# dimensions
dim(ax2, (0, W + 22), (W, W + 22), "100", offset=6)
dim(ax2, (-20, 0), (-20, W), "100", rot=90, offset=-6)
dim(ax2, (W - RAIL, -22), (W, -22), "8.5", offset=-7)
dim(ax2, (W + 22, W - RAIL), (W + 22, W), "8.5", rot=90, offset=7)
ax2.annotate("6.5 mm", xy=(W + PROT, W / 2), xytext=(W + 24, W / 2 + 10), fontsize=7.5,
             color=COLORS["accent_2"], ha="left", va="center",
             arrowprops=dict(arrowstyle="-|>", color=COLORS["accent_2"], lw=0.9, mutation_scale=9))
ax2.text(W / 2, -40, "rails slide in the deployer guide channels;\nno protrusion beyond the rail "
         "envelope except\nthe 6.5 mm allowance between the rails", fontsize=7.5, ha="center",
         va="top", color=COLORS["ink"], style="italic")
ax2.text(W / 2, 84, "PC/104 stack inside", fontsize=7.5, color=COLORS["grey"], ha="center", va="center")
ax2.set_xlim(-45, W + 60)
ax2.set_ylim(-85, W + 40)
ax2.set_title("End view (X–Y), 1U cross-section", fontsize=9, pad=2)

fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.02, wspace=0.05)
save(fig, Path(__file__).stem)
