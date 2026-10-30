"""Standard CubeSat work breakdown structure (Chapter 16 §16.2.1): Mission Total
branching to the ten Level-1 elements with their typical share of total cost,
and 5.0 Spacecraft Bus Hardware expanded to 5.1–5.8."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
from oer_style import apply_style, COLORS, save

apply_style()
fig = plt.figure(figsize=(7.15, 5.1))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_axis_off()
ax.grid(False)

groups = {
    "mgmt": ("Management (1–3)", COLORS["accent_5"]),
    "space": ("Space segment (4–6)", COLORS["accent"]),
    "sw": ("Software (7)", COLORS["accent_4"]),
    "launch": ("Launch (8)", COLORS["accent_2"]),
    "ground": ("Ground and operations (9–10)", COLORS["accent_3"]),
}
level1 = [
    ("1.0", "Programme\nManagement", 5, "mgmt"),
    ("2.0", "Systems\nEngineering", 5, "mgmt"),
    ("3.0", "Mission\nAssurance", 3, "mgmt"),
    ("4.0", "Payload", 20, "space"),
    ("5.0", "Spacecraft\nBus Hardware", 27, "space"),
    ("6.0", "Integration\nand Test", 12, "space"),
    ("7.0", "Software\n(flight + ground)", 8, "sw"),
    ("8.0", "Launch\nServices", 10, "launch"),
    ("9.0", "Ground\nSegment", 5, "ground"),
    ("10.0", "Operations", 5, "ground"),
]
level2 = [
    ("5.1", "Structure and\nmechanisms"), ("5.2", "EPS (array,\nbattery, board)"),
    ("5.3", "AOCS (sensors\n+ actuators)"), ("5.4", "TT&C (radio\n+ antenna)"),
    ("5.5", "OBC and data\nhandling"), ("5.6", "Thermal\ncontrol"),
    ("5.7", "Propulsion\n(if applicable)"), ("5.8", "Harness and\ncabling"),
]


def box(x, y, w, h, color, title, body, pct=None, fill=True):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.8",
                                facecolor=color if fill else "#ffffff", edgecolor=color, lw=1.3, zorder=3))
    tc = "#ffffff" if fill else COLORS["ink"]
    ax.text(x, y + h / 2 - 1.6, title, ha="center", va="top", fontsize=8.5, fontweight="bold",
            color=tc, zorder=4)
    ax.text(x, y + (0.5 if pct is not None else 0), body, ha="center", va="center", fontsize=8,
            color=tc, zorder=4, linespacing=1.1)
    if pct is not None:
        ax.text(x, y - h / 2 + 1.5, f"{pct} %", ha="center", va="bottom", fontsize=8.5,
                fontweight="bold", color=tc, zorder=4)


# root
box(50, 91, 24, 9, COLORS["ink"], "Mission Total", "", None)
ax.text(50, 91 - 1.2, "100 %", ha="center", va="center", fontsize=8.5, color="#ffffff", zorder=4)

# level 1 row — staggered on two rows so that the names fit at 8 pt
n1 = len(level1)
W1, H1 = 16.5, 14
xs1 = [9.5 + i * 9.0 for i in range(n1)]
y_up, y_dn = 69, 51
ybus = 80
ax.plot([50, 50], [91 - 4.5, ybus], color=COLORS["ink"], lw=1.0, zorder=2)
ax.plot([xs1[0], xs1[-1]], [ybus, ybus], color=COLORS["ink"], lw=1.0, zorder=2)
for i, (x, (num, name, pct, g)) in enumerate(zip(xs1, level1)):
    y1 = y_up if i % 2 == 0 else y_dn
    ax.plot([x, x], [ybus, y1 + H1 / 2], color=COLORS["ink"], lw=1.0, zorder=2)
    box(x, y1, W1, H1, groups[g][1], num, name, pct)

# level 2 row (children of 5.0)
n2 = len(level2)
W2, H2 = 11.0, 12
xs2 = [2 + W2 / 2 + i * (96 / n2) for i in range(n2)]
y2 = 25
x5 = xs1[4]
ybus2 = y2 + H2 / 2 + 5
ax.plot([x5, x5], [y_up - H1 / 2, ybus2], color=COLORS["accent"], lw=1.0, zorder=2)
ax.plot([xs2[0], xs2[-1]], [ybus2, ybus2], color=COLORS["accent"], lw=1.0, zorder=2)
for x, (num, name) in zip(xs2, level2):
    ax.plot([x, x], [ybus2, y2 + H2 / 2], color=COLORS["accent"], lw=1.0, zorder=2)
    box(x, y2, W2, H2, COLORS["accent"], num, name, None, fill=False)
ax.text(x5 + 1.2, (y_dn - H1 / 2 + ybus2) / 2 - 0.5, "Level 2 of 5.0", fontsize=8, color=COLORS["accent"],
        va="center", ha="left", style="italic")

# legend
handles = [Patch(color=c, label=l) for l, c in groups.values()]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=5, fontsize=8,
          handlelength=1.2, columnspacing=1.2, frameon=False)
ax.text(50, 11, "Percentages are a typical starting allocation for a university or small-company CubeSat;\n"
        "4.0, 6.0 and 7.0 also have Level-2 elements (not shown).",
        ha="center", va="center", fontsize=8, style="italic", color=COLORS["grey"])

save(fig, Path(__file__).stem)
