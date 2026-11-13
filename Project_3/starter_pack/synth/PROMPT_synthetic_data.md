# Task: create a synthetic test set for an LLM judge (JSONL)

You are creating test data for an "LLM judge" that checks customer-service replies of a car-rental company before
they are sent. The judge reads ONE reply at a time and answers PASS or FAIL for the criterion below, using the
company policy below as the only source of truth.

Your test set will be used ONLY to test the judge (never to train it or as prompt examples), so **label accuracy is
everything**. If a case is even slightly ambiguous, leave it out.

---

## 1. The criterion the labels follow

> **Does the reply over-promise?**
> Decide whether the reply **over-promises**: commits the company to more than the policy guarantees.
> That includes a more generous number than the policy, leaving out a condition the policy attaches, a wider scope
> than the policy allows, more certainty than the policy gives ("always", "will", "guaranteed" where the policy says
> "usually", "may", "subject to availability"), or a policy detail that favours the customer more than the policy does.
>
> - `pass`: the reply does not over-promise.
> - `fail`: the reply over-promises at least once.
>
> Tone, length, politeness, register (formal or informal) and language do not matter. A reply that is less generous
> than the policy is not an over-promise for this criterion. General reassurance without a specific commitment
> ("we are here to help") is not an over-promise.

## 2. The company policy (fictional, the only source of truth)

### Car rental

| key | Rule |
|---|---|
| free_cancellation | Bookings with the **Pay later** rate can be cancelled free of charge up to **48 hours before pick-up**. A later cancellation, or any cancellation of a **prepaid** booking, costs **one day's rental price**. Instead of cancelling, the pick-up date can usually be changed (subject to availability). |
| late_return | Grace period of **29 minutes** after the agreed return time, **only while the branch is open**. After that an additional rental day **may** be charged. A rental can often be extended before the return time if the car is not reserved for another customer; **some** branches also offer this by phone. |
| extension | Extensions (app or phone) are usually possible **if the car is not reserved for another customer**, charged at the **current daily rate**. |
| deposit | Mid-size car: **500 EUR**, blocked on a **credit card in the main driver's name** (no debit cards, one card). Released once the car has been checked and **returned undamaged**. Depending on the bank it can take up to **10 days** until the amount is available again. |
| documents | Driving licence plus ID card or passport. **Some** branches accept digital driving licences. |
| young_driver | Minimum age **21**, licence held for at least one year. Drivers under twenty-five pay **15 EUR per day** and can book many, **not all**, car categories (up to mid-size). |
| additional_driver | **12 EUR per day**. The additional driver must be **present at pick-up with a valid licence**. Can usually be added to an existing booking at the counter. |
| child_seat | **10 EUR per day**, on request, **subject to availability** at the pick-up branch (no guarantee). **Most** (not all) branches also have booster seats. |
| one_way | Only **between airport branches in the same country**. One-way fee **90 EUR**, added to the rental price. The return branch can usually be changed later in the account. |
| upgrade | No free upgrade on request. If the booked category is unavailable, a higher category at no extra cost. Paid upgrades are often possible at the counter, depending on availability. |
| key_drop | Out-of-hours return only at branches with a key box (**some** branches, not all). The customer remains responsible for the car **until the branch opens and checks it**. |
| cross_border | Only to **neighbouring EU countries**, and only if **declared at booking**. Cross-border fee **25 EUR** per rental. The protection package normally stays valid there. |
| fuel | Full-to-full. Missing fuel is charged at the **branch price** plus a service fee of **20 EUR**. **Some** branches offer a prepaid fuel option. |
| excess | Basic protection: excess **950 EUR** per damage. Premium protection reduces it to zero, **except for tyre and glass damage**. |

### Online shop orders

| key | Rule |
|---|---|
| free_cancellation (shop) | Orders can be cancelled free of charge up to **48 hours after booking**, **if not yet shipped**. |
| refund_days | Refunds are paid to the **original payment method** within **14 days**, **once the returned item has been checked**. A confirmation e-mail is sent as soon as the refund has been issued. |

---

## 3. What to create

### 3a. Source replies (the "originals"): 10 of them, on these topics ONLY
Use these policy topics (they are deliberately NOT the ones the judge was developed on):
`young_driver`, `one_way`, `cross_border`, `key_drop`, `excess`, `free_cancellation` (car), `documents`,
`deposit` (focus: which card is accepted), `free_cancellation (shop)`, `fuel` (focus: prepaid option only).

For each topic write ONE customer question and ONE good reply in **English**, 2–3 sentences, natural
customer-service style. A good reply MUST:
- state every number exactly as the policy does;
- keep every condition the policy attaches to each rule it mentions (only if, as long as, unless, while, who, where);
- keep the policy's level of certainty ("usually", "some", "may", "subject to availability") or be less certain;
- never be borderline. Do NOT replace "some branches" by "often", do NOT drop "subject to availability" even if
  you hedge. When in doubt, copy the policy's wording more closely.
It may leave out policy details it does not talk about.

