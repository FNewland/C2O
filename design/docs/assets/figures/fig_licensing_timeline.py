"""Licensing timeline for a Canadian CubeSat overlaid on the Phase A–D schedule (Ch 2 §2.7.4).

Schedule: the Chapter 2 Problem 4 project (SRR ≈ month 4, PDR month 9, CDR
month 18, launch month 30). Regulatory durations are the indicative values of
Table 2.1 (ISED pre-application 2–4 weeks; ISED technical review 3–6 months;
ITU coordination 2–7 years) and of §2.6/§2.8 (RSSSA licence and export permits
must be in hand before launch; apply early). The bars are indicative, not a
prediction for any particular mission.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from oer_style import apply_style, COLORS, save

apply_style()

fig, ax = plt.subplots(figsize=(6.9, 3.9))
T_END = 30

# --- lifecycle phases (top band) --------------------------------------------
phases = [("Phase A", 0, 4), ("Phase B", 4, 9), ("Phase C", 9, 18), ("Phase D", 18, 30)]
cols = [COLORS["accent"], COLORS["accent_3"], COLORS["accent_5"], COLORS["accent_2"]]
y_ph = 8.0
for (name, a, b), c in zip(phases, cols):
    ax.add_patch(Rectangle((a, y_ph - 0.35), b - a, 0.7, facecolor=c, alpha=0.85, lw=0))
    ax.text((a + b) / 2, y_ph, name, ha="center", va="center", color="white",
            fontsize=8.5, fontweight="bold")
for m, lab in [(4, "SRR"), (9, "PDR"), (18, "CDR"), (30, "Launch")]:
    ax.axvline(m, color=COLORS["grey"], lw=0.8, ls=":", zorder=0)
    ax.text(m, y_ph + 0.55, lab, ha="center", va="bottom", fontsize=8, color=COLORS["ink"])

# --- regulatory tasks (bars) -------------------------------------------------
# (label, start, end, colour, note)
tasks = [
    ("ISED pre-application (2–4 wk)", 3.0, 4.0, COLORS["accent"], ""),
    ("ISED technical review (3–6 mo)", 4.0, 10.0, COLORS["accent"], ""),
    ("ITU coordination (2–7 yr)", 6.0, 30.0, COLORS["accent_2"], "critical path"),
    ("RSSSA operating licence (EO)", 9.0, 24.0, COLORS["accent_3"], ""),
    ("Export permits (EIPA; ITAR TAA)", 18.0, 27.0, COLORS["accent_4"], ""),
]
for i, (lab, a, b, c, note) in enumerate(tasks):
    y = 6.5 - i * 1.2
    ax.add_patch(Rectangle((a, y - 0.3), b - a, 0.6, facecolor=c, alpha=0.85, lw=0))
    if note:
        ax.text((a + b) / 2, y, note, ha="center", va="center", fontsize=7.5,
                color="white", style="italic", fontweight="bold")
# ITU coordination may run past launch: hatched extension
ax.add_patch(Rectangle((30, 6.5 - 2 * 1.2 - 0.3), 2.5, 0.6, facecolor="none",
                       edgecolor=COLORS["accent_2"], hatch="///", lw=0.8, clip_on=True))

# --- milestones (diamonds) ---------------------------------------------------
ms = [
    (4.0, 6.5, "formal application"),
    (6.0, 6.5 - 2 * 1.2, "ITU API filing (by ISED)"),
    (29.0, 6.5 - 2 * 1.2, "MIFR entry;\nradio licence"),
]
for x, y, lab in ms:
    ax.plot(x, y, marker="D", ms=7, color=COLORS["ink"], zorder=5)
ax.text(4.4, 6.5 + 0.42, "formal application", ha="left", va="bottom", fontsize=7.5, style="italic")
ax.text(6.0, 6.5 - 2 * 1.2 - 0.45, "ITU API filing (by ISED)", ha="left", va="top",
        fontsize=7.5, style="italic")
ax.text(28.6, 6.5 - 2 * 1.2 - 0.45, "MIFR entry → radio licence", ha="right", va="top",
        fontsize=7.5, style="italic")

ax.text(0.4, 0.55, "Start spectrum work in Phase A: ITU coordination alone can take\n"
        "longer than the whole development schedule.", fontsize=8, style="italic",
        color=COLORS["grey"], va="bottom",
        bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none"))

ax.set_xlim(0, 32.5)
ax.set_ylim(0.3, 9.3)
ax.set_xlabel("Months after project kick-off")
ax.set_xticks(range(0, 31, 3))
ax.set_yticks([6.5 - i * 1.2 for i in range(len(tasks))])
ax.set_yticklabels([t[0] for t in tasks], fontsize=8)
ax.tick_params(axis="y", length=0)
ax.grid(False)
ax.spines["left"].set_visible(False)
save(fig, Path(__file__).stem)
