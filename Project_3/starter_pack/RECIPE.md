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
Plain code extracts **facts** and never decides alone: every number in the reply that appears nowhere in the policy
is listed in the prompt as a note for the model to check. (Once the rule has proven itself on the examples, it does
lower the bar from two FAIL votes to one; see below.)

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

**Examples are picked by code from the dev pairs:** up to 8 pairs, one per edit type with label-changing types
first (then the others alphabetically; with criterion 1's 9 edit types, "translation" is not shown as a pair), the
good reply next to its edited copy with both labels and what changed, plus 3 single good replies. They come from different source replies where possible, preferring short,
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
| Version 6: quantities never get the benefit of the doubt | full dev (226) | 0.871 | 0.840 | 0.904 | 94% |
| **Version 8 (E5): only the criterion decides (current)** | full dev (226) | **0.915** | **0.886** | **0.947** | — |

**Version 8 (E5).** Step 3 only *lists* differences; step 4 lets only the criterion decide: for each difference
the model must quote the part of the criterion it breaks, otherwise it writes "not covered" and ignores it, and
the examples override any rule of thumb from step 3. Found with the practice criteria below; it also helped the
original criterion (+0.07 over version 6's three-run mean of 0.84; per case 22 vs 6, McNemar p = 0.004).

**Practice criteria (dress rehearsal for the surprise criterion).** We wrote two new criteria in the official style
and relabelled the dev cases for them (`mock/`), giving the judge only 15–17 examples, as in the surprise task:
A "states policy facts correctly" (certainty changes and dropped conditions now *pass*) and B "keeps the policy's
conditions" (wrong numbers and details now *pass*).

| | A: facts correct | B: conditions kept |
|---|---|---|
| Starting judge (baseline) | 0.932 | 0.556 |
| Version 6 | 0.873 | 0.698 |
| **Version 8 (E5)** | **0.931** | **0.806** |

Version 6 still applied criterion 1's rules of thumb to new criteria (it failed 73% of dropped conditions that
criterion A allows). Making the criterion the only judge fixed most of this.

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

**Noise and consistency (event endpoint, `claude-haiku-4.5`).** Version 6 run three times from scratch on all 226
cases, with the proxy's response cache bypassed so every call reaches the model:

| run | combined | catch | keep |
|---|---|---|---|
| 1 | 0.845 | 0.783 | 0.918 |
| 2 | 0.832 | 0.766 | 0.911 |
| 3 | 0.838 | 0.776 | 0.911 |

- Consistency (`score.py --repeat`, 235 replies): same verdict **96.6%** (run 1 vs 2) and **98.3%** (run 2 vs 3);
  kappa between runs 0.93 and 0.97.
- Run-to-run noise in the combined score is about ±0.01, so we only accept a change that beats that clearly.
- Our best single-run estimate is therefore **about 0.84**, not the 0.871 of one earlier run.
- Uncertainty: dev has only 9 source replies, so 95% intervals grouped by source reply are wide (`stats.py`);
  per-case paired tests (McNemar) still show version 6 beats the baseline (57 vs 21 cases, p < 0.001).

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
"Does the reply state the policy correctly?" (numbers, conditions, scope, details; errors in both directions).
**Nothing changed in the code:** only `--criterion surprise/CRITERION.md` and `--dev surprise/dev_pairs.jsonl`
(73 labelled pairs). Held out by source reply (`cv_eval.py`), so the judge never sees examples from the scored
replies.

| | combined | catch | keep |
|---|---|---|---|
| Baseline | 0.652 | 0.600 | 0.715 |
| **Ours, recipe unchanged** | **0.863** | **0.833** | **0.895** |

Per case 20 vs 5 (McNemar p = 0.004). Our practice criteria A ("facts correct") and B ("conditions kept") had
rehearsed almost exactly this criterion. Diagnosis of the 10 remaining errors: 3 come from one source reply
("we can often extend by phone" vs. the policy's "some branches"), 2 from our deliberate rule that a hedge
("often") already conveys a general caveat ("depending on availability"), 1 from the model inventing a condition.
We left the recipe unchanged: loosening the caveat rule would bring back false alarms on good replies.

## Where each part comes from (references)
Each part of the recipe follows an established idea; we adapted it to this task and measured it here.

| Part of the recipe | Idea it follows | Reference |
|---|---|---|
| Reason step by step before the verdict | chain-of-thought prompting | Wei et al., *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*, NeurIPS 2022 |
| Fixed evaluation steps, then a verdict | LLM evaluators with explicit evaluation steps | Liu et al., *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment*, EMNLP 2023 |
| Split the reply into single statements and check each against the source | atomic-fact decomposition | Min et al., *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*, EMNLP 2023 |
| LLM as a judge; known weaknesses (position, verbosity, leniency) | LLM-as-a-judge | Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, NeurIPS 2023 |
| Labelled examples in the prompt | in-context (few-shot) learning | Brown et al., *Language Models are Few-Shot Learners*, NeurIPS 2020 |
| Choosing examples by what they teach | example selection matters | Liu et al., *What Makes Good In-Context Examples for GPT-3?*, DeeLIO 2022 |
| Two calls with the examples in a different order | results depend on example order; aggregating over orders reduces this | Lu et al., *Fantastically Ordered Prompts and Where to Find Them*, ACL 2022; Zhao et al., *Calibrate Before Use*, ICML 2021 |
| Several reasoning paths, then aggregate | self-consistency | Wang et al., *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, ICLR 2023 |
| Examples as minimal pairs (good reply vs. one-change copy) | contrast sets, counterfactual data | Gardner et al., *Evaluating Models' Local Decision Boundaries via Contrast Sets*, Findings of EMNLP 2020; Kaushik et al., *Learning the Difference that Makes a Difference with Counterfactually-Augmented Data*, ICLR 2020 |
| Testing harmless vs. harmful edits, new edit types, synthetic stress set | behavioural testing (invariance and directional tests) | Ribeiro et al., *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*, ACL 2020 |
| Judges ignore harmless edits but miss meaning changes (the problem itself) | construct sensitivity of judges | *A Judge Should Know What Changed*, arXiv:2608.24419 (project background reading) |
| Agreement and consistency measured with kappa | chance-corrected agreement | Cohen, *A Coefficient of Agreement for Nominal Scales*, Educational and Psychological Measurement, 1960 |
| Paired comparison of two versions on the same cases | McNemar's test | McNemar, *Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages*, Psychometrika, 1947 |
| Confidence intervals resampling whole source replies | (cluster) bootstrap | Efron & Tibshirani, *An Introduction to the Bootstrap*, 1993 |

## What did not work
- **"Write down every difference, however small"** (version 1): made the judge nitpick good replies for not
  repeating policy caveats verbatim. Asking for differences *in meaning*, with the conditions-vs-caveats
  distinction, fixed most of it.
- **Telling the model who benefits from a changed quantity** (version 7, reverted). With no wrong-number example,
  Haiku read a lower fee as "less generous" and passed it (unseen wrong numbers: 37% caught in version 6). A
  sentence on direction ("a lower fee benefits the payer") raised that to 69%, but the full dev score fell from
  0.871 to 0.838, so we kept version 6. Unseen kinds of number edits remain a known weak spot. Part of the
  difference between versions may be run-to-run noise (see consistency).
- **E6, explicit quantity reasoning + number rule as a note only** (rejected). The synthetic set showed misses on
  number direction ("per rental" instead of "per day", "24 h before pick-up" instead of 48 h). E6 asked the model
  to write policy value, reply value, basis and who gains, and stopped the number rule from lowering the vote
  threshold. Criterion 1 fell from ~0.90 to 0.783 (wrong numbers caught 94% → 54%; per case 8 better vs 40 worse,
  McNemar p < 0.001), and the synthetic tuning half did not improve (0.933 vs 0.951). The self-validated number rule
  is doing real work; direction errors remain a known limit.
- **E7, only the "who gains" sentence for quantities** (rejected; same idea as version 7, now on top of E5 with the
  number rule unchanged). Synthetic tuning half unchanged (0.951 = 0.951; "per rental" edits 100% caught), but
  criterion 1 fell to 0.862 (wrong numbers 94% → 71%; per case 9 better vs 23 worse, p = 0.02). Third failed attempt
  at explicit direction reasoning (version 7, E6, E7): with Haiku it adds more wrong reasoning than it fixes.
- **E8/E9, tone and greetings only when the criterion is about them** (rejected). A third practice criterion C
  ("does the reply start with the answer?", openers fail) showed that our step 2 ("skip greetings … tone does not
  matter") blinds the judge for such criteria: E5 0.720 vs starting judge 0.424. E8 (that sentence made
  conditional) reached **0.958** on C but criterion 1 fell to 0.846; E9 (sentence kept plus an explicit exception)
  0.839 on C, criterion 1 0.821. A control run of unchanged E5 right afterwards gave **0.910** (98.3% same verdicts
  as its first run), so the endpoint was stable and both drops were real (E9 vs control: 7 better vs 29 worse,
  p < 0.001). Lesson: the E5 prompt is finely balanced; every extra instruction in steps 2–3 cost 0.05–0.09 on
  criterion 1. Known limit: criteria about tone or format (still well above the starting judge).

**Final version: E5.** Criterion 1, five independent runs of the same code: 0.915 / 0.897 / 0.910 / 0.878 / 0.854
(mean 0.891, about 0.9; run-to-run spread larger than the ±0.01 we first estimated, about ±0.03); consistency 98.3%.
Criterion 2, two runs: 0.863 / 0.851 (mean 0.857).
Synthetic set 1: 0.931 (starting judge 0.810); synthetic set 2 (100 further cases): 0.908 (starting judge 0.781).
Practice criteria A / B / C: 0.931 / 0.806 / 0.720 (starting judge 0.932 / 0.556 / 0.424).
- **Tuning further on the remaining wrong originals:** the last ones (e.g. "we can often extend" vs. the policy's
  "some branches") are borderline even for a human reader. More prompt wording would only fit these few dev replies.
