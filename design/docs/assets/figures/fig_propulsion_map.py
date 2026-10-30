"""Specific impulse versus thrust map of CubeSat propulsion options (Ch 12 §12.2.3).

Regions are the Isp and thrust ranges of the §12.2.5 comparison table (cold gas
40–75 s / 10–100 mN; warm gas 80–100 s / 5–50 mN; green monopropellant
230–250 s / 0.1–1 N; electrospray/FEEP 500–5000 s / 0.01–1 mN; Hall effect
800–3000 s / 1–50 mN), each annotated with its power during firing from the
same table. The three §12.2.5 worked-example design points (ΔV = 112 m/s,
5 kg dry) are marked at the Isp used in the example and a representative
thrust from the products named in §12.2.3 (VACCO/Busek-class cold gas ≈ 30 mN,
Aerojet MPS-130 class 1 N, Enpulsion NANO class 0.35 mN).
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from oer_style import apply_style, COLORS, save

apply_style()

# (name, thrust range N, Isp range s, colour, power label)
regions = [
    ("Cold gas", (10e-3, 100e-3), (40, 75), COLORS["accent"], "< 1 W (valve)"),
    ("Warm gas / resistojet", (5e-3, 50e-3), (80, 100), COLORS["accent_6"], "5–15 W"),
    ("Green monopropellant", (0.1, 1.0), (230, 250), COLORS["accent_3"], "2–10 W (preheat)"),
    ("Electrospray / FEEP", (0.01e-3, 1e-3), (500, 5000), COLORS["accent_4"], "20–60 W"),
    ("Hall effect", (1e-3, 50e-3), (800, 3000), COLORS["accent_2"], "50–300 W"),
]

fig, ax = plt.subplots(figsize=(7.2, 4.8))
for name, (f0, f1), (i0, i1), col, pw in regions:
    ax.add_patch(Rectangle((f0, i0), f1 - f0, i1 - i0, facecolor=col, alpha=0.22,
                           edgecolor=col, lw=1.4))
# labels (placed by hand to avoid overlaps)
lab = {
    "Cold gas": (30e-3, 45, "Cold gas · < 1 W (valve)"),
    "Warm gas / resistojet": (15e-3, 125, "Warm gas / resistojet\n5–15 W"),
    "Green monopropellant": (0.32, 560, "Green monopropellant\n2–10 W (preheat)"),
    "Electrospray / FEEP": (0.08e-3, 2600, "Electrospray / FEEP\n20–60 W"),
    "Hall effect": (7e-3, 1500, "Hall effect\n50–300 W"),
}
for name, (f0, f1), (i0, i1), col, pw in regions:
    x, y, text = lab[name]
    ax.text(x, y, text, ha="center", va="center", fontsize=8, color=col, fontweight="bold",
            linespacing=1.15)

# CubeSat power envelope note
ax.text(0.007e-3, 19000,
        "CubeSat power envelope ≈ 20–60 W during firing:\n"
        "electrospray fits; Hall-effect thrusters need ≥ 50 W",
        ha="left", va="top", fontsize=7.5, style="italic", color=COLORS["ink"],
        bbox=dict(boxstyle="round,pad=0.3", facecolor=COLORS["band"], edgecolor="none"))

# §12.2.5 worked-example design points (ΔV = 112 m/s, m_dry = 5 kg)
pts = [
    (30e-3, 60, "cold gas: Isp 60 s,\n1.05 kg propellant", (12, 2)),
    (1.0, 235, "green monopropellant: Isp 235 s,\n0.249 kg propellant", (-10, 8)),
    (0.35e-3, 1200, "electrospray: Isp 1200 s,\n0.048 kg propellant", (-8, -10)),
]
for f, isp, text, off in pts:
    ax.plot(f, isp, marker="*", ms=14, color=COLORS["ink"], markeredgecolor="white",
            markeredgewidth=0.8, zorder=5)
    ax.annotate(text, xy=(f, isp), xytext=off, textcoords="offset points", fontsize=7.5,
                ha="center" if off[0] == 0 else ("right" if off[0] < 0 else "left"),
                va="top" if off[1] < 0 else "bottom", color=COLORS["ink"], zorder=6)
ax.plot([], [], marker="*", ms=11, color=COLORS["ink"], ls="none",
        label="§12.2.5 design points (ΔV = 112 m/s, 5 kg dry)")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(5e-6, 2.0)
ax.set_ylim(30, 20000)
ax.set_xticks([1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1])
ax.set_xticklabels(["0.01 mN", "0.1 mN", "1 mN", "10 mN", "100 mN", "1 N"])
ax.set_yticks([30, 100, 300, 1000, 3000, 10000])
ax.set_yticklabels(["30", "100", "300", "1000", "3000", "10 000"])
ax.set_xlabel("Thrust")
ax.set_ylabel("Specific impulse $I_{sp}$ (s)")
ax.grid(True, which="major")
ax.grid(False, which="minor")
ax.legend(loc="upper right", bbox_to_anchor=(0.995, 0.86), fontsize=7.5)
ax.set_title("CubeSat propulsion options: specific impulse versus thrust", pad=8)
save(fig, Path(__file__).stem)
