"""Sample figure: ground track of a 600 km Sun-synchronous orbit (one orbit + horizon)."""
import numpy as np
import matplotlib.pyplot as plt
from uottawa_brand import apply_style, COLORS, add_footer

apply_style()

# Earth & orbit constants
MU = 398_600.4418            # km^3/s^2
RE = 6378.137                # km
J2 = 1.082_626_68e-3
WE = 7.2921159e-5            # rad/s (Earth rotation)

# Orbit: 600 km altitude, SSO (i ~ 97.79 deg)
h = 600.0
a = RE + h
e = 0.0
i_deg = 97.79
RAAN0 = 0.0
arg_p0 = 0.0
nu0 = 0.0

n = np.sqrt(MU / a**3)
T = 2 * np.pi / n
t = np.linspace(0, 1.4 * T, 4000)  # 1.4 orbits

i = np.deg2rad(i_deg)
M = n * t
E = M.copy()
for _ in range(20):
    E = M + e * np.sin(E)
nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))
u = arg_p0 + nu  # argument of latitude (e=0)

# Position in ECI
r = a * (1 - e * np.cos(E))
x_p = r * np.cos(u)
y_p = r * np.sin(u) * np.cos(i)
z_p = r * np.sin(u) * np.sin(i)

# RAAN drift (J2 nodal regression)
n_dot_RAAN = -1.5 * n * J2 * (RE / a) ** 2 * np.cos(i) / (1 - e**2) ** 2
RAAN = RAAN0 + n_dot_RAAN * t

# Rotate by -RAAN (apply RAAN)
cR, sR = np.cos(RAAN), np.sin(RAAN)
x_eci = cR * x_p - sR * y_p
y_eci = sR * x_p + cR * y_p
z_eci = z_p

# ECI -> ECEF (only Earth rotation, ignore precession)
gst = WE * t
ce, se = np.cos(gst), np.sin(gst)
x_ecef =  ce * x_eci + se * y_eci
y_ecef = -se * x_eci + ce * y_eci
z_ecef = z_eci

lat = np.rad2deg(np.arcsin(z_ecef / np.linalg.norm([x_ecef, y_ecef, z_ecef], axis=0)))
lon = np.rad2deg(np.arctan2(y_ecef, x_ecef))
# Wrap longitude to (-180, 180] and split traces at jumps so lines don't streak across the map
lon = ((lon + 180) % 360) - 180
breaks = np.where(np.abs(np.diff(lon)) > 180)[0] + 1
lon_seg = np.insert(lon, breaks, np.nan)
lat_seg = np.insert(lat, breaks, np.nan)

fig, ax = plt.subplots(figsize=(8.0, 4.2))

# Background world graticule
for L in range(-180, 181, 30):
    ax.axvline(L, color=COLORS["polar"], lw=0.6, zorder=0)
for L in range(-90, 91, 30):
    ax.axhline(L, color=COLORS["polar"], lw=0.6, zorder=0)
ax.axhline(0, color=COLORS["warm_grey"], lw=0.8, zorder=0)   # Equator
ax.axvline(0, color=COLORS["warm_grey"], lw=0.8, zorder=0)   # Prime meridian

ax.plot(lon_seg, lat_seg, color=COLORS["garnet"], lw=1.6, label="Ground track")

# Mark Ottawa
ax.plot(-75.7, 45.4, "o", color=COLORS["charcoal"], ms=5)
ax.annotate("Ottawa", (-75.7, 45.4), xytext=(6, 6),
            textcoords="offset points", fontsize=9, color=COLORS["charcoal"])

ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)
ax.set_xticks(range(-180, 181, 60))
ax.set_yticks(range(-90, 91, 30))
ax.set_xlabel("Longitude (deg)")
ax.set_ylabel("Latitude (deg)")
ax.set_title(f"Ground Track — {int(h)} km Sun-synchronous orbit (i = {i_deg}°)")
ax.legend(loc="lower left", frameon=False)

add_footer(fig)
fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/fig_ground_track.png")
print("OK ground track")
