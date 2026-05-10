"""Parabolic dish gain pattern — polar plot."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()

# Parabolic dish gain: G_max in dBi, pattern G(theta) ~ G_max * (J1(u)/u)^2 * 4
# Where u = ka sin(theta), k = 2*pi/lambda, a = D/2
# Use simpler: G(theta) = G_max - 12*(theta/HPBW)^2  (typical parametric model)
freq = 2.2e9   # 2.2 GHz S-band
c = 3e8
lam = c/freq

# Two cases: a 0.6 m dish (high gain) and a patch antenna (low gain)
fig, ax = plt.subplots(1, 2, figsize=(10.0, 4.4),
                       subplot_kw={"projection":"polar"})

theta = np.linspace(-np.deg2rad(60), np.deg2rad(60), 600)

# Dish 1: 0.6 m dish, S-band
D1 = 0.6
HPBW1 = 70 * lam / D1   # deg, rule-of-thumb
HPBW1_rad = np.deg2rad(HPBW1)
Gmax1 = 10 * np.log10(0.55 * (np.pi * D1 / lam)**2)
G1 = Gmax1 - 12 * (theta/HPBW1_rad)**2
G1 = np.clip(G1, -10, None)

# Patch antenna: ~6 dBi peak, ~80 deg HPBW
Gmax2 = 6.0
HPBW2 = 80
HPBW2_rad = np.deg2rad(HPBW2)
G2 = Gmax2 - 12 * (theta/HPBW2_rad)**2
G2 = np.clip(G2, -10, None)

for axi, G, Gmax, HPBW, label, color in [
    (ax[0], G1, Gmax1, HPBW1, f"0.6 m dish — G = {Gmax1:.1f} dBi", COLORS["garnet"]),
    (ax[1], G2, Gmax2, HPBW2, f"S-band patch — G = {Gmax2:.1f} dBi", COLORS["blue"]),
]:
    axi.plot(theta, G, color=color, lw=2.0)
    axi.fill_between(theta, -10, G, color=color, alpha=0.18)
    axi.set_theta_zero_location("N")
    axi.set_theta_direction(-1)
    axi.set_thetalim(-np.deg2rad(60), np.deg2rad(60))
    axi.set_rlim(-10, max(Gmax+5, 35))
    axi.set_title(label + f"\nHPBW ≈ {HPBW:.1f}°", pad=14, fontsize=10)
    axi.grid(True, alpha=0.4)
    axi.set_rticks([0, 10, 20, 30])
    axi.set_xticks(np.deg2rad([-60,-30,0,30,60]))
    axi.set_xticklabels(["-60°", "-30°", "0°", "30°", "60°"])

fig.suptitle("Antenna Patterns — High-gain dish vs low-gain patch",
             fontsize=12, color=COLORS["charcoal"], y=1.02)
add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_antenna_pattern.png")
print("OK antenna pattern")
