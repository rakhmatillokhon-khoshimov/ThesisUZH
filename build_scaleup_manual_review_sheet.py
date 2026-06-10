#!/usr/bin/env python3
"""Build a manual-review queue for the 60-prompt scale-up.

The output is deliberately meeting-safe: it contains labels, paths, and review
prompts, but not raw model outputs. Raw outputs stay in the private logs.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parent
DEFAULT_PROMPT_BANK = ROOT / "prompt_bank_60.csv"

FIELDS = [
    "prompt_id",
    "category_id",
    "category",
    "source",
    "review_required",
    "review_reasons",
    "visible_divergence",
    "divergence_type",
    "api_refusal_status",
    "app_refusal_status",
    "api_safety_framing",
    "app_safety_framing",
    "api_format_compliance",
    "app_format_compliance",
    "api_unsupported_inference",
    "app_unsupported_inference",
    "api_factuality",
    "app_factuality",
    "api_ui_surface_signature",
    "app_ui_surface_signature",
    "app_transcription_status",
    "app_screenshot_path",
    "manual_verdict",
    "substantive_divergence",
    "final_divergence_type",
    "reviewer_notes",
    "claim_safe_summary",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def is_non_none_surface(value: str) -> bool:
    return value.strip() not in {"", "none", "missing"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build scale-up manual-review sheet.")
    parser.add_argument("--prompt-bank", type=Path, default=DEFAULT_PROMPT_BANK)
    parser.add_argument("--pairwise", type=Path, required=True)
    parser.add_argument("--app-log-private", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--clean-control-count",
        type=int,
        default=10,
        help="Number of non-flagged clean OpenAI pairs to add as controls.",
    )
    args = parser.parse_args()

    prompts = read_csv(args.prompt_bank)
    pairwise = [
        row for row in read_csv(args.pairwise)
        if row.get("model_family") == "openai"
    ]
    app_by_id = {row["prompt_id"]: row for row in read_csv(args.app_log_private)}
    prompt_by_id = {row["prompt_id"]: row for row in prompts}

    rows: List[Dict[str, str]] = []
    clean_controls_added = 0
    for pair in pairwise:
        prompt_id = pair["prompt_id"]
        prompt = prompt_by_id.get(prompt_id, {})
        app_row = app_by_id.get(prompt_id, {})
        reasons: List[str] = []

        if prompt.get("category_id") == "B":
            reasons.append("category_b")
        if pair.get("visible_divergence") == "yes":
            reasons.append("automated_divergence")
        if is_non_none_surface(pair.get("app_ui_surface_signature", "")):
            reasons.append("ui_surface")
        if app_row.get("transcription_status") == "needs_review":
            reasons.append("transcription_needs_review")
        if "collection_block" in pair.get("divergence_type", ""):
            reasons.append("collection_block")

        if not reasons and clean_controls_added < args.clean_control_count:
            reasons.append("clean_control_sample")
            clean_controls_added += 1

        review_required = "yes" if reasons else "no"
        claim_summary = "Private-log review required before quoting."
        if prompt.get("category_id") == "B":
            claim_summary = "High-risk refusal prompt; do not quote raw prompt or output in shared text."
        elif pair.get("visible_divergence") == "no":
            claim_summary = "Candidate clean control unless manual review finds a substantive difference."

        rows.append({
            "prompt_id": prompt_id,
            "category_id": prompt.get("category_id", ""),
            "category": prompt.get("category", pair.get("category", "")),
            "source": prompt.get("source", ""),
            "review_required": review_required,
            "review_reasons": ";".join(reasons) if reasons else "none",
            "visible_divergence": pair.get("visible_divergence", ""),
            "divergence_type": pair.get("divergence_type", ""),
            "api_refusal_status": pair.get("api_refusal_status", ""),
            "app_refusal_status": pair.get("app_refusal_status", ""),
            "api_safety_framing": pair.get("api_safety_framing", ""),
            "app_safety_framing": pair.get("app_safety_framing", ""),
            "api_format_compliance": pair.get("api_format_compliance", ""),
            "app_format_compliance": pair.get("app_format_compliance", ""),
            "api_unsupported_inference": pair.get("api_unsupported_inference", ""),
            "app_unsupported_inference": pair.get("app_unsupported_inference", ""),
            "api_factuality": pair.get("api_factuality", ""),
            "app_factuality": pair.get("app_factuality", ""),
            "api_ui_surface_signature": pair.get("api_ui_surface_signature", ""),
            "app_ui_surface_signature": pair.get("app_ui_surface_signature", ""),
            "app_transcription_status": app_row.get("transcription_status", ""),
            "app_screenshot_path": app_row.get("screenshot_path", ""),
            "manual_verdict": "",
            "substantive_divergence": "",
            "final_divergence_type": "",
            "reviewer_notes": "",
            "claim_safe_summary": claim_summary,
        })

    write_csv(args.out, rows)
    required_count = sum(1 for row in rows if row["review_required"] == "yes")
    print(f"Wrote {len(rows)} rows to {args.out}")
    print(f"Manual-review required rows: {required_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
