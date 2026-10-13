"""Cost S-curve for the EOSat-3U bottom-up estimate (Chapter 16 §16.1.6, 456.8 kEUR)
from a Monte Carlo over the cost-element distributions of §16.4.1, with P50/P70/P80
marked.  numpy only (no scipy)."""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from oer_style import apply_style, COLORS, save

apply_style()
rng = np.random.default_rng(16)
N = 200_000


def normal(cbe, s):      # ± s (1σ) of the estimate
    return rng.normal(cbe, s * cbe, N)


def lognormal(cbe, s):   # median = CBE, σ of ln(cost) = s → right-skewed
    return cbe * np.exp(rng.normal(0.0, s, N))


def triangular(cbe, s):  # mode = CBE, bounds ± s
    return rng.triangular(cbe * (1 - s), cbe, cbe * (1 + s), N)


def uniform(cbe, s):     # bounds ± s
    return rng.uniform(cbe * (1 - s), cbe * (1 + s), N)


# §16.1.6 bottom-up column (kEUR) mapped onto the §16.4.1 element classes
elements = [
    ("COTS bus hardware (5.0)",   102.7, normal,     0.10),
    ("Custom payload (4.0)",       58.0, lognormal,  0.30),
    ("Integration and test (6.0)", 19.3, lognormal,  0.25),
    ("Software (7.0)",             12.9, triangular, 0.40),
    ("PM / SE / MA (1.0–3.0)",     20.9, uniform,    0.25),
    ("Launch (8.0)",              195.0, normal,     0.15),
    ("Ground segment (9.0)",        8.0, normal,     0.10),
    ("Operations (10.0)",          40.0, uniform,    0.25),
]
total = sum(f(c, s) for _, c, f, s in elements)
cbe = sum(c for _, c, _, _ in elements)
p50, p70, p80 = np.percentile(total, [50, 70, 80])
p_cbe = (total <= cbe).mean()
print(f"CBE={cbe:.1f}  P50={p50:.1f}  P70={p70:.1f}  P80={p80:.1f}  "
      f"P70/P50={p70 / p50:.3f}  P80/P50={p80 / p50:.3f}  P(cost<=CBE)={p_cbe:.3f}")

# ---- figure
fig, ax = plt.subplots(figsize=(7.3, 4.3))
xs = np.sort(total)
cdf = np.arange(1, N + 1) / N
ax.plot(xs, cdf, color=COLORS["accent"], lw=2.2, label="cumulative probability (S-curve)")

# histogram (density) behind, on a twin axis
ax2 = ax.twinx()
ax2.hist(total, bins=80, density=True, color=COLORS["band"], edgecolor="none", zorder=0)
ax2.set_yticks([])
ax2.set_ylim(0, ax2.get_ylim()[1] * 2.6)
ax2.grid(False)
ax2.spines["right"].set_visible(False)
ax2.spines["top"].set_visible(False)
ax.set_zorder(ax2.get_zorder() + 1)
ax.patch.set_visible(False)

xlo, xhi = 380, 560
ax.set_xlim(xlo, xhi)
ax.set_ylim(0, 1.0)
ax.set_xlabel("Total mission cost (kEUR)")
ax.set_ylabel("Probability that cost ≤ x")
ax.set_yticks([0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0])

# confidence levels
for p, val, c in [(0.5, p50, COLORS["accent_3"]), (0.7, p70, COLORS["accent_5"]),
                  (0.8, p80, COLORS["accent_2"])]:
    ax.plot([xlo, val], [p, p], color=c, lw=1.0, ls="--")
    ax.plot([val, val], [0, p], color=c, lw=1.0, ls="--")
    ax.plot(val, p, "o", color=c, ms=6, zorder=5)
    ax.text(val + 2, p - 0.035, f"P{int(p * 100)} = {val:.0f} kEUR", ha="left", va="top",
            fontsize=8.5, color=c, fontweight="bold")

# current best estimate (point estimate)
ax.plot([cbe, cbe], [0, p_cbe], color=COLORS["ink"], lw=1.2)
ax.plot(cbe, p_cbe, "s", color=COLORS["ink"], ms=5, zorder=5)
ax.annotate(f"point estimate (CBE)\n{cbe:.1f} kEUR → P{p_cbe * 100:.0f}", xy=(cbe, p_cbe),
            xytext=(cbe - 14, 0.62), ha="right", va="top", fontsize=8.5,
            arrowprops=dict(arrowstyle="-|>", color=COLORS["ink"], lw=0.9), linespacing=1.2)
ax.text(p80 + 10, 0.06, "right-skewed tail →", ha="left", va="bottom", fontsize=8,
        style="italic", color=COLORS["grey"])
ax.text((p50 + p80) / 2 + 9, 0.285, "cost reserve P50 → P80\n" + f"= {p80 - p50:.0f} kEUR",
        ha="center", va="bottom", fontsize=8.5, color=COLORS["accent_2"], linespacing=1.2)
ax.annotate("", xy=(p80, 0.26), xytext=(p50, 0.26),
            arrowprops=dict(arrowstyle="<->", color=COLORS["accent_2"], lw=1.0))

# element legend (distribution classes)
txt = "Monte Carlo, 200 000 draws, elements independent:\n" + "\n".join(
    f"  {n}: {f.__name__}, ± {int(s * 100)} %" for n, _, f, s in elements)
ax.text(0.02, 0.98, txt, transform=ax.transAxes, ha="left", va="top", fontsize=8,
        color=COLORS["ink"], linespacing=1.25,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=COLORS["grey_light"]))

save(fig, Path(__file__).stem)
