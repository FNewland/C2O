"""Canadian space regulatory framework — hub-and-spoke schematic (Ch 2 §2.5).

A central "space activity" node is connected to the five federal bodies that
regulate it (CSA, ISED, GAC, DND/DRDC, Transport Canada), each box naming its
statute, and to the three international bodies (ITU, UN COPUOS, MTCR) whose
instruments reach a Canadian mission through ISED and GAC or through treaty
obligations.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from oer_style import apply_style, COLORS, save

apply_style()

fig, ax = plt.subplots(figsize=(7.5, 5.2))
ax.set_xlim(0, 17)
ax.set_ylim(0, 10.8)
ax.axis("off")


def box(x, y, w, h, title, body, fc, fs_t=9, fs_b=7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                facecolor=fc, edgecolor=fc, linewidth=1.2, zorder=2))
    ax.text(x + w / 2, y + h - 0.33, title, ha="center", va="center",
            fontsize=fs_t, fontweight="bold", color="white", zorder=3)
    ax.text(x + w / 2, y + (h - 0.6) / 2, body, ha="center", va="center",
            fontsize=fs_b, color="white", linespacing=1.2, zorder=3)


def line(p, q, color=COLORS["grey"], style="-"):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=color, linestyle=style,
            linewidth=1.3, zorder=1, solid_capstyle="round")


# --- central node -----------------------------------------------------------
cx, cy, cw, ch = 6.9, 4.1, 3.7, 2.0
box(cx, cy, cw, ch, "Space activity",
    "design · build · launch\noperate · distribute data",
    COLORS["ink"], fs_t=10, fs_b=7.5)
C = (cx + cw / 2, cy + ch / 2)

# --- federal bodies (left column) ------------------------------------------
fw, fh = 5.9, 1.55
federal = [
    (8.55, "CSA", "Canadian Space Agency Act\ncoordination, policy, funding"),
    (6.45, "ISED", "Radiocommunication Act (radio licence)\nRSSSA (remote-sensing licence)"),
    (4.35, "GAC", "Export and Import Permits Act (ECL)\nControlled Goods Program"),
    (2.25, "DND / DRDC", "National Defence Act\ndual-use technology, classification"),
    (0.15, "Transport Canada", "launch operations\n(no statute yet — future)"),
]
for y, name, body in federal:
    box(0.3, y, fw, fh, name, body, COLORS["accent"])
    line((0.3 + fw, y + fh / 2), (cx, C[1]))

# --- international bodies (right column) ------------------------------------
iw, ih = 4.6, 1.55
intl = [
    (7.9, "ITU", "Radio Regulations\nfrequency coordination, MIFR"),
    (4.35, "UN COPUOS", "treaty obligations: registration,\ndebris-mitigation guidelines"),
    (0.8, "MTCR", "missile-technology controls\n(ECL Group 6)"),
]
for y, name, body in intl:
    box(12.1, y, iw, ih, name, body, COLORS["accent_2"])

# COPUOS → central node (treaty obligations implemented nationally)
line((12.1, 4.35 + ih / 2), (cx + cw, C[1]))
# ITU → ISED and MTCR → GAC: dashed, routed via the top / bottom of the centre column
line((12.1, 7.9 + ih / 2), (cx + cw * 0.6, cy + ch + 0.1), color=COLORS["accent_2"], style="--")
ax.text(cx + cw / 2, 8.3, "ITU filings are submitted\nby ISED on Canada's behalf", ha="center",
        va="bottom", fontsize=7.5, style="italic", color=COLORS["accent_2"],
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"), zorder=4)
line((12.1, 0.8 + ih / 2), (cx + cw * 0.6, cy - 0.1), color=COLORS["accent_2"], style="--")
ax.text(cx + cw / 2, 2.0, "MTCR controls enter the\nECL administered by GAC", ha="center",
        va="top", fontsize=7.5, style="italic", color=COLORS["accent_2"],
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"), zorder=4)

# column headings
ax.text(0.3 + fw / 2, 10.65, "Federal regulators and their statutes", ha="center", va="top",
        fontsize=9, fontweight="bold", color=COLORS["accent"])
ax.text(12.1 + iw / 2, 10.65, "International bodies", ha="center", va="top",
        fontsize=9, fontweight="bold", color=COLORS["accent_2"])

save(fig, Path(__file__).stem)
