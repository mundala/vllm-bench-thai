# Run 2 objective checks (NOT a quality score)

These are surface statistics computed by `script/checks.py` on the saved run 2 answers. They measure length, script, cap hits, repetition and determinism. They say nothing about whether an answer is correct, helpful, fluent or natural Thai. Quality is not scored here.

Command: `python3 -I script/checks.py` (run from the repo root; output below is pasted verbatim).

## Data source

- Full answer text is stored per request, but only for the concurrency-1 level. `bench.py` writes `answers` only when `conc == 1`, so each `results/run2/<config>.json` holds 64 answers (one per request).
- `finish_reason` is **not** stored per request. The only cap signal is the aggregate count `hit_max_tokens` (`finish == "length"`) in the concurrency-1 level summary. Per-answer cap flags and per-answer token counts cannot be recovered.
- `answers_readable.md` is a human-readable view of the same answers (first answer per prompt). The script reads the JSON, not this file.
- The 1,024-token cap is not written into the JSON. It comes from `README.md` and `RESULTS.md` (the run 2 section) and the header of `answers_readable.md`.

## Output

```
Run dir: results/run2
NOT a quality score. Surface statistics only.

| config | answers | hit 1,024 cap | Thai-block share of chars | mean Thai chars/answer | any CJK | 20-char repeat 3+x | identical to prompt modal answer | prompts with >1 distinct answer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q3-bf16 | 64 | 5/64 (7.8%) | 79.7% | 634.7 | 0.0% | 21.9% | 96.9% | 2/23 |
| q3-fp8 | 64 | 7/64 (10.9%) | 79.1% | 620.2 | 0.0% | 15.6% | 100.0% | 0/23 |
| q3-awq | 64 | 8/64 (12.5%) | 79.9% | 647.5 | 0.0% | 29.7% | 100.0% | 0/23 |
| typhoon-bf16 | 64 | 0/64 (0.0%) | 88.2% | 307.8 | 0.0% | 7.8% | 84.4% | 10/23 |

Requests per prompt (count of prompts with that many requests): 
  q3-bf16: {2: 5, 3: 18}
  q3-fp8: {2: 5, 3: 18}
  q3-awq: {2: 5, 3: 18}
  typhoon-bf16: {2: 5, 3: 18}

| config | GPU $/hr | conc-1 wall s | total Thai chars | Thai chars/s (recalc) | Thai chars/s (stored) | $/1M Thai chars (recalc) | $/1M Thai chars (stored) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q3-bf16 | 0.89 | 489.3 | 40620 | 83.01 | 83.01 | 2.98 | 2.98 |
| q3-fp8 | 0.89 | 288.9 | 39696 | 137.40 | 137.40 | 1.80 | 1.80 |
| q3-awq | 0.89 | 195.3 | 41442 | 212.19 | 212.19 | 1.17 | 1.17 |
| typhoon-bf16 | 0.89 | 197.2 | 19702 | 99.91 | 99.91 | 2.47 | 2.47 |
```

## Column definitions

- **answers**: saved concurrency-1 answers for the config (64 requests).
- **hit 1,024 cap**: `hit_max_tokens` from the concurrency-1 summary, divided by requests. Aggregate count only.
- **Thai-block share of chars**: code points in U+0E00 to U+0E7F, summed over all 64 answers, divided by total code points in those answers. Spaces, digits, Latin text and Markdown are in the denominator.
- **mean Thai chars/answer**: Thai-block code points divided by 64.
- **any CJK**: share of answers containing at least one code point in U+4E00 to U+9FFF.
- **20-char repeat 3+x**: share of answers in which some 20-code-point window (overlapping windows, counted by start position) occurs 3 or more times in that answer.
- **identical to prompt modal answer**: for each prompt, count the answers equal to the most common answer for that prompt, then divide the total by 64. A value of 100% means every repeat of every prompt matched.
- **prompts with >1 distinct answer**: prompts whose repeat requests did not all return the same text.

## GPU cost per 1M Thai characters

Formula, using the rate recorded in the JSON and the concurrency-1 wall time:

```
Thai chars/s     = (total Thai-block chars in the 64 answers) / (conc-1 wall seconds)
$ per 1M Thai    = (GPU $/hr / 3600) / (Thai chars/s) * 1,000,000
```

Check, q3-awq: 0.89 / 3600 / (41442 / 195.3) * 1e6 = 1.17. This matches the stored value.

The script's recomputed values match the `$/1M Thai chars` values stored by `bench.py` at concurrency 1 (2.98, 1.80, 1.17, 2.47). The cost is a single-stream figure for one pod at a flat assumed rate of 0.89 $/hr. The rate comes from the JSON and is not verified per config. Costs at concurrency 8 and 32 are in each config's `results/run2/<config>.txt` table and are not repeated here.

## Limits

- **Cap count is aggregate only.** There is no per-answer `finish_reason` and no per-answer token count, so the cap share cannot be linked to specific answers.
- **Prompts repeat 2 or 3 times, not 64.** 64 requests cycle through 23 prompts: 18 prompts appear 3 times and 5 appear 2 times. The "identical across 64 requests per prompt" check is therefore computed per prompt over 2 or 3 answers.
- **Not fully deterministic at temperature 0.** Some repeats differ: 2 of 23 prompts for q3-bf16 and 10 of 23 for typhoon-bf16. The cause (serving nondeterminism or something else) was not investigated.
- **The 20-character repeat check is crude.** It flags legitimate repetition too. For example, q3-bf16 repeats "ต้องจ่ายดอกเบี้ย 5,000" three times in one worked example. It does not measure degenerate looping.
- **Thai-block share is a character-share, not a language-quality measure.** Typhoon's lower mean Thai chars per answer (307.8 versus about 620 to 650 for the Qwen3 configs) reflects shorter answers, not better or worse answers.
- **CJK check is a code-point range.** U+4E00 to U+9FFF also covers Japanese kanji. The check found none, so this does not affect the result.
- **Cap value is not stored in the JSON.** The 1,024 figure comes from the docs. Nothing in the saved data confirms that the run used that cap.
- **Configs are different models.** The "identical" numbers are within-config only. No cross-config comparison of answer content is made here.
