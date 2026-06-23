#!/usr/bin/env python3
"""Shared clean-academic styling for all thesis figures.

Centralizes the colour palette, human-readable category/channel labels, and
matplotlib rcParams so every figure looks consistent and print-friendly.
Import and call ``apply()`` at the top of each figure script.
"""
from __future__ import annotations

import matplotlib as mpl

# --- Colourblind-safe palette (Okabe-Ito derived, softened for print) ---------
BLUE = "#3B6EA5"     # primary
RED = "#C0413B"      # accent / focal (OpenAI API, refusal story)
ORANGE = "#E08A3C"
GREEN = "#4E9B6B"
PURPLE = "#7E6BAE"
BROWN = "#8C6D55"
GRAY = "#A6ADB4"     # muted (non-focal baselines)
INK = "#2A2D31"      # text / ticks
GRID = "#E2E6EA"

# --- Six prompt categories: stable colour + readable label thesis-wide --------
CATEGORY_COLORS = {"A": BLUE, "B": RED, "C": ORANGE, "D": GREEN, "E": PURPLE, "F": BROWN}

CATEGORY_LABELS = {
    "A": "A  Allowed-sensitive",
    "B": "B  Refusal-expected",
    "C": "C  Boundary / framing",
    "D": "D  Instruction-following",
    "E": "E  Social recommendation",
    "F": "F  Factual control",
}

# compact two-line labels for crowded x-axes
CATEGORY_AXIS = {
    "A": "A\nAllowed-\nsensitive",
    "B": "B\nRefusal-\nexpected",
    "C": "C\nBoundary /\nframing",
    "D": "D\nInstruction-\nfollowing",
    "E": "E\nSocial\nrec.",
    "F": "F\nFactual\ncontrol",
}

# --- Four collection channels -------------------------------------------------
CHANNEL_LABELS = {
    "openai_api": "OpenAI\nAPI",
    "chatgpt_app": "ChatGPT\napp",
    "claude_api": "Claude\nAPI",
    "gemini_api": "Gemini\nAPI",
}
# Focal contrast (OpenAI API vs ChatGPT app) carries colour; baselines muted.
CHANNEL_COLORS = {
    "openai_api": RED,
    "chatgpt_app": BLUE,
    "claude_api": GRAY,
    "gemini_api": GRAY,
}


def apply() -> None:
    """Apply the shared rcParams. Call once at the start of a figure script."""
    mpl.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 11,
        "axes.titlesize": 12.5,
        "axes.titleweight": "semibold",
        "axes.titlepad": 10,
        "axes.labelsize": 11,
        "axes.labelcolor": INK,
        "axes.edgecolor": "#9AA1A8",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9.5,
        "legend.frameon": False,
        "text.color": INK,
    })


def value_label(ax, x, y, text, dy=0.012, **kw):
    """Place a small value label above a point/bar consistently."""
    ax.annotate(text, (x, y), xytext=(0, 6), textcoords="offset points",
                ha="center", va="bottom", fontsize=kw.pop("fontsize", 9.5),
                color=INK, **kw)
