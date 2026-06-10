#!/usr/bin/env python3
"""Generate secondary findings from the corrected 60-pair scale-up.

These analyses do not collect new data. They reuse the frozen prompt bank,
corrected pairwise labels, human-reviewed labels, and raw API/app outputs to
answer follow-up questions that strengthen the thesis:

- Which final cases are carried by which mechanism?
- What did manual review add beyond automated first-pass flags?
- Which channel is stricter / more cautious / more source-supported?
- Is app verbosity itself enough to explain the final divergence count?
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results" / "analysis"
DEFAULT_OUT = ANALYSIS / "secondary"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def median(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return float(statistics.median(values))


def mean(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return float(statistics.mean(values))


def sign_test_two_sided(positive: int, negative: int) -> float | None:
    n = positive + negative
    if n == 0:
        return None
    tail = min(positive, negative)
    p = 2 * sum(math.comb(n, k) * (0.5**n) for k in range(tail + 1))
    return min(1.0, p)


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return [round(max(0, centre - margin), 3), round(min(1, centre + margin), 3)]


def pct(k: int, n: int) -> float:
    return round(k / n, 3) if n else 0.0


def split_types(value: str) -> set[str]:
    if not value or value == "none":
        return set()
    return {part.strip() for part in value.split(";") if part.strip() and part.strip() != "none"}


def count_by(rows: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(row)
    out = []
    for name, items in sorted(groups.items()):
        n = len(items)
        yes = sum(item["substantive_divergence"] == "yes" for item in items)
        minor = sum(item["substantive_divergence"] == "minor" for item in items)
        out.append(
            {
                key: name,
                "n": n,
                "substantive": yes,
                "minor": minor,
                "clean": n - yes - minor,
                "substantive_rate": pct(yes, n),
                "wilson95": wilson(yes, n),
            }
        )
    return sorted(out, key=lambda r: (-int(r["substantive"]), -float(r["substantive_rate"]), str(r[key])))


def ordinal_direction(rows: list[dict[str, object]], left: str, right: str, order: dict[str, int]) -> Counter:
    counter: Counter[str] = Counter()
    for row in rows:
        a = order.get(str(row[left]), None)
        b = order.get(str(row[right]), None)
        if a is None or b is None or a == b:
            counter["same"] += 1
        elif a > b:
            counter["api_higher"] += 1
        else:
            counter["app_higher"] += 1
    return counter


def build_markdown(summary: dict[str, object]) -> str:
    m = summary["mechanism_decomposition"]
    review = summary["manual_review_yield"]
    length = summary["length_analysis"]
    direction = summary["directionality"]
    meta = summary["metadata_highlights"]

    lines = [
        "# Secondary Findings — Corrected 60-Pair Scale-Up",
        "",
        "Derived from existing local artifacts; no new collection was performed.",
        "",
        "## Thesis-Safe New Findings",
        "",
        "### 1. Manual review was not cosmetic; it changed the evidentiary boundary.",
        "",
        f"- Automated visible-divergence flags covered {review['automated_visible_flags']} rows.",
        f"- Of those, {review['automated_to_substantive']} became final substantive cases and "
        f"{review['automated_to_minor']} became minor/non-claim cases.",
        f"- Two final substantive cases ({', '.join(review['substantive_from_nonvisible_ids'])}) were not automated visible-divergence flags; they were caught through UI-surface/manual review.",
        f"- No automated visible-divergence flag became fully clean after review; the scorer had high triage value but only {review['substantive_precision_visible_flags']:.3f} claim precision.",
        "",
        "Interpretation: manual review is a real methods contribution. It both suppresses overclaiming and catches UI-surface cases the automated scorer under-detects.",
        "",
        "### 2. The final 17 cases split into two mechanisms: response-core shifts and access-surface shifts.",
        "",
        f"- Non-UI response-core anchors, counting refusal/factuality/format even when a UI surface is also present: {m['non_ui_response_core_count']}/60.",
        f"- Cases with no UI-surface label at all: {m['no_ui_related_count']}/60.",
        f"- Pure UI-surface or UI-plus-safety-only cases: {m['pure_ui_or_ui_safety_count']}/60.",
        f"- Safety-framing-only cases: {m['safety_only_count']}/60.",
        "",
        "Interpretation: the thesis can now say the access-channel effect is not a single phenomenon. Some cases are about the response itself; others are about sources, local context, or the app surface.",
        "",
        "### 3. Directionality is asymmetric but not one-dimensional.",
        "",
        f"- Refusal status: API higher/stricter in {direction['refusal_status_all'].get('api_higher', 0)} rows; app higher/stricter in {direction['refusal_status_all'].get('app_higher', 0)} row(s).",
        f"- Safety framing: API higher in {direction['safety_framing_all'].get('api_higher', 0)} rows; app higher in {direction['safety_framing_all'].get('app_higher', 0)} rows.",
        f"- Factuality among evaluated factual rows: app better in {direction['factuality'].get('app_better', 0)} rows; API better in {direction['factuality'].get('api_better', 0)} rows.",
        f"- Format compliance: API-only pass/app fail in {direction['format_compliance'].get('api_pass_app_fail', 0)} row; app-only pass/API fail in {direction['format_compliance'].get('app_pass_api_fail', 0)} row.",
        "",
        "Interpretation: do not frame the result as simply app = lenient or API = safe. The app is often more contextual/source-supported, while the API can be more refusal-heavy and sometimes more format-compliant.",
        "",
        "### 4. App verbosity is real, but verbosity is not the finding.",
        "",
        f"- App responses were longer in {length['app_longer']}/{length['n']} pairs; exact sign-test p={length['sign_test_p']:.3g}.",
        f"- Median API output length: {length['api_words_median']:.1f} words; median app output length: {length['app_words_median']:.1f} words; median app-minus-API delta: {length['delta_words_median']:.1f} words.",
        f"- The social-recommendation negative-control category still had app-longer outputs in {length['social_recommendation']['app_longer']}/{length['social_recommendation']['n']} rows, but 0 final substantive divergences.",
        "",
        "Interpretation: length and helpfulness style are background channel differences, but they are not sufficient for a substantive divergence claim. This strengthens the conservative coding stance.",
        "",
        "## Exploratory Only",
        "",
        f"- High small-cell rates appear in {', '.join(meta['small_cell_high_rate_sources'])}; these are useful for discussion but too small for independent claims.",
        f"- BBQ-adapted social rows produced {meta['bbq_minor']} minor cases but {meta['bbq_substantive']} substantive cases, reinforcing their role as negative controls rather than positive findings.",
        "",
        "## Derived Artifacts",
        "",
        "- `secondary_findings.json`",
        "- `mechanism_decomposition.csv`",
        "- `manual_review_yield.csv`",
        "- `directionality_summary.csv`",
        "- `length_analysis.csv`",
        "- `metadata_substantive_rates.csv`",
        "- `secondary_findings_tables.tex`",
        "",
    ]
    return "\n".join(lines)


def build_tex(summary: dict[str, object]) -> str:
    m = summary["mechanism_decomposition"]
    review = summary["manual_review_yield"]
    length = summary["length_analysis"]
    direction = summary["directionality"]

    p_value = float(length["sign_test_p"])
    p_tex = f"{p_value:.2e}"
    mantissa, exponent = p_tex.split("e")
    p_tex = rf"{mantissa}\times 10^{{{int(exponent)}}}"

    return rf"""
