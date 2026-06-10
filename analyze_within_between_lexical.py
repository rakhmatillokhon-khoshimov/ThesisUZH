#!/usr/bin/env python3
"""Within-channel vs between-channel lexical divergence.

Question: is the API-vs-app text divergence larger than the API's own
run-to-run sampling variability on the same prompts?

For every prompt we compute token Jaccard similarity for:
  - within-channel pairs: OpenAI API r1 vs r2, r1 vs r3, r2 vs r3
  - between-channel pair: OpenAI API r1 vs ChatGPT app (single shot)

If between-channel similarity is systematically *lower* than within-channel
similarity, the cross-channel text difference exceeds the channel's own
stochastic noise floor on the identical metric. Paired analysis on prompt_id
(Wilcoxon signed-rank + sign counts). Purely descriptive/exploratory; uses
only data already on disk.

Outputs: pilot_outputs/20260608/analysis_scaleup_cleaned/lexical_within_between/
  - within_between_lexical.json
  - within_between_lexical.tex  (thesis table)
  - within_between_rows.csv
"""
import csv
import json
import math
import re
from pathlib import Path
from statistics import mean, median

BASE = Path(__file__).resolve().parent
R1_DIR = BASE / "pilot_outputs/20260605/openai_api_scaleup_60/responses"
REPS_DIR = BASE / "pilot_outputs/20260609/reps/openai_api/responses"
APP_LOG = BASE / "pilot_outputs/20260608/chatgpt_app_scaleup_60_cleaned/chatgpt_app_log_private.csv"
PAIRWISE = BASE / "pilot_outputs/20260608/analysis_scaleup_cleaned/pairwise_results.csv"
OUT_DIR = BASE / "pilot_outputs/20260608/analysis_scaleup_cleaned/lexical_within_between"

