# vllm-bench-thai

A small, honest benchmark of open-weight models serving Thai on vLLM: speed, memory and cost on one
rented RTX 4090, comparing full precision (BF16) with quantised versions (FP8, AWQ).

**Status:** speed, memory and cost are measured (run 2). **Thai answer quality has a blind Codex draft pass in `scoring/scores.csv` (92 rows, `scoring/key.json` unopened); human native-Thai review and unblinding are still pending.**

## Headline result

On an RTX 4090 at $0.89/hr, with 32 concurrent requests, Qwen3-8B AWQ served about 2,470 output
tokens/s at roughly $0.10 per million output tokens. The BF16 version served about 1,040 tokens/s at
roughly $0.24. Whether AWQ or FP8 hurt Thai output is **not answered yet**: the answers are saved and a
blind scoring pack is ready in `scoring/` (see [How Thai quality gets scored](#how-thai-quality-gets-scored)).
Until those scores exist, treat the speed gain as unproven for Thai quality.

Full tables, memory, kernels and caveats are in [RESULTS.md](RESULTS.md).

## What I measured

- Time to first token (TTFT), p50 and p95, at concurrency 1, 8 and 32.
- Output tokens per second, and Thai characters per second.
- Cost per million output tokens and per million Thai characters, from the hourly GPU price.
- Weights memory and KV cache capacity, read from the vLLM server logs.

Configs: Qwen3-8B in BF16, FP8 and AWQ, plus one Thai-tuned model, Typhoon2-Qwen2.5-7B in BF16.
Locked for every config: `--max-model-len 4096 --gpu-memory-utilization 0.90`. 23 Thai prompts,
64 requests per level, temperature 0. vLLM 0.34.0.

## How to run it

On the GPU pod, so internet latency stays out of TTFT (local loopback time is still included):

```bash
MAXTOK=1024 ./run_all.sh q3-awq 0.89     # configs: q3-bf16 | q3-fp8 | q3-awq | typhoon-bf16
```

`run_all.sh` starts vLLM with the locked flags, waits for it, runs `script/bench.py`, saves the
server log and results under `results/`, then stops the server. The second argument is the GPU
price in USD per hour.

## Where results live

`run_all.sh` writes to `results/`. The published run-2 files were then moved by hand into
`results/run2/` (and run 1 into `results/run1/`). Run the tests with `python -m pytest`.

## Honest limits

- **Quality is unscored.** `results/run2/answers_readable.md` holds the saved answers (concurrency 1)
  for a Thai-speaking reviewer. Until that is done, this is a speed and cost benchmark only.
- **Small sample.** 23 prompts, 64 requests per level, one run per config.
- **TTFT** is the time to the first streamed text chunk. The gap figures are gaps between streamed
  chunks. They are not true inter-token latency.
- **FP8 on a 4090** runs weight-only through a Marlin kernel, because the GPU has no native FP8
  compute. The FP8 numbers describe this GPU only.
- **Typhoon2 answers are shorter** (about 195 tokens on average, against about 450 for Qwen3), so
  compare it by cost per Thai character, not per token.
- **Cost** is GPU rental only and counts output tokens only.
- **Prefix caching** was on in all runs. I have not measured its effect.

## What failed

- **Run 1 was unfair.** I capped replies at 256 tokens, which cut off about 58 to 67% of Qwen3 answers.
  A cut-off answer cannot be judged fairly, so I reran with a 1,024-token cap. Run 1 stays in
  `results/run1/` for comparison only.
- **Run to run variation.** Qwen3 BF16 at concurrency 32 gave 1,386 tokens/s in run 1 and 1,044 in
  run 2. I have not found the cause.

## Laptop baseline (Ollama, CPU only)

Median of 5 counted runs after 1 warm-up. Temperature 0, max_tokens 150, `script/ttft.py`.
The tokens/s column is 1,000 divided by the median gap, as `script/ttft.py` calculates it.

| server | model | quantisation | median TTFT (ms) | median gap (ms) | tokens/s |
| --- | --- | --- | --- | --- | --- |
| Ollama (laptop, CPU) | qwen2.5:7b (7.6B parameters, Qwen2.5-7B-Instruct) | Q4_K_M, image digest 845dbda0ea48 | 354 | 334 | 3.0 |

The model name is stored in `ollama-test.json`. The quantisation and digest come from `ollama show qwen2.5:7b`
on the laptop that holds this model (Intel i5-1145G7, 32 GB RAM, no GPU used). The result file does not
record which machine ran the benchmark, so confirm the hardware before quoting this row.

## How Thai quality gets scored

`scoring/blind_sheet.md` holds all 92 saved answers (4 configs x 23 prompts) with shuffled labels.
Scores go in `scoring/scores.csv` using `scoring/RUBRIC.md`; `python3 -I script/unblind.py` then prints the
mean per config. The key (`scoring/key.json`) is git-ignored and is opened only after scoring.
This is one reviewer's judgement, not a validated study.

## Why

I lead an LLM safety evaluation team and run quantised models locally on Ollama. This is my first
step into measuring inference speed and cost properly, and I wanted the failures written down too.

## AI assistance

Some scripts and the write-up were drafted with AI coding assistants (Claude Code, Codex). I ran the
benchmarks, and I checked the numbers against the saved result files.