\begin{{longtable}}{{L{{0.29\linewidth}}rrL{{0.43\linewidth}}}}
\caption{{Secondary mechanism decomposition for final substantive cases.}}\\
\toprule
Scenario & Count & Denominator & Interpretation \\
\midrule
\endfirsthead
\caption[]{{Secondary mechanism decomposition (continued).}}\\
\toprule
Scenario & Count & Denominator & Interpretation \\
\midrule
\endhead
\bottomrule
\endfoot
All final substantive cases & {m['final_substantive_count']} & 60 & corrected manual-review count \\
Non-UI response-core anchors & {m['non_ui_response_core_count']} & 60 & refusal, factuality, or format anchor, even if UI also appears \\
No UI-surface label at all & {m['no_ui_related_count']} & 60 & conservative count after excluding every UI-surface case \\
Pure UI or UI-plus-safety only & {m['pure_ui_or_ui_safety_count']} & 60 & access-surface/context cases without refusal/factual/format anchor \\
Safety-framing only & {m['safety_only_count']} & 60 & cases carried only by the softest label \\
\end{{longtable}}

\begin{{longtable}}{{L{{0.32\linewidth}}rrL{{0.37\linewidth}}}}
\caption{{Manual-review yield from automated and non-automated triage.}}\\
\toprule
Triage source & Rows & Final substantive & Interpretation \\
\midrule
\endfirsthead
\caption[]{{Manual-review yield (continued).}}\\
\toprule
Triage source & Rows & Final substantive & Interpretation \\
\midrule
\endhead
\bottomrule
\endfoot
Automated visible-divergence flag & {review['automated_visible_flags']} & {review['automated_to_substantive']} & precision {review['substantive_precision_visible_flags']:.2f}; remaining flagged rows were minor \\
Not an automated visible-divergence flag & {review['nonvisible_rows']} & {review['nonvisible_to_substantive']} & substantive cases caught through UI/manual review: {', '.join(review['substantive_from_nonvisible_ids'])} \\
Review-required rows & {review['review_required_rows']} & {review['review_required_to_substantive']} & total manual-review workload \\
\end{{longtable}}

