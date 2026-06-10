# Public Data Notice

This repository is a public-safe thesis export. It preserves enough material to
read, compile, and audit the thesis claims at the summary-artifact level, while
excluding materials that should not be published on GitHub.

## Included

- Redacted 60-prompt bank and prompt taxonomy.
- Coding guide and claim-safe case summaries.
- Final reviewed coding summaries without raw prompt or full raw output text.
- Generated statistics, tables, and figures used by the thesis.
- Analysis scripts used to produce the summary artifacts.
- Final thesis PDF and supervisor progress presentation.

## Excluded

- Private prompt banks with executable high-risk prompt text.
- Raw API logs, raw app logs, and raw JSON response files.
- Screenshot archives and OCR text archives.
- Private second-coder packets, primary-label keys, and blind sheets containing
  raw prompt/output material.
- API credentials and local `.env` files.
- Historical meeting drafts, administrative forms, CVs, and unrelated thesis
  search material.

## Why Raw Data Is Excluded

The study includes high-risk benchmark prompts from refusal and safety datasets.
The thesis reports redacted descriptors, labels, counts, screenshots paths, and
claim-safe excerpts where needed, but it avoids publishing executable prompt
text or full high-risk model outputs. This keeps the public repository useful
for methodological review without unnecessarily distributing harmful material.

## Private Reproduction

Full end-to-end reproduction from raw model outputs requires the private local
archive. That archive is not part of this GitHub-ready export.
