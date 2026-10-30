"""EOSat-3U mode-transition state machine (Chapter 18 §18.2.2): Detumble, Nominal
(standby), Imaging, Downlink, Eclipse and Safe, with the transition conditions.
Safe is reachable from every state by a fault and is left only by ground command."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from oer_style import apply_style, COLORS, save

apply_style()
fig = plt.figure(figsize=(7.15, 5.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_axis_off()
ax.grid(False)

FAULT = COLORS["accent_2"]
GND = COLORS["accent_3"]
INK = COLORS["ink"]

states = {
    "Detumble": (50, 88, 22, 9, COLORS["accent_4"], "magnetorquers only"),
    "Nominal": (50, 65, 24, 11, COLORS["accent"], "standby, Sun-pointing, 4.0 W"),
    "Imaging": (22, 42, 16, 10, COLORS["accent"], "fine pointing, 8.0 W"),
    "Eclipse": (50, 42, 16, 10, COLORS["accent_6"], "reduced ops, 3.5 W"),
    "Downlink": (78, 42, 16, 10, COLORS["accent"], "S-band, 10.0 W"),
}
box = {}
for name, (x, y, w, h, c, sub) in states.items():
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=1.2",
                                facecolor="#ffffff", edgecolor=c, lw=1.6, zorder=3))
    ax.text(x, y + 1.6, name.upper() if name != "Nominal" else "NOMINAL", ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=c, zorder=4)
    ax.text(x, y - 1.9, sub, ha="center", va="center", fontsize=8, color=COLORS["grey"], zorder=4)
    box[name] = (x - w / 2, x + w / 2, y - h / 2, y + h / 2)  # left, right, bottom, top

# Safe mode bar
sx0, sx1, sy, sh = 7, 93, 11, 9
ax.add_patch(FancyBboxPatch((sx0, sy - sh / 2), sx1 - sx0, sh, boxstyle="round,pad=0.02,rounding_size=1.2",
                            facecolor=COLORS["band_2"], edgecolor=FAULT, lw=1.8, zorder=3))
ax.text(50, sy + 1.6, "SAFE MODE", ha="center", va="center", fontsize=9.5, fontweight="bold",
        color=FAULT, zorder=4)
ax.text(50, sy - 1.9, "survival only, magnetic Sun-pointing, beacon, 2.0 W — holds until the ground intervenes",
        ha="center", va="center", fontsize=8, color=COLORS["grey"], zorder=4)


def arrow(p0, p1, color=INK, rad=0.0, lw=1.3, ls="-", style="-|>"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=12, color=color, lw=lw,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}", zorder=2,
                                 shrinkA=0, shrinkB=0))


def label(x, y, s, color=INK, ha="center", va="center", **kw):
    ax.text(x, y, s, fontsize=8, color=color, ha=ha, va=va, zorder=5,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"), **kw)


# separation → Detumble
arrow((50, 99), (50, box["Detumble"][3]))
label(52, 96.5, "separation from deployer", ha="left")

# Detumble → Nominal
arrow((50, box["Detumble"][2]), (50, box["Nominal"][3]))
label(52, 77, "angular rate < threshold", ha="left")

# Nominal ↔ Imaging
arrow((42, box["Nominal"][2]), (22, box["Imaging"][3]), rad=0.25)
arrow((27, box["Imaging"][3]), (46, box["Nominal"][2]), rad=0.25)
label(26, 56.5, "schedule, SoC > limit")
label(37, 49, "complete")

# Nominal ↔ Downlink
arrow((58, box["Nominal"][2]), (78, box["Downlink"][3]), rad=-0.25)
arrow((73, box["Downlink"][3]), (54, box["Nominal"][2]), rad=-0.25)
label(74, 56.5, "station in view, link up")
label(63, 49, "complete / LOS")

# Nominal ↔ Eclipse
arrow((48.5, box["Nominal"][2]), (48.5, box["Eclipse"][3]))
arrow((51.5, box["Eclipse"][3]), (51.5, box["Nominal"][2]))
label(47, 53.5, "Sun not\nin view", ha="right", linespacing=1.1)
label(53, 53.5, "Sun in\nview", ha="left", linespacing=1.1)

# Imaging / Downlink → Eclipse
arrow((box["Imaging"][1], 42), (box["Eclipse"][0], 42))
arrow((box["Downlink"][0], 42), (box["Eclipse"][1], 42))
label(36, 45.2, "Sun not\nin view", linespacing=1.1)
label(64, 45.2, "Sun not\nin view", linespacing=1.1)

# faults → Safe (every state)
for name, x in [("Imaging", 22), ("Eclipse", 50), ("Downlink", 78)]:
    arrow((x, box[name][2]), (x, sy + sh / 2), color=FAULT)
    label(x + 1.2, 27, "fault", color=FAULT, ha="left")
# Nominal fault: right-hand rail
arrow((box["Nominal"][1], 65), (96, 65), color=FAULT, style="-")
arrow((96, 65), (96, sy), color=FAULT, style="-")
arrow((96, sy), (sx1, sy), color=FAULT)
label(97, 40, "fault", color=FAULT, ha="left", rotation=90)
# Detumble fault: left-hand rail
arrow((box["Detumble"][0], 88), (4, 88), color=FAULT, style="-")
arrow((4, 88), (4, sy), color=FAULT, style="-")
arrow((4, sy), (sx0, sy), color=FAULT)
label(3, 50, "fault", color=FAULT, ha="right", rotation=90)

# Safe → Nominal: ground command only (right side, inside the fault rail)
arrow((91, sy + sh / 2), (91, 69), color=GND, style="-", ls="--", lw=1.4)
arrow((91, 69), (box["Nominal"][1], 69), color=GND, ls="--", lw=1.4)
label(92.3, 60, "ground command only", color=GND, ha="left", rotation=90)
# Safe → Detumble: rate limit exceeded (left side)
arrow((9, sy + sh / 2), (9, 92), color=COLORS["accent_4"], style="-", ls="--", lw=1.2)
arrow((9, 92), (box["Detumble"][0], 92), color=COLORS["accent_4"], ls="--", lw=1.2)
label(7.7, 60, "rate limit exceeded", color=COLORS["accent_4"], ha="right", rotation=90)

save(fig, Path(__file__).stem)
