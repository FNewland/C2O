"""β-angle over a year (ISS-like vs 10:30 LTAN SSO) and eclipse fraction vs β.

Left: daily sweep of sin β = cos δ☉ sin i sin(Ω − α☉) + sin δ☉ cos i with the
node precessing at the J2 rate; the ±(i + ε) envelope and ±β* lines are shown.
Right: f_ecl(β) from the Ch 7 β-form equation (circular orbit, cylindrical shadow).
"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()

RE = 6378.137
MU = 398_600.4418
J2 = 1.082_626_68e-3
EPS = np.deg2rad(23.44)      # obliquity

cases = [
    {"label": "ISS-like (51.6°, 400 km)", "alt": 400, "i": 51.6,
     "color": COLORS["accent"], "sso": False, "ltan": None},
    {"label": "SSO 10:30 LTAN (98°, 600 km)", "alt": 600, "i": 98.0,
     "color": COLORS["accent_2"], "sso": True, "ltan": 10.5},
]

days = np.arange(0, 366)
lam_sun = 2 * np.pi * (days - 80) / 365.25          # ecliptic longitude (0 at ~Mar 21)
dec = np.arcsin(np.sin(EPS) * np.sin(lam_sun))       # solar declination
ra = np.arctan2(np.cos(EPS) * np.sin(lam_sun), np.cos(lam_sun))   # solar RA


def beta_star(h):
    return np.arcsin(RE / (RE + h))


fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))

ax = axes[0]
for c in cases:
    a = RE + c["alt"]
    inc = np.deg2rad(c["i"])
    n = np.sqrt(MU / a**3)
    raan_dot = -1.5 * n * J2 * (RE / a) ** 2 * np.cos(inc) * 86400   # rad/day
    if c["sso"]:
        # LTAN fixes the node relative to the Sun: Ω − α☉ = (LTAN − 12 h) × 15°/h
        raan = ra + np.deg2rad((c["ltan"] - 12.0) * 15.0)
    else:
        raan = np.deg2rad(0.0) + raan_dot * days
    sb = np.cos(dec) * np.sin(inc) * np.sin(raan - ra) + np.sin(dec) * np.cos(inc)
    beta = np.rad2deg(np.arcsin(np.clip(sb, -1, 1)))
    ax.plot(days, beta, color=c["color"], lw=1.8, label=c["label"])
    env = min(c["i"], 180 - c["i"]) + 23.44
    bs = np.rad2deg(beta_star(c["alt"]))
    if not c["sso"]:
        ax.axhspan(-env, env, color=c["color"], alpha=0.08, lw=0)
        ax.text(5, -env - 1.5, f"ISS envelope ±(i + 23.4°) = ±{env:.0f}°",
                fontsize=8, color=c["color"], va="top", clip_on=True)
        ax.axhline(bs, color=c["color"], lw=0.8, ls=":")
        ax.axhline(-bs, color=c["color"], lw=0.8, ls=":")
        ax.text(360, bs + 1.5, f"β* = {bs:.0f}° at 400 km — fully sunlit beyond",
                fontsize=7.5, color=c["color"], ha="right", va="bottom", clip_on=True)
    else:
        ax.fill_between(days, beta.min(), beta.max(), color=c["color"], alpha=0.12, lw=0)
        ax.text(183, beta.min() - 9,
                f"SSO band {beta.min():.0f}° … {beta.max():.0f}° (set by LTAN)",
                fontsize=8, color=c["color"], ha="center", va="top", clip_on=True)

ax.axhline(0, color=COLORS["grey_light"], lw=0.8)
ax.set_xlabel("Day of year")
ax.set_ylabel("β-angle (deg)")
ax.set_title("β-angle through the year")
ax.set_xlim(0, 365)
ax.set_ylim(-90, 90)
ax.set_yticks(range(-90, 91, 30))
ax.legend(loc="lower center", fontsize=8.5, ncol=1,
          bbox_to_anchor=(0.5, -0.36))

# Right: eclipse fraction vs β  (Ch 7 β-form equation)
ax = axes[1]
beta_grid = np.deg2rad(np.linspace(-90, 90, 1801))
for c in cases:
    h = c["alt"]
    bs = beta_star(h)
    f = np.zeros_like(beta_grid)
    m = np.abs(beta_grid) < bs
    arg = np.sqrt(h**2 + 2 * RE * h) / ((RE + h) * np.cos(beta_grid[m]))
    f[m] = np.arccos(np.clip(arg, -1, 1)) / np.pi
    ax.plot(np.rad2deg(beta_grid), f * 100, lw=2.0, color=c["color"], label=c["label"])
    ax.axvline(np.rad2deg(bs), color=c["color"], lw=0.8, ls=":")
    ax.axvline(-np.rad2deg(bs), color=c["color"], lw=0.8, ls=":")
    if h == 400:
        ax.text(0, f.max() * 100 + 1.0, f"max {f.max()*100:.0f} % at β = 0 ({h} km)",
                fontsize=8, color=c["color"], ha="center", va="bottom", clip_on=True)
    else:
        ax.text(0, f.max() * 100 - 2.0, f"max {f.max()*100:.0f} % ({h} km)",
                fontsize=8, color=c["color"], ha="center", va="top", clip_on=True)

ax.text(-88, 48.5, "fully sunlit for |β| ≥ β*:\nβ* = 70° (400 km), 66° (600 km)",
        fontsize=8, color=COLORS["grey"], ha="left", va="top", clip_on=True)

ax.set_xlabel("β-angle (deg)")
ax.set_ylabel("Eclipse fraction of orbit (%)")
ax.set_title("Eclipse fraction vs β-angle")
ax.set_xlim(-90, 90)
ax.set_ylim(0, 50)
ax.legend(loc="lower center", fontsize=8.5, bbox_to_anchor=(0.5, -0.36))

fig.subplots_adjust(wspace=0.3, bottom=0.3)
save(fig, Path(__file__).stem)
