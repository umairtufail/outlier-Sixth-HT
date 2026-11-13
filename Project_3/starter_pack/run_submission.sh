#!/usr/bin/env bash
# 16:00-16:45: run the frozen judge on both hidden test sets, twice each.
# Usage: bash run_submission.sh <criterion1_cases.jsonl> <criterion2_cases.jsonl> <CRITERION2.md> <criterion2_dev.jsonl>
# Do NOT set JUDGE_LLM_CACHE here: repeat runs must call the model again (consistency is scored).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
[ $# -eq 4 ] || { echo "usage: $0 c1_cases.jsonl c2_cases.jsonl CRITERION2.md c2_dev.jsonl"; exit 1; }
set -a; . ../.env; set +a
unset JUDGE_LLM_CACHE
export FINAL_JUDGE_NO_PROXY_CACHE=1  # the event proxy caches identical requests; run 2 must really call the model
export FINAL_JUDGE_MAX_RPM="${FINAL_JUDGE_MAX_RPM:-180}"  # stay under the proxy limit (200/min per key); use 90 if the team limit is 100
W="${WORKERS:-40}"  # enough parallel requests to reach the pace; the pacing in final_judge.py prevents 429 stalls
[ "${JUDGE_LLM_MODEL}" = "claude-haiku-4.5" ] || { echo "JUDGE_LLM_MODEL must be claude-haiku-4.5"; exit 1; }
PY=../.venv/bin/python
OUT="${OUTDIR:-../submission}"  # OUTDIR only for a dress rehearsal
mkdir -p "$OUT"
for run in 1 2; do
  $PY run_judge.py --workers "$W" --judge final_judge.py --pairs "$1" --criterion JUDGE1_CRITERION.md --policy policy.md \
      --dev dev_pairs.jsonl --seed $run --out "$OUT/criterion1_run$run.csv"
  $PY run_judge.py --workers "$W" --judge final_judge.py --pairs "$2" --criterion "$3" --policy policy.md \
      --dev "$4" --seed $run --out "$OUT/criterion2_run$run.csv"
done
ls -l "$OUT"/
