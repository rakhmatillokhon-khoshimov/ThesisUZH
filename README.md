# Auditing Access Channel Effects in LLM Behavior

This repository contains the public thesis package for a Master's thesis on
observable differences between a bare OpenAI API condition and the official
ChatGPT consumer-app deployment.

The empirical comparison uses a frozen 60-prompt diagnostic suite. The public
repository includes the redacted prompt bank, thesis source, generated summary
tables, figures, analysis scripts, and final PDF. Private raw prompts, raw model
outputs, screenshots, API response JSON files, and second-coder handoff packets
are intentionally excluded.

## Current Thesis Claim

On a frozen, benchmark-grounded 60-prompt suite, a bare OpenAI Responses API
condition (`gpt-4o`, no custom system prompt) and the productized ChatGPT app
deployment produced different observable behavior under documented collection
conditions. The strongest response-core differences are refusal granularity and
factual support, with additional product-surface findings such as visible
sources and localized context.

The thesis does not claim that access channel alone, a hidden system prompt,
retrieval policy, routing rule, or moderation component caused the observed
differences.

## Repository Layout

- `thesis_draft/` - LaTeX thesis source.
- `docs/` - final thesis PDF and plain-text abstract.
- `meeting_visuals/` - figures used by the thesis.
- `pilot_outputs/20260608/analysis_scaleup_cleaned/` - public-safe generated
  analysis summaries and LaTeX tables.
- `prompt_bank_60.csv` - shared/redacted 60-prompt bank.
- `prompt_taxonomy.*`, `taxonomy_coding_guide.md` - prompt and coding
  definitions.
- `*.py` - analysis and table-generation scripts retained for auditability.
- `presentations/` - current supervisor progress presentation.

## Build the Thesis

From the repository root:

```bash
cd thesis_draft
pdflatex main.tex
pdflatex main.tex
```

The checked public export was verified to compile to an 88-page PDF.

## Reproducibility Boundary

This public export is designed to compile the thesis and inspect the summary
analysis artifacts. It is not a full raw-data release. The following materials
remain local/private:

- `prompt_bank_60_private.csv` and other executable high-risk prompt files;
- raw API logs, raw app logs, API JSON response folders, and screenshot archives;
- `app_collection_kit/` prompt sheets;
- second-coder handoff packets and primary-label keys;
- `.env` files and API credentials.

See `PUBLIC_DATA_NOTICE.md` for the exact exclusion policy.

## Key Results Snapshot

- Complete OpenAI API vs ChatGPT app pairs: 60/60.
- Final substantive observable divergences after review: 17/60.
- Response-core subset: 10/60.
- Full-refusal asymmetry: API-only 5, app-only 0; McNemar exact `p=0.0625`.
- OpenAI API refusal label stability across three API runs: Fleiss `kappa=1.0`.
- Within-channel API lexical similarity exceeded API-vs-app similarity on 60/60
  prompts.
- Human inter-rater reliability remains pending in the public thesis text.

## Suggested GitHub Setup

```bash
cd /Users/rakhmatillokhonkhoshimov/Thesis/thesis-github-ready
git init
git add .
git commit -m "Initial public thesis repository"
```

Before pushing, keep the repo public-safe by checking that no files with
`private`, `PRIVATE`, `screenshots_private`, `responses`, or `.env` appear in
`git status`.
