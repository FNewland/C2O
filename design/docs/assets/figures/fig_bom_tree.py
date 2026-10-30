"""BOM hierarchy tree (spacecraft → subsystem → assembly → component → part) with
per-node roll-up columns: mass, power, cost, lowest TRL, longest lead time.
Illustrative values for a 3U CubeSat; roll-ups are computed from the leaves."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from oer_style import apply_style, COLORS, save

apply_style()

# (level, item ID, description, qty, mass g, power W, cost kEUR, TRL, lead wk)
# Leaves carry unit values; parents are rolled up (quantity-weighted) below.
rows = [
    (0, "S/C-001",         "Spacecraft",                 1, None, None, None, None, None),
    (1, "STR-000",         "Structure",                  1, 350,  0.0,  8.0,  9,  8),
    (1, "EPS-000",         "Electrical power (EPS)",     1, None, None, None, None, None),
    (2, "EPS-SA-000",      "Solar array assembly",       1, None, None, None, None, None),
    (3, "EPS-SA-001",      "Solar cell string",          3, None, None, None, None, None),
    (4, "EPS-SA-001-01",   "Azur 3G30C cell",            8, 2.5,  0.0,  0.20, 9,  8),
    (4, "EPS-SA-001-02",   "Bypass diode",               8, 0.1,  0.0,  0.01, 9,  2),
    (3, "EPS-SA-002",      "Substrate panel",            2, 45,   0.0,  0.80, 8, 10),
    (2, "EPS-BAT-000",     "Battery assembly",           1, 260,  0.5,  3.2,  9, 12),
    (2, "EPS-PCB-000",     "Power board",                1, 94,   0.2,  8.5,  9, 12),
    (1, "OBC-000",         "On-board computer",          1, 80,   1.2, 10.0,  9, 10),
    (1, "AOCS-000",        "Attitude control",           1, 430,  4.5, 42.0,  7, 20),
    (1, "TTC-000",         "Communications",             1, 180,  8.0, 20.5,  9, 14),
    (1, "PLD-000",         "Payload (imager)",           1, 600,  5.0, 58.0,  6, 26),
    (1, "HAR-000",         "Harness",                    1, 120,  0.0,  2.5,  9,  4),
]

# ---- roll-up: each node's totals = qty × (sum of children or its own unit values)
n = len(rows)
tot = [None] * n  # per-node *per-unit* totals (mass, power, cost, minTRL, maxLead)


def children(i):
    lvl = rows[i][0]
    j = i + 1
    while j < n and rows[j][0] > lvl:
        if rows[j][0] == lvl + 1:
            yield j
        j += 1


def rollup(i):
    lvl, _id, _d, qty, m, p, c, trl, lead = rows[i]
    kids = list(children(i))
    if not kids:
        tot[i] = (m, p, c, trl, lead)
        return tot[i]
    M = P = C = 0.0
    TRL, LEAD = 9, 0
    for k in kids:
        km, kp, kc, kt, kl = rollup(k)
        q = rows[k][3]
        M += q * km
        P += q * kp
        C += q * kc
        TRL = min(TRL, kt)
        LEAD = max(LEAD, kl)
    tot[i] = (M, P, C, TRL, LEAD)
    return tot[i]


rollup(0)
is_leaf = [not list(children(i)) for i in range(n)]

# ---- drawing
fig = plt.figure(figsize=(7.15, 5.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_axis_off()
ax.set_xlim(0, 100)
ax.set_ylim(-1.7, n + 2.4)
ax.grid(False)

x_ind = 1.5       # left margin
dx = 4.0          # indent per level
x_desc = 30.8     # description column start
cols = [("Qty", 55.0), ("Mass\n(g)", 63.5), ("Power\n(W)", 72.0),
        ("Cost\n(kEUR)", 81.5), ("Lowest\nTRL", 89.5), ("Longest\nlead (wk)", 99.0)]
level_colors = [COLORS["accent"], COLORS["accent_6"], COLORS["accent_3"],
                COLORS["accent_5"], COLORS["grey"]]

# header
yh = n + 0.6
ax.text(x_ind, yh, "Item ID", fontsize=8.5, fontweight="bold", va="center")
ax.text(x_desc, yh, "Description", fontsize=8.5, fontweight="bold", va="center")
for name, xc in cols:
    ax.text(xc, yh, name, fontsize=8.5, fontweight="bold", va="center", ha="right",
            linespacing=1.0)
ax.plot([0, 100], [n - 0.05, n - 0.05], color=COLORS["ink"], lw=0.8)
ax.text(x_ind, n + 1.9, "Indent = BOM level (0 spacecraft, 1 subsystem, 2 assembly, 3 component, 4 part).\n"
        "Bold rows are roll-ups of the rows beneath them.",
        fontsize=8, style="italic", color=COLORS["grey"], va="center", linespacing=1.2)

for i, (lvl, iid, desc, qty, *_) in enumerate(rows):
    y = n - 1 - i
    bold = not is_leaf[i]
    if lvl == 0:
        ax.add_patch(Rectangle((0, y - 0.5), 100, 1, facecolor=COLORS["band"],
                               edgecolor="none", zorder=0))
    elif i % 2 == 0:
        ax.add_patch(Rectangle((0, y - 0.5), 100, 1, facecolor="#f6f6f6",
                               edgecolor="none", zorder=0))
    x = x_ind + dx * lvl
    # tree connector lines
    if lvl > 0:
        px = x_ind + dx * (lvl - 1) + 0.9
        ax.plot([px, x - 0.6], [y, y], color=COLORS["grey_light"], lw=0.9, zorder=1)
        # vertical line up to parent row
        j = i - 1
        while rows[j][0] >= lvl:
            j -= 1
        ax.plot([px, px], [y, n - 1 - j - 0.45], color=COLORS["grey_light"], lw=0.9, zorder=1)
    ax.text(x, y, iid, fontsize=8, va="center", family="DejaVu Sans Mono",
            color=level_colors[lvl], fontweight="bold" if bold else "normal")
    ax.text(x_desc, y, desc, fontsize=8.5, va="center",
            fontweight="bold" if bold else "normal")
    M, P, C, T, L = tot[i]
    vals = [f"{qty}", f"{M:.0f}" if M >= 10 else f"{M:.1f}", f"{P:.1f}", f"{C:.2f}" if C < 1 else f"{C:.1f}",
            f"{T}", f"{L}"]
    for (name, xc), v in zip(cols, vals):
        ax.text(xc, y, v, fontsize=8.5, va="center", ha="right",
                fontweight="bold" if bold else "normal")

# footnote on roll-up rules
ax.text(x_ind, -1.1, "Roll-up rules: mass, power and cost are quantity-weighted sums of the children;\n"
        "TRL is the minimum and lead time the maximum over the children.  "
        "Leaf values are per unit (illustrative).",
        fontsize=8, style="italic", color=COLORS["grey"], va="center", linespacing=1.2)

save(fig, Path(__file__).stem)
