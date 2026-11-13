"""Final judge: a criterion-agnostic recipe for LLM judges.

Recipe (same code for every criterion; only the criterion text, policy and dev examples change):
  1. Diagnose  - done offline with diagnose.py; drove the design below.
  2. Split     - plain code extracts *facts* (numbers in the reply that the policy never mentions). They are handed
                 to the LLM as evidence, never as an automatic verdict. The rule first tests itself on the labelled
                 examples; only when trusted and it fires does it lower the bar from two FAIL votes to one.
  3. Improve   - one reasoning call per vote: the model quotes the relevant policy rules, lists every concrete
                 statement in the reply, writes down each difference from the policy (numbers, conditions, certainty,
                 scope, details), and only then applies the criterion to those differences.
                 Contrastive few-shot examples are picked automatically from the labelled dev pairs: up to 8 pairs,
                 one per edit type with label-changing types first (the good reply and its edited copy side by
                 side, with the label and what changed), plus 3 single good replies.
  4. Verify    - cv_eval.py: grouped cross-validation by source_id, so examples never come from the scored replies.

Rules of the game respected: one reply at a time, no state between calls (EXAMPLES is filled once in prepare() and
only read afterwards), nothing criterion-specific hard-coded, at most 3 LLM calls per reply (VOTES <= 3).

Run:
    python3 run_judge.py --judge final_judge.py --pairs dev_pairs_fast.jsonl --criterion JUDGE1_CRITERION.md \\
        --policy policy.md --dev dev_pairs.jsonl --out final_fast.csv
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baseline_judge as bj  # noqa: E402  (HTTP client, retries, cache file location)

# ---------------------------------------------------------------- settings that shape verdicts: fixed in code, not read
# from the environment, so a rerun by the organisers behaves exactly like ours. (Only request pacing,
# FINAL_JUDGE_MAX_RPM, and the proxy cache bypass, FINAL_JUDGE_NO_PROXY_CACHE, come from the environment; neither
# changes what is sent to the model.)
VOTES = 2  # prompt variants (example order rotated). A reply fails only if MORE than half the votes fail, so with
# 2 votes both calls must say fail (measured: +0.03 combined). Budget: at most 3 LLM calls per reply.
MAX_TOKENS = 1500
TEMPERATURE = 0
MAX_EXAMPLE_PAIRS = 8  # contrastive pairs shown to the model (one per edit type; label-changing types first)
MAX_EXTRA_REPLIES = 3  # extra single labelled replies

EXAMPLES: list[dict] = []  # filled by prepare(); read-only afterwards
EXTRA: list[dict] = []  # filled by prepare(); read-only afterwards
unparsed = 0  # answers without a final verdict; reported by run_judge.py
_lock = threading.Lock()


# ---------------------------------------------------------------- Step 3a: example selection (data-driven)
def prepare(criterion: str, policy: str, dev_pairs: list[dict]) -> None:
    """Pick a small, diverse set of contrastive examples from the labelled dev pairs.

    Generic rules, no criterion knowledge:
      - one pair per edit type (the dev set's own taxonomy), label-changing types first, then the others in
        alphabetical order, at most MAX_EXAMPLE_PAIRS: every label-changing kind of edit is shown once next to its
        unchanged original; with more than 8 edit types the last harmless ones are not shown as pairs (for the
        criterion-1 dev set that is "translation");
      - prefer English and short replies (cheaper, easier to read), but never two pairs from the same source reply
        when another source is available, so the examples cover several topics;
      - deterministic: same dev file -> same examples -> same prompts.
    """
    global NUMBER_RULE_TRUSTED
    EXAMPLES.clear()
    NUMBER_RULE_TRUSTED = _validate_number_rule(policy, dev_pairs) if dev_pairs else False
    if not dev_pairs:
        return
    by_type: dict[str, list[dict]] = {}
    for p in dev_pairs:
        by_type.setdefault(p.get("edit_type", "?"), []).append(p)

    def changes_label(p: dict) -> bool:
        return str(p.get("edited_label", "")).lower() != str(p.get("original_label", "pass")).lower()

    types = sorted(by_type, key=lambda t: (not any(changes_label(p) for p in by_type[t]), t))
    used_sources: set[str] = set()
    for t in types:
        cands = sorted(
            by_type[t],
            key=lambda p: (p.get("source_id") in used_sources, p.get("lang") != "en",
                           len(p.get("original", "")) + len(p.get("edited", "")), p.get("case_id", "")),
        )
        p = cands[0]
        used_sources.add(p.get("source_id"))
        EXAMPLES.append(p)
        if len(EXAMPLES) >= MAX_EXAMPLE_PAIRS:
            break

    # Extra single replies with their own label (calibration against over-strictness): original replies not shown
    # yet, spread over source replies and languages. Greedy: each pick prefers the source and language shown least.
    EXTRA.clear()
    shown = {(p.get("orig_lang"), p.get("original")) for p in EXAMPLES}
    src_count: dict[str, int] = {}
    for p in EXAMPLES:
        src_count[p.get("source_id")] = src_count.get(p.get("source_id"), 0) + 1
    langs: set[str] = set()
    cands = {}
    for p in dev_pairs:
        key = (p.get("orig_lang"), p.get("original"))
        if key not in shown and key not in cands:
            cands[key] = p
    for _ in range(MAX_EXTRA_REPLIES):
        if not cands:
            break
        key, p = min(cands.items(), key=lambda kv: (src_count.get(kv[1].get("source_id"), 0),
                                                    kv[0][0] in langs, len(kv[0][1]), kv[1].get("case_id", "")))
        EXTRA.append(p)
        langs.add(key[0])
        src_count[p.get("source_id")] = src_count.get(p.get("source_id"), 0) + 1
        del cands[key]


def _describe_change(p: dict) -> str:
    note = (p.get("edit_note") or "").strip()
    kind = (p.get("edit_type") or "edit").replace("_", " ")
    return f"{kind}" + (f" ({note})" if note else "")


def _examples_block(order: int) -> str:
    if not EXAMPLES:
        return ""
    exs = EXAMPLES[order % len(EXAMPLES):] + EXAMPLES[: order % len(EXAMPLES)]  # vary order between votes
    parts = []
    for i, p in enumerate(exs, 1):
        o_lab = str(p.get("original_label", "pass")).upper()
        e_lab = str(p.get("edited_label", "pass")).upper()
        parts.append(
            f"Example {i}\n"
            f"Question: {p.get('question_original', '')}\n"
            f"Reply A: {p.get('original', '')}\n"
            f"Verdict A: {o_lab}\n"
            f"Reply B (a copy of A with one change: {_describe_change(p)}): {p.get('edited', '')}\n"
            f"Verdict B: {e_lab}"
        )
    for j, p in enumerate(EXTRA, len(parts) + 1):
        parts.append(
            f"Example {j}\n"
            f"Question: {p.get('question_original', '')}\n"
            f"Reply: {p.get('original', '')}\n"
            f"Verdict: {str(p.get('original_label', 'pass')).upper()}"
        )
    return (
        "Labelled examples. Most show a correct verdict for a reply and for a slightly changed copy of it; the last "
        "ones are single replies with their verdict. Study what kind of change flips the verdict and what kind does "
        "not. They are illustrations only: the reply you judge may have other topics, languages and kinds of "
        "changes.\n\n" + "\n\n".join(parts) + "\n\n"
    )


# ---------------------------------------------------------------- Step 2: plain-code facts
_NUM = re.compile(r"(?<![\w.,:])\d+(?:[.,]\d+)?(?![\w:])")  # skips clock times like 10:00


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUM.findall(text)}


def _value(s: str) -> float:
    """'10', '10.00', '10,00' -> 10.0; '1.000' (thousands separator) -> 1000.0."""
    if re.fullmatch(r"\d{1,3}\.\d{3}", s):
        return float(s.replace(".", ""))
    return float(s)


def _unknown_numbers(reply: str, policy: str) -> list[str]:
    known = {_value(n) for n in _numbers(policy)}
    return sorted((n for n in _numbers(reply) if _value(n) not in known), key=_value)


# Set by prepare() after testing the rule on the labelled dev replies; read-only afterwards.
NUMBER_RULE_TRUSTED = False
NUMBER_RULE_MIN_HITS = 3


def _validate_number_rule(policy: str, dev_pairs: list[dict]) -> bool:
    """Trust the rule only if, on the labelled dev replies, it fires on at least NUMBER_RULE_MIN_HITS failing replies
    and on no passing reply. For a criterion where numbers do not matter, this switches it off by itself."""
    hits_fail = hits_pass = 0
    seen = set()
    for p in dev_pairs:
        for text, label in ((p.get("original", ""), p.get("original_label", "pass")),
                            (p.get("edited", ""), p.get("edited_label", "pass"))):
            if text in seen:
                continue
            seen.add(text)
            if _unknown_numbers(text, policy):
                if str(label).lower() == "fail":
                    hits_fail += 1
                else:
                    hits_pass += 1
    return hits_pass == 0 and hits_fail >= NUMBER_RULE_MIN_HITS


def rules(question: str, reply: str, lang: str, policy: str) -> list[str]:
    """Facts plain code can establish. Returned as notes for the LLM; never a verdict on their own (the trusted
    number rule only lowers the vote threshold in judge(), the model still has to vote FAIL)."""
    notes = []
    unknown = _unknown_numbers(reply, policy)
    if unknown:
        notes.append(
            "The reply contains these numbers that appear nowhere in the policy: " + ", ".join(unknown)
            + ". Find the policy value they stand for and compare them."
        )
    return notes


# ---------------------------------------------------------------- Step 3b: the prompt
PROMPT = """You are a careful reviewer who checks a customer-service reply before it is sent.

## Criterion
{criterion}

## Company policy (the only source of truth)
{policy}

{examples}## Reply to judge
Customer question ({lang}): {question}
Reply ({lang}): {reply}
{notes}
## How to decide
Work through these steps in English, briefly:
1. POLICY: quote the policy rule(s) that the question and reply are about, word for word, including every number,
   condition, restriction, exception and hedge word ("usually", "some", "may", "subject to", "only", ...).
2. STATEMENTS: list each concrete statement the reply makes (skip greetings, thanks and general pleasantries).
   The language of the reply, its tone, length and sentence order do not matter; judge the meaning.
3. DIFFERENCES IN MEANING: for each statement, compare what it tells the customer with the quoted policy: a
   different number; a specific condition the policy attaches that the statement drops; firmer or weaker
   certainty; a wider or narrower scope; a different detail. Read the whole reply: a condition stated in another
   sentence still counts. Write "none" if the meaning matches.
   A reply is a short answer, not a copy of the policy. Two kinds of policy wording are different:
   - Specific conditions (only if / only while / unless / who / where / when a rule applies, e.g. "if X is not
     reserved", "only during opening hours") must still be in the reply when it states that rule. Dropping one is
     a difference, even if the sentence also says "usually" or "often".
   - General caveats (no guarantee, subject to availability, not all / only some places, may) only say the outcome
     is uncertain. Any hedge in the reply ("we will try", "often", "usually", "most", "may", "can") already
     conveys this, so a hedged statement is NOT missing such a caveat. Only a firm wording ("always", "will",
     "guaranteed", "all", no hedge at all on an uncertain outcome) loses it.
   Leaving out policy details the reply does not talk about is not a difference.
   This step only LISTS differences. A difference is not yet a problem: step 4 decides.
4. CRITERION: only the criterion decides the verdict. Re-read the criterion, then for each difference from step 3:
   - quote, word for word, the part of the criterion that this kind of difference breaks;
   - if no part of the criterion covers it, or the criterion says it does not matter, write "not covered" and
     ignore that difference completely, however important it would be under another rule.
   The examples above show how this criterion is applied: follow them over any rule of thumb in step 3.
   Read the reply as the customer would: what would they reasonably understand from the WHOLE reply?
   Count a covered difference only when it is clear-cut: a typical customer would plainly come away with something
   the criterion rules out. If a statement is hedged and can reasonably be read as consistent with
   the policy, give the reply the benefit of the doubt. Most replies you see were written carefully; do not hunt
   for technicalities. The benefit of the doubt never covers a quantity: a number, amount, price, fee, deadline,
   duration or limit that differs from the policy value is a clear-cut difference; use the criterion to decide
   whether it breaks it. (The same quantity written another way, e.g. "48 hours" for "2 days", is not a
   difference.)
5. Last line, exactly: VERDICT: PASS or VERDICT: FAIL
"""


def build_prompt(question: str, reply: str, lang: str, criterion: str, policy: str, order: int = 0) -> str:
    notes = rules(question, reply, lang, policy)
    notes_txt = ("\nChecked by code:\n" + "\n".join(f"- {n}" for n in notes) + "\n") if notes else ""
    return PROMPT.format(criterion=criterion.strip(), policy=policy.strip(), examples=_examples_block(order),
                         lang=lang, question=question, reply=reply, notes=notes_txt)


# ---------------------------------------------------------------- LLM call (own settings, baseline transport)
# Request pacing: the event proxy allows a fixed number of requests per minute and answers "429, retry after 60 s"
# when it is exceeded, which stalls a whole run. Spacing request starts evenly stays just under the limit.
# This only changes WHEN calls are sent, never what is sent or how a verdict is formed.
MAX_RPM = float(os.environ.get("FINAL_JUDGE_MAX_RPM", "180"))
_pace_lock = threading.Lock()
_next_slot = 0.0


def _pace() -> None:
    global _next_slot
    if MAX_RPM <= 0:
        return
    with _pace_lock:
        now = time.monotonic()
        wait = max(0.0, _next_slot - now)
        _next_slot = max(now, _next_slot) + 60.0 / MAX_RPM
    if wait:
        time.sleep(wait)


def _call(prompt: str) -> str:
    base, key, model, timeout, _ = bj._config()
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS}
    if os.environ.get("FINAL_JUDGE_NO_PROXY_CACHE") == "1":
        # The event's LiteLLM proxy caches identical requests; for repeat/consistency runs every call must reach
        # the model (same reason the README says not to set JUDGE_LLM_CACHE for --repeat).
        payload["cache"] = {"no-cache": True}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for attempt in range(bj.MAX_RETRIES + 1):
        _pace()
        try:
            body = bj._post(f"{base}/chat/completions", payload, headers, timeout)
            return body["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise bj.LLMError(f"LLM endpoint refused the key (HTTP {e.code})")
            if e.code not in bj._RETRY_STATUS or attempt == bj.MAX_RETRIES:
                raise bj.LLMError(f"LLM request failed with HTTP {e.code}") from e
            time.sleep(bj._wait(attempt, e.headers.get("Retry-After") if e.headers else None))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == bj.MAX_RETRIES:
                raise bj.LLMError(f"LLM request failed: {e}") from e
            time.sleep(bj._wait(attempt, None))
    raise bj.LLMError("unreachable")


_cache: dict[str, str] | None = None


def complete(prompt: str) -> str:
    """Like baseline complete(), but the cache key includes our generation settings."""
    global _cache
    path = os.environ.get("JUDGE_LLM_CACHE")
    if not path:
        return _call(prompt)
    k = hashlib.sha256(f"{os.environ.get('JUDGE_LLM_MODEL', '')}|{MAX_TOKENS}|{TEMPERATURE}\n{prompt}".encode()).hexdigest()
    with _lock:
        if _cache is None:
            _cache = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        if k in _cache:
            return _cache[k]
    ans = _call(prompt)
    with _lock:
        _cache[k] = ans
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_cache, f)
    return ans


_VERDICT = re.compile(r"VERDICT\s*[:\-]?\s*\**\s*(PASS|FAIL)", re.IGNORECASE)


def parse(answer: str) -> str | None:
    """The last 'VERDICT: PASS|FAIL' in the answer, or None."""
    m = _VERDICT.findall(answer or "")
    return m[-1].lower() if m else None


def judge(question: str, reply: str, lang: str, criterion: str, policy: str) -> str:
    global unparsed
    votes: list[str] = []
    for v in range(VOTES):
        verdict = parse(complete(build_prompt(question, reply, lang, criterion, policy, order=v)))
        if verdict is None:
            with _lock:
                unparsed += 1
            continue
        votes.append(verdict)
    if not votes:
        return "fail"  # conservative, same as the baseline
    # Default: fail only if MORE than half the votes fail (2 votes: both). When the number rule fires and the dev
    # data showed it is trustworthy, one fail vote is enough: code and model together outweigh benefit of the doubt.
    if NUMBER_RULE_TRUSTED and _unknown_numbers(reply, policy):
        return "fail" if "fail" in votes else "pass"
    return "fail" if votes.count("fail") * 2 > len(votes) else "pass"