Then translate each original into **two** of German, French, Spanish, Italian (rotate so each language is used
5 times). Each translation is its own original with the same `source_id`. Total: 10 × 3 = **30 originals**.

### 3b. Edited copies: about 3 per original, about 90 cases in total
Each case = one original + one edited copy with **exactly one change**. Mix the edit types below so that roughly
half the cases are harmful and half harmless, every edit type appears at least 4 times, and all languages appear.

**Harmless edits (edited label = pass):**
| edit_type | what to do |
|---|---|
| `polite_opener` | add a polite first sentence ("Thanks for reaching out.") |
| `filler_padding` | insert a neutral sentence ("We hope this helps.") without any commitment |
| `sentence_reorder` | swap two sentences, meaning unchanged |
| `translation` | the edited copy is a translation of an English original into another language (set `orig_lang` = "en", `lang` = the new language) |
| `number_format` *(new)* | the same number written differently: "€90", "90 euros", "ninety euros", "two days" for "48 hours" |
| `register_change` *(new)* | formal ↔ informal ("Sie" → "du", "you may" → "you can"), same meaning |
| `list_format` *(new)* | turn the reply into a short bullet list, same content |
| `less_generous` *(new)* | a detail stricter or more expensive than the policy (e.g. "95 EUR" instead of "90 EUR", "48 hours" → "72 hours" before pick-up). NOT an over-promise under the criterion, so `pass` |

**Harmful edits (edited label = fail):**
| edit_type | what to do |
|---|---|
| `hedge_removal` | "usually"/"some"/"may" → "always"/"all"/"will" |
| `condition_removal` | delete one condition the policy attaches |
| `wrong_number` | a number more generous to the customer (lower fee, longer window, younger age) |
| `wrong_policy_detail` | a detail that favours the customer more (debit cards accepted, any country, any branch) |
| `quantifier_widening` *(new)* | "some branches" → "our branches" / "every branch" |
| `negation_flip` *(new)* | a restriction turned around ("is not covered" → "is covered") |
| `added_promise` *(new)* | add one sentence with a commitment the policy does not give ("We will refund it immediately.") |
| `unit_change` *(new)* | "per rental" ↔ "per day" or similar, in the direction that favours the customer |

Rules for every edit:
- Change exactly ONE place. Everything else stays word for word identical.
- The original must stay a clean `pass`.
- Only keep a case if a careful human reader would agree with the label without discussion.

---

## 4. Output format (exactly this)

Write **one JSON object per line** (JSONL), UTF-8, no comments, no surrounding text, no markdown fences.
Save it as `synth_pairs.jsonl` (if you cannot save files, print only the JSONL lines).

Fields of every line:
| field | value |
|---|---|
| `case_id` | `SYN-0001`, `SYN-0002`, … |
| `source_id` | one id per topic, the same for its translations: `SYN-S01` … `SYN-S10` |
| `source_kind` | `"synthetic"` |
| `intent` | the topic key, e.g. `"cross_border"` |
| `lang` | language of the edited reply: `en`, `de`, `fr`, `es`, `it` |
| `orig_lang` | language of the original (differs from `lang` only for `translation`) |
| `question_original` | the customer question, in `orig_lang` |
| `question` | the customer question, in `lang` |
| `original` | the good reply |
| `edited` | the edited copy |
| `edit_type` | one of the edit types above |
| `edit_family` | `"harmless"` or `"harmful"` |
| `expected_verdict_change` | `true` for harmful, `false` for harmless |
| `original_label` | always `"pass"` |
| `edited_label` | `"pass"` (harmless) or `"fail"` (harmful) |
| `edit_note` | what changed, short, e.g. `"'some branches' -> 'every branch'"` |
| `edited_unpadded` | same as `edited` |
| `length_padding` | `null` |
| `label_reason` | one sentence: why the label is right, quoting the policy |

Example line (format only; topic not from your list):
{"case_id": "SYN-0001", "source_id": "SYN-S00", "source_kind": "synthetic", "intent": "additional_driver", "lang": "en", "orig_lang": "en", "question_original": "Can my partner drive the car too?", "question": "Can my partner drive the car too?", "original": "Yes, you can add your partner as an additional driver for 12 EUR per day. Your partner needs to be present at pick-up with a valid driving licence.", "edited": "Yes, you can add your partner as an additional driver for 12 EUR per day. Your partner can be added later by phone.", "edit_type": "condition_removal", "edit_family": "harmful", "expected_verdict_change": true, "original_label": "pass", "edited_label": "fail", "edit_note": "removed: 'needs to be present at pick-up with a valid driving licence'", "edited_unpadded": "Yes, you can add your partner as an additional driver for 12 EUR per day. Your partner can be added later by phone.", "length_padding": null, "label_reason": "Policy: the additional driver must be present at pick-up with a valid licence; the edit drops this condition."}

## 5. Final self-check before you answer
- About 90 lines, every line valid JSON with all fields.
- Every `original` is a clean pass; every edit changes one place only.
- Every edit type appears at least 4 times; harmful and harmless roughly balanced; all 5 languages present.
- No case where you hesitated about the label.
