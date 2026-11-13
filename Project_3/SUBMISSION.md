# Submission: Project 3, Judge the Judge — team Outlier

## Authors
**Team name:** Outlier

**Project:** Project 3: Judge the Judge — a recipe for building LLM judges you can trust

## Problem and approach
A customer-service chatbot's replies are checked by an AI judge before they are sent. The starting judge misses
small changes in meaning: it let **93% of dropped conditions** through ("You can usually extend your rental" without
"as long as the car is not reserved"). For SIXT that means accidental promises to customers.

Our goal was a **recipe**, not one tuned judge: the same code must work for a criterion it has never seen, with
only the criterion text, the policy and a few labelled examples as input.

The recipe (`starter_pack/final_judge.py`, full write-up in `starter_pack/RECIPE.md`):
1. **Diagnose** where the judge fails (per edit type and language, reading the model's own reasoning).
2. **Code checks facts.** Numbers in the reply that appear nowhere in the policy are passed to the model as a fact
   note. The rule **tests itself on the labelled examples** first and is trusted only if it fires on at least 3
   failing examples and never on a passing one; when trusted and it fires, one fail vote is enough instead of two
   (so code never decides alone, but a trusted rule does lower the bar).
3. **The model reasons in fixed steps:** quote the policy rule → list the reply's statements → list every
   difference in meaning → **only the criterion decides**: for each difference the model must quote the part of the
   criterion it breaks, or write "not covered". Few-shot examples are chosen by code from the labelled pairs (up to
   8 minimal pairs, one per edit type with label-changing types first, so with criterion 1's 9 edit types
   "translation" is not shown as a pair; plus three single good replies). Two calls with the examples in a different order;
   the reply fails only if both say FAIL (benefit of the doubt for hedged wording, never for quantities).
4. **Verify honestly:** examples never come from the replies being scored (grouped by source reply); edit types
   never shown; a synthetic set with new topics and edit types; self-made practice criteria; repeated runs.

Assumptions: the policy text is the only source of truth; the labelled examples are representative of the criterion.

## Models and why
The model is fixed by the challenge. We compared prompt/recipe versions, not models.

| Model | Open-weight or closed | Where it runs | Main metric(s) | Cost and time per item | Chosen? |
| --- | --- | --- | --- | --- | --- |
| claude-haiku-4.5 (starting judge, 1 call) | closed | event LiteLLM proxy | combined 0.697 on dev | 1 call, ~1 s | baseline |
| claude-haiku-4.5 (our recipe, 2 calls) | closed | event LiteLLM proxy | combined ~0.91 on dev | 2 calls (~4k tokens each), ~1 cent, a few seconds | **yes** (required model; best version) |

Settings: temperature 0, 1,500 output tokens, 2 votes per reply (max 3 allowed), request pacing under the proxy's
rate limit.

## Results
All numbers with the organisers' `score.py`; held out by source reply (examples never from the scored replies).

**Criterion 1 (does the reply over-promise?), dev set, 226 cases**

| | combined | catch | keep |
|---|---|---|---|
| Starting judge | 0.697 | 0.592 | 0.847 |
| **Ours (3 runs)** | **0.915 / 0.897 / 0.910** | 0.886 / 0.857 / 0.876 | 0.947 / 0.941 / 0.948 |

- Dropped conditions caught: 7% → 80%. Certainty changes ("usually" → "always"): 50% → 100%.
- **Consistency** (`score.py --repeat`): **98.3%** same verdict, kappa 0.97 (235 replies).
- Per-case paired test vs the previous version: 22 vs 6 cases better, McNemar p = 0.004. Confidence intervals
  are wide because dev has only 9 source replies (`stats.py`).
- **Edit types never shown as examples:** the score holds (an earlier version scored 0.809 with each edit type
  hidden from the examples vs 0.803 with all types shown).
- **Synthetic set** (90 cases, 10 policy topics not in dev, 7 new edit types such as negation flips, invented
  promises, "per day" → "per rental", "€90" vs "90 EUR"): **ours 0.931 vs starting judge 0.810**; a second
  synthetic set (100 further cases): **0.908 vs 0.781**.

**New criteria (dress rehearsal before the surprise criterion).** We wrote practice criteria and relabelled the dev
cases, giving the judge only 12–17 examples, run with unchanged code:

| | starting judge | ours |
|---|---|---|
| A: states policy facts correctly | 0.932 | **0.931** |
| B: keeps the policy's conditions | 0.556 | **0.806** |
| C: starts with the answer (no opening pleasantry) | 0.424 | **0.720** |

**Criterion 2 (surprise criterion: "does the reply state the policy correctly?"), 73 labelled examples**

Our code was not changed: only `--criterion surprise/CRITERION.md` and `--dev surprise/dev_pairs.jsonl`. Our number
is held out by source reply (the judge only sees examples from other source replies), not the flattering
"score on the same examples" run.

| | combined | catch | keep |
|---|---|---|---|
| Starting judge | 0.652 | 0.600 | 0.715 |
| **Ours, recipe unchanged** | **0.863** | **0.833** | **0.895** |

- Per case: ours right where the starting judge is wrong 20 times, the reverse 5 times (McNemar p = 0.004).
- Dropped conditions caught 20% → 70%; translations kept 38% → 88%; wrong details 100%.
- The 10 remaining errors sit in 3 of the 9 source replies and are mostly borderline: "we can often extend by
  phone" vs. the policy's "some branches", and "often possible" without "depending on availability" (our rule that
  a hedge already conveys a general caveat passes it; the labels fail it). We did not tune for these: the same rule
  is what keeps good replies from being failed.

