# Scale-Up Plan After Meeting 3

Prepared: 5 June 2026  
Status: bank generated and validated; OpenAI API side collected; ChatGPT app side pending

## Objective

Move from the 20-prompt method pilot to a first thesis-scale collection without expanding the thesis beyond the agreed scope. The core empirical comparison remains:

- OpenAI API;
- official ChatGPT consumer app.

Claude and Gemini remain API-only extension baselines unless consumer-app collection is feasible without disrupting the schedule. Sparkloom remains a qualitative wrapper vignette unless explicitly widened later.

## Scale-Up Size

Use a 60-prompt first scale-up set rather than jumping directly to 80. This is large enough to test category-level patterns while preserving time for manual review, writing, and robustness checks. The first bank has now been generated as `prompt_bank_60.csv` for meeting-safe review and `prompt_bank_60_private.csv` for controlled local collection.

| Category | Target count | Sources |
| --- | ---: | --- |
| A Allowed-sensitive / over-refusal | 12 | XSTest, OR-Bench |
| B Refusal-expected | 10 | Do-Not-Answer, HarmBench |
| C Boundary / safety framing | 10 | AILuminate-informed prompts, HELM-style hazard framing |
| D Instruction following | 8 | IFEval |
| E Social recommendations | 10 | BBQ-adapted scenarios |
| F Neutral factual controls | 10 | SimpleQA, TruthfulQA |
| **Total** | **60** |  |

Optional expansion to 72 or 80 prompts should happen only if collection and manual review stay on schedule.

Validated source counts in the generated bank:

- XSTest: 12
- Do-Not-Answer: 7
- HarmBench: 3
- AILuminate-informed: 10
- IFEval: 8
- BBQ-adapted prompts: 10
- SimpleQA: 6
- TruthfulQA: 4

## Collection Design

| Step | Output |
| --- | --- |
| Freeze 60-prompt bank | Done: `prompt_bank_60.csv` with category, source, expected behavior, risk level, coding focus |
| API collection | Done: 60/60 OpenAI API rows with `gpt-4o`, no custom system prompt, exact model string logged |
| App collection | ChatGPT app, one fresh chat per prompt where possible, screenshot archive, transcription QA |
| Extension APIs | Claude/Gemini APIs on same 60 prompts if time allows |
| Scoring | automated first-pass labels plus pairwise divergences |
| Manual review | all flagged rows, all Category B rows, all UI-surface rows, and a random clean subset |

## Updated Coding Variables

Use the following formal labels:

- `refusal_status`
- `safety_framing_strength`
- `answer_directness`
- `format_compliance`
- `unsupported_inference`
- `factuality`
- `verbosity`
- `ui_surface_signature`

`ui_surface_signature` values:

- `none`
- `web_search`
- `map_widget`
- `local_context`
- `reasoning_trace`
- `source_card`
- `file_or_canvas`
- `wrapper_orchestration`
- `other`

The label records only visible behavior. It must not be used to infer hidden system prompts or internal routing.

## Screenshot Transcription QA

Screenshot collection is acceptable if QA is documented.

Minimum QA:

- every app row has a screenshot path;
- every app row has transcribed `raw_output`;
- all high-risk rows are checked against screenshots in the private log;
- all candidate divergence examples are checked against screenshots;
- at least 20 percent of non-flagged rows are randomly checked;
- rows with cropped or uncertain text are marked `transcription_status=needs_review`.

## Sparkloom Handling

The existing 10-row Sparkloom safe subset is scored separately as wrapper evidence:

- 5 blueprint reframes;
- 5 orchestration-only sessions;
- all rows coded as `ui_surface_signature=wrapper_orchestration`.

Use Sparkloom only for a short qualitative wrapper vignette unless Aleksandra explicitly asks to extend it. Do not include it in the core API-versus-ChatGPT result tables.

## Immediate Implementation Sequence

1. Done: build `prompt_bank_60.csv` and private local collection bank.
2. Done: run schema, category-balance, redaction, and source-mapping checks.
3. Done: update OpenAI runner for both 20-prompt and 60-prompt banks.
4. Done: collect OpenAI API rows.
5. Done: create API-only first-pass summary with clear no-channel-claim boundary.
6. Next: collect ChatGPT screenshots and transcriptions.
7. Run transcription QA.
8. Run pairwise scorer.
9. Manually review all flagged rows.
10. Produce a short scale-up result memo for Aleksandra.

## Open Questions For Aleksandra

1. Is the 60-prompt first scale-up size acceptable, or should the target be closer to 80?
2. Should Claude/Gemini API runs be collected for all 60 prompts or only for the final reduced analysis set?
3. Should Sparkloom remain a vignette, or should it be extended to the full 20-prompt pilot before being frozen?
4. Is delayed self-recoding acceptable for reliability, or should we try to find a second coder for a subset?
