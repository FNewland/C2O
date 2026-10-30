"""Antenna patterns — high-gain parabolic dish (Airy pattern) vs S-band patch."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()

freq = 2.25e9            # S-band (Ch 11 worked example)
c = 3e8
lam = c / freq


def J1(x):
    """Bessel J1 via its integral form (numpy only)."""
    tau = np.linspace(0, np.pi, 2001)
    x = np.atleast_1d(x)[:, None]
    f = np.cos(tau[None, :] - x * np.sin(tau[None, :]))
    return np.trapezoid(f, tau, axis=1) / np.pi


# --- 3 m ground dish: uniformly illuminated circular aperture (Airy) ---
D1 = 3.0
eff = 0.6
Gmax1 = 10 * np.log10(eff * (np.pi * D1 / lam) ** 2)       # ≈ 35 dBi
HPBW1 = 70 * lam / D1                                        # deg (rule of thumb)
deg1 = np.linspace(-20, 20, 2001)
u = (np.pi * D1 / lam) * np.sin(np.deg2rad(deg1))
u_safe = np.where(np.abs(u) < 1e-9, 1e-9, u)
pat1 = (2 * J1(u_safe) / u_safe) ** 2
G1 = Gmax1 + 10 * np.log10(np.clip(pat1, 1e-6, None))

# --- S-band patch: cos^n model, ~6 dBi, ~80° HPBW ---
Gmax2 = 6.0
HPBW2 = 80.0
n = np.log(0.5) / np.log(np.cos(np.deg2rad(HPBW2 / 2)))
deg2 = np.linspace(-90, 90, 721)
G2 = Gmax2 + 10 * np.log10(np.clip(np.cos(np.deg2rad(deg2)) ** n, 1e-6, None))

fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2), sharey=True)

panels = [
    (axes[0], deg1, G1, Gmax1, HPBW1, 20,
     f"3 m parabolic dish — G = {Gmax1:.0f} dBi, HPBW ≈ {HPBW1:.1f}°", COLORS["accent"]),
    (axes[1], deg2, G2, Gmax2, HPBW2, 90,
     f"S-band patch — G = {Gmax2:.0f} dBi, HPBW ≈ {HPBW2:.0f}°", COLORS["accent_2"]),
]
for ax, th, G, Gmax, HPBW, span, label, color in panels:
    ax.plot(th, G, color=color, lw=1.8)
    ax.fill_between(th, -10, G, color=color, alpha=0.15)
    ax.axvspan(-HPBW / 2, HPBW / 2, color=COLORS["band"], alpha=0.8, zorder=0)
    ax.axhline(Gmax - 3, color=COLORS["grey"], lw=0.8, ls=":")
    ax.text(-span + 0.03 * 2 * span, Gmax - 3 + 1, "−3 dB", fontsize=8,
            color=COLORS["grey"], va="bottom", clip_on=True)
    ax.set_xlim(-span, span)
    ax.set_ylim(-10, 40)
    ax.set_xlabel("Angle from boresight (deg)")
    ax.set_title(label, fontsize=10.5)
    ax.grid(True, alpha=0.4)

axes[0].set_ylabel("Gain (dBi)")
axes[0].text(0, -6, "half-power beamwidth\n(shaded)", ha="center", va="bottom",
             fontsize=8, color=COLORS["grey"], clip_on=True)
axes[0].annotate("sidelobes\n(−17.6 dB first)", xy=(5.0, Gmax1 - 17.6),
                 xytext=(11, 28), fontsize=8, color=COLORS["accent"],
                 arrowprops=dict(arrowstyle="->", color=COLORS["accent"], lw=0.9),
                 annotation_clip=True)
axes[1].text(0, -6, "half-power beamwidth (shaded)", ha="center", va="bottom",
             fontsize=8, color=COLORS["grey"], clip_on=True)

fig.suptitle(f"Antenna gain patterns at {freq/1e9:.2f} GHz — high-gain dish vs low-gain patch",
             fontsize=12, fontweight="bold", y=1.03)
save(fig, Path(__file__).stem)
