"""Four-wheel reaction-wheel pyramid geometry (Ch 10 §10.3.2).

Left: isometric view of the body frame with the four wheel spin axes, each
raised by the cant angle β above the body X–Y plane and spaced 90° in azimuth
(along +X, +Y, −X, −Y), as in the distribution matrix D of §10.3.2 whose
columns are (±cos β, 0, sin β) and (0, ±cos β, sin β). Right: view along +Z
showing the 90° azimuth spacing. Drawn for β = 30°.
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Arc, FancyArrowPatch
from oer_style import apply_style, COLORS, save

apply_style()

beta = np.radians(30)
cb, sb = np.cos(beta), np.sin(beta)
# wheel spin axes (unit vectors) — columns of D
axes = [np.array([cb, 0, sb]), np.array([0, cb, sb]), np.array([-cb, 0, sb]), np.array([0, -cb, sb])]
cols = [COLORS["accent"], COLORS["accent_2"], COLORS["accent_3"], COLORS["accent_4"]]
names = ["w1", "w2", "w3", "w4"]


AZ, EL = np.radians(-30), np.radians(25)


def iso(v):
    """Oblique projection: rotate about Z by AZ, then tilt by elevation EL."""
    x, y, z = v
    xr = x * np.cos(AZ) - y * np.sin(AZ)
    yr = x * np.sin(AZ) + y * np.cos(AZ)
    return np.array([xr, z * np.cos(EL) + yr * np.sin(EL)])


fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.8), gridspec_kw={"width_ratios": [1.5, 1]})
for a in (ax, ax2):
    a.set_aspect("equal")
    a.axis("off")

# ---------------- left: isometric ------------------------------------------
L = 1.9
o = iso([0, 0, 0])
for v, lab, off in [([L, 0, 0], "X", (0.14, -0.02)), ([0, L, 0], "Y", (0.12, 0.08)),
                    ([0, 0, 1.6], "Z", (0, 0.12))]:
    p = iso(v)
    ax.add_patch(FancyArrowPatch(o, p, arrowstyle="-|>", mutation_scale=12,
                                 color=COLORS["ink"], lw=1.2))
    ax.text(p[0] + off[0], p[1] + off[1], lab, fontsize=10, fontweight="bold",
            ha="center", va="center")
# faint body X–Y plane outline
sq = [iso(v) for v in ([L, L, 0], [-L, L, 0], [-L, -L, 0], [L, -L, 0], [L, L, 0])]
ax.plot([p[0] for p in sq], [p[1] for p in sq], color=COLORS["grey_light"], lw=0.8, ls="--")

R = 1.55
for v, c, n in zip(axes, cols, names):
    tip = iso(R * v)
    foot = iso(R * np.array([v[0], v[1], 0]))
    # projection onto the X–Y plane (dashed) and vertical riser
    ax.plot([o[0], foot[0]], [o[1], foot[1]], color=c, lw=0.9, ls=":")
    ax.plot([foot[0], tip[0]], [foot[1], tip[1]], color=c, lw=0.9, ls=":")
    ax.add_patch(FancyArrowPatch(o, tip, arrowstyle="-|>", mutation_scale=13, color=c, lw=2.0))
    # wheel disc perpendicular to the axis, drawn as an ellipse at the tip
    disc = iso(1.15 * v)
    ang = np.degrees(np.arctan2(tip[1] - o[1], tip[0] - o[0]))
    ax.add_patch(Ellipse(disc, 0.42, 0.16, angle=ang + 90, facecolor=c, alpha=0.35,
                         edgecolor=c, lw=1.0))
    lab = iso(1.85 * v)
    ax.text(lab[0], lab[1], n, color=c, fontsize=9, fontweight="bold", ha="center", va="center")

# cant-angle arc for wheel 1 (in the X–Z plane) and wheel 2 (Y–Z plane)
for v, c, txt in [(axes[0], cols[0], "β"), (axes[1], cols[1], "β")]:
    pts = [iso(0.75 * np.array([np.cos(t) * v[0] / cb, np.cos(t) * v[1] / cb, np.sin(t)]))
           for t in np.linspace(0, beta, 20)]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c, lw=1.0)
    mid = iso(0.95 * np.array([np.cos(beta / 2) * v[0] / cb, np.cos(beta / 2) * v[1] / cb,
                               np.sin(beta / 2)]))
    ax.text(mid[0], mid[1], txt, color=c, fontsize=9, ha="center", va="center", style="italic")

ax.set_xlim(-2.3, 2.3)
ax.set_ylim(-1.3, 1.9)
ax.set_title("Four-wheel pyramid, cant angle β above the X–Y plane", fontsize=9, pad=4)

# ---------------- right: top view along +Z ---------------------------------
r = 1.3
for v, c, n in zip(axes, cols, names):
    tip = r * np.array([v[0], v[1]]) / cb
    ax2.add_patch(FancyArrowPatch((0, 0), tip, arrowstyle="-|>", mutation_scale=12, color=c, lw=2.0))
    perp = np.array([-tip[1], tip[0]]) / np.linalg.norm(tip)
    lp = tip * 0.85 + 0.28 * perp
    ax2.text(lp[0], lp[1], n, color=c, fontsize=9, fontweight="bold", ha="center", va="center")
ax2.add_patch(Arc((0, 0), 1.2, 1.2, theta1=0, theta2=90, color=COLORS["grey"], lw=1.0))
ax2.text(0.55, 0.55, "90°", fontsize=8, color=COLORS["grey"], ha="center", va="center")
ax2.plot([-1.75, 1.75], [0, 0], color=COLORS["grey_light"], lw=0.8, zorder=0)
ax2.plot([0, 0], [-1.75, 1.75], color=COLORS["grey_light"], lw=0.8, zorder=0)
ax2.text(1.8, 0, "+X", fontsize=8.5, fontweight="bold", ha="left", va="center")
ax2.text(0, 1.8, "+Y", fontsize=8.5, fontweight="bold", ha="center", va="bottom")
ax2.plot(0, 0, marker="o", ms=5, color=COLORS["ink"])
ax2.text(0.12, -0.2, "+Z out of page", fontsize=7, color=COLORS["grey"], va="top")
ax2.set_xlim(-2.1, 2.3)
ax2.set_ylim(-2.0, 2.1)
ax2.set_title("View along +Z: azimuths 90° apart", fontsize=9, pad=4)

# D-matrix columns under the panels
fig.text(0.5, 0.02,
         "Columns of the distribution matrix D (wheel spin axes in the body frame):\n"
         "w1 = (cos β, 0, sin β)     w2 = (0, cos β, sin β)     w3 = (−cos β, 0, sin β)     w4 = (0, −cos β, sin β)",
         fontsize=7.5, va="bottom", ha="center", color=COLORS["ink"])
fig.subplots_adjust(bottom=0.17, top=0.9, left=0.02, right=0.98, wspace=0.05)

save(fig, Path(__file__).stem)
