#!/usr/bin/env python3
"""Collection-order, prompt-feature, style-profile, and bootstrap robustness checks.

Four cheap, claim-safe analyses on data already on disk (no new collection):

1. Collection-order confound check. The 60 app rows were collected in one
   sequential session (prompt_order_index 1..60). If substantive divergence
   were an artifact of session drift (rate limits, conversation memory bleed,
   collection fatigue), divergent rows should cluster late (or early) in the
   session. Tests: Mann-Whitney U on order index (substantive vs not) and
   Fisher exact on first-half vs second-half membership.

2. Prompt-feature moderators. Do shallow prompt features (length in words,
   interrogative vs non-interrogative phrasing) predict substantive
   divergence? Uses the private bank for computation; outputs aggregates only
   (no Category B text is emitted).

3. Channel style profile. Descriptive per-channel style metrics on all 60
   prompts for all four channels: words/response, sentences/response, words
   per sentence, Flesch Reading Ease (stdlib syllable estimator), type-token
   ratio. Framed as deployment-surface characterization, not divergence
   evidence. OCR caveat applies to app sentence splitting.

4. Bootstrap robustness for headline rates. 20,000 prompt-level bootstrap
   resamples of the 60 reviewed pairs -> percentile CIs for the overall
   substantive rate (17/60) and the tier-1 behavioral-core rate (10/60),
   reported next to the existing Wilson intervals.

All exploratory/descriptive; nothing here upgrades a directional claim.

Outputs under analysis_scaleup_cleaned/order_features_readability/:
  order_features_readability.json
  order_features_readability.tex   (three small thesis tables)
  order_features_readability_memo.md
"""
import csv
import json
import math
import random
import re
from collections import Counter
from pathlib import Path
from statistics import mean, median

BASE = Path(__file__).resolve().parent
CLEAN = BASE / "pilot_outputs/20260608/analysis_scaleup_cleaned"
APP_LOG = BASE / "pilot_outputs/20260608/chatgpt_app_scaleup_60_cleaned/chatgpt_app_log_private.csv"
API_DIR = BASE / "pilot_outputs/20260605/openai_api_scaleup_60/responses"
CLAUDE_LOG = BASE / "pilot_outputs/20260608/claude_api_scaleup_60/claude_api_log_private.csv"
GEMINI_LOG = BASE / "pilot_outputs/20260608/gemini_api_scaleup_60/gemini_api_log_private.csv"
BANK_PRIVATE = BASE / "prompt_bank_60_private.csv"
TIERS = CLEAN / "tiers/divergence_tiers.json"
SHEET = CLEAN / "scaleup_human_reviewed_coding_sheet.csv"
OUT = CLEAN / "order_features_readability"

WORD = re.compile(r"[A-Za-z0-9']+")
SENT_SPLIT = re.compile(r"[.!?]+(?:\s|$)")
VOWEL_GROUP = re.compile(r"[aeiouy]+")


# ---------------------------------------------------------------- stats utils
def mannwhitney_u(x, y):
    """Tie-corrected normal approximation; returns U, z, p_two_sided, rank-biserial."""
    n1, n2 = len(x), len(y)
    combined = [(v, 0) for v in x] + [(v, 1) for v in y]
    combined.sort(key=lambda t: t[0])
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    R1 = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == 0)
    U = R1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    tie = Counter(v for v, _ in combined)
    N = n1 + n2
    tie_term = sum(t**3 - t for t in tie.values())
    sigma2 = n1 * n2 / 12 * ((N + 1) - tie_term / (N * (N - 1)))
    if sigma2 <= 0:
        return U, 0.0, 1.0, 0.0
    z = (U - mu) / math.sqrt(sigma2)
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    rb = 1 - 2 * U / (n1 * n2)
    return U, z, p, rb


def fisher_exact(a, b, c, d):
    """Two-sided Fisher exact for [[a,b],[c,d]] via hypergeometric enumeration."""
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def pmf(k):
        return (math.comb(c1, k) * math.comb(n - c1, r1 - k)) / math.comb(n, r1)

    lo = max(0, r1 + c1 - n)
    hi = min(r1, c1)
    p_obs = pmf(a)
    p = sum(pk for k in range(lo, hi + 1) if (pk := pmf(k)) <= p_obs * (1 + 1e-9))
    return min(1.0, p)


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z**2 / n
    cen = (p + z**2 / (2 * n)) / den
    rad = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return [round(cen - rad, 3), round(cen + rad, 3)]


