# ChatGPT Screenshot And Text Collection QA Protocol

**Purpose:** define the consumer-app collection standard after the 29 May supervision meeting. Screenshot-based collection is acceptable if transcription quality is checked; direct text export remains preferable when easy, but is no longer a blocker for scale-up.

## Status

The 27 May screenshot run is usable as evidence that all 20 prompts were submitted to the ChatGPT website, including the high-risk refusal prompts. Aleksandra's guidance was that a full app rerun is not needed before scale-up if the screenshot-to-text transcription is reliable.

Remaining weaknesses to document:

- the visible model label is not reliably captured in the screenshots;
- session-reset status is marked as unknown;
- screenshots are harder to audit than direct text logs unless a QA pass is documented.

For full-scale collection, screenshots are acceptable if every row has a screenshot path, a transcribed raw output, a `ui_surface_signature`, and a transcription QA status.

## Account And Browser Setup

1. Use a dedicated ChatGPT account created only for the thesis pilot.
2. Use a separate browser profile or private window.
3. Turn off memory/personalization if the account UI exposes that setting.
4. Do not install extensions that alter ChatGPT output rendering.
5. Record the approximate account settings in the log.
6. Do not bypass CAPTCHAs, rate limits, login checks, or safety controls.

## Run Conditions

| Field | Required value |
|---|---|
| Channel | official ChatGPT consumer app |
| Prompt order | P01 to P20 |
| Session policy | new chat per prompt where possible |
| Prompt form | single user message, no added context |
| Output capture | screenshot archive plus copied text if available; otherwise verified transcription |
| Screenshot | save one screenshot per response as supporting evidence |
| High-risk prompts | P06-P09 collected only if the account remains usable and the app accepts the prompt |

## Logging Procedure

For each prompt:

1. Open a new chat.
2. Paste exactly the prompt text from `pilot_prompt_bank_private.csv`.
3. Wait until the response is complete.
4. Copy the full assistant response text into `raw_output` if possible; otherwise transcribe from the screenshot.
5. Record the visible model label if shown.
6. Record `ui_surface_signature` and `ui_surface_notes` for tools, citations, maps, reasoning indicators, local-context elements, or other UI-only behavior.
7. Save a screenshot to `pilot_outputs/YYYYMMDD/chatgpt_app_clean_text/screenshots/Pxx.png`.
8. Move to the next prompt.

## Output File

Create or fill:

`pilot_outputs/YYYYMMDD/chatgpt_app_collection/chatgpt_app_log_private.csv`

Use the same fields as:

`pilot_outputs/20260527/chatgpt_app_manual_screenshots/chatgpt_app_log_private.csv`

Shared logs must redact raw high-risk outputs for P06-P09.

## Transcription QA

For each collection batch:

1. Verify all rows have a screenshot path.
2. Verify all rows have transcribed `raw_output`.
3. Manually compare a random subset of at least 20 percent of screenshots against the CSV text.
4. For any row with cropped or uncertain text, mark `transcription_status=needs_review`.
5. For high-risk rows, verify the private log only; keep shared files redacted.

## Acceptance Criteria

- 20 rows exist.
- Every row has a full copied or verified transcribed `raw_output`.
- Every row has a screenshot path.
- `model_label_visible` is filled where visible; otherwise explicitly `not_visible`.
- `session_reset` is `true`, `false`, or `unknown`, not blank.
- `ui_surface_signature` is coded for all rows.
- `transcription_status` is `verified`, `needs_review`, or `not_applicable`.
- No high-risk raw prompt or output appears in shared files.
