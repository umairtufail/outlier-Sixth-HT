"""Leave-one-edit-type-out evaluation: how does the judge do on a kind of edit it has never seen an example of?

    python3 loo_eval.py --judge final_judge.py --pairs dev_pairs.jsonl --criterion JUDGE1_CRITERION.md \\
        --policy policy.md --out loo_verdicts.csv

For each edit type T and each source fold k, the cases of type T in fold k are judged with examples drawn only from
OTHER folds and OTHER edit types. This simulates the hidden test set (new source replies and new edit types).
Compare its score with cv_eval.py (same folds, all edit types allowed as examples).
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
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--types", help="comma-separated edit types to evaluate (default: all)")
    a = ap.parse_args()

    pairs = run_judge._jsonl(a.pairs)
    criterion = open(a.criterion, encoding="utf-8").read()
    policy = open(a.policy, encoding="utf-8").read()

    def fold(src: str) -> int:  # same split as cv_eval.py
        return int(hashlib.md5(src.encode()).hexdigest(), 16) % a.folds

    res: dict = {}
    types = sorted({p["edit_type"] for p in pairs})
    scored_path = a.pairs
    if a.types:
        types = [t for t in types if t in a.types.split(",")]
        scored_path = a.out + ".pairs.jsonl"
        with open(scored_path, "w", encoding="utf-8") as f:
            for p in pairs:
                if p["edit_type"] in types:
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
    for t in types:
        for k in range(a.folds):
            test = [p for p in pairs if p["edit_type"] == t and fold(p["source_id"]) == k]
            train = [p for p in pairs if p["edit_type"] != t and fold(p["source_id"]) != k]
            if not test:
                continue
            print(f"{t} fold {k}: {len(test)} cases, {len(train)} example candidates (no {t})", file=sys.stderr)
            res.update(run_judge.run(a.judge, test, criterion, policy, train, workers=a.workers))

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "original", "edited"])
        for cid in sorted(res):
            w.writerow([cid, *res[cid]])
    print(f"wrote {len(res)} rows to {a.out}", file=sys.stderr)
    subprocess.run([sys.executable, "score.py", a.out, scored_path, "--baseline", "baseline_dev_verdicts.csv"])


if __name__ == "__main__":
    main()
