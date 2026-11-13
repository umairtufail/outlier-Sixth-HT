# Test cases (16:00)

The unseen test cases for both criteria, **without labels**. Your code is frozen: run your 16:00 commit of
`final_judge.py` unchanged, with `claude-haiku-4.5`.

| File | Cases | Run it with |
|---|---|---|
| `criterion1_cases.jsonl` | 291 | the original criterion (`JUDGE1_CRITERION.md`) |
| `criterion2_cases.jsonl` | 311 | the surprise criterion (`surprise/CRITERION.md`) |

Pull them into your fork:

```bash
git pull https://github.com/sixt-hackathon-2026/sixt-hackathon-2026.git main
```

Then from `Project_3/starter_pack/` run each criterion **twice**:

```bash
mkdir -p ../submission
python3 run_judge.py --judge final_judge.py --pairs hidden/criterion1_cases.jsonl --criterion JUDGE1_CRITERION.md \
    --policy policy.md --dev dev_pairs.jsonl --out ../submission/criterion1_run1.csv --seed 1
python3 run_judge.py --judge final_judge.py --pairs hidden/criterion1_cases.jsonl --criterion JUDGE1_CRITERION.md \
    --policy policy.md --dev dev_pairs.jsonl --out ../submission/criterion1_run2.csv --seed 2
python3 run_judge.py --judge final_judge.py --pairs hidden/criterion2_cases.jsonl --criterion surprise/CRITERION.md \
    --policy policy.md --dev surprise/dev_pairs.jsonl --out ../submission/criterion2_run1.csv --seed 1
python3 run_judge.py --judge final_judge.py --pairs hidden/criterion2_cases.jsonl --criterion surprise/CRITERION.md \
    --policy policy.md --dev surprise/dev_pairs.jsonl --out ../submission/criterion2_run2.csv --seed 2
```

Push the four files in `Project_3/submission/` by **16:45**.

You cannot score these yourself: there are no labels. We score your files and rerun a sample with your 16:00 code.
