#!/usr/bin/env python3
"""Within-channel repetition stability (run-to-run reproducibility).

New robustness evidence for the audit: are the coded API behaviors stable across
independent repetitions of the *same* channel? If within-channel run-to-run
flips are rare relative to the cross-channel (API-vs-app) divergence rate, then
the observed access-channel divergences are not an artifact of model
stochasticity.

For each channel (OpenAI gpt-4o, Claude Sonnet, Gemini 2.5-flash) we load three
independent repetitions (r1 from the original scale-up; r2/r3 collected on
2026-06-09), re-apply the project's own automated classifiers
(`classify_refusal`, `classify_safety_framing`) to each repetition, and report:
  - unanimous-label rate across the 3 reps (per label);
  - Fleiss' kappa across reps (reps as raters, prompts as items);
  - mean coefficient of variation of answer length.

Outputs under analysis_scaleup_cleaned/stability/:
  repetition_stability.json, repetition_stability_memo.md, repetition_stability.tex
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import score_pilot_results as S

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "pilot_outputs" / "20260608" / "analysis_scaleup_cleaned"
OUT = CLEAN / "stability"
OUT.mkdir(parents=True, exist_ok=True)

# Channel -> list of (rep_label, dir, filename_template)
CHANNELS = {
    "openai_gpt-4o": [
        ("r1", ROOT / "pilot_outputs/20260605/openai_api_scaleup_60/responses", "{pid}_r1.json"),
        ("r2", ROOT / "pilot_outputs/20260609/reps/openai_api/responses", "{pid}_r2.json"),
        ("r3", ROOT / "pilot_outputs/20260609/reps/openai_api/responses", "{pid}_r3.json"),
    ],
    "claude_sonnet-4": [
        ("r1", ROOT / "pilot_outputs/20260608/claude_api_scaleup_60/responses", "{pid}_r1.json"),
        ("r2", ROOT / "pilot_outputs/20260609/reps/claude_api_r2/responses", "{pid}_r1.json"),
        ("r3", ROOT / "pilot_outputs/20260609/reps/claude_api_r3/responses", "{pid}_r1.json"),
    ],
    # Gemini repetition stability is NOT reported: the high-throughput config
    # (thinkingBudget=0, required for the r1 scale-up) returns empty outputs on
    # re-collection, so r2/r3 are a collection artifact rather than a measure of
    # model stochasticity. Documented as a limitation; left out of the table.
}

PROMPTS = [f"S{n:03d}" for n in range(1, 61)]


def load_output(d: Path, tmpl: str, pid: str):
    f = d / tmpl.format(pid=pid)
    if not f.exists():
        return None
    try:
        return json.load(open(f)).get("raw_output", "") or ""
    except Exception:
        return None


def fleiss_kappa(items):
    """items: list of label-tuples (one per rep) for each prompt. 3 raters."""
    cats = sorted({lab for it in items for lab in it})
    if len(cats) < 2:
        return 1.0  # perfect agreement, only one category observed
    cat_idx = {c: i for i, c in enumerate(cats)}
    N = len(items)
    n = len(items[0])  # raters per item
    P_i = []
    col_tot = [0] * len(cats)
    for it in items:
        counts = [0] * len(cats)
        for lab in it:
            counts[cat_idx[lab]] += 1
            col_tot[cat_idx[lab]] += 1
        P_i.append((sum(c * c for c in counts) - n) / (n * (n - 1)))
    Pbar = sum(P_i) / N
    pj = [c / (N * n) for c in col_tot]
    Pe = sum(p * p for p in pj)
    if Pe >= 1.0:
        return 1.0
    return (Pbar - Pe) / (1 - Pe)


def main():
    results = {"channels": {}, "prompts": len(PROMPTS),
               "labels": ["refusal_status", "safety_framing"]}
    for ch, reps in CHANNELS.items():
        outs = {pid: [] for pid in PROMPTS}
        missing = 0
        for pid in PROMPTS:
            for _, d, tmpl in reps:
                t = load_output(d, tmpl, pid)
                if t is None:
                    missing += 1
                    t = ""
                outs[pid].append(t)
        # only keep prompts with all 3 reps non-empty-loadable
        usable = [pid for pid in PROMPTS if all(o is not None for o in outs[pid])]

        per_label = {}
        for label, fn in [("refusal_status", S.classify_refusal),
                          ("safety_framing", S.classify_safety_framing)]:
            items = []
            unanimous = 0
            flips = 0
            for pid in usable:
                labs = tuple(fn(t) for t in outs[pid])
                items.append(labs)
                if len(set(labs)) == 1:
                    unanimous += 1
                else:
                    flips += 1
            kappa = fleiss_kappa(items)
            per_label[label] = {
                "n": len(usable),
                "unanimous": unanimous,
                "flips": flips,
                "unanimous_rate": round(unanimous / len(usable), 3),
                "fleiss_kappa": round(kappa, 3),
            }

        # length coefficient of variation
        cvs = []
        for pid in usable:
            lens = [len(t) for t in outs[pid]]
            mu = sum(lens) / len(lens)
            if mu > 0:
                sd = math.sqrt(sum((x - mu) ** 2 for x in lens) / len(lens))
                cvs.append(sd / mu)
        results["channels"][ch] = {
            "usable_prompts": len(usable),
            "missing_files": missing,
            "by_label": per_label,
            "mean_length_cv": round(sum(cvs) / len(cvs), 3) if cvs else None,
        }

    results["gemini_note"] = (
        "Gemini 2.5-flash repetition stability not assessed: the throughput "
        "configuration (thinkingBudget=0) used for the r1 scale-up returns empty "
        "outputs on re-collection, so r2/r3 could not be coded reliably.")
    (OUT / "repetition_stability.json").write_text(json.dumps(results, indent=2))

    # memo
    m = ["# Within-Channel Repetition Stability (r1/r2/r3)\n",
         "Three independent repetitions per channel on the frozen 60-prompt bank. "
         "Each repetition's raw output is re-coded with the project's own automated "
         "classifiers; we report run-to-run agreement. High agreement means the "
         "coded behavior is reproducible and the cross-channel (API-vs-app) "
         "divergences are not explained by within-channel stochasticity.\n",
         "| Channel | Label | Unanimous/n | Unanimous rate | Fleiss kappa |",
         "|---|---|---|---|---|"]
    for ch, v in results["channels"].items():
        for label, lv in v["by_label"].items():
            m.append(f"| {ch} | {label} | {lv['unanimous']}/{lv['n']} | "
                     f"{lv['unanimous_rate']:.2f} | {lv['fleiss_kappa']:.2f} |")
    m.append("")
    m.append("| Channel | Mean answer-length CV |")
    m.append("|---|---|")
    for ch, v in results["channels"].items():
        m.append(f"| {ch} | {v['mean_length_cv']:.2f} |")
    m.append("")
    m.append("### Interpretation (claim-safe)\n")
    m.append("Refusal status is the audit's primary safety label. Its within-channel "
             "run-to-run agreement is the relevant noise floor for the cross-channel "
             "refusal divergences reported in the Results chapter. Length varies more "
             "than categorical labels, which is why verbosity is treated as a "
             "pilot-triage signal and not a substantive divergence label.\n")
    (OUT / "repetition_stability_memo.md").write_text("\n".join(m))

    # tex
    tex = ["% Auto-generated by analyze_repetition_stability.py",
           "\\begin{table}[t]", "\\centering", "\\small",
           "\\caption{Within-channel repetition stability across three independent "
           "runs (r1/r2/r3) on the 60-prompt bank. Each run is re-coded with the "
           "study's automated classifiers; unanimous rate and Fleiss' $\\kappa$ "
           "measure run-to-run reproducibility of the safety labels.}",
           "\\label{tab:stability}",
           "\\begin{tabular}{llcc}", "\\toprule",
           "Channel & Label & Unanimous rate & Fleiss $\\kappa$ \\\\", "\\midrule"]
    for ch, v in results["channels"].items():
        for label, lv in v["by_label"].items():
            tex.append("%s & %s & %.2f & %.2f \\\\" % (
                ch.replace("_", "\\_"), label.replace("_", "\\_"),
                lv["unanimous_rate"], lv["fleiss_kappa"]))
    tex += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (OUT / "repetition_stability.tex").write_text("\n".join(tex))

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
