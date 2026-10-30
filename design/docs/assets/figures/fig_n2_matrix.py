"""N² interface matrix for a 6U CubeSat — 8 subsystems, interface types M/E/T/D/R/O/S."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from oer_style import apply_style, COLORS, save

apply_style()
subs = ["Power", "AOCS", "Thermal", "Comms", "Struct.", "Prop.", "OBC", "Payload"]
N = len(subs)

# (row = source, col = destination) → interface type code (Table 8.2)
edges = {
    ("Power", "AOCS"): "E",    ("AOCS", "Power"): "D",
    ("Power", "Comms"): "E",   ("Comms", "Power"): "D",
    ("Power", "Thermal"): "T", ("Thermal", "Power"): "T",
    ("Power", "Payload"): "E", ("Payload", "Power"): "D",
    ("Power", "OBC"): "E",     ("OBC", "Power"): "D",
    ("Power", "Prop."): "E",
    ("Struct.", "AOCS"): "M",  ("AOCS", "Struct."): "M",
    ("Struct.", "Payload"): "M",
    ("Struct.", "Prop."): "M",
    ("OBC", "AOCS"): "S",      ("AOCS", "OBC"): "D",      # flight software hosts AOCS
    ("OBC", "Comms"): "D",     ("Comms", "OBC"): "D",
    ("OBC", "Payload"): "S",   ("Payload", "OBC"): "D",   # payload command set / driver
    ("Comms", "Payload"): "R",
    ("Comms", "AOCS"): "O",    # antenna vs star-tracker field of view
    ("Thermal", "Payload"): "T",
    ("AOCS", "Payload"): "M",  # wheel micro-vibration coupling
    ("Prop.", "Thermal"): "T",
}
names = {"M": "Mechanical", "E": "Electrical", "T": "Thermal", "D": "Data",
         "R": "RF", "O": "Optical", "S": "Software"}

fig, ax = plt.subplots(figsize=(9.0, 7.2))
for i in range(N):
    for j in range(N):
        x, y = j, N - 1 - i
        if i == j:
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=COLORS["diag"], edgecolor="white"))
            ax.text(x + 0.5, y + 0.5, subs[i], ha="center", va="center",
                    color="white", fontsize=8.5, fontweight="bold")
            continue
        kind = edges.get((subs[i], subs[j]))
        if kind is None:
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor="#f3f3f3", edgecolor="white"))
        else:
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=COLORS[kind],
                                       edgecolor="white", alpha=0.9))
            ax.text(x + 0.5, y + 0.5, kind, ha="center", va="center",
                    color="white", fontweight="bold", fontsize=11)

# Row/column guides
for k, name in enumerate(subs):
    ax.text(-0.15, N - 0.5 - k, name, ha="right", va="center", fontsize=8.5, color=COLORS["grey"])
    ax.text(k + 0.5, N + 0.12, name, ha="center", va="bottom", fontsize=8.5, color=COLORS["grey"])
ax.text(-0.15, N + 0.12, "from ↓ / to →", ha="right", va="bottom", fontsize=8,
        color=COLORS["grey"], style="italic")

ax.set_xlim(-1.6, N + 0.1)
ax.set_ylim(-0.1, N + 0.6)
ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)

legend = [Patch(color=COLORS[k], label=f"{v} ({k})") for k, v in names.items()]
ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=9,
          title="Interface type", title_fontsize=9)
ax.set_title("N² interface matrix — 6U CubeSat (illustrative), read row → column", pad=22)

save(fig, Path(__file__).stem)
