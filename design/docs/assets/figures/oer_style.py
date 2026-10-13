"""
Shared style module for the Concurrent Spacecraft Design open textbook figures.

Neutral, print-safe palette (works in greyscale), no institutional branding,
no watermark. Every generator in this directory should:

    from oer_style import apply_style, COLORS, SERIES, save
    apply_style()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ...
    save(fig, "fig_name")          # writes fig_name.png next to this file

`save()` uses bbox_inches="tight" with a small pad; keep every annotation
inside the axes (use annotation_clip=True or clip_on=True) so the canvas is
not stretched by stray text.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent

# Colour-blind-safe, greyscale-distinct palette (Okabe–Ito based)
COLORS = {
    "ink": "#1f1f1f",          # text, axes
    "accent": "#1f4e79",       # primary line / emphasis (deep blue)
    "accent_2": "#c55a11",     # secondary (burnt orange)
    "accent_3": "#2e7d32",     # tertiary (green)
    "accent_4": "#6a1b9a",     # quaternary (purple)
    "accent_5": "#b8860b",     # (dark goldenrod)
    "accent_6": "#00838f",     # (teal)
    "grey": "#6e6e6e",
    "grey_light": "#bdbdbd",
    "band": "#e8eef5",         # shaded bands / highlight regions
    "band_2": "#fdf0e6",
    "white": "#ffffff",
    # Interface-type codes used in N² figures (distinct in colour AND lightness)
    "M": "#8d6e63",            # mechanical — brown
    "E": "#1f4e79",            # electrical — blue
    "T": "#c55a11",            # thermal — orange
    "D": "#2e7d32",            # data — green
    "R": "#6a1b9a",            # RF — purple
    "O": "#b8860b",            # optical — gold
    "S": "#00838f",            # software — teal
    "diag": "#1f1f1f",         # diagonal cells
}

SERIES = [
    COLORS["accent"], COLORS["accent_2"], COLORS["accent_3"],
    COLORS["accent_4"], COLORS["accent_5"], COLORS["accent_6"], COLORS["grey"],
]


def apply_style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.edgecolor": COLORS["ink"],
        "axes.labelcolor": COLORS["ink"],
        "xtick.color": COLORS["ink"],
        "ytick.color": COLORS["ink"],
        "text.color": COLORS["ink"],
        "axes.prop_cycle": mpl.cycler(color=SERIES),
        "axes.grid": True,
        "grid.color": COLORS["grey_light"],
        "grid.linewidth": 0.5,
        "grid.alpha": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 200,
        "lines.linewidth": 2.0,
    })


def save(fig, name: str, *, pad: float = 0.15) -> Path:
    """Save `fig` as <name>.png beside this module. Returns the path."""
    out = HERE / f"{name}.png"
    fig.savefig(out, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    print(f"OK {name} -> {out.name}")
    return out


def add_note(ax, text: str, loc: str = "lower right", **kw) -> None:
    """Small italic note inside the axes (replacement for the old footer)."""
    x, y, ha, va = {
        "lower right": (0.99, 0.02, "right", "bottom"),
        "lower left": (0.01, 0.02, "left", "bottom"),
        "upper right": (0.99, 0.98, "right", "top"),
        "upper left": (0.01, 0.98, "left", "top"),
    }[loc]
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va,
            fontsize=8, style="italic", color=COLORS["grey"], clip_on=True, **kw)
