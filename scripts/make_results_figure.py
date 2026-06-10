#!/usr/bin/env python3
"""Generate the Results summary figure from the cleaned statistics JSON.

Left panel: substantive divergence rate by category with Wilson 95% CIs.
Right panel: full refusals on refusal-expected prompts by channel.
Reads scaleup_statistics.json (compute_scaleup_statistics.py must run first).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    ("allowed_sensitive_over_refusal", "A allowed-\nsensitive"),
    ("disallowed_refusal_expected", "B refusal-\nexpected"),
    ("boundary_safety_framing", "C boundary/\nframing"),
    ("instruction_following", "D instruction"),
    ("social_recommendation", "E social\nrec."),
    ("neutral_factual_control", "F factual\ncontrol"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    base = ROOT / "results/analysis"
    ap.add_argument("--stats", type=Path, default=base / "scaleup_statistics.json")
    ap.add_argument("--summary", type=Path, default=base / "results_summary.json")
    ap.add_argument("--out", type=Path, default=ROOT / "figures/results_divergence_summary.png")
    args = ap.parse_args()

    stats = json.loads(args.stats.read_text())
    props = stats["substantive_proportions"]
    summary = json.loads(args.summary.read_text())
    cats = [lbl for k, lbl in ORDER]
    pr = [props[k]["k"] / props[k]["n"] for k, _ in ORDER]
    ks = [props[k]["k"] for k, _ in ORDER]
    ns = [props[k]["n"] for k, _ in ORDER]
    los = [props[k]["k"] / props[k]["n"] - props[k]["wilson95"][0] for k, _ in ORDER]
    his = [props[k]["wilson95"][1] - props[k]["k"] / props[k]["n"] for k, _ in ORDER]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    xp = range(len(cats))
    ax1.bar(xp, pr, color="#4C78A8", alpha=.85)
    ax1.errorbar(xp, pr, yerr=[los, his], fmt="none", ecolor="black", capsize=4, lw=1)
    ax1.set_xticks(list(xp)); ax1.set_xticklabels(cats, fontsize=8)
    ax1.set_ylabel("Substantive divergence rate"); ax1.set_ylim(0, 1)
    ax1.set_title("Substantive API–app divergence by category\n(Wilson 95% CI)", fontsize=10)
    for i, (k, n) in enumerate(zip(ks, ns)):
        ax1.text(i, pr[i] + max(his) * 0.15 + .02, f"{k}/{n}", ha="center", fontsize=8)

    channel_counts = summary["category_status_counts"]
    key = "disallowed_refusal_expected:full_refusal"
    ch = ["OpenAI\nAPI", "ChatGPT\napp", "Claude\nAPI", "Gemini\nAPI"]
    fr = [
        channel_counts.get("openai_api", {}).get(key, 0),
        channel_counts.get("chatgpt_app", {}).get(key, 0),
        channel_counts.get("claude_api", {}).get(key, 0),
        channel_counts.get("gemini_api", {}).get(key, 0),
    ]
    p_value = stats["refusal_mcnemar"]["category_B_refusal_expected"]["p_value_exact"]
    ax2.bar(ch, fr, color=["#E45756", "#54A24B", "#9D755D", "#B279A2"], alpha=.85)
    ax2.set_ylabel("Full refusals (of 10)"); ax2.set_ylim(0, 10)
    ax2.set_title(f"Full refusals on refusal-expected prompts\n(McNemar API vs app: p={p_value:.3f})", fontsize=10)
    for i, v in enumerate(fr):
        ax2.text(i, v + .15, str(v), ha="center", fontsize=9)

    plt.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.out, dpi=150, bbox_inches="tight")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
