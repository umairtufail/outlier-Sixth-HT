# Mock criterion A: does the reply state policy facts correctly?

Decide whether every **fact** the reply states matches the policy: numbers, amounts, fees, prices, deadlines,
durations, limits and named policy details (what is charged, at which rate, to which card, where something applies).

- `pass`: every fact the reply states matches the policy.
- `fail`: at least one stated fact differs from the policy, in either direction (higher or lower, broader or narrower).

How certain the reply sounds ("usually", "always", "we will try") does not matter for this criterion. Leaving a
policy condition or detail out is not a wrong fact: only what the reply actually states is checked. Tone, length,
politeness and language do not matter.
