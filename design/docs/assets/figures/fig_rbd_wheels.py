"""Reliability block diagrams for the reaction-wheel example of Chapter 15 §15.4.6:
three wheels in series (R = 0.98 each) versus four wheels in a 3-of-4 voting block."""
from math import comb
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from oer_style import apply_style, COLORS, save

apply_style()
R = 0.98
R_series = R ** 3
R_3of4 = sum(comb(4, i) * R ** i * (1 - R) ** (4 - i) for i in range(3, 5))

fig = plt.figure(figsize=(7.05, 3.45))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(-1, 48)
ax.set_axis_off()
ax.grid(False)

BW, BH = 9.5, 6.0


def block(x, y, label, sub, color=COLORS["accent"]):
    ax.add_patch(FancyBboxPatch((x - BW / 2, y - BH / 2), BW, BH, boxstyle="round,pad=0.02,rounding_size=0.8",
                                facecolor="#ffffff", edgecolor=color, lw=1.5, zorder=3))
    ax.text(x, y + 1.0, label, ha="center", va="center", fontsize=9, fontweight="bold", zorder=4)
    ax.text(x, y - 1.5, sub, ha="center", va="center", fontsize=8.5, color=COLORS["grey"], zorder=4)


def wire(p0, p1, arrow=False, color=COLORS["ink"]):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>" if arrow else "-", mutation_scale=10,
                                 color=color, lw=1.2, zorder=2, shrinkA=0, shrinkB=0))


def node(x, y):
    ax.add_patch(Circle((x, y), 0.7, facecolor=COLORS["ink"], edgecolor="none", zorder=4))


# ---------------- Configuration A: series ----------------
yA = 28
xs = [10.5, 23, 35.5]
ax.text(23, 44, "Configuration A: three wheels in series", ha="center", va="center",
        fontsize=10, fontweight="bold")
ax.text(23, 40.5, "all three must work (series)", ha="center", va="center", fontsize=8.5,
        color=COLORS["grey"], style="italic")
wire((2, yA), (xs[0] - BW / 2, yA))
for k, x in enumerate(xs):
    block(x, yA, f"Wheel {k + 1}", f"R = {R:.2f}")
    if k < 2:
        wire((x + BW / 2, yA), (xs[k + 1] - BW / 2, yA))
wire((xs[-1] + BW / 2, yA), (44, yA), arrow=True)
node(2, yA)
ax.text(23, 16, r"$R_{\rm system} = R^3 = 0.98^3$" + f" = {R_series:.3f}", ha="center", va="center",
        fontsize=10, color=COLORS["accent"])
ax.text(23, 11.5, "one wheel failure ends 3-axis control", ha="center", va="center", fontsize=8.5,
        color=COLORS["grey"], style="italic")

# ---------------- Configuration B: 3-of-4 ----------------
x0, x1 = 54, 96          # input / output bus x
xb = 71                  # block centre x
ax.text(75, 44, "Configuration B: four wheels, 3-of-4 voting", ha="center", va="center",
        fontsize=10, fontweight="bold")
ax.text(75, 40.5, "any three of the four must work (k-of-n)", ha="center", va="center",
        fontsize=8.5, color=COLORS["grey"], style="italic")
ys = [36, 29, 22, 15]
# input bus
wire((x0, ys[-1]), (x0, ys[0]))
wire((50, ys[1] + 3.5), (x0, ys[1] + 3.5))
node(50, ys[1] + 3.5)
for k, y in enumerate(ys):
    wire((x0, y), (xb - BW / 2, y))
    block(xb, y, f"Wheel {k + 1}", f"R = {R:.2f}", color=COLORS["accent_3"])
    wire((xb + BW / 2, y), (84, y))
# voting gate
gx, gy = 88, (ys[0] + ys[-1]) / 2
ax.add_patch(FancyBboxPatch((gx - 4, gy - 11.5), 8, 23, boxstyle="round,pad=0.02,rounding_size=1.0",
                            facecolor=COLORS["band"], edgecolor=COLORS["accent_3"], lw=1.5, zorder=3))
ax.text(gx, gy, "3\nof\n4", ha="center", va="center", fontsize=10, fontweight="bold",
        color=COLORS["accent_3"], zorder=4, linespacing=1.1)
for y in ys:
    wire((84, y), (gx - 4, y))
wire((gx + 4, gy), (99, gy), arrow=True)
ax.text(73, 7.5, r"$R_{\rm system} = R^4 + 4R^3(1-R) = 0.9224 + 0.0753$" + f" = {R_3of4:.4f} ≈ {R_3of4:.3f}",
        ha="center", va="center", fontsize=9.2, color=COLORS["accent_3"])
ax.text(73, 2.8, "one wheel may fail: any three of the four span all three axes\n(pyramid geometry, Chapter 10 §10.3)",
        ha="center", va="center", fontsize=8.5, color=COLORS["grey"], style="italic")

# divider
ax.plot([48.5, 48.5], [10, 46], color=COLORS["grey_light"], lw=0.8, ls="--")
print(f"R_series={R_series:.4f}  R_3of4={R_3of4:.4f}")
save(fig, Path(__file__).stem)
