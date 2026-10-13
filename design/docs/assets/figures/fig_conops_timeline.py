"""ConOps timeline — LEOP → Commissioning → Nominal → Disposal."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()
fig, ax = plt.subplots(figsize=(11.5, 3.6))
ax.set_xlim(-0.5, 18)
ax.set_ylim(2.8, 7.4)
ax.axis("off")
ax.set_title("Mission operations timeline (representative LEO mission)", pad=6)

phases = [
    ("LEOP",          0.5, 1.7, COLORS["accent_2"], "Days 0–7",
     "Sequential power-on,\nantenna deploy,\nfirst contact, detumble"),
    ("Commissioning", 2.4, 3.4, COLORS["accent_3"], "Weeks 1–6",
     "Subsystem checkouts,\npayload calibration,\nfirst light"),
    ("Nominal operations", 6.0, 8.4, COLORS["accent"], "Years 1–N",
     "Pass planning, imaging, downlink,\nmomentum management,\nanomaly response"),
    ("EOL / disposal", 14.6, 2.2, COLORS["grey"], "≤ 25-yr clock",
     "De-orbit burn /\npassivation;\ndecay clock starts"),
]
y0, h = 5.3, 1.6
for name, x, w, color, dur, txt in phases:
    box = FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.04",
                         linewidth=0, facecolor=color, alpha=0.92)
    ax.add_patch(box)
    ax.text(x + w / 2, y0 + h * 0.65, name, ha="center", va="center",
            color="white", fontweight="bold", fontsize=9.5)
    ax.text(x + w / 2, y0 + h * 0.25, dur, ha="center", va="center",
            color="white", fontsize=8.0, style="italic")
    cx = x + w / 2
    ax.plot([cx, cx], [y0, 3.9], color=color, lw=0.8, alpha=0.6, zorder=0)
    ax.text(cx, 3.75, txt, ha="center", va="top", fontsize=8,
            color=color, linespacing=1.3, clip_on=True)

# Time arrow between the band and the activity text
ax.annotate("", xy=(17.4, 4.6), xytext=(0.3, 4.6),
            arrowprops=dict(arrowstyle="->", color=COLORS["ink"], lw=1.0))
ax.text(17.4, 4.75, "time", color=COLORS["grey"], fontsize=8.5, ha="right")

save(fig, Path(__file__).stem)
