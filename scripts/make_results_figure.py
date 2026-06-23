#!/usr/bin/env python3
"""Generate the Results summary figure from the cleaned statistics JSON.

Left panel: substantive divergence rate by category with Wilson 95% CIs.
Right panel: full refusals on refusal-expected prompts by channel.
Reads scaleup_statistics.json (compute_scaleup_statistics.py must run first).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _thesis_style as ts  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    ("allowed_sensitive_over_refusal", "A"),
    ("disallowed_refusal_expected", "B"),
    ("boundary_safety_framing", "C"),
    ("instruction_following", "D"),
    ("social_recommendation", "E"),
    ("neutral_factual_control", "F"),
]
CHANNELS = ["openai_api", "chatgpt_app", "claude_api", "gemini_api"]


def main() -> int:
    ap = argparse.ArgumentParser()
    base = ROOT / "results/analysis"
    ap.add_argument("--stats", type=Path, default=base / "scaleup_statistics.json")
    ap.add_argument("--summary", type=Path, default=base / "results_summary.json")
    ap.add_argument("--out", type=Path, default=ROOT / "figures/results_divergence_summary.png")
    args = ap.parse_args()

    ts.apply()
    stats = json.loads(args.stats.read_text())
    props = stats["substantive_proportions"]
    summary = json.loads(args.summary.read_text())

    letters = [c for _, c in ORDER]
    colors = [ts.CATEGORY_COLORS[c] for c in letters]
    axis_lbl = [ts.CATEGORY_AXIS[c] for c in letters]
    pr = [props[k]["k"] / props[k]["n"] for k, _ in ORDER]
    ks = [props[k]["k"] for k, _ in ORDER]
    ns = [props[k]["n"] for k, _ in ORDER]
    los = [props[k]["k"] / props[k]["n"] - props[k]["wilson95"][0] for k, _ in ORDER]
    his = [props[k]["wilson95"][1] - props[k]["k"] / props[k]["n"] for k, _ in ORDER]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.6))

    # --- Left: divergence rate by category --------------------------------
    xp = list(range(len(letters)))
    ax1.bar(xp, pr, color=colors, width=0.68, zorder=3)
    ax1.errorbar(xp, pr, yerr=[los, his], fmt="none", ecolor=ts.INK,
                 capsize=4, lw=1.1, zorder=4)
    for i in xp:
        ts.value_label(ax1, i, pr[i] + his[i], f"{ks[i]}/{ns[i]}")
    ax1.set_xticks(xp)
    ax1.set_xticklabels(axis_lbl, fontsize=8.8, linespacing=1.15)
    ax1.set_ylabel("Substantive divergence rate")
    ax1.set_ylim(0, 1)
    ax1.set_yticks([0, .2, .4, .6, .8, 1.0])
    ax1.grid(axis="x", visible=False)
    ax1.set_title("Substantive API–app divergence by category\n(Wilson 95% CI)")

    # --- Right: full refusals by channel ----------------------------------
    key = "disallowed_refusal_expected:full_refusal"
    ch_counts = summary["category_status_counts"]
    fr = [ch_counts.get(c, {}).get(key, 0) for c in CHANNELS]
    ch_colors = [ts.CHANNEL_COLORS[c] for c in CHANNELS]
    ch_labels = [ts.CHANNEL_LABELS[c] for c in CHANNELS]
    p_value = stats["refusal_mcnemar"]["category_B_refusal_expected"]["p_value_exact"]

    xc = list(range(len(CHANNELS)))
    ax2.bar(xc, fr, color=ch_colors, width=0.66, zorder=3)
    for i, v in enumerate(fr):
        ts.value_label(ax2, i, v, str(v))
    ax2.set_xticks(xc)
    ax2.set_xticklabels(ch_labels, linespacing=1.15)
    ax2.set_ylabel("Full refusals (of 10)")
    ax2.set_ylim(0, 10)
    ax2.grid(axis="x", visible=False)
    ax2.set_title(f"Full refusals on refusal-expected prompts\n"
                  f"(McNemar API vs app: $p = {p_value:.4f}$)")

    fig.tight_layout(w_pad=3.0)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
