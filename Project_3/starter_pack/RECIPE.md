# Our recipe for building an LLM judge

A repeatable recipe for a criterion you have never seen. Only the inputs change: criterion text, policy, and a few
labelled example pairs. Code: `final_judge.py`. Honest evaluation: `cv_eval.py`. Numbers come from `score.py`.

## Step 1. Diagnose
Run `diagnose.py` on the baseline, then on every new version. Read the model's own reasoning on the wrong cases,
not only the counts: the cause is usually one repeated pattern.

- Baseline: the two failures that cost the most were **dropped conditions** (93% missed) and **certainty changes**
  ("usually" → "always", 50% missed). It also failed 14% of the good *original* replies, which counts as a wrong
  case even when the edited reply is failed correctly.
- Our first version over-corrected: it failed the edited reply 98% of the time, but also failed 26% of the good
  originals. Its reasoning showed one pattern: it demanded that policy caveats appear word for word ("subject to
  availability"), even when the reply already hedged ("we will try to reserve one").
- Lesson for any criterion: track **"original pass"** separately. A judge that is too strict looks like it misses
  harmful edits, because both sides of the pair fail.

## Step 2. Split: rules vs. LLM
Plain code extracts **facts**, never verdicts: every number in the reply that appears nowhere in the policy is listed
in the prompt as a note for the model to check.

- On dev this note fires on all 35 wrong-number edits and on no harmless edit.
- It is not an automatic fail on purpose: a number that differs from the policy can be harmless for another
  criterion, or less generous than the policy, which the Judge 1 criterion allows; and an unseen harmless edit
  such as "48 hours" → "2 days" introduces a new number. The LLM applies the criterion.
- **The rule checks itself on the dev examples** (version 5): in `prepare()`, it is trusted only if it fires on at
  least 3 failing dev replies and on no passing one. When trusted and it fires, one fail vote out of two is enough
  (otherwise both calls must say fail). For a criterion where numbers do not matter, it switches itself off.
- Number formats are normalised (10 = 10.00 = 10,00; clock times like 10:00 are skipped).
- Check: on dev the rule fires on all 35 wrong-number edits and on no good reply.

## Step 3. Improve the LLM part
One reasoning call per reply, structured as steps the model writes out, ending in `VERDICT: PASS|FAIL`:

1. **Policy:** quote the relevant rules word for word, including numbers, conditions and hedge words.
2. **Statements:** list each concrete statement in the reply; ignore greetings and pleasantries, language, tone and
   sentence order.
3. **Differences in meaning:** compare each statement with the policy. One distinction fixed the over-strictness:
   - *specific conditions* (only if / only while / unless / who / where) must still be stated;
   - *general caveats* (no guarantee, subject to availability, only some places) are conveyed by any hedge
     ("try", "often", "usually"). Only firm wording ("always", "will", "guaranteed") loses them.
4. **Criterion:** decide which differences break the criterion, applying its text literally, including what it says
   does not count, and reading the reply as the customer would.

**Examples are picked by code from the dev pairs:** one pair per edit type, the good reply next to its edited copy
with both labels and what changed. They come from different source replies where possible, preferring short,
English ones. The same code picks examples for the surprise criterion.

Settings are fixed in code (temperature 0, 1,500 output tokens) so a rerun behaves the same; unparsed answers are
counted and reported.

## Step 4. Verify
`cv_eval.py` splits dev by `source_id` into 3 folds: the examples shown to the model never come from the replies
being scored.

| | set | combined | catch | keep | originals passed |
|---|---|---|---|---|---|
| Baseline | full dev (226) | 0.697 | 0.592 | 0.847 | 86% |
| Version 2 (current) | full dev (226) | 0.692 | 0.632 | 0.766 | 78% |
| Baseline | fast (119) | 0.658 | 0.550 | 0.820 | — |
| Version 1 | fast (119) | 0.676 | 0.733 | 0.627 | 74% |
| Version 2 (current) | fast (119) | 0.728 | 0.717 | 0.740 | 80% |

| Version 3: benefit of the doubt | full dev (226) | 0.752 | 0.712 | 0.796 | 82% |
| Version 3 + fail only if 2 of 2 calls fail | full dev (226) | 0.779 | 0.709 | 0.864 | 87% |
| Version 4: + 3 extra good replies as examples | full dev (226) | 0.791 | 0.724 | 0.871 | 87% |
| Version 5: + self-validated number rule | full dev (226) | 0.803 | 0.746 | 0.871 | 87% |
| **Version 6: quantities never get the benefit of the doubt (current)** | full dev (226) | **0.871** | **0.840** | **0.904** | **94%** |

Version 2 tied the baseline: the remaining loss was failed *original* replies, concentrated in one source reply
(the late-return answer "if you call us, we can often extend", where the policy says only "some branches" offer
this by phone, failed 29 of 29 times). Two changes fixed most of it:
- **Benefit of the doubt (version 3):** count a difference only when it is clear-cut for a customer reading the
  whole reply; a hedged statement that can reasonably be read as consistent with the policy passes.
- **Two calls, fail only if both fail:** the second call shows the examples in a different order. A borderline
  reply that one call fails is often passed by the other; a clear violation is failed by both. Uses 2 of the 3
  allowed calls.
- **Extra good replies as examples (version 4):** besides the pairs, 3 single correct replies chosen by code
  (spread over source replies and languages) show the model what acceptable hedging looks like. Small gain
  (+0.012), largest in German.

Run time: about 8.5 minutes for 226 cases with 2 fresh calls per reply (5 parallel workers).

- Check: the gain holds on edit types you did not tune on. `loo_eval.py` judges each edit type with that type
  removed from the examples (and examples still from other source replies only), simulating unseen edit types:

| full dev (226) | combined | catch | keep |
|---|---|---|---|
| Baseline | 0.697 | 0.592 | 0.847 |
| Version 5, all edit types in examples | 0.803 | 0.746 | 0.871 |
| Version 5, **edit type never shown** | **0.809** | 0.745 | 0.884 |

  The score holds. One weak spot: an unseen kind of wrong number is caught 57% of the time (baseline 80%), because
  the number rule only trusts itself when the examples contain wrong numbers. Per language with unseen edit types:
  de 0.78, en 0.82, es 0.74, fr 0.78, it 0.81.

## Surprise criterion
*(To fill in after 14:30.)* Only `--criterion` and `--dev` change.

| | combined | catch | keep |
|---|---|---|---|
| Baseline | | | |
| Ours, recipe unchanged | | | |

## What did not work
- **"Write down every difference, however small"** (version 1): made the judge nitpick good replies for not
  repeating policy caveats verbatim. Asking for differences *in meaning*, with the conditions-vs-caveats
  distinction, fixed most of it.
- **Telling the model who benefits from a changed quantity** (version 7, reverted). With no wrong-number example,
  Haiku read a lower fee as "less generous" and passed it (unseen wrong numbers: 37% caught in version 6). A
  sentence on direction ("a lower fee benefits the payer") raised that to 69%, but the full dev score fell from
  0.871 to 0.838, so we kept version 6. Unseen kinds of number edits remain a known weak spot. Part of the
  difference between versions may be run-to-run noise (see consistency).
- **Tuning further on the remaining wrong originals:** the last ones (e.g. "we can often extend" vs. the policy's
  "some branches") are borderline even for a human reader. More prompt wording would only fit these few dev replies.
