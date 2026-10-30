"""Requirement hierarchy tree for the agricultural-monitoring EO mission (Ch 5 §5.4.1).

Stakeholder need → mission requirement MR-001 → system requirements
(SR-PL-001, SR-AOCS-001, SR-LINK-001) → subsystem requirements
(SSR-PL-001a, SSR-AOCS-001a, SSR-LINK-001a) → component level, with the
requirement texts of §5.4.1 and the level definitions of §5.4.2.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()

fig, ax = plt.subplots(figsize=(7.5, 6.0))
ax.set_xlim(0, 15)
ax.set_ylim(0, 12.6)
ax.axis("off")


def node(x, y, w, h, head, body, col, filled=True, fs=7.2, dashed=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                facecolor=col if filled else "white", edgecolor=col,
                                linewidth=1.3, linestyle="--" if dashed else "-", zorder=2))
    tc = "white" if filled else COLORS["ink"]
    ax.text(x + 0.18, y + h - 0.3, head, ha="left", va="center", fontsize=8,
            fontweight="bold", color=tc, zorder=3)
    ax.text(x + 0.18, y + (h - 0.5) / 2 - 0.02, body, ha="left", va="center", fontsize=fs,
            color=tc, linespacing=1.15, zorder=3)
    return (x + w / 2, y + h, x + w / 2, y)  # top-centre and bottom-centre


def connect(parent, children, label):
    px, py = parent[2], parent[3]
    ymid = py - 0.32
    ax.plot([px, px], [py, ymid], color=COLORS["grey"], lw=1.2, zorder=1)
    xs = [c[0] for c in children]
    ax.plot([min(xs), max(xs)], [ymid, ymid], color=COLORS["grey"], lw=1.2, zorder=1)
    for c in children:
        ax.annotate("", xy=(c[0], c[1]), xytext=(c[0], ymid),
                    arrowprops=dict(arrowstyle="-|>", color=COLORS["grey"], lw=1.2,
                                    mutation_scale=9))
    ax.text(px + 0.15, ymid + 0.05, label, ha="left", va="bottom", fontsize=7,
            style="italic", color=COLORS["grey"], zorder=3)


# level labels on the left margin
levels = [(11.35, "Stakeholder\nneed"), (9.15, "Mission\nrequirement"),
          (6.55, "System\nrequirements"), (3.75, "Subsystem\nrequirements"),
          (1.15, "Component\nrequirements")]
for y, lab in levels:
    ax.text(0.05, y, lab, ha="left", va="center", fontsize=7.5, color=COLORS["grey"],
            fontweight="bold", linespacing=1.1)

X0 = 2.6  # left edge of the tree area
W = 13.0 - X0 + 2.0  # width available

# need
need = node(X0 + 3.0, 10.6, 6.3, 1.5, "Stakeholder need",
            "“Timely agricultural monitoring\nfor food security”", COLORS["ink"])
# mission requirement
mr = node(X0 + 1.9, 8.2, 8.5, 1.9, "MR-001",
          "The system shall provide multispectral imagery\nwith GSD ≤ 10 m and revisit "
          "≤ 5 days over the\ntarget region", COLORS["accent"])
connect(need, [mr], "derives")

# system requirements (three columns)
cw, ch = 3.9, 2.05
xs = [X0 + 0.0, X0 + 4.2, X0 + 8.4]
sr = [
    node(xs[0], 5.5, cw, ch, "SR-PL-001",
         "The payload shall achieve\nGSD ≤ 10 m at nadir from\nthe operational orbit",
         COLORS["accent_3"]),
    node(xs[1], 5.5, cw, ch, "SR-AOCS-001",
         "The AOCS shall provide\npointing accuracy ≤ 0.1°\n(3σ) during imaging",
         COLORS["accent_3"]),
    node(xs[2], 5.5, cw, ch, "SR-LINK-001",
         "The comms system shall\ndownlink ≥ 5 GB/day",
         COLORS["accent_3"]),
]
connect(mr, sr, "decomposes into")

# subsystem requirements
ssr_txt = [
    ("SSR-PL-001a", "The telescope aperture\nshall be ≥ 80 mm"),
    ("SSR-AOCS-001a", "The star tracker shall\nprovide ≤ 5 arcsec attitude\nknowledge (3σ)"),
    ("SSR-LINK-001a", "The X-band transmitter\nshall provide ≥ 2 W\nRF power"),
]
ssr = []
for i, (h, b) in enumerate(ssr_txt):
    n = node(xs[i], 2.75, cw, ch, h, b, COLORS["accent_2"])
    ssr.append(n)
    connect(sr[i], [n], "derives" if i == 0 else "")

# component level (dashed, illustrative)
comp_txt = [
    "optics, detector, baffle\nspecifications",
    "star-tracker optical head,\nIMU, wheel specifications",
    "transmitter, antenna,\ncable-loss specifications",
]
for i, b in enumerate(comp_txt):
    n = node(xs[i], 0.3, cw, 1.55, "Component level", b, COLORS["grey"], filled=False,
             dashed=True, fs=7.2)
    connect(ssr[i], [n], "allocates to" if i == 0 else "")

ax.text(0.05, 12.5, "Every requirement traces up to its\nparent and down to its children (§5.4.3)",
        ha="left", va="top", fontsize=7.5, style="italic",
        color=COLORS["grey"])
save(fig, Path(__file__).stem)
