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
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _thesis_style as ts  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "results/analysis"
VIS = BASE / "figures"
VIS.mkdir(exist_ok=True)


def fig_within_between():
    cat = {r["prompt_id"]: r["category_id"] for r in
           csv.DictReader(open(CLEAN / "scaleup_human_reviewed_coding_sheet.csv"))}
    rows = list(csv.DictReader(open(CLEAN / "lexical_within_between/within_between_rows.csv")))
    fig, ax = plt.subplots(figsize=(6.8, 5.6))
    # shaded region: below the diagonal = "API closer to its own re-runs than to the app"
    ax.fill_between([0, 1], [0, 1], 0, color=ts.BLUE, alpha=0.04, zorder=0)
    ax.plot([0, 1], [0, 1], ls="--", lw=1.1, color="#9AA1A8", zorder=1)
    ax.annotate("equal similarity", xy=(0.70, 0.70), rotation=39, fontsize=9,
                color="#7A828A", ha="center", va="bottom")
    for c in "ABCDEF":
        xs = [float(r["within_j_mean"]) for r in rows if cat[r["prompt_id"]] == c]
        ys = [float(r["between_j_r1_app"]) for r in rows if cat[r["prompt_id"]] == c]
        ax.scatter(xs, ys, s=58, alpha=0.9, color=ts.CATEGORY_COLORS[c],
                   label=ts.CATEGORY_LABELS[c], edgecolor="white", linewidth=0.8, zorder=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Within-channel similarity\n(mean token Jaccard, OpenAI API r1/r2/r3 pairs)")
    ax.set_ylabel("Between-channel similarity\n(token Jaccard, API r1 vs ChatGPT app)")
    ax.set_title("API self-similarity vs API–app similarity\nper prompt (n = 60)")
    ax.legend(loc="upper left", handletextpad=0.3, borderpad=0.4, labelspacing=0.35)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(VIS / "within_between_scatter.png")
    plt.close(fig)


def fig_agreement_heatmap():
    data = json.load(open(CLEAN / "channel_agreement/channel_agreement.json"))
    pair = data["refusal_pairwise"]
    chans = ["openai_api", "chatgpt_app", "claude_api", "gemini_api"]
    labels = [ts.CHANNEL_LABELS[c] for c in chans]
    M = np.ones((4, 4))
    for i, a in enumerate(chans):
        for j, b in enumerate(chans):
            if i == j:
                continue
            key = f"{a}__{b}" if f"{a}__{b}" in pair else f"{b}__{a}"
            M[i, j] = pair[key]["agreement"]

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    masked = np.ma.masked_where(np.eye(4, dtype=bool), M)
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad("#F2F3F4")  # diagonal in light gray
    im = ax.imshow(masked, vmin=0.85, vmax=1.0, cmap=cmap)
    # crisp white cell borders
    ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 4, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2.5)
    ax.tick_params(which="minor", length=0)
    ax.grid(which="major", visible=False)
    ax.set_xticks(range(4), labels)
    ax.set_yticks(range(4), labels)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i in range(4):
        for j in range(4):
            if i == j:
                ax.text(j, i, "—", ha="center", va="center", color="#B3B8BD", fontsize=12)
            else:
                v = M[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        color="white" if v > 0.955 else ts.INK,
                        fontsize=11.5, fontweight="medium")
    ax.set_title("Refusal-posture agreement between channels\n(60 prompts)")
    cb = fig.colorbar(im, ax=ax, shrink=0.82, pad=0.03)
    cb.set_label("Proportion of prompts with the same label", fontsize=10)
    cb.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(VIS / "channel_agreement_heatmap.png")
    plt.close(fig)


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(10.2, 4.8))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    def box(cx, cy, w, h, text, fc="#EAF1F8", ec=ts.BLUE, fs=8.2, wrap=22):
        x, y = cx - w / 2, cy - h / 2
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.022",
            fc=fc, ec=ec, lw=1.5, mutation_aspect=2.1, zorder=2))
        wrapped = "\n".join(textwrap.fill(ln, width=wrap, break_long_words=False)
                            for ln in text.split("\n"))
        ax.text(cx, cy, wrapped, ha="center", va="center", fontsize=fs,
                linespacing=1.25, color=ts.INK, zorder=3)
        return dict(l=x, r=x + w, t=y + h, b=y, cx=cx, cy=cy)

    def arrow(p1, p2):
        ax.annotate("", xy=p2, xytext=p1, zorder=1,
                    arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#5A6168",
                                    shrinkA=1, shrinkB=1))

    bank = box(0.095, 0.50, 0.17, 0.34,
               "Frozen 60-prompt bank\n6 categories\nbenchmark-grounded\nhigh-risk rows redacted", fs=8.0)
    api = box(0.375, 0.78, 0.21, 0.22,
              "OpenAI Responses API\ngpt-4o · no system prompt\nr2/r3 repetitions")
    basel = box(0.375, 0.50, 0.21, 0.13, "Claude & Gemini APIs\nvendor baselines",
                fc="#F1F2F3", ec="#9AA1A8", fs=7.9)
    app = box(0.375, 0.22, 0.21, 0.22,
              "ChatGPT consumer app\nscreenshot-backed\nmanual collection")
    qa = box(0.625, 0.22, 0.17, 0.22,
             "Transcription QA\nvalidation gate\nprompt-echo cleaning\nscreenshot corrections", fs=7.9)
    score = box(0.80, 0.50, 0.16, 0.30, "Pairwise scoring\nmanual review\nsix final labels")
    out1 = box(0.945, 0.70, 0.10, 0.24, "17 cases\n10 core\n7 surface",
               fc="#FBEAE7", ec=ts.RED, fs=8.0, wrap=12)
    out2 = box(0.945, 0.30, 0.10, 0.24, "Stats\nsensitivity\nstability\nIRR",
               fc="#FBEAE7", ec=ts.RED, fs=8.0, wrap=12)

    arrow((bank["r"], 0.58), (api["l"], api["cy"]))
    arrow((bank["r"], 0.50), (basel["l"], basel["cy"]))
    arrow((bank["r"], 0.42), (app["l"], app["cy"]))
    arrow((app["r"], app["cy"]), (qa["l"], qa["cy"]))
    arrow((api["r"], api["cy"]), (score["l"], 0.60))
    arrow((basel["r"], basel["cy"]), (score["l"], 0.50))
    arrow((qa["r"], qa["cy"]), (score["l"], 0.40))
    arrow((score["r"], 0.56), (out1["l"], out1["cy"]))
    arrow((score["r"], 0.44), (out2["l"], out2["cy"]))

    fig.tight_layout()
    fig.savefig(VIS / "study_design_pipeline.png")
    plt.close(fig)


if __name__ == "__main__":
    ts.apply()
    fig_within_between()
    fig_agreement_heatmap()
    fig_pipeline()
    print("wrote:",
          VIS / "within_between_scatter.png",
          VIS / "channel_agreement_heatmap.png",
          VIS / "study_design_pipeline.png", sep="\n  ")
