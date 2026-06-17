#!/usr/bin/env python3
"""Generate LaTeX-ready tables and JSON summaries for the thesis Results chapter."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def latex_escape(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("&", "\\&")
        .replace("%", "\\%")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate thesis results tables.")
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pairwise = [
        row for row in read_csv(args.analysis_dir / "pairwise_results.csv")
        if row.get("model_family") == "openai"
    ]
    reviewed = read_csv(args.analysis_dir / "scaleup_human_reviewed_coding_sheet.csv")
    summary_json = json.loads((args.analysis_dir / "results_summary.json").read_text(encoding="utf-8"))

    category_div = Counter()
    div_type_counts = Counter()
    ui_counts = Counter()
    substantive_rows = []

    for row in reviewed:
        if row.get("substantive_divergence") != "yes":
            continue
        if row.get("visible_divergence") == "not_collected":
            continue
        # Count UI-surface signatures only among final retained (substantive)
        # cases, matching the table caption and the ui_surface_signature total
        # in the corrected-summary and reviewed-coding tables.
        ui = row.get("app_ui_surface_signature", "none")
        if ui not in {"", "none", "missing"}:
            ui_counts[ui] += 1
        category_div[row.get("category", "unknown")] += 1
        for part in row.get("final_divergence_type", "").split(";"):
            if part and part != "none":
                div_type_counts[part] += 1
        substantive_rows.append(row)

    completeness = {
        "prompt_count": len(pairwise),
        "complete_pairs": sum(1 for r in pairwise if r.get("visible_divergence") != "not_collected"),
        "automated_divergences": sum(1 for r in pairwise if r.get("visible_divergence") == "yes"),
        "substantive_manual": len(substantive_rows),
        "created_at": datetime.now().astimezone().isoformat(),
    }
    (args.out_dir / "completeness_summary.json").write_text(
        json.dumps(completeness, indent=2) + "\n",
        encoding="utf-8",
    )

    partial_note = ""
    if completeness["complete_pairs"] < completeness["prompt_count"]:
        partial_note = (
            f"% INTERIM: {completeness['complete_pairs']}/{completeness['prompt_count']} "
            "complete pairs; regenerate after full app collection.\n"
        )

    lines = [
        "% Script-produced scale-up results tables",
        partial_note,
        "",
        "\\begin{longtable}{llr}",
        "\\toprule",
        "Category & Divergence type & Count \\\\",
        "\\midrule",
    ]
    for cat, count in sorted(category_div.items()):
        lines.append(f"{latex_escape(cat)} & substantive & {count} \\\\")
    lines.extend(["\\bottomrule", "\\end{longtable}", ""])

    lines.extend([
        "\\begin{longtable}{lr}",
        "\\toprule",
        "UI-surface signature & Count \\\\",
        "\\midrule",
    ])
    for sig, count in ui_counts.most_common():
        lines.append(f"\\texttt{{{latex_escape(sig)}}} & {count} \\\\")
    lines.extend(["\\bottomrule", "\\end{longtable}", ""])

    (args.out_dir / "scaleup_results_tables.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    memo_lines = [
        "# Scale-Up Result Memo",
        "",
        f"Generated: {completeness['created_at']}",
        "",
        f"- Complete OpenAI pairs: {completeness['complete_pairs']}/60",
        f"- Automated first-pass divergences: {completeness['automated_divergences']}",
        f"- Substantive after manual review: {completeness['substantive_manual']}",
        "",
        "## Substantive cases (claim-safe summaries)",
        "",
    ]
    for row in substantive_rows[:25]:
        memo_lines.append(
            f"- **{row['prompt_id']}** ({row['category']}): {row['claim_safe_summary']} "
            f"[{row['final_divergence_type']}]"
        )
    (args.out_dir / "scaleup_result_memo.md").write_text("\n".join(memo_lines) + "\n", encoding="utf-8")

    payload = {
        "completeness": completeness,
        "category_substantive_counts": dict(category_div),
        "divergence_type_counts": dict(div_type_counts),
        "ui_surface_counts": dict(ui_counts),
        "channel_summary": summary_json,
    }
    (args.out_dir / "scaleup_analysis_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(completeness, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