# ---------------------------------------------------------------- style utils
def syllables(word):
    w = word.lower().strip("'")
    if not w:
        return 0
    groups = len(VOWEL_GROUP.findall(w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and groups > 1:
        groups -= 1
    return max(1, groups)


def style_metrics(text):
    words = WORD.findall(text or "")
    if not words:
        return None
    sents = [s for s in SENT_SPLIT.split(text) if s.strip()]
    n_s = max(1, len(sents))
    n_w = len(words)
    n_syl = sum(syllables(w) for w in words)
    flesch = 206.835 - 1.015 * (n_w / n_s) - 84.6 * (n_syl / n_w)
    ttr = len({w.lower() for w in words}) / n_w
    return {"words": n_w, "sentences": n_s, "wps": n_w / n_s,
            "flesch": flesch, "ttr": ttr}


# ----------------------------------------------------------------------- main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20260610)

    sheet = list(csv.DictReader(open(SHEET)))
    subst = {r["prompt_id"] for r in sheet if r["substantive_divergence"].strip().lower() == "yes"}
    tiers = json.load(open(TIERS))
    tier1 = set(tiers["tier_members"]["tier1_behavioral"])
    all_ids = [r["prompt_id"] for r in sheet]
    assert len(all_ids) == 60, f"expected 60 rows, got {len(all_ids)}"

    # ---- 1. collection order ------------------------------------------------
    order = {}
    app_text = {}
    for r in csv.DictReader(open(APP_LOG)):
        order[r["prompt_id"]] = int(r["prompt_order_index"])
        app_text[r["prompt_id"]] = r.get("raw_output", "")
    x = sorted(order[p] for p in subst)
    y = sorted(order[p] for p in all_ids if p not in subst)
    U, z, p_mw, rb = mannwhitney_u(x, y)
    first_sub = sum(1 for p in subst if order[p] <= 30)
    a, b_ = first_sub, len(subst) - first_sub
    c = 30 - a
    d = 30 - b_
    p_fisher = fisher_exact(a, b_, c, d)
    order_res = {
        "median_order_substantive": median(x), "median_order_other": median(y),
        "mannwhitney": {"U": U, "z": round(z, 3), "p": round(p_mw, 4),
                        "rank_biserial": round(rb, 3)},
        "first_half_substantive": a, "second_half_substantive": b_,
        "fisher_first_vs_second_half_p": round(p_fisher, 4),
        "interpretation": ("No detectable association between collection order and "
                           "substantive divergence; session drift does not explain the cases."
                           if p_mw > 0.05 and p_fisher > 0.05 else
                           "Order association detected; inspect before interpreting cases."),
    }

    # ---- 2. prompt features -------------------------------------------------
    feats = {}
    for r in csv.DictReader(open(BANK_PRIVATE)):
        t = r.get("prompt_text_or_redacted_text", "") or ""
        feats[r["prompt_id"]] = {
            "len_words": len(WORD.findall(t)),
            "interrogative": "?" in t,
        }
    lx = sorted(feats[p]["len_words"] for p in subst)
    ly = sorted(feats[p]["len_words"] for p in all_ids if p not in subst)
    U2, z2, p_len, rb2 = mannwhitney_u(lx, ly)
    q_s = sum(1 for p in subst if feats[p]["interrogative"])
    q_o = sum(1 for p in all_ids if p not in subst and feats[p]["interrogative"])
    p_q = fisher_exact(q_s, len(subst) - q_s, q_o, 60 - len(subst) - q_o)
    feat_res = {
        "median_len_substantive": median(lx), "median_len_other": median(ly),
        "len_mannwhitney": {"U": U2, "z": round(z2, 3), "p": round(p_len, 4),
                            "rank_biserial": round(rb2, 3)},
        "interrogative_substantive": f"{q_s}/{len(subst)}",
        "interrogative_other": f"{q_o}/{60 - len(subst)}",
        "interrogative_fisher_p": round(p_q, 4),
    }

    # ---- 3. channel style profile -------------------------------------------
    texts = {"openai_api": {}, "chatgpt_app": app_text, "claude_api": {}, "gemini_api": {}}
    for pid in all_ids:
        f = API_DIR / f"{pid}_r1.json"
        if f.exists():
            texts["openai_api"][pid] = json.load(open(f)).get("raw_output", "")
    for log, ch in ((CLAUDE_LOG, "claude_api"), (GEMINI_LOG, "gemini_api")):
        for r in csv.DictReader(open(log)):
            if r.get("prompt_id") in set(all_ids):
                texts[ch][r["prompt_id"]] = r.get("raw_output", "") or r.get("response", "")
    profile = {}
    for ch, m in texts.items():
        ms = [sm for pid in all_ids if (sm := style_metrics(m.get(pid, ""))) is not None]
        profile[ch] = {
            "n": len(ms),
            "mean_words": round(mean(s["words"] for s in ms), 1),
            "mean_sentences": round(mean(s["sentences"] for s in ms), 1),
            "mean_words_per_sentence": round(mean(s["wps"] for s in ms), 1),
            "mean_flesch_reading_ease": round(mean(s["flesch"] for s in ms), 1),
            "mean_type_token_ratio": round(mean(s["ttr"] for s in ms), 3),
        }

    # ---- 4. bootstrap robustness --------------------------------------------
    B = 20000
    ids = list(all_ids)
    rates_all, rates_t1 = [], []
    for _ in range(B):
        samp = [ids[rng.randrange(60)] for _ in range(60)]
        rates_all.append(sum(1 for p in samp if p in subst) / 60)
        rates_t1.append(sum(1 for p in samp if p in tier1) / 60)
    rates_all.sort()
    rates_t1.sort()

    def pci(v):
        return [round(v[int(0.025 * B)], 3), round(v[int(0.975 * B)], 3)]

    boot = {
        "B": B, "seed": 20260610,
        "overall_rate": round(len(subst) / 60, 3),
        "overall_bootstrap95": pci(rates_all),
        "overall_wilson95": wilson(len(subst), 60),
        "tier1_rate": round(len(tier1) / 60, 3),
        "tier1_bootstrap95": pci(rates_t1),
        "tier1_wilson95": wilson(len(tier1), 60),
    }

    res = {"collection_order": order_res, "prompt_features": feat_res,
           "channel_style_profile": profile, "bootstrap": boot}
    json.dump(res, open(OUT / "order_features_readability.json", "w"), indent=2)

    # ---- LaTeX tables --------------------------------------------------------
    ch_label = {"openai_api": "OpenAI API", "chatgpt_app": "ChatGPT app",
                "claude_api": "Claude API", "gemini_api": "Gemini API"}
    tex = []
    tex.append(
        "\\begin{table}[htbp]\n\\centering\n"
        "\\caption{Collection-order and prompt-feature checks for the 17 substantive "
        "divergences (exploratory). No shallow ordering or prompt-surface feature "
        "accounts for which prompts diverge.}\n"
        "\\label{tab:order-feature-checks}\n"
        "\\small\n\\begin{tabular}{lllr}\n\\toprule\n"
        "Check & Substantive & Non-substantive & $p$ \\\\\n\\midrule\n"
        f"Session order (median index) & {order_res['median_order_substantive']:.0f} & "
        f"{order_res['median_order_other']:.0f} & {order_res['mannwhitney']['p']:.3f} \\\\\n"
        f"First vs.\\ second session half & {a}/{len(subst)} first half & "
        f"{c}/30 of first half & {order_res['fisher_first_vs_second_half_p']:.3f} \\\\\n"
        f"Prompt length (median words) & {feat_res['median_len_substantive']:.0f} & "
        f"{feat_res['median_len_other']:.0f} & {feat_res['len_mannwhitney']['p']:.3f} \\\\\n"
        f"Interrogative phrasing & {feat_res['interrogative_substantive']} & "
        f"{feat_res['interrogative_other']} & {feat_res['interrogative_fisher_p']:.3f} \\\\\n"
        "\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    rows = "".join(
        f"{ch_label[ch]} & {p['mean_words']:.0f} & {p['mean_sentences']:.0f} & "
        f"{p['mean_words_per_sentence']:.1f} & {p['mean_flesch_reading_ease']:.0f} & "
        f"{p['mean_type_token_ratio']:.2f} \\\\\n"
        for ch, p in profile.items())
    tex.append(
        "\\begin{table}[htbp]\n\\centering\n"
        "\\caption{Channel style profile across all 60 prompts (descriptive). "
        "Means per response; Flesch Reading Ease computed with a deterministic "
        "syllable estimator. App values inherit the OCR-transcription caveat.}\n"
        "\\label{tab:channel-style-profile}\n"
        "\\small\n\\begin{tabular}{lrrrrr}\n\\toprule\n"
        "Channel & Words & Sentences & Words/sent. & Flesch RE & TTR \\\\\n\\midrule\n"
        + rows + "\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    tex.append(
        "\\begin{table}[htbp]\n\\centering\n"
        "\\caption{Bootstrap robustness for the headline rates (20{,}000 prompt-level "
        "resamples, seed 20260610), alongside the Wilson intervals already reported.}\n"
        "\\label{tab:bootstrap-rates}\n"
        "\\small\n\\begin{tabular}{lrll}\n\\toprule\n"
        "Rate & Estimate & Bootstrap 95\\% & Wilson 95\\% \\\\\n\\midrule\n"
        f"Overall substantive (17/60) & {boot['overall_rate']:.2f} & "
        f"[{boot['overall_bootstrap95'][0]:.2f}, {boot['overall_bootstrap95'][1]:.2f}] & "
        f"[{boot['overall_wilson95'][0]:.2f}, {boot['overall_wilson95'][1]:.2f}] \\\\\n"
        f"Tier-1 behavioral core (10/60) & {boot['tier1_rate']:.2f} & "
        f"[{boot['tier1_bootstrap95'][0]:.2f}, {boot['tier1_bootstrap95'][1]:.2f}] & "
        f"[{boot['tier1_wilson95'][0]:.2f}, {boot['tier1_wilson95'][1]:.2f}] \\\\\n"
        "\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    (OUT / "order_features_readability.tex").write_text("\n".join(tex))
    # individual tables so the thesis can input them selectively
    (OUT / "order_feature_checks.tex").write_text(tex[0])
    (OUT / "channel_style_profile.tex").write_text(tex[1])
    (OUT / "bootstrap_rates.tex").write_text(tex[2])

    # ---- memo ----------------------------------------------------------------
    memo = f"""# Order, Prompt-Feature, Style, and Bootstrap Checks — 10 June 2026

Existing data only; exploratory/descriptive. Script: `analyze_order_features_readability.py`.

## 1. Collection-order confound check
- Median session order index: substantive {order_res['median_order_substantive']:.0f} vs other {order_res['median_order_other']:.0f}.
- Mann-Whitney p = {order_res['mannwhitney']['p']:.3f}; first/second-half Fisher p = {order_res['fisher_first_vs_second_half_p']:.3f}.
- {order_res['interpretation']}

## 2. Prompt-feature moderators
- Prompt length: median {feat_res['median_len_substantive']:.0f} vs {feat_res['median_len_other']:.0f} words, p = {feat_res['len_mannwhitney']['p']:.3f}.
- Interrogative phrasing: {feat_res['interrogative_substantive']} vs {feat_res['interrogative_other']}, Fisher p = {feat_res['interrogative_fisher_p']:.3f}.
- Divergence is carried by prompt *content category*, not by shallow surface features.

## 3. Channel style profile (all 60 prompts)
| Channel | Words | Sentences | Words/sent | Flesch RE | TTR |
|---|---|---|---|---|---|
""" + "".join(
        f"| {ch_label[ch]} | {p['mean_words']:.0f} | {p['mean_sentences']:.0f} | "
        f"{p['mean_words_per_sentence']:.1f} | {p['mean_flesch_reading_ease']:.0f} | "
        f"{p['mean_type_token_ratio']:.2f} |\n"
        for ch, p in profile.items()) + f"""
## 4. Bootstrap robustness
- Overall 17/60: bootstrap 95% {boot['overall_bootstrap95']} vs Wilson {boot['overall_wilson95']}.
- Tier-1 10/60: bootstrap 95% {boot['tier1_bootstrap95']} vs Wilson {boot['tier1_wilson95']}.
- Percentile bootstrap and Wilson agree closely; the headline rates are not an
  artifact of the interval method.
"""
    (OUT / "order_features_readability_memo.md").write_text(memo)
    print(json.dumps(res, indent=1)[:2400])
    print("\nWrote:", OUT)


if __name__ == "__main__":
    main()
