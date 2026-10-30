"""Ground track of a 600 km Sun-synchronous orbit over 1.5 revolutions."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()

MU = 398_600.4418            # km^3/s^2
RE = 6378.137                # km
J2 = 1.082_626_68e-3
WE = 7.2921159e-5            # rad/s

h = 600.0
a = RE + h
e = 0.0
i_deg = 97.79

n = np.sqrt(MU / a**3)
T = 2 * np.pi / n
t = np.linspace(0, 1.5 * T, 4000)

i = np.deg2rad(i_deg)
M = n * t
E = M.copy()
for _ in range(20):
    E = M + e * np.sin(E)
nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))
u = nu

r = a * (1 - e * np.cos(E))
x_p = r * np.cos(u)
y_p = r * np.sin(u) * np.cos(i)
z_p = r * np.sin(u) * np.sin(i)

raan_dot = -1.5 * n * J2 * (RE / a) ** 2 * np.cos(i) / (1 - e**2) ** 2
RAAN = raan_dot * t
cR, sR = np.cos(RAAN), np.sin(RAAN)
x_eci = cR * x_p - sR * y_p
y_eci = sR * x_p + cR * y_p
z_eci = z_p

gst = WE * t
ce, se = np.cos(gst), np.sin(gst)
x_ecef = ce * x_eci + se * y_eci
y_ecef = -se * x_eci + ce * y_eci
z_ecef = z_eci

lat = np.rad2deg(np.arcsin(z_ecef / np.sqrt(x_ecef**2 + y_ecef**2 + z_ecef**2)))
lon = np.rad2deg(np.arctan2(y_ecef, x_ecef))
lon = ((lon + 180) % 360) - 180
breaks = np.where(np.abs(np.diff(lon)) > 180)[0] + 1
lon_seg = np.insert(lon, breaks, np.nan)
lat_seg = np.insert(lat, breaks, np.nan)

fig, ax = plt.subplots(figsize=(8.0, 4.2))
for L in range(-180, 181, 30):
    ax.axvline(L, color=COLORS["grey_light"], lw=0.5, zorder=0)
for L in range(-90, 91, 30):
    ax.axhline(L, color=COLORS["grey_light"], lw=0.5, zorder=0)
ax.axhline(0, color=COLORS["grey"], lw=0.8, zorder=0)
ax.axvline(0, color=COLORS["grey"], lw=0.8, zorder=0)

ax.plot(lon_seg, lat_seg, color=COLORS["accent"], lw=1.6)
ax.plot(lon[0], lat[0], "o", color=COLORS["accent"], ms=5)
ax.annotate("start (ascending node)", (lon[0], lat[0]), xytext=(6, -12),
            textcoords="offset points", fontsize=8, color=COLORS["accent"],
            annotation_clip=True)

ax.plot(-75.7, 45.4, "o", color=COLORS["ink"], ms=5)
ax.annotate("Ottawa", (-75.7, 45.4), xytext=(6, 6),
            textcoords="offset points", fontsize=9, color=COLORS["ink"],
            annotation_clip=True)

ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)
ax.set_xticks(range(-180, 181, 60))
ax.set_yticks(range(-90, 91, 30))
ax.set_xlabel("Longitude (deg)")
ax.set_ylabel("Latitude (deg)")
ax.set_title(f"Ground track — {int(h)} km Sun-synchronous orbit (i = {i_deg}°), 1.5 revolutions")
ax.grid(False)

save(fig, Path(__file__).stem)