\begin{{longtable}}{{L{{0.38\linewidth}}rL{{0.42\linewidth}}}}
\caption{{Directionality and verbosity checks.}}\\
\toprule
Check & Count & Notes \\
\midrule
\endfirsthead
\caption[]{{Directionality and verbosity checks (continued).}}\\
\toprule
Check & Count & Notes \\
\midrule
\endhead
\bottomrule
\endfoot
API stricter refusal status & {direction['refusal_status_all'].get('api_higher', 0)} & app stricter in {direction['refusal_status_all'].get('app_higher', 0)} row \\
App higher safety framing & {direction['safety_framing_all'].get('app_higher', 0)} & API higher in {direction['safety_framing_all'].get('api_higher', 0)} rows \\
App better factuality/support & {direction['factuality'].get('app_better', 0)} & API better in {direction['factuality'].get('api_better', 0)} rows \\
App longer responses & {length['app_longer']}/{length['n']} & exact sign-test $p={p_tex}$ \\
Social-control app-longer rows & {length['social_recommendation']['app_longer']}/{length['social_recommendation']['n']} & final substantive divergences remain 0 \\
\end{{longtable}}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", type=Path, default=ANALYSIS)
    parser.add_argument("--prompt-bank", type=Path, default=ROOT / "data/prompts/prompt_bank_60.csv")
    parser.add_argument("--api-log", type=Path, default=ROOT / "data" / "private" / "20260605" / "openai_api_scaleup_60" / "api_log_private.csv")
    parser.add_argument("--app-log", type=Path, default=ROOT / "data" / "private" / "20260608" / "chatgpt_app_scaleup_60_cleaned" / "chatgpt_app_log_private.csv")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    human = read_csv(args.analysis_dir / "scaleup_human_reviewed_coding_sheet.csv")
    pairwise = read_csv(args.analysis_dir / "pairwise_results.csv")
    prompt_bank = {row["prompt_id"]: row for row in read_csv(args.prompt_bank)}
    api_log = {row["prompt_id"]: row for row in read_csv(args.api_log)}
    app_log = {row["prompt_id"]: row for row in read_csv(args.app_log)}

    rows: list[dict[str, object]] = []
    pairwise_by_id = {row["prompt_id"]: row for row in pairwise}
    for row in human:
        pid = row["prompt_id"]
        merged: dict[str, object] = {**prompt_bank[pid], **pairwise_by_id[pid], **row}
        api_words = len(api_log[pid]["raw_output"].split())
        app_words = len(app_log[pid]["raw_output"].split())
        merged["api_words"] = api_words
        merged["app_words"] = app_words
        merged["delta_words_app_minus_api"] = app_words - api_words
        rows.append(merged)

    final_yes = [row for row in rows if row["substantive_divergence"] == "yes"]

    mechanism_counter: Counter[str] = Counter()
    token_counter: Counter[str] = Counter()
    mechanism_rows: list[dict[str, object]] = []
    for row in final_yes:
        tokens = split_types(str(row["final_divergence_type"]))
        token_counter.update(tokens)
        if "refusal_status" in tokens:
            mechanism = "refusal_boundary_or_status"
        elif "factuality" in tokens:
            mechanism = "factual_support"
        elif "format_compliance" in tokens:
            mechanism = "format_compliance"
        elif tokens == {"ui_surface_signature"}:
            mechanism = "ui_surface_only"
        elif tokens == {"ui_surface_signature", "safety_framing"}:
            mechanism = "ui_surface_plus_safety_framing"
        elif tokens == {"safety_framing"}:
            mechanism = "safety_framing_only"
        else:
            mechanism = "other"
        mechanism_counter[mechanism] += 1
        mechanism_rows.append(
            {
                "prompt_id": row["prompt_id"],
                "category": row["category"],
                "final_divergence_type": row["final_divergence_type"],
                "mechanism_bucket": mechanism,
                "has_ui_surface": "ui_surface_signature" in tokens,
                "has_response_core": bool(tokens & {"refusal_status", "factuality", "format_compliance"}),
            }
        )

    automated_visible = [row for row in rows if row["visible_divergence"] == "yes"]
    nonvisible = [row for row in rows if row["visible_divergence"] != "yes"]
    substantive_from_nonvisible = [str(row["prompt_id"]) for row in nonvisible if row["substantive_divergence"] == "yes"]
    review_required = [row for row in rows if row["review_required"] == "yes"]

    refusal_order = {"answered": 0, "partial_refusal_or_safe_redirect": 1, "full_refusal": 2, "block": 3}
    safety_order = {"none": 0, "light": 1, "moderate": 2, "strong": 3}
    refusal_direction = ordinal_direction(rows, "api_refusal_status", "app_refusal_status", refusal_order)
    safety_direction = ordinal_direction(rows, "api_safety_framing", "app_safety_framing", safety_order)
    refusal_direction_final = ordinal_direction(final_yes, "api_refusal_status", "app_refusal_status", refusal_order)
    safety_direction_final = ordinal_direction(final_yes, "api_safety_framing", "app_safety_framing", safety_order)

    factuality = Counter()
    for row in rows:
        api = str(row["api_factuality"])
        app = str(row["app_factuality"])
        if api == app:
            factuality["same"] += 1
        elif api == "possible_factual_mismatch" and app == "expected_supported":
            factuality["app_better"] += 1
        elif api == "expected_supported" and app == "possible_factual_mismatch":
            factuality["api_better"] += 1
        elif api == "not_applicable" or app == "not_applicable":
            factuality["not_applicable_mismatch"] += 1
        else:
            factuality["other"] += 1

    format_counter = Counter()
    for row in rows:
        api = str(row["api_format_compliance"])
        app = str(row["app_format_compliance"])
        if api == app:
            format_counter["same"] += 1
        elif api == "pass" and app == "fail":
            format_counter["api_pass_app_fail"] += 1
        elif api == "fail" and app == "pass":
            format_counter["app_pass_api_fail"] += 1
        elif api == "not_applicable" or app == "not_applicable":
            format_counter["not_applicable_mismatch"] += 1
        else:
            format_counter["other"] += 1

    ui_rows = [row for row in rows if row["app_ui_surface_signature"] != "none"]
    ui_by_signature = {}
    for signature in sorted({str(row["app_ui_surface_signature"]) for row in ui_rows}):
        items = [row for row in ui_rows if row["app_ui_surface_signature"] == signature]
        ui_by_signature[signature] = {
            "n": len(items),
            "substantive": sum(row["substantive_divergence"] == "yes" for row in items),
            "minor": sum(row["substantive_divergence"] == "minor" for row in items),
            "clean": sum(row["substantive_divergence"] == "no" for row in items),
        }

    deltas = [int(row["delta_words_app_minus_api"]) for row in rows]
    app_longer = sum(delta > 0 for delta in deltas)
    api_longer = sum(delta < 0 for delta in deltas)
    length_groups: list[dict[str, object]] = []
    for key in ["category", "substantive_divergence", "risk_level", "expected_response_class"]:
        groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            groups[str(row[key])].append(row)
        for group, items in sorted(groups.items()):
            group_deltas = [int(row["delta_words_app_minus_api"]) for row in items]
            pos = sum(delta > 0 for delta in group_deltas)
            neg = sum(delta < 0 for delta in group_deltas)
            length_groups.append(
                {
                    "grouping": key,
                    "group": group,
                    "n": len(items),
                    "api_words_median": median(int(row["api_words"]) for row in items),
                    "app_words_median": median(int(row["app_words"]) for row in items),
                    "delta_words_median": median(group_deltas),
                    "delta_words_mean": round(mean(group_deltas) or 0.0, 1),
                    "app_longer": pos,
                    "api_longer": neg,
                    "sign_test_p": sign_test_two_sided(pos, neg),
                    "substantive": sum(row["substantive_divergence"] == "yes" for row in items),
                }
            )

    metadata_rows: list[dict[str, object]] = []
    for key in ["category", "source", "risk_level", "expected_response_class", "subcategory"]:
        for item in count_by(rows, key):
            item["grouping"] = key
            item["group"] = item.pop(key)
            metadata_rows.append(item)

    small_cell_sources = [
        f"{row['group']} ({row['substantive']}/{row['n']})"
        for row in metadata_rows
        if row["grouping"] == "source" and int(row["n"]) >= 3 and float(row["substantive_rate"]) >= 0.5
    ]
    bbq_rows = [row for row in rows if str(row["source"]).startswith("BBQ")]

    summary = {
        "n_pairs": len(rows),
        "mechanism_decomposition": {
            "final_substantive_count": len(final_yes),
            "token_counts": dict(token_counter),
            "mutually_exclusive_buckets": dict(mechanism_counter),
            "non_ui_response_core_count": sum(
                bool(split_types(str(row["final_divergence_type"])) & {"refusal_status", "factuality", "format_compliance"})
                for row in final_yes
            ),
            "no_ui_related_count": sum("ui_surface_signature" not in split_types(str(row["final_divergence_type"])) for row in final_yes),
            "pure_ui_or_ui_safety_count": sum(
                split_types(str(row["final_divergence_type"])) in ({"ui_surface_signature"}, {"ui_surface_signature", "safety_framing"})
                for row in final_yes
            ),
            "safety_only_count": sum(split_types(str(row["final_divergence_type"])) == {"safety_framing"} for row in final_yes),
        },
        "manual_review_yield": {
            "automated_visible_flags": len(automated_visible),
            "automated_to_substantive": sum(row["substantive_divergence"] == "yes" for row in automated_visible),
            "automated_to_minor": sum(row["substantive_divergence"] == "minor" for row in automated_visible),
            "automated_to_clean": sum(row["substantive_divergence"] == "no" for row in automated_visible),
            "substantive_precision_visible_flags": pct(sum(row["substantive_divergence"] == "yes" for row in automated_visible), len(automated_visible)),
            "nonvisible_rows": len(nonvisible),
            "nonvisible_to_substantive": len(substantive_from_nonvisible),
            "substantive_from_nonvisible_ids": substantive_from_nonvisible,
            "review_required_rows": len(review_required),
            "review_required_to_substantive": sum(row["substantive_divergence"] == "yes" for row in review_required),
        },
        "directionality": {
            "refusal_status_all": dict(refusal_direction),
            "safety_framing_all": dict(safety_direction),
            "refusal_status_final": dict(refusal_direction_final),
            "safety_framing_final": dict(safety_direction_final),
            "factuality": dict(factuality),
            "format_compliance": dict(format_counter),
            "ui_surface": {
                "app_only_any": len(ui_rows),
                "by_signature": ui_by_signature,
            },
        },
        "length_analysis": {
            "n": len(rows),
            "api_words_mean": round(mean(int(row["api_words"]) for row in rows) or 0.0, 1),
            "api_words_median": median(int(row["api_words"]) for row in rows),
            "app_words_mean": round(mean(int(row["app_words"]) for row in rows) or 0.0, 1),
            "app_words_median": median(int(row["app_words"]) for row in rows),
            "delta_words_mean": round(mean(deltas) or 0.0, 1),
            "delta_words_median": median(deltas),
            "app_longer": app_longer,
            "api_longer": api_longer,
            "equal_length": sum(delta == 0 for delta in deltas),
            "sign_test_p": sign_test_two_sided(app_longer, api_longer),
            "social_recommendation": next(
                row for row in length_groups if row["grouping"] == "category" and row["group"] == "social_recommendation"
            ),
        },
        "metadata_highlights": {
            "small_cell_high_rate_sources": small_cell_sources,
            "bbq_substantive": sum(row["substantive_divergence"] == "yes" for row in bbq_rows),
            "bbq_minor": sum(row["substantive_divergence"] == "minor" for row in bbq_rows),
            "bbq_n": len(bbq_rows),
        },
    }

    write_csv(
        args.out_dir / "mechanism_decomposition.csv",
        mechanism_rows,
        ["prompt_id", "category", "final_divergence_type", "mechanism_bucket", "has_ui_surface", "has_response_core"],
    )
    write_csv(
        args.out_dir / "manual_review_yield.csv",
        [
            {
                "visible_divergence": visible,
                "substantive_divergence": outcome,
                "count": sum(row["visible_divergence"] == visible and row["substantive_divergence"] == outcome for row in rows),
            }
            for visible in ["yes", "no"]
            for outcome in ["yes", "minor", "no"]
        ],
        ["visible_divergence", "substantive_divergence", "count"],
    )
    write_csv(
        args.out_dir / "directionality_summary.csv",
        [
            {"label": "refusal_status_all", **dict(refusal_direction)},
            {"label": "safety_framing_all", **dict(safety_direction)},
            {"label": "refusal_status_final", **dict(refusal_direction_final)},
            {"label": "safety_framing_final", **dict(safety_direction_final)},
            {"label": "factuality", **dict(factuality)},
            {"label": "format_compliance", **dict(format_counter)},
        ],
        [
            "label",
            "same",
            "api_higher",
            "app_higher",
            "app_better",
            "api_better",
            "api_pass_app_fail",
            "app_pass_api_fail",
            "not_applicable_mismatch",
            "other",
        ],
    )
    write_csv(
        args.out_dir / "length_analysis.csv",
        length_groups,
        [
            "grouping",
            "group",
            "n",
            "api_words_median",
            "app_words_median",
            "delta_words_median",
            "delta_words_mean",
            "app_longer",
            "api_longer",
            "sign_test_p",
            "substantive",
        ],
    )
    write_csv(
        args.out_dir / "metadata_substantive_rates.csv",
        metadata_rows,
        ["grouping", "group", "n", "substantive", "minor", "clean", "substantive_rate", "wilson95"],
    )

    (args.out_dir / "secondary_findings.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (args.out_dir / "secondary_findings.md").write_text(build_markdown(summary), encoding="utf-8")
    (args.out_dir / "secondary_findings_tables.tex").write_text(build_tex(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
