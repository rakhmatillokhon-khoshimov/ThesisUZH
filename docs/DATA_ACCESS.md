# Data Access

This repository contains enough material to read, compile, and audit the thesis
claims at the summary-artifact level. Materials that should not be published on
GitHub are excluded.

## Included

- Redacted 60-prompt bank and prompt taxonomy.
- Coding guide and claim-safe case summaries.
- Final reviewed coding summaries without raw prompt or full raw output text.
- Derived statistics, tables, and figures used by the thesis.
- Analysis scripts used to produce the summary artifacts.
- Final thesis PDF and supervisor progress presentation.

## Excluded

- Restricted prompt banks with executable high-risk prompt text.
- Raw API logs, raw app logs, and raw JSON response files.
- Screenshot archives and OCR text archives.
- Restricted second-coder packets, primary-label keys, and blind sheets containing
  raw prompt/output material.
- API credentials and local `.env` files.
- Historical meeting drafts, administrative forms, CVs, and unrelated thesis
  search material.

## Why Raw Data Is Excluded

The study includes high-risk benchmark prompts from refusal and safety datasets.
The thesis reports redacted descriptors, labels, counts, screenshot evidence, and
claim-safe excerpts where needed, but it avoids publishing executable prompt
text or full high-risk model outputs. This keeps the public repository useful
for methodological review without unnecessarily distributing harmful material.

## Restricted Reproduction

Full end-to-end reproduction from raw model outputs requires the restricted local
archive. That archive is not part of this repository.
