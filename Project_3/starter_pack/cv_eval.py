"""Grouped cross-validation for a judge: examples never come from the source replies being scored.

    python3 cv_eval.py --judge final_judge.py --pairs dev_pairs.jsonl --criterion JUDGE1_CRITERION.md \\
        --policy policy.md --out cv_verdicts.csv [--folds 3] [--workers 5]

Splits the pairs into folds by source_id. For each fold, the judge's prepare() gets the pairs of the OTHER folds as
its labelled examples, and the fold is judged. The merged verdicts are written to --out and scored with score.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys

import run_judge


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True)
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--criterion", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dev", help="example pool (default: --pairs)")
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    pairs = run_judge._jsonl(a.pairs)
    pool = run_judge._jsonl(a.dev) if a.dev else pairs
    criterion = open(a.criterion, encoding="utf-8").read()
    policy = open(a.policy, encoding="utf-8").read()

    def fold(src: str) -> int:  # stable split by source reply
        return int(hashlib.md5(src.encode()).hexdigest(), 16) % a.folds

    res: dict = {}
    for k in range(a.folds):
        test = [p for p in pairs if fold(p["source_id"]) == k]
        train = [p for p in pool if fold(p["source_id"]) != k]
        if not test:
            continue
        print(f"fold {k}: judging {len(test)} cases with {len(train)} example candidates", file=sys.stderr)
        res.update(run_judge.run(a.judge, test, criterion, policy, train, a.seed, workers=a.workers, progress=True))

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "original", "edited"])
        for cid in sorted(res):
            w.writerow([cid, *res[cid]])
    print(f"wrote {len(res)} rows to {a.out}", file=sys.stderr)
    subprocess.run([sys.executable, "score.py", a.out, a.pairs, "--baseline", "baseline_dev_verdicts.csv"])


if __name__ == "__main__":
    main()
