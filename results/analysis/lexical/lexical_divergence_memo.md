# Classifier-Independent Lexical Divergence (API vs app)

An objective cross-check of the manual taxonomy. No project coder is used; we measure raw text divergence between the OpenAI API and ChatGPT app outputs on 60 prompts.

## Do coder-flagged prompts also diverge more objectively?

Token Jaccard similarity (higher = more similar text):

- Substantive prompts (n=17): mean 0.1886, median 0.1812
- Other prompts (n=43): mean 0.2345, median 0.2245
- Mann--Whitney U = 259, z = -1.747, p = 0.0806, rank-biserial = 0.291.

The prompts the coders marked substantive have lower API-vs-app text overlap, in the expected direction, though the difference is only directional at this sample size (p = 0.0806, not significant at .05). It is consistent evidence that the manual taxonomy tracks an objective surface signal rather than coder preference, but it is not independently conclusive.

## Direction of the difference (robust descriptive findings)

- The app answer is longer than the API answer on 51/60 prompts (mean length ratio app/api = 3.0061).
- Source/citation markers: app 6 vs API 3 total.
- Hedge markers: app 63 vs API 31 total.

### Interpretation (claim-safe)

These are surface-text measures, not semantic judgements. Their value is convergent validity: an independent, reproducible signal agrees with the manual divergence labels and shows the app answers are systematically longer and carry more source-like and hedging markers.
