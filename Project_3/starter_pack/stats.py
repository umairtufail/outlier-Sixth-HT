"""Confidence intervals and paired comparison for judge verdicts (no LLM calls).

    python3 stats.py dev_pairs.jsonl A.csv [B.csv] [--n 2000]

- One file: combined score with a 95% cluster-bootstrap interval. Clusters are source replies (source_id): cases
  from one source reply are strongly correlated (DATACARD), so resampling single cases would overstate certainty.
- Two files (same judge inputs, two versions): the difference B - A with its 95% interval, the share of bootstrap
  samples where B beats A, and an exact McNemar test on per-case correctness (cases one version gets right and the
  other wrong).
Scoring is score.py's own `score()`, so the numbers match score.py exactly.
"""
from __future__ import annotations

import argparse
import math
import random
from collections import defaultdict

import score as S


def combined(cases: list[dict], v: dict) -> float:
    return S.score(cases, v)["combined"]


def correct(c: dict, v: dict) -> bool:
    o, e = v[c["case_id"]]
    return o == "pass" and e == ("fail" if c["edit_family"] == "harmful" else "pass")


def mcnemar_p(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value (binomial test on the discordant cases)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs")
    ap.add_argument("a")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    cases = S.read_pairs(args.pairs)
    va = S.read_verdicts(args.a)
    vb = S.read_verdicts(args.b) if args.b else None
    by_src: dict[str, list[dict]] = defaultdict(list)
    for c in cases:
        by_src[c["source_id"]].append(c)
    srcs = sorted(by_src)
    rng = random.Random(args.seed)

    sa, sd = [], []
    for _ in range(args.n):
        sample = [c for s in (rng.choice(srcs) for _ in srcs) for c in by_src[s]]
        try:
            a = combined(sample, va)
            if vb is not None:
                sd.append(combined(sample, vb) - a)
            sa.append(a)
        except (ValueError, ZeroDivisionError):
            continue
    sa = sorted(x for x in sa if not math.isnan(x))

    def ci(xs: list[float]) -> tuple[float, float]:
        xs = sorted(x for x in xs if not math.isnan(x))
        return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]

    lo, hi = ci(sa)
    print(f"A {args.a}: combined {combined(cases, va):.3f}   95% CI [{lo:.3f}, {hi:.3f}]   ({len(srcs)} source replies)")
    if vb is None:
        return
    lo_b, hi_b = ci([a + d for a, d in zip(sa, sd)])
    d0 = combined(cases, vb) - combined(cases, va)
    dlo, dhi = ci(sd)
    win = sum(d > 0 for d in sd) / len(sd)
    b_only = sum(correct(c, vb) and not correct(c, va) for c in cases)
    a_only = sum(correct(c, va) and not correct(c, vb) for c in cases)
    print(f"B {args.b}: combined {combined(cases, vb):.3f}")
    print(f"B - A: {d0:+.3f}   95% CI [{dlo:+.3f}, {dhi:+.3f}]   B better in {win:.0%} of bootstrap samples")
    print(f"per case: B right/A wrong {b_only}, A right/B wrong {a_only}, exact McNemar p = {mcnemar_p(b_only, a_only):.3f}")


if __name__ == "__main__":
    main()
