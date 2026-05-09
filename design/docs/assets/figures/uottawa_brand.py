"""
Shared style module for SpaceCDF figures.
Applies the uOttawa Horizon brand palette and typography to matplotlib.

Usage:
    from uottawa_brand import apply_style, COLORS
    apply_style()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ...
"""
from __future__ import annotations
import matplotlib as mpl
import matplotlib.pyplot as plt

# uOttawa Horizon palette (from official brand guidelines)
COLORS = {
    "garnet": "#8f001a",        # Primary Garnet
    "garnet_2": "#9c1c30",      # Secondary Garnet
    "charcoal": "#2d2d2c",      # Charcoal Grey
    "charcoal_2": "#3a3a37",
    "warm_grey": "#80746c",
    "warm_grey_2": "#908681",
    "blue": "#636d77",
    "blue_2": "#6d7983",
    "green": "#67796c",
    "green_2": "#728479",
    "polar": "#f2f2f2",
    "white": "#ffffff",
}

# Sequenced palette for series plots (max contrast first)
SERIES = [
    COLORS["garnet"],
    COLORS["blue"],
    COLORS["green"],
    COLORS["warm_grey"],
    COLORS["charcoal"],
    COLORS["garnet_2"],
    COLORS["blue_2"],
    COLORS["green_2"],
]


def apply_style():
    """Apply the uOttawa-branded matplotlib style globally."""
    mpl.rcParams.update({
        # Typography — falls back gracefully when Work Sans/Spectral aren't installed.
        "font.family": "sans-serif",
        "font.sans-serif": ["Work Sans", "DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.labelweight": "regular",
        # Colours
        "axes.edgecolor": COLORS["charcoal"],
        "axes.labelcolor": COLORS["charcoal"],
        "xtick.color": COLORS["charcoal"],
        "ytick.color": COLORS["charcoal"],
        "text.color": COLORS["charcoal"],
        "axes.titlecolor": COLORS["charcoal"],
        # Spines & grid
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": COLORS["polar"],
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        # Lines
        "lines.linewidth": 2.0,
        "axes.prop_cycle": mpl.cycler(color=SERIES),
        # Figure
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "figure.dpi": 110,
    })


def add_footer(fig, doc_title: str = "SpaceCDF · uOttawa SEDTI"):
    """Draw a subtle bottom-right wordmark on a figure."""
    fig.text(
        0.99, 0.005, doc_title,
        ha="right", va="bottom",
        fontsize=7, color=COLORS["warm_grey"], alpha=0.9,
    )
