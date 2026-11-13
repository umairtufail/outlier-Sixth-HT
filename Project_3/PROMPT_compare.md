# Evaluate your judge version against our main version (self-contained)

You changed the LLM judge for SIXT Hackathon Project 3 ("Judge the Judge"). We want to decide fairly whether your
version or our main version (`Project_3/starter_pack/final_judge.py`, called **E5**) goes into the submission.
Everything you need is in the team repo: data, practice criteria, synthetic test sets and E5's reference results.
Run the commands below exactly, do not change data or scoring scripts, and send back the report in section 6.

## 1. Get the code and data (one time, ~3 min)
```bash
git clone -b project3-judge https://github.com/umairtufail/outlier-Sixth-HT.git outlier-judge
cd outlier-judge/Project_3
bash setup.sh                       # needs Python 3.11+; creates .venv and .env
```
Open `Project_3/.env` and set (ask the team for the key in private; never commit it or paste it in chat):
```
JUDGE_LLM_BASE_URL=https://llm.orange.sixt.com/v1
JUDGE_LLM_API_KEY=<team key>
JUDGE_LLM_MODEL=claude-haiku-4.5
```
Put your version next to the main one, e.g. `Project_3/starter_pack/final_judge_mine.py` (start from a copy of
`final_judge.py` if you like). Do not edit `final_judge.py`.

## 2. Fixed conditions (all runs)
- Model `claude-haiku-4.5` on the event endpoint. No caches (the event proxy caches identical requests, so set
  `FINAL_JUDGE_NO_PROXY_CACHE=1`; leave `JUDGE_LLM_CACHE` unset).
- Rules of the challenge: the judge sees one reply at a time, keeps no state between calls, makes at most 3 LLM
  calls per reply, and hard-codes nothing criterion-specific (everything comes from criterion text, policy, examples).
- The team shares one rate limit: only one person runs at a time. **Never between 14:15 and 16:45.**

```bash
cd Project_3/starter_pack
set -a; . ../.env; set +a
unset JUDGE_LLM_CACHE; export FINAL_JUDGE_NO_PROXY_CACHE=1 FINAL_JUDGE_MAX_RPM=300
J=final_judge_mine.py
R=reference_e5                      # E5's verdict files, for comparison
```
If your judge file does not contain the pacing code of `final_judge.py`, use `--workers 15` instead of 40 to avoid
"429 rate limit" stalls.

## 3. The four tests (~25 min in total, in this order)
**T1. Criterion 1, held out by source reply.** Use `cv_eval.py`, NOT `run_judge.py --dev dev_pairs.jsonl` (that
shows the judge examples from the same replies it is scored on and inflates the score).
```bash
../.venv/bin/python cv_eval.py --workers 40 --judge $J --pairs dev_pairs.jsonl \
  --criterion JUDGE1_CRITERION.md --policy policy.md --out mine_c1.csv
```
**T2. New criteria with few examples (rehearsal for the surprise criterion).**
```bash
../.venv/bin/python cv_eval.py --workers 40 --judge $J --pairs mock/B_pairs.jsonl --dev mock/B_dev_few.jsonl \
  --criterion mock/MOCK_B_CRITERION.md --policy policy.md --out mine_B.csv
../.venv/bin/python cv_eval.py --workers 40 --judge $J --pairs mock/C_pairs.jsonl --dev mock/C_dev_few.jsonl \
  --criterion mock/MOCK_C_CRITERION.md --policy policy.md --out mine_C.csv
```
**T3. Unseen topics and edit types (synthetic set 2, 100 cases).**
```bash
../.venv/bin/python run_judge.py --workers 40 --judge $J --pairs synth/synth2_pairs.jsonl \
  --criterion JUDGE1_CRITERION.md --policy policy.md --dev dev_pairs.jsonl --out mine_synth2.csv
../.venv/bin/python score.py mine_synth2.csv synth/synth2_pairs.jsonl
```
**T4. Consistency: T1 a second time, compared with the first.**
```bash
../.venv/bin/python cv_eval.py --workers 40 --judge $J --pairs dev_pairs.jsonl \
  --criterion JUDGE1_CRITERION.md --policy policy.md --out mine_c1_run2.csv
../.venv/bin/python score.py mine_c1.csv dev_pairs.jsonl --repeat mine_c1_run2.csv
```

## 4. Paired comparison with E5 (no LLM calls)
```bash
../.venv/bin/python stats.py dev_pairs.jsonl $R/e5_c1.csv mine_c1.csv
../.venv/bin/python stats.py dev_pairs.jsonl $R/e5_c1_control.csv mine_c1.csv
../.venv/bin/python stats.py mock/C_pairs.jsonl $R/e5_C.csv mine_C.csv
../.venv/bin/python stats.py synth/synth2_pairs.jsonl $R/e5_synth2.csv mine_synth2.csv
```
(`stats.py` resamples whole source replies and runs an exact McNemar test on the cases the two versions disagree on.)

## 5. How we decide (fixed in advance)
E5, measured under the same conditions (files in `reference_e5/`):

| Test | E5 | Starting judge |
|---|---|---|
| T1 criterion 1, combined | 0.915, 0.897, 0.910 (three runs, mean 0.907; noise ±0.01–0.02) | 0.697 |
| T2 practice B, combined | 0.806 | 0.556 |
| T2 practice C, combined | 0.720 | 0.424 |
| T3 synthetic set 2, combined | 0.908 | 0.781 |
| T4 consistency | 98.3% same verdict | – |

Your version wins only if **all** of these hold:
1. T1: both your runs are at least **0.89**, and the paired test is not clearly worse (no McNemar p < 0.05 in E5's
   favour);
2. at least one of T2 or T3 is **clearly better** than E5 (by more than 0.02), and none is clearly worse;
3. T4: consistency at least **95%**;
4. it follows the rules in section 2.
A difference of 0.01 is noise. A tie keeps E5 (already tested and pushed). Note: three changes that looked sensible
(explicit "who benefits" reasoning for numbers, tone-aware step 2, number rule as a note only) each lowered T1 by
0.05–0.13, so check T1 first: if run 1 is below 0.87, you can stop there.

## 6. What to send back (copy this template)
```
Version: <file name> — what I changed in one or two sentences: <...>
Calls per reply: <n>

T1 criterion 1 (cv_eval):   run 1 combined <x> (catch <x>, keep <x>)   run 2 combined <x>
T2 practice B: <x>          practice C: <x>
T3 synthetic set 2: <x>     (catch <x>, keep <x>)
T4 consistency: same verdict <x>%, kappa <x>
stats vs e5_c1:         B - A <x> [CI], per case <n> vs <n>, McNemar p <x>
stats vs e5_c1_control: B - A <x> [CI], per case <n> vs <n>, McNemar p <x>
stats practice C:       B - A <x>, McNemar p <x>
stats synthetic 2:      B - A <x>, McNemar p <x>
Run time of T1: <minutes>
Anything unusual (errors, "429" messages, unparsed answers): <...>
```
Also commit your judge file and the five `mine_*.csv` files to a new branch (e.g. `try-<name>`), or send them.
