# Auditing Access Channel Effects in LLM Behavior

This repository contains the thesis source, summary data, analysis code, and
compiled PDF for a Master's thesis on observable differences between a bare
OpenAI API condition and the official ChatGPT consumer-app deployment.

The empirical comparison uses a frozen 60-prompt diagnostic suite. The repository
includes the redacted prompt bank, thesis source, derived summary tables,
figures, analysis scripts, and final PDF. Restricted prompt text, raw model
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

- `thesis/` - LaTeX thesis source.
- `docs/` - final thesis PDF, abstract, and data-access note.
- `figures/` - figures used by the thesis.
- `results/analysis/` - reviewed summary data, statistics, and LaTeX tables.
- `data/prompts/prompt_bank_60.csv` - shared/redacted 60-prompt bank.
- `data/prompts/prompt_taxonomy.*`, `data/prompts/taxonomy_coding_guide.md` - prompt and coding
  definitions.
- `scripts/` - analysis and table-generation scripts retained for auditability.
- `protocols/` - collection, coding, transcription QA, and reliability protocols.

## Build the Thesis

From the repository root:

```bash
cd thesis
pdflatex -interaction=nonstopmode -halt-on-error main.tex
biber main
makeglossaries main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

On this macOS TeX Live install, `make thesis` falls back to
`/usr/local/texlive/2025/bin/universal-darwin/makeglossaries` if
`makeglossaries` is not on `PATH`.

The repository was verified to compile to a 95-page PDF.

## Reproducibility Boundary

This repository is designed to compile the thesis and inspect the summary
analysis artifacts. It is not a full raw-data release. The following materials
remain restricted:

- `prompt_bank_60_private.csv` and other executable high-risk prompt files;
- raw API logs, raw app logs, API JSON response folders, and screenshot archives;
- `app_collection_kit/` prompt sheets;
- second-coder handoff packets and primary-label keys;
- `.env` files and API credentials.

See `docs/DATA_ACCESS.md` for the exact exclusion policy.

## Key Results Snapshot

- Complete OpenAI API vs ChatGPT app pairs: 60/60.
- Final substantive observable divergences after review: 17/60.
- Response-core subset: 10/60.
- Full-refusal asymmetry: API-only 5, app-only 0; McNemar exact `p=0.0625`.
- OpenAI API refusal label stability across three API runs: Fleiss `kappa=1.0`.
- Within-channel API lexical similarity exceeded API-vs-app similarity on 60/60
  prompts.
- Human inter-rater reliability on 54 blind coding units: refusal status,
  format compliance, and unsupported inference `kappa=1.0`; factuality
  `kappa=0.72`; UI-surface signature `kappa=0.54`; safety-framing strength
  `kappa=0.06` and is treated only as descriptive context.
