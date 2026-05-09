"""N² interface matrix for a CubeSat — 8 subsystems."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()
subs = ["Power", "AOCS", "Thermal", "Comms", "Structure",
        "Propulsion", "Data/OBC", "Payload"]
N = len(subs)

# Encode interface presence:
#   0 = no interface, 1 = data, 2 = electrical, 3 = mechanical,
#   4 = thermal, 5 = RF, 6 = optical
M = np.zeros((N, N), dtype=int)

# i = source (row), j = destination (col)
edges = {
    ("Power","AOCS"): 2, ("AOCS","Power"): 1,
    ("Power","Comms"): 2, ("Comms","Power"): 1,
    ("Power","Thermal"): 4, ("Thermal","Power"): 4,
    ("Power","Payload"): 2, ("Payload","Power"): 1,
    ("Power","Data/OBC"): 2, ("Data/OBC","Power"): 1,
    ("Power","Propulsion"): 2,
    ("Structure","AOCS"): 3, ("AOCS","Structure"): 3,
    ("Structure","Payload"): 3,
    ("Structure","Propulsion"): 3,
    ("Data/OBC","AOCS"): 1, ("AOCS","Data/OBC"): 1,
    ("Data/OBC","Comms"): 1, ("Comms","Data/OBC"): 1,
    ("Data/OBC","Payload"): 1, ("Payload","Data/OBC"): 1,
    ("Comms","Payload"): 5,
    ("Comms","AOCS"): 6,    # antenna vs star tracker FOV
    ("Thermal","Payload"): 4,
    ("AOCS","Payload"): 3,  # RW vibration coupling
    ("Propulsion","Thermal"): 4,
}

cmap_lookup = {
    1: COLORS["garnet"],   # data
    2: COLORS["blue"],     # electrical
    3: COLORS["warm_grey"],# mechanical
    4: COLORS["green"],    # thermal
    5: COLORS["garnet_2"], # RF
    6: COLORS["charcoal"], # optical
}
labels = {1:"D", 2:"E", 3:"M", 4:"T", 5:"R", 6:"O"}

for (a, b), kind in edges.items():
    i, j = subs.index(a), subs.index(b)
    M[i, j] = kind

fig, ax = plt.subplots(figsize=(8.4, 7.0))
# Diagonal cells = subsystems
for i, name in enumerate(subs):
    ax.add_patch(plt.Rectangle((i, N-1-i), 1, 1,
                               facecolor=COLORS["charcoal"], edgecolor="white"))
    ax.text(i+0.5, N-0.5-i, name, ha="center", va="center",
            color="white", fontsize=8.5, fontweight="bold")

# Off-diagonal cells
for i in range(N):
    for j in range(N):
        if i == j:
            continue
        kind = M[i, j]
        if kind == 0:
            ax.add_patch(plt.Rectangle((j, N-1-i), 1, 1,
                                        facecolor=COLORS["polar"],
                                        edgecolor="white"))
        else:
            color = cmap_lookup[kind]
            ax.add_patch(plt.Rectangle((j, N-1-i), 1, 1,
                                        facecolor=color, edgecolor="white",
                                        alpha=0.85))
            ax.text(j+0.5, N-0.5-i, labels[kind], ha="center", va="center",
                    color="white", fontweight="bold", fontsize=10)

ax.set_xlim(0, N); ax.set_ylim(0, N)
ax.set_aspect("equal")
ax.set_xticks([]); ax.set_yticks([])
ax.invert_yaxis()
# Hide spines for cleaner look
for s in ax.spines.values(): s.set_visible(False)

# Legend
from matplotlib.patches import Patch
legend = [
    Patch(color=cmap_lookup[1], label="Data (D)"),
    Patch(color=cmap_lookup[2], label="Electrical (E)"),
    Patch(color=cmap_lookup[3], label="Mechanical (M)"),
    Patch(color=cmap_lookup[4], label="Thermal (T)"),
    Patch(color=cmap_lookup[5], label="RF (R)"),
    Patch(color=cmap_lookup[6], label="Optical (O)"),
]
ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(1.02, 1.0),
          frameon=False, fontsize=9)

ax.set_title("N² Interface Matrix — 6U CubeSat (illustrative)",
             fontsize=12, color=COLORS["charcoal"], pad=10)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_n2_matrix.png")
print("OK N² matrix")