**What did not work** (details in `RECIPE.md`): asking for "every difference, however small" (judge too strict);
three attempts at explicit "who benefits" reasoning for numbers (each lowered criterion 1, e.g. 0.91 → 0.86);
turning the number rule into a note only (0.91 → 0.78).

**Limits:** the judge still misreads the direction of some number changes on new topics (wrong numbers on new
topics caught ~63%); dev has only 9 source replies, so hidden-test scores will likely be somewhat lower.

## How to run
From a fresh clone (Python 3.11+):

```bash
cd Project_3
bash setup.sh                      # venv + .env from .env.example
# fill in .env: JUDGE_LLM_BASE_URL, JUDGE_LLM_API_KEY, JUDGE_LLM_MODEL=claude-haiku-4.5
set -a; . .env; set +a
cd starter_pack
# judge a pairs file
../.venv/bin/python run_judge.py --judge final_judge.py --pairs dev_pairs.jsonl \
    --criterion JUDGE1_CRITERION.md --policy policy.md --dev dev_pairs.jsonl --out verdicts.csv
../.venv/bin/python score.py verdicts.csv dev_pairs.jsonl
# honest evaluation (examples from other source replies only)
../.venv/bin/python cv_eval.py --judge final_judge.py --pairs dev_pairs.jsonl \
    --criterion JUDGE1_CRITERION.md --policy policy.md --out cv.csv
# final submission runs (both criteria, twice each)
bash run_submission.sh <criterion1_cases.jsonl> <criterion2_cases.jsonl> <CRITERION2.md> <criterion2_dev.jsonl>
```

Environment variables (names only): `JUDGE_LLM_BASE_URL`, `JUDGE_LLM_API_KEY`, `JUDGE_LLM_MODEL`; optional
`FINAL_JUDGE_NO_PROXY_CACHE=1` (bypass the event proxy's response cache for repeat runs), `FINAL_JUDGE_MAX_RPM`.
No secrets or real data are in the repository.

Other tools: `loo_eval.py` (edit types never shown), `stats.py` (cluster bootstrap, McNemar), `mock/` (practice
criteria), `synth/` (synthetic test set and the prompt that generated it).

## Demo
`submission/slides.pdf` (max 5 slides). [TBD]

## Next steps
- **For SIXT:** run the judge on every chatbot reply before it is sent; show the agent the reason and the policy
  line when a reply is blocked; choose strict or balanced mode depending on the risk of a topic.
- Number direction: a small, separate check for quantities (value, unit, basis) instead of more prompt text.
- More source replies for evaluation (dev has 9), and human labels for borderline cases.
