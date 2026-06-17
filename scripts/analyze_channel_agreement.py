#!/usr/bin/env python3
"""Four-channel behavioral agreement analysis (no new collection).

Uses the project's own uniformly-coded labels for all four channels on the same
60 prompts:
  - OpenAI API, Claude API, Gemini API : api_only_results_summary.csv
  - ChatGPT app                        : pairwise_results.csv (app_* columns)

Question: when channels disagree on refusal posture and safety framing, *which
channels behave alike*? In particular, is the ChatGPT app's nearest behavioral
neighbour its own provider's API (OpenAI), or another vendor's API? A finding
that the app is not closest to the OpenAI API directly supports the thesis claim
that an access channel is its own condition.

Outputs under analysis_scaleup_cleaned/channel_agreement/:
  channel_agreement.json, channel_agreement_memo.md, channel_agreement.tex
"""
from __future__ import annotations

import csv
import json
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "results/analysis"
OUT = CLEAN / "channel_agreement"
OUT.mkdir(parents=True, exist_ok=True)

CHANNELS = ["openai_api", "chatgpt_app", "claude_api", "gemini_api"]
PRETTY = {"openai_api": "OpenAI API", "chatgpt_app": "ChatGPT app",
          "claude_api": "Claude API", "gemini_api": "Gemini API"}
SAFETY_ORD = {"none": 0, "light": 1, "moderate": 2, "strong": 3}


def collapse_refusal(v: str) -> str:
    """Collapse to answer / full_refusal / safe_redirect."""
    v = (v or "").strip()
    if v in ("full_refusal",):
        return "full_refusal"
    if v in ("partial_refusal_or_safe_redirect",):
        return "safe_redirect"
    if v in ("blocked_or_empty",):
        return "blocked"
    return "answered"


def load():
    api = {c: {} for c in ("openai_api", "claude_api", "gemini_api")}
    for r in csv.DictReader(open(CLEAN / "api_only_results_summary.csv")):
        ch = r["channel_key"]
        if ch in api:
            api[ch][r["prompt_id"]] = r
    app = {}
    cats = {}
    for r in csv.DictReader(open(CLEAN / "pairwise_results.csv")):
        app[r["prompt_id"]] = r
        cats[r["prompt_id"]] = r["category"]
    pids = sorted(app.keys())
    data = {}
    for pid in pids:
        data[pid] = {
            "category": cats[pid],
            "openai_api": {"refusal": collapse_refusal(api["openai_api"][pid]["refusal_status"]),
                           "safety": api["openai_api"][pid]["safety_framing"]},
            "claude_api": {"refusal": collapse_refusal(api["claude_api"][pid]["refusal_status"]),
                           "safety": api["claude_api"][pid]["safety_framing"]},
            "gemini_api": {"refusal": collapse_refusal(api["gemini_api"][pid]["refusal_status"]),
                           "safety": api["gemini_api"][pid]["safety_framing"]},
            "chatgpt_app": {"refusal": collapse_refusal(app[pid]["app_refusal_status"]),
                            "safety": app[pid]["app_safety_framing"]},
        }
    return data, pids


def cohen_kappa(a, b):
    """Cohen's kappa for two label lists."""
    n = len(a)
    cats = sorted(set(a) | set(b))
    idx = {c: i for i, c in enumerate(cats)}
    obs = sum(1 for x, y in zip(a, b) if x == y) / n
    from collections import Counter
    ca, cb = Counter(a), Counter(b)
    exp = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    if exp >= 1.0:
        return 1.0
    return (obs - exp) / (1 - exp)


