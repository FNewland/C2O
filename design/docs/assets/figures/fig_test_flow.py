"""Environmental test sequence for a proto-flight CubeSat (Chapter 14 §14.3.1)
drawn as a vertical flowchart with the post-vibration anomaly loop and the
qualification / acceptance / proto-flight levels annotated beside the
vibration and thermal-vacuum steps."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
from oer_style import apply_style, COLORS, save

apply_style()
fig = plt.figure(figsize=(7.15, 8.2))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_axis_off()
ax.grid(False)

XC = 30          # main column centre
W, H = 34, 4.6   # box width / height
steps = [
    ("Receive flight hardware", "term"),
    ("Initial functional test (baseline)", "func"),
    ("Sine vibration, 3 axes", "env"),
    ("Random vibration, 3 axes", "env"),
    ("Post-vibration functional test", "func"),
    ("Anomaly?", "dec"),
    ("Thermal vacuum, 4 cycles\n(functional test at each extreme)", "env"),
    ("Post-TVAC functional test", "func"),
    ("EMC test (if required)", "env"),
    ("Mass and CG measurement", "meas"),
    ("Deployer fit check", "meas"),
    ("Final functional test", "func"),
    ("Pack and ship to launch site", "term"),
]
face = {"term": COLORS["band"], "func": "#ffffff", "env": COLORS["band_2"],
        "meas": "#ffffff", "dec": "#ffffff"}
edge = {"term": COLORS["accent"], "func": COLORS["accent"], "env": COLORS["accent_2"],
        "meas": COLORS["grey"], "dec": COLORS["accent_4"]}

n = len(steps)
top, bottom = 95.5, 4.5
gaps = [1.0] * (n - 1)
gaps[4] = 0.95          # functional → decision
gaps[5] = 1.35          # decision → TVAC (taller box, "no" label)
cum = [0.0]
for g in gaps:
    cum.append(cum[-1] + g)
ys = [top - c * (top - bottom) / cum[-1] for c in cum]
ypos = {}

for (label, kind), y in zip(steps, ys):
    ypos[label] = y
    if kind == "dec":
        d = Polygon([(XC - 13, y), (XC, y + 3.2), (XC + 13, y), (XC, y - 3.2)], closed=True,
                    facecolor=face[kind], edgecolor=edge[kind], lw=1.4, zorder=3)
        ax.add_patch(d)
        ax.text(XC, y, label, ha="center", va="center", fontsize=9, fontweight="bold",
                color=edge[kind], zorder=4)
        continue
    hh = H + (1.6 if "\n" in label else 0)
    box = FancyBboxPatch((XC - W / 2, y - hh / 2), W, hh,
                         boxstyle="round,pad=0.02,rounding_size=1.2" if kind == "term"
                         else "square,pad=0.02",
                         facecolor=face[kind], edgecolor=edge[kind], lw=1.4, zorder=3)
    ax.add_patch(box)
    ax.text(XC, y, label, ha="center", va="center", fontsize=9, zorder=4, linespacing=1.15)

# vertical connectors
for i in range(n - 1):
    y0 = ys[i] - (H / 2 if steps[i][1] != "dec" else 3.2) - (0.8 if "\n" in steps[i][0] else 0)
    y1 = ys[i + 1] + (H / 2 if steps[i + 1][1] != "dec" else 3.2) + (0.8 if "\n" in steps[i + 1][0] else 0)
    ax.add_patch(FancyArrowPatch((XC, y0), (XC, y1), arrowstyle="-|>", mutation_scale=11,
                                 color=COLORS["ink"], lw=1.1, zorder=2, shrinkA=0, shrinkB=0))
# "no" label on the decision exit
yd = ypos["Anomaly?"]
ax.text(XC + 1.2, yd - 4.6, "no", fontsize=8.5, va="center", ha="left", color=COLORS["grey"])

# anomaly loop: decision → investigate (right) → back to post-vibration functional
yf = ypos["Post-vibration functional test"]
xr = 62
ax.add_patch(FancyBboxPatch((xr - 11, yd - H / 2), 22, H, boxstyle="square,pad=0.02",
                            facecolor="#ffffff", edgecolor=COLORS["accent_4"], lw=1.4, zorder=3))
ax.text(xr, yd, "Investigate and\nresolve", ha="center", va="center", fontsize=9, zorder=4,
        linespacing=1.15)
ax.add_patch(FancyArrowPatch((XC + 13, yd), (xr - 11, yd), arrowstyle="-|>", mutation_scale=11,
                             color=COLORS["accent_4"], lw=1.2, zorder=2, shrinkA=0, shrinkB=0))
ax.text((XC + 13 + xr - 11) / 2, yd + 1.1, "yes", fontsize=8.5, ha="center", va="bottom",
        color=COLORS["accent_4"])
# return path: up from the box, then left into the functional-test box
ax.add_patch(FancyArrowPatch((xr, yd + H / 2), (xr, yf), arrowstyle="-", color=COLORS["accent_4"],
                             lw=1.2, zorder=2, shrinkA=0, shrinkB=0))
ax.add_patch(FancyArrowPatch((xr, yf), (XC + W / 2, yf), arrowstyle="-|>", mutation_scale=11,
                             color=COLORS["accent_4"], lw=1.2, zorder=2, shrinkA=0, shrinkB=0))
ax.text(xr + 1.2, (yd + H / 2 + yf) / 2, "re-test", fontsize=8.5, ha="left", va="center",
        color=COLORS["accent_4"])

# ---- level annotations (Chapter 14 §14.2.2 table and §14.3.4)
def note(y, title, lines):
    x0 = 52
    ax.plot([XC + W / 2 + 0.8, x0 - 1.2], [y, y], color=COLORS["accent_2"], lw=0.8, ls=":")
    ax.text(x0, y + 0.3, title, fontsize=8.5, fontweight="bold", va="bottom", ha="left",
            color=COLORS["accent_2"])
    ax.text(x0, y - 0.6, lines, fontsize=8, va="top", ha="left", linespacing=1.25)


yv = (ypos["Sine vibration, 3 axes"] + ypos["Random vibration, 3 axes"]) / 2
note(yv, "Vibration levels",
     "Qualification: MPE + 3 dB, 2 min per axis\n"
     "Acceptance: MPE, 1 min per axis\n"
     "Proto-flight: MPE + 3 dB, 1 min per axis")
yt = ypos["Thermal vacuum, 4 cycles\n(functional test at each extreme)"]
note(yt, "Thermal-vacuum levels",
     "Qualification: predicted ± 15 °C, 8 cycles\n"
     "Acceptance: predicted ± 10 °C, 4 cycles\n"
     "Proto-flight: predicted ± 10 °C, 4 cycles\n"
     "Vacuum < 10⁻⁵ mbar; ≥ 1 h dwell at each extreme")

# legend of box types
lx, ly = 52, 22
items = [("Environmental test", "env"), ("Functional test", "func"), ("Measurement / inspection", "meas")]
for k, (lab, kind) in enumerate(items):
    yy = ly - k * 3.2
    ax.add_patch(FancyBboxPatch((lx, yy - 1.0), 5, 2.0, boxstyle="square,pad=0",
                                facecolor=face[kind], edgecolor=edge[kind], lw=1.2))
    ax.text(lx + 6.5, yy, lab, fontsize=8.5, va="center")
ax.text(lx, ly - 3 * 3.2 - 0.8, "MPE = maximum predicted environment", fontsize=8,
        style="italic", color=COLORS["grey"], va="center")

save(fig, Path(__file__).stem)
