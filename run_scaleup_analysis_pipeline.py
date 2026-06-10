#!/usr/bin/env python3
"""Run the full scale-up analysis pipeline after app collection."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_APP_OUT = ROOT / "pilot_outputs" / "20260608"
DEFAULT_API_OUT = ROOT / "pilot_outputs" / "20260605"
APP_LOG = DEFAULT_APP_OUT / "chatgpt_app_scaleup_60_cleaned" / "chatgpt_app_log_private.csv"
APP_SHARED = DEFAULT_APP_OUT / "chatgpt_app_scaleup_60_cleaned" / "chatgpt_app_log_shared.csv"
API_LOG = DEFAULT_API_OUT / "openai_api_scaleup_60" / "api_log_private.csv"
ANALYSIS_OUT = DEFAULT_APP_OUT / "analysis_scaleup_cleaned"
PROMPT_BANK = ROOT / "prompt_bank_60.csv"
MEETING_PACKAGE = ROOT / "meeting_package"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT.parent).returncode


def copy_meeting_artifacts(analysis_out: Path) -> None:
    """Copy analysis summaries into meeting_package for supervisor review."""
    MEETING_PACKAGE.mkdir(parents=True, exist_ok=True)
    copies = [
        (analysis_out / "results_summary.json", MEETING_PACKAGE / "scaleup_results_summary.json"),
        (analysis_out / "thesis_tables" / "scaleup_analysis_summary.json", MEETING_PACKAGE / "scaleup_analysis_summary.json"),
        (analysis_out / "thesis_tables" / "completeness_summary.json", MEETING_PACKAGE / "scaleup_completeness_summary.json"),
        (analysis_out / "thesis_tables" / "scaleup_result_memo.md", MEETING_PACKAGE / "scaleup_result_memo.md"),
        (analysis_out / "intra_coder_reliability.json", MEETING_PACKAGE / "intra_coder_reliability.json"),
        (ROOT / "meeting_package" / "validation_scaleup_app_log.json", MEETING_PACKAGE / "validation_scaleup_app_log.json"),
    ]
    for src, dst in copies:
        if src.exists() and src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
            print(f"Copied {src.name} -> {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scale-up analysis pipeline.")
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--allow-partial", action="store_true", help="Allow incomplete app log (interim runs).")
    parser.add_argument("--app-log-private", type=Path, default=APP_LOG)
    parser.add_argument("--app-log-shared", type=Path, default=APP_SHARED)
    parser.add_argument("--openai-api-log", type=Path, default=API_LOG)
    parser.add_argument("--out-dir", type=Path, default=ANALYSIS_OUT)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_validation:
        validate_cmd = [
            sys.executable,
            str(ROOT / "validate_scaleup_app_log.py"),
            "--app-log-private",
            str(args.app_log_private),
            "--app-log-shared",
            str(args.app_log_shared),
            "--out-json",
            str(MEETING_PACKAGE / "validation_scaleup_app_log.json"),
        ]
        if args.allow_partial:
            validate_cmd.append("--allow-partial")
        code = run(validate_cmd)
        if code != 0:
            print("Validation failed; fix app log before scoring.", file=sys.stderr)
            return code

    code = run([
        sys.executable,
        str(ROOT / "score_pilot_results.py"),
        "--prompt-bank",
        str(PROMPT_BANK),
        "--out-dir",
        str(args.out_dir),
        "--openai-api-log",
        str(args.openai_api_log),
        "--chatgpt-app-log",
        str(args.app_log_private),
    ])
    if code != 0:
        return code

    code = run([
        sys.executable,
        str(ROOT / "build_scaleup_manual_review_sheet.py"),
        "--pairwise",
        str(args.out_dir / "pairwise_results.csv"),
        "--app-log-private",
        str(args.app_log_private),
        "--out",
        str(args.out_dir / "scaleup_manual_review_sheet.csv"),
    ])
    if code != 0:
        return code

    code = run([
        sys.executable,
        str(ROOT / "apply_scaleup_manual_review.py"),
        "--review-sheet",
        str(args.out_dir / "scaleup_manual_review_sheet.csv"),
        "--pairwise",
        str(args.out_dir / "pairwise_results.csv"),
        "--out",
        str(args.out_dir / "scaleup_human_reviewed_coding_sheet.csv"),
    ])
    if code != 0:
        return code

    code = run([
        sys.executable,
        str(ROOT / "compute_intra_coder_reliability.py"),
        "--review-sheet",
        str(args.out_dir / "scaleup_manual_review_sheet.csv"),
        "--out-json",
        str(args.out_dir / "intra_coder_reliability.json"),
    ])
    if code != 0:
        return code

    code = run([
        sys.executable,
        str(ROOT / "generate_scaleup_thesis_tables.py"),
        "--analysis-dir",
        str(args.out_dir),
        "--out-dir",
        str(args.out_dir / "thesis_tables"),
    ])
    if code != 0:
        return code

    copy_meeting_artifacts(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
