#!/usr/bin/env python3
"""Generate the three additional thesis figures from existing analysis outputs.

  1. within_between_scatter.png  - per-prompt within-channel vs between-channel
     token Jaccard (all 60 prompts), colored by category.
  2. channel_agreement_heatmap.png - pairwise refusal-posture agreement among
     the four channels.
  3. study_design_pipeline.png  - schematic of the audit pipeline (Methods).

All values are read from generated artifacts; nothing is hard-coded except the
pipeline schematic labels.
"""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "results/analysis"
VIS = BASE / "figures"
VIS.mkdir(exist_ok=True)

CAT_NAMES = {
    "A": "A allowed-sensitive", "B": "B refusal-expected", "C": "C boundary",
    "D": "D instruction", "E": "E social control", "F": "F factual control",
}
CAT_COLORS = {
    "A": "#4C72B0", "B": "#C44E52", "C": "#DD8452",
    "D": "#55A868", "E": "#8172B3", "F": "#937860",
}


def fig_within_between():
    cat = {r["prompt_id"]: r["category_id"] for r in
           csv.DictReader(open(CLEAN / "scaleup_human_reviewed_coding_sheet.csv"))}
    rows = list(csv.DictReader(open(CLEAN / "lexical_within_between/within_between_rows.csv")))
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    for c in "ABCDEF":
        xs = [float(r["within_j_mean"]) for r in rows if cat[r["prompt_id"]] == c]
        ys = [float(r["between_j_r1_app"]) for r in rows if cat[r["prompt_id"]] == c]
        ax.scatter(xs, ys, s=42, alpha=0.85, color=CAT_COLORS[c], label=CAT_NAMES[c],
                   edgecolor="white", linewidth=0.6)
    lim = 1.0
    ax.plot([0, lim], [0, lim], ls="--", lw=1, color="gray", zorder=0)
    ax.annotate("equal similarity", xy=(0.62, 0.66), rotation=38, fontsize=8.5,
                color="gray")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Within-channel similarity\n(mean token Jaccard, OpenAI API r1/r2/r3 pairs)")
    ax.set_ylabel("Between-channel similarity\n(token Jaccard, API r1 vs ChatGPT app)")
    ax.set_title("API self-similarity vs API–app similarity, per prompt (n = 60)")
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9)
    ax.grid(alpha=0.25, lw=0.5)
    fig.tight_layout()
    fig.savefig(VIS / "within_between_scatter.png", dpi=200)
    plt.close(fig)


def fig_agreement_heatmap():
    data = json.load(open(CLEAN / "channel_agreement/channel_agreement.json"))
    pair = data["refusal_pairwise"]
    chans = ["openai_api", "chatgpt_app", "claude_api", "gemini_api"]
    labels = ["OpenAI\nAPI", "ChatGPT\napp", "Claude\nAPI", "Gemini\nAPI"]
    M = np.ones((4, 4))
    for i, a in enumerate(chans):
        for j, b in enumerate(chans):
            if i == j:
                continue
            key = f"{a}__{b}" if f"{a}__{b}" in pair else f"{b}__{a}"
            M[i, j] = pair[key]["agreement"]
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    im = ax.imshow(M, vmin=0.85, vmax=1.0, cmap="YlGnBu")
    ax.set_xticks(range(4), labels)
    ax.set_yticks(range(4), labels)
    for i in range(4):
        for j in range(4):
            v = M[i, j]
            ax.text(j, i, f"{v:.2f}" if i != j else "—",
                    ha="center", va="center",
                    color="white" if v > 0.955 and i != j else "black", fontsize=10)
    ax.set_title("Refusal-posture agreement between channels (60 prompts)")
    fig.colorbar(im, ax=ax, shrink=0.8, label="proportion of prompts with same label")
    fig.tight_layout()
    fig.savefig(VIS / "channel_agreement_heatmap.png", dpi=200)
    plt.close(fig)


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.axis("off")

    def box(x, y, w, h, text, fc="#EAF0F8", ec="#4C72B0", fs=8.6):
        ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.3,
                                   joinstyle="round"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#444444"))

    # column 1: prompt bank
    box(0.005, 0.40, 0.165, 0.26, "Frozen 60-prompt bank\n6 categories\n(benchmark-grounded,\nhigh-risk rows redacted)", fs=8.2)
    # column 2: two channels
    box(0.225, 0.66, 0.18, 0.22, "OpenAI Responses API\ngpt-4o, no system prompt\n+ r2/r3 repetitions")
    box(0.225, 0.14, 0.18, 0.22, "ChatGPT consumer app\nscreenshot-backed\nmanual collection")
    box(0.225, 0.42, 0.18, 0.14, "Claude / Gemini APIs\n(vendor baselines)", fc="#F4F4F4", ec="#999999", fs=8.0)
    # column 3: QA
    box(0.47, 0.14, 0.16, 0.22, "Transcription QA:\nvalidation gate,\nprompt-echo cleaning,\nscreenshot corrections")
    # column 4: scoring + review
    box(0.685, 0.40, 0.15, 0.26, "Automated pairwise\nscoring (triage)\n+ manual review\n(6 final labels)", fs=8.2)
    # column 5: outputs
    box(0.885, 0.56, 0.105, 0.26, "17 substantive\ncases, tiered\n10 / 4 / 3", fc="#FDEEE9", ec="#C44E52")
    box(0.885, 0.20, 0.105, 0.26, "Paired stats,\nsensitivity,\nstability,\nreliability prep", fc="#FDEEE9", ec="#C44E52")

    arrow(0.165, 0.62, 0.225, 0.74)
    arrow(0.165, 0.49, 0.225, 0.49)
    arrow(0.165, 0.44, 0.225, 0.27)
    arrow(0.405, 0.25, 0.47, 0.25)
    arrow(0.63, 0.27, 0.69, 0.45)
    arrow(0.405, 0.74, 0.66, 0.58)
    arrow(0.405, 0.49, 0.69, 0.51)
    arrow(0.83, 0.57, 0.885, 0.66)
    arrow(0.83, 0.48, 0.885, 0.34)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(VIS / "study_design_pipeline.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig_within_between()
    fig_agreement_heatmap()
    fig_pipeline()
    print("wrote:",
          VIS / "within_between_scatter.png",
          VIS / "channel_agreement_heatmap.png",
          VIS / "study_design_pipeline.png", sep="\n  ")