# Same tokenizer as analyze_lexical_divergence.py for cross-table consistency.
TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> set:
    return set(TOKEN_RE.findall((text or "").lower()))


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def load_api_text(path: Path) -> str:
    # raw_output is the model text; "response" is the full API envelope dict.
    # Same field choice as analyze_lexical_divergence.py.
    d = json.loads(path.read_text())
    return str(d.get("raw_output", "") or "")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # substantive flags for subgroup view (final reviewed coding sheet)
    reviewed = BASE / "pilot_outputs/20260608/analysis_scaleup_cleaned/scaleup_human_reviewed_coding_sheet.csv"
    substantive = {}
    with open(reviewed) as f:
        for row in csv.DictReader(f):
            substantive[row["prompt_id"]] = str(row.get("substantive_divergence", "")).strip().lower() in {
                "yes", "true", "1", "substantive"}

    app_text = {}
    with open(APP_LOG) as f:
        for row in csv.DictReader(f):
            app_text[row["prompt_id"]] = row.get("raw_output", "")

    rows = []
    skipped = []
    for r1_path in sorted(R1_DIR.glob("S*_r1.json")):
        pid = r1_path.name.split("_")[0]
        r2_path = REPS_DIR / f"{pid}_r2.json"
        r3_path = REPS_DIR / f"{pid}_r3.json"
        if not (r2_path.exists() and r3_path.exists() and pid in app_text):
            skipped.append(pid)
            continue
        t1 = load_api_text(r1_path)
        t2 = load_api_text(r2_path)
        t3 = load_api_text(r3_path)
        ta = app_text[pid]
        if not t1.strip() or not t2.strip() or not t3.strip() or not ta.strip():
            skipped.append(pid)
            continue
        within = [jaccard(t1, t2), jaccard(t1, t3), jaccard(t2, t3)]
        between = jaccard(t1, ta)
        rows.append({
            "prompt_id": pid,
            "substantive": substantive.get(pid, False),
            "within_j_mean": round(mean(within), 4),
            "within_j_min": round(min(within), 4),
            "between_j_r1_app": round(between, 4),
            "delta_within_minus_between": round(mean(within) - between, 4),
        })

    n = len(rows)
    w = [r["within_j_mean"] for r in rows]
    b = [r["between_j_r1_app"] for r in rows]
    d = [r["delta_within_minus_between"] for r in rows]
    n_pos = sum(1 for x in d if x > 0)
    n_neg = sum(1 for x in d if x < 0)
    n_zero = n - n_pos - n_neg

    # Wilcoxon signed-rank (normal approximation, zero-excluded)
    nz = [x for x in d if x != 0]
    ranked = sorted((abs(x), x) for x in nz)
    ranks = {}
    i = 0
    while i < len(ranked):
        j = i
        while j < len(ranked) and ranked[j][0] == ranked[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[id(ranked[k])] = avg_rank
        i = j
    # simpler: recompute ranks positionally
    abs_sorted = sorted(range(len(nz)), key=lambda k: abs(nz[k]))
    rank_vals = [0.0] * len(nz)
    i = 0
    while i < len(abs_sorted):
        j = i
        while j < len(abs_sorted) and abs(nz[abs_sorted[j]]) == abs(nz[abs_sorted[i]]):
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            rank_vals[abs_sorted[k]] = avg_rank
        i = j
    w_plus = sum(rank_vals[k] for k in range(len(nz)) if nz[k] > 0)
    w_minus = sum(rank_vals[k] for k in range(len(nz)) if nz[k] < 0)
    nn = len(nz)
    mu = nn * (nn + 1) / 4.0
    sigma = math.sqrt(nn * (nn + 1) * (2 * nn + 1) / 24.0)
    z = (min(w_plus, w_minus) - mu) / sigma if sigma > 0 else 0.0
    # two-sided p from normal approx
    p = 2 * 0.5 * math.erfc(abs(z) / math.sqrt(2))

    # exact sign-test p (binomial two-sided, zeros dropped)
    def binom_two_sided(k: int, n_: int) -> float:
        from math import comb
        pk = sum(comb(n_, i) for i in range(0, min(k, n_ - k) + 1)) / 2 ** n_
        return min(1.0, 2 * pk)

    sign_p = binom_two_sided(min(n_pos, n_neg), n_pos + n_neg)

    sub_rows = [r for r in rows if r["substantive"]]
    non_rows = [r for r in rows if not r["substantive"]]

    summary = {
        "n_prompts": n,
        "skipped": skipped,
        "within_jaccard_mean": round(mean(w), 4),
        "within_jaccard_median": round(median(w), 4),
        "between_jaccard_mean": round(mean(b), 4),
        "between_jaccard_median": round(median(b), 4),
        "delta_mean": round(mean(d), 4),
        "delta_median": round(median(d), 4),
        "n_within_greater": n_pos,
        "n_between_greater": n_neg,
        "n_tied": n_zero,
        "wilcoxon_z": round(z, 3),
        "wilcoxon_p_two_sided_normal_approx": float(f"{p:.3g}"),
        "sign_test_p_two_sided": float(f"{sign_p:.3g}"),
        "substantive_subgroup": {
            "n": len(sub_rows),
            "within_mean": round(mean(r["within_j_mean"] for r in sub_rows), 4) if sub_rows else None,
            "between_mean": round(mean(r["between_j_r1_app"] for r in sub_rows), 4) if sub_rows else None,
        },
        "nonsubstantive_subgroup": {
            "n": len(non_rows),
            "within_mean": round(mean(r["within_j_mean"] for r in non_rows), 4) if non_rows else None,
            "between_mean": round(mean(r["between_j_r1_app"] for r in non_rows), 4) if non_rows else None,
        },
        "note": (
            "Within-channel = mean token Jaccard over the three OpenAI API run pairs "
            "(r1r2, r1r3, r2r3); between-channel = Jaccard(API r1, app). Exploratory."
        ),
    }

    (OUT_DIR / "within_between_lexical.json").write_text(json.dumps(summary, indent=2))
    with open(OUT_DIR / "within_between_rows.csv", "w", newline="") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wcsv.writeheader()
        wcsv.writerows(rows)

    tex = f"""% Auto-generated by analyze_within_between_lexical.py
\\begin{{table}}[t]\\centering\\small
\\caption{{Within-channel versus between-channel lexical similarity (token Jaccard) on the {n} fully repeated prompts. Within-channel is the mean similarity of the three OpenAI API repetition pairs on the same prompt; between-channel is the similarity of the first API run to the single ChatGPT app response. Exploratory paired comparison.}}
\\label{{tab:withinbetween}}
\\begin{{tabular}}{{lcc}}
\\toprule
Comparison & Mean Jaccard & Median Jaccard \\\\
\\midrule
Within OpenAI API (r1/r2/r3 pairs) & {summary['within_jaccard_mean']:.2f} & {summary['within_jaccard_median']:.2f} \\\\
Between channels (API r1 vs.\\ app) & {summary['between_jaccard_mean']:.2f} & {summary['between_jaccard_median']:.2f} \\\\
\\midrule
\\multicolumn{{3}}{{l}}{{Within $>$ between on {n_pos}/{n} prompts (sign test $p={sign_p:.2g}$; Wilcoxon $z={z:.2f}$, $p={p:.2g}$)}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    (OUT_DIR / "within_between_lexical.tex").write_text(tex)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
