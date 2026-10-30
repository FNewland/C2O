"""Ground-segment block diagram (Chapter 17 §17.1.1): the five functional blocks
joined by a data network, the RF interface to the space segment and the product
interface to the user segment."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse
from oer_style import apply_style, COLORS, save

apply_style()
fig = plt.figure(figsize=(7.15, 4.8))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_axis_off()
ax.grid(False)


def block(x, y, w, h, title, lines, color=COLORS["accent"], fill="#ffffff", top_off=8.0):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=1.0",
                                facecolor=fill, edgecolor=color, lw=1.5, zorder=3))
    ax.text(x, y + h / 2 - 1.8, title, ha="center", va="top", fontsize=9, fontweight="bold",
            color=color, zorder=4, linespacing=1.1)
    if lines:
        ax.text(x - w / 2 + 2.0, y + h / 2 - top_off, "\n".join("• " + l for l in lines), ha="left",
                va="top", fontsize=8, zorder=4, linespacing=1.25)


def arrow(p0, p1, color=COLORS["ink"], style="-|>", lw=1.3, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=11, color=color, lw=lw,
                                 linestyle=ls, zorder=2, shrinkA=0, shrinkB=0))


# ground-segment boundary
ax.add_patch(FancyBboxPatch((3, 5), 82, 74, boxstyle="round,pad=0.02,rounding_size=1.5",
                            facecolor="#fafafa", edgecolor=COLORS["grey"], lw=1.0, ls="--", zorder=1))
ax.text(83, 77.5, "GROUND SEGMENT", fontsize=9, fontweight="bold", color=COLORS["grey"], va="top", ha="right")

# top row
block(19, 60, 28, 30, "Ground-station network",
      ["Antenna(s)", "RF front-end (LNA, PA)", "Modem / baseband", "Tracking (Doppler, pointing)",
       "Data capture", "Timing (GPS-disciplined)"], color=COLORS["accent_2"])
block(50, 60, 26, 30, "Mission control\nsystem (MCS)",
      ["Telemetry processing", "Telecommand generation", "Scheduling", "Monitoring, limit checks",
       "Anomaly management"])
block(76, 60, 15, 30, "Flight\ndynamics\n(FDS)",
      ["Orbit\n  determination", "Orbit\n  prediction", "Manoeuvre\n  planning", "Conjunction\n  assessment"],
      color=COLORS["accent_4"], top_off=11.0)

# data network bus
yb = 36
ax.add_patch(FancyBboxPatch((8, yb - 1.6), 74, 3.2, boxstyle="round,pad=0.02,rounding_size=1.0",
                            facecolor=COLORS["band"], edgecolor=COLORS["accent"], lw=1.0, zorder=2))
ax.text(45, yb, "Data network (LAN / VPN between sites)", ha="center", va="center", fontsize=8.5,
        color=COLORS["accent"], zorder=4)
for x in [19, 50, 76]:
    arrow((x, 60 - 15), (x, yb + 1.6), style="<|-|>")

# bottom row
block(25, 20, 30, 20, "Mission planning system",
      ["Pass scheduling", "Resource planning (power, data)", "Conflict resolution"],
      color=COLORS["accent_3"])
block(62, 20, 30, 20, "Data processing and archive",
      ["Level 0–2 processing", "Archive / catalogue", "Distribution to users"],
      color=COLORS["accent_5"])
for x in [25, 62]:
    arrow((x, yb - 1.6), (x, 20 + 10), style="<|-|>")

# space segment (RF interface)
ax.add_patch(Ellipse((19, 94), 24, 9, facecolor=COLORS["band_2"], edgecolor=COLORS["accent_2"],
                     lw=1.2, zorder=3))
ax.text(19, 94, "Space segment\n(spacecraft)", ha="center", va="center", fontsize=8.5, zorder=4,
        linespacing=1.1)
arrow((19, 89.5), (19, 60 + 15), style="<|-|>", color=COLORS["accent_2"], lw=1.6)
ax.text(21, 84.5, "RF interface: telecommand up,\ntelemetry and payload data down", ha="left", va="center", fontsize=8,
        color=COLORS["accent_2"], linespacing=1.15)

# user segment (product interface)
ax.add_patch(Ellipse((93, 20), 12, 14, facecolor="#f3f3f3", edgecolor=COLORS["accent_5"],
                     lw=1.2, zorder=3))
ax.text(93, 20, "User\nsegment", ha="center", va="center", fontsize=8.5, zorder=4, linespacing=1.1)
arrow((62 + 15, 20), (87, 20), color=COLORS["accent_5"], lw=1.6)
ax.text(82, 23.2, "products", ha="center", va="bottom", fontsize=8, color=COLORS["accent_5"])
save(fig, Path(__file__).stem)
