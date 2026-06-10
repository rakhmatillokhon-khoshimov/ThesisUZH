# Four-Channel Behavioral Agreement (no new collection)

Uses the study's own uniformly-coded labels for all four channels on the same 60 prompts. Refusal posture is collapsed to {answered, safe\_redirect, full\_refusal}.

## Context: refusal-posture agreement with the ChatGPT app

Refusal-posture agreement with the ChatGPT app, by channel:

| Channel | Agreement with app | Disagreements |
|---|---:|---:|
| Gemini API | 0.967 | 2 |
| Claude API | 0.950 | 3 |
| OpenAI API | 0.900 | 6 |

The app's closest channel on refusal posture is **Gemini API**; the OpenAI API ranks #3 of three. This is secondary context, not a new primary result: the consumer app does not behave most like its own provider's raw API on this label set.

## Why: only the OpenAI API uses bare full refusals

| Channel | Bare full refusals | Safe redirects |
|---|---:|---:|
| OpenAI API | 5 | 0 |
| ChatGPT app | 0 | 6 |
| Claude API | 0 | 5 |
| Gemini API | 1 | 4 |

Every channel except the OpenAI API resolves refusal-expected prompts through bounded safe redirection rather than a bare refusal. The ChatGPT app patterns with the other consumer-grade / instruction-tuned surfaces, not with the plain OpenAI Responses API.

## Refusal agreement across the three raw APIs

Fleiss' kappa across the OpenAI, Claude, and Gemini APIs on collapsed refusal posture is 0.431. Pairwise Cohen's kappa and agreement:

| Pair | Agreement | Cohen kappa |
|---|---:|---:|
| OpenAI API vs ChatGPT app | 0.900 | 0.429 |
| OpenAI API vs Claude API | 0.883 | 0.270 |
| OpenAI API vs Gemini API | 0.933 | 0.579 |
| ChatGPT app vs Claude API | 0.950 | 0.700 |
| ChatGPT app vs Gemini API | 0.967 | 0.802 |
| Claude API vs Gemini API | 0.917 | 0.459 |

## Safety framing: who adds the most caution

| Channel | Mean framing (0--3) | Any-framing rate |
|---|---:|---:|
| OpenAI API | 0.52 | 0.38 |
| ChatGPT app | 0.72 | 0.57 |
| Claude API | 0.68 | 0.47 |
| Gemini API | 0.98 | 0.65 |

### Interpretation (claim-safe)

These are observable agreement patterns among coded labels, not claims about shared internal mechanisms. The bounded interpretation is that the bare OpenAI API condition is not a reliable proxy for the productized ChatGPT app on refusal posture in this collection.
