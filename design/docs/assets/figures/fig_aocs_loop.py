"""AOCS closed-loop block diagram (Ch 10 §10.1).

Reference attitude → error → controller → actuators → spacecraft dynamics
(Euler's equation, with the disturbance torques of §10.2 injected at the
plant) → sensors → attitude estimator (Kalman filter) → fed back to the
summing junction.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from oer_style import apply_style, COLORS, save

apply_style()

fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.set_xlim(0, 16)
ax.set_ylim(0, 8.3)
ax.axis("off")


def block(x, y, w, h, title, sub, col, filled=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                facecolor=col if filled else "white", edgecolor=col,
                                linewidth=1.4, zorder=2))
    tc = "white" if filled else COLORS["ink"]
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=8.5,
            fontweight="bold", color=tc, zorder=3)
    ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=7,
            color=tc, style="italic", zorder=3, linespacing=1.1)


def arrow(p, q, label=None, lx=0, ly=0.25, color=COLORS["ink"], ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13, color=color,
                                 linewidth=1.4, zorder=4, shrinkA=0, shrinkB=0))
    if label:
        ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, ha=ha, va="center",
                fontsize=7.5, color=color, zorder=5)


def wire(points, color=COLORS["ink"]):
    xs, ys = zip(*points)
    ax.plot(xs, ys, color=color, lw=1.4, zorder=4, solid_joinstyle="miter")


# forward path (y = 5.0)
yF, h = 4.4, 1.3
sj = (1.7, yF + h / 2)  # summing junction
ax.add_patch(Circle(sj, 0.3, facecolor="white", edgecolor=COLORS["ink"], lw=1.4, zorder=3))
ax.text(sj[0], sj[1], "Σ", ha="center", va="center", fontsize=10, zorder=4)
ax.text(sj[0] - 0.22, sj[1] + 0.34, "+", ha="center", va="center", fontsize=8, zorder=4)
ax.text(sj[0] + 0.12, sj[1] - 0.42, "−", ha="center", va="center", fontsize=9, zorder=4)

block(2.8, yF, 3.1, h, "Controller", "control law\n(PD / PID)", COLORS["accent"])
block(6.8, yF, 3.2, h, "Actuators", "wheels, magnetorquers,\nthrusters", COLORS["accent"])
block(10.8, yF, 4.0, h, "Spacecraft dynamics", "$I\\dot{\\omega} + \\omega \\times I\\omega = T_{ext} + T_{ctrl}$",
      COLORS["ink"])

# reference input
arrow((0.3, sj[1]), (sj[0] - 0.3, sj[1]), "reference\nattitude $q_{ref}$", lx=-0.1, ly=0.75)
arrow((sj[0] + 0.3, sj[1]), (2.8, sj[1]), "error", lx=-0.08, ly=0.42)
arrow((5.9, sj[1]), (6.8, sj[1]), "torque\ndemand", ly=0.9)
arrow((10.0, sj[1]), (10.8, sj[1]), "$T_{ctrl}$", ly=0.35)

# disturbance torques injected at the plant
block(10.4, 6.7, 4.8, 1.3, "Disturbance torques $T_{ext}$",
      "gravity gradient, drag, SRP,\nresidual magnetic dipole (§10.2)", COLORS["accent_2"], filled=False)
arrow((12.8, 6.7), (12.8, yF + h + 0.02), color=COLORS["accent_2"])

# output: true attitude
out = (15.4, sj[1])
wire([(14.8, sj[1]), (out[0], sj[1])])
ax.add_patch(Circle(out, 0.07, color=COLORS["ink"], zorder=5))
ax.text(15.6, sj[1] + 0.35, "true\nattitude\n$q, \\omega$", ha="right", va="bottom", fontsize=7.5)

# feedback path (y = 1.6)
yB = 1.2
block(10.0, yB, 3.6, h, "Sensors", "star tracker, Sun sensors,\nmagnetometer, gyros", COLORS["accent_3"])
block(3.6, yB, 4.0, h, "Attitude estimator", "Kalman filter fuses the\nmeasurements into $\\hat{q}, \\hat{\\omega}$",
      COLORS["accent_3"])
wire([(out[0], sj[1]), (out[0], yB + h / 2), (13.6, yB + h / 2)])
ax.add_patch(FancyArrowPatch((13.65, yB + h / 2), (13.6, yB + h / 2), arrowstyle="-|>",
                             mutation_scale=13, color=COLORS["ink"], lw=1.4, zorder=4))
arrow((10.0, yB + h / 2), (7.6, yB + h / 2), "measurements", ly=0.3)
wire([(3.6, yB + h / 2), (sj[0], yB + h / 2)])
arrow((sj[0], yB + h / 2), (sj[0], sj[1] - 0.3), "estimated\nattitude $\\hat{q}$", lx=-0.1, ly=0, ha="right")

# sensor noise injected at the sensors
ax.annotate("sensor noise, bias, misalignment", xy=(11.7, yB + h + 0.02), xytext=(11.7, yB + h + 0.75),
            ha="center", va="bottom", fontsize=7.5, color=COLORS["grey"],
            arrowprops=dict(arrowstyle="-|>", color=COLORS["grey"], lw=1.1, mutation_scale=11))

ax.text(0.3, 0.3, "The loop runs in the flight software; the same structure applies to every "
        "sensor/actuator architecture in this chapter.", fontsize=7.5, style="italic",
        color=COLORS["grey"], va="bottom")

save(fig, Path(__file__).stem)