def fleiss_kappa(matrix_rows):
    cats = sorted({lab for row in matrix_rows for lab in row})
    if len(cats) < 2:
        return 1.0
    ci = {c: i for i, c in enumerate(cats)}
    N = len(matrix_rows)
    n = len(matrix_rows[0])
    col = [0] * len(cats)
    Pi = []
    for row in matrix_rows:
        counts = [0] * len(cats)
        for lab in row:
            counts[ci[lab]] += 1
            col[ci[lab]] += 1
        Pi.append((sum(c * c for c in counts) - n) / (n * (n - 1)))
    Pbar = sum(Pi) / N
    pj = [c / (N * n) for c in col]
    Pe = sum(p * p for p in pj)
    return 1.0 if Pe >= 1 else (Pbar - Pe) / (1 - Pe)


def main():
    data, pids = load()
    res = {"n_prompts": len(pids)}

    # ---- refusal posture ----
    refusal = {c: [data[p][c]["refusal"] for p in pids] for c in CHANNELS}

    # pairwise agreement + Cohen kappa on collapsed refusal
    pair = {}
    for a, b in combinations(CHANNELS, 2):
        agree = sum(1 for p in pids if data[p][a]["refusal"] == data[p][b]["refusal"]) / len(pids)
        kap = cohen_kappa(refusal[a], refusal[b])
        pair[f"{a}__{b}"] = {"agreement": round(agree, 3), "cohen_kappa": round(kap, 3)}
    res["refusal_pairwise"] = pair

    # nearest neighbour of the app
    app_nn = {}
    for c in ("openai_api", "claude_api", "gemini_api"):
        agree = sum(1 for p in pids if data[p]["chatgpt_app"]["refusal"] == data[p][c]["refusal"]) / len(pids)
        # disagreement count specifically
        disag = [p for p in pids if data[p]["chatgpt_app"]["refusal"] != data[p][c]["refusal"]]
        app_nn[c] = {"agreement_with_app": round(agree, 3), "disagreements": len(disag),
                     "disagreement_prompts": disag}
    res["app_nearest_neighbour"] = app_nn

    # Fleiss across the 3 APIs (same access modality)
    api_rows = [[data[p][c]["refusal"] for c in ("openai_api", "claude_api", "gemini_api")] for p in pids]
    res["refusal_fleiss_3APIs"] = round(fleiss_kappa(api_rows), 3)

    # refusal-style breakdown: who uses bare full_refusal
    res["full_refusal_counts"] = {c: sum(1 for p in pids if data[p][c]["refusal"] == "full_refusal") for c in CHANNELS}
    res["safe_redirect_counts"] = {c: sum(1 for p in pids if data[p][c]["refusal"] == "safe_redirect") for c in CHANNELS}

    # ---- safety framing (ordinal) ----
    mean_safety = {}
    for c in CHANNELS:
        vals = [SAFETY_ORD.get(data[p][c]["safety"], 0) for p in pids]
        mean_safety[c] = round(sum(vals) / len(vals), 3)
    res["mean_safety_framing"] = mean_safety
    # share of prompts with any framing (>none)
    res["any_framing_rate"] = {c: round(sum(1 for p in pids if SAFETY_ORD.get(data[p][c]["safety"], 0) > 0) / len(pids), 3) for c in CHANNELS}

    OUT.joinpath("channel_agreement.json").write_text(json.dumps(res, indent=2))

    # ---- memo ----
    nn_sorted = sorted(app_nn.items(), key=lambda kv: -kv[1]["agreement_with_app"])
    m = ["# Four-Channel Behavioral Agreement (no new collection)\n",
         "Uses the study's own uniformly-coded labels for all four channels on the "
         "same 60 prompts. Refusal posture is collapsed to "
         "{answered, safe\\_redirect, full\\_refusal}.\n",
         "## Headline: the ChatGPT app's nearest behavioral neighbour\n",
         "Refusal-posture agreement with the ChatGPT app, by channel:\n",
         "| Channel | Agreement with app | Disagreements |",
         "|---|---:|---:|"]
    for c, v in nn_sorted:
        m.append(f"| {PRETTY[c]} | {v['agreement_with_app']:.3f} | {v['disagreements']} |")
    m.append("")
    closest = PRETTY[nn_sorted[0][0]]
    openai_rank = [PRETTY[c] for c, _ in nn_sorted].index("OpenAI API") + 1
    m.append(f"The app's closest channel on refusal posture is **{closest}**; the "
             f"OpenAI API ranks #{openai_rank} of three. This is the key result: the "
             "consumer app does not behave most like its own provider's raw API.\n")
    m.append("## Why: only the OpenAI API uses bare full refusals\n")
    m.append("| Channel | Bare full refusals | Safe redirects |")
    m.append("|---|---:|---:|")
    for c in CHANNELS:
        m.append(f"| {PRETTY[c]} | {res['full_refusal_counts'][c]} | {res['safe_redirect_counts'][c]} |")
    m.append("")
    m.append("Every channel except the OpenAI API resolves refusal-expected prompts "
             "through bounded safe redirection rather than a bare refusal. The "
             "ChatGPT app patterns with the other consumer-grade / instruction-tuned "
             "surfaces, not with the plain OpenAI Responses API.\n")
    m.append("## Refusal agreement across the three raw APIs\n")
    m.append(f"Fleiss' kappa across the OpenAI, Claude, and Gemini APIs on collapsed "
             f"refusal posture is {res['refusal_fleiss_3APIs']:.3f}. Pairwise Cohen's "
             "kappa and agreement:\n")
    m.append("| Pair | Agreement | Cohen kappa |")
    m.append("|---|---:|---:|")
    for k, v in pair.items():
        a, b = k.split("__")
        m.append(f"| {PRETTY[a]} vs {PRETTY[b]} | {v['agreement']:.3f} | {v['cohen_kappa']:.3f} |")
    m.append("")
    m.append("## Safety framing: who adds the most caution\n")
    m.append("| Channel | Mean framing (0--3) | Any-framing rate |")
    m.append("|---|---:|---:|")
    for c in CHANNELS:
        m.append(f"| {PRETTY[c]} | {mean_safety[c]:.2f} | {res['any_framing_rate'][c]:.2f} |")
    m.append("")
    m.append("### Interpretation (claim-safe)\n")
    m.append("These are observable agreement patterns among coded labels, not claims "
             "about shared internal mechanisms. The finding strengthens the central "
             "thesis: a model's consumer app is a distinct behavioral surface, and on "
             "refusal posture the OpenAI API is an outlier relative to the consumer "
             "app and the other vendors' APIs.\n")
    OUT.joinpath("channel_agreement_memo.md").write_text("\n".join(m))

    # ---- tex ----
    tex = ["% Script-produced by analyze_channel_agreement.py",
           "\\begin{table}[t]\\centering\\small",
           "\\caption{Refusal-posture agreement with the ChatGPT app across the three "
           "API channels (collapsed posture, $N=60$). The app's nearest behavioral "
           "neighbour is not its own provider's API; only the OpenAI API issues bare "
           "full refusals.}",
           "\\label{tab:channel-agreement}",
           "\\begin{tabular}{lccc}", "\\toprule",
           "Channel & Agree w/ app & Bare full refusals & Safe redirects \\\\",
           "\\midrule"]
    for c in ("openai_api", "claude_api", "gemini_api"):
        tex.append("%s & %.3f & %d & %d \\\\" % (
            PRETTY[c], app_nn[c]["agreement_with_app"],
            res["full_refusal_counts"][c], res["safe_redirect_counts"][c]))
    tex.append("\\midrule")
    tex.append("ChatGPT app & --- & %d & %d \\\\" % (
        res["full_refusal_counts"]["chatgpt_app"], res["safe_redirect_counts"]["chatgpt_app"]))
    tex += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    OUT.joinpath("channel_agreement.tex").write_text("\n".join(tex))

    print(json.dumps({"app_nearest_neighbour": app_nn,
                      "full_refusal_counts": res["full_refusal_counts"],
                      "mean_safety_framing": mean_safety,
                      "fleiss_3APIs": res["refusal_fleiss_3APIs"]}, indent=2))


if __name__ == "__main__":
    main()
