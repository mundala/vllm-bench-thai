# Results

Two runs on a rented RTX 4090, 25 Nov 2026. **Run 2 is the one to read.** Run 1 is kept only for
comparison, because its 256-token cap cut off most Qwen3 answers.

## Setup (both runs)

- GPU: RunPod RTX 4090, 24 GB (Ada), billed at $0.89/hr.
- vLLM 0.34.0. Locked for every config: `--max-model-len 4096 --gpu-memory-utilization 0.90`.
- 23 Thai prompts, 64 requests per concurrency level (1, 8, 32), temperature 0, streaming.
- The client ran on the pod, so internet latency is not in the TTFT numbers. Local loopback HTTP and scheduling time still are.
- Qwen3 configs ran with thinking off. The Typhoon2 run sent no thinking flag.
- Three warm-up requests, not counted. `bench.py` sends the first three prompts before timing starts.

## Run 2 (1,024-token cap)

| config | conc | tok/s | TTFT p50 ms | TTFT p95 ms | $/1M output tok | $/1M Thai chars | capped |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3-8B BF16 | 1 | 58 | 41 | 51 | 4.24 | 2.98 | 5/64 |
| Qwen3-8B BF16 | 8 | 379 | 56 | 67 | 0.65 | 0.45 | 7/64 |
| Qwen3-8B BF16 | 32 | 1,044 | 74 | 167 | 0.24 | 0.17 | 6/64 |
| Qwen3-8B FP8 | 1 | 97 | 27 | 36 | 2.54 | 1.80 | 7/64 |
| Qwen3-8B FP8 | 8 | 658 | 35 | 58 | 0.38 | 0.26 | 7/64 |
| Qwen3-8B FP8 | 32 | 1,734 | 73 | 185 | 0.14 | 0.10 | 6/64 |
| Qwen3-8B AWQ | 1 | 149 | 24 | 31 | 1.65 | 1.17 | 8/64 |
| Qwen3-8B AWQ | 8 | 954 | 29 | 52 | 0.26 | 0.18 | 6/64 |
| Qwen3-8B AWQ | 32 | 2,473 | 63 | 168 | 0.10 | 0.07 | 7/64 |
| Typhoon2-Qwen2.5-7B BF16 | 1 | 63 | 37 | 41 | 3.91 | 2.47 | 0/64 |
| Typhoon2-Qwen2.5-7B BF16 | 8 | 443 | 50 | 62 | 0.56 | 0.35 | 0/64 |
| Typhoon2-Qwen2.5-7B BF16 | 32 | 1,018 | 61 | 167 | 0.24 | 0.15 | 0/64 |

All 64 requests succeeded at every level. "capped" means the reply hit the token limit.

Memory, from the vLLM server logs:

| config | weights | KV cache capacity |
| --- | --- | --- |
| Qwen3-8B BF16 | 15.27 GiB | 28,160 tokens |
| Qwen3-8B FP8 | 8.90 GiB | 74,240 tokens |
| Qwen3-8B AWQ | 5.71 GiB | 97,280 tokens |
| Typhoon2 BF16 | 14.29 GiB | 95,232 tokens |

Kernels, from the same logs: BF16 uses FlashAttention. FP8 uses a Marlin FP8 kernel in
weight-only mode, because the 4090 has no native FP8 compute (vLLM prints a warning saying so).
AWQ uses the Marlin AWQ kernel. Prefix caching was on in all four.

## What the numbers do and don't say

- **Quantisation is cheaper per token on this GPU.** At concurrency 32, AWQ cost about 0.10 USD per
  million output tokens against 0.24 for BF16. The KV cache figures suggest part of the gain comes from
  smaller weights leaving more room for the cache. The FP8 result is for this GPU only, since it is not
  true FP8 maths here.
- **Typhoon2 is not directly comparable by token.** Its answers average about 195 tokens against about
  450 for Qwen3, so cost per Thai character is the fairer column.
- **Quality is NOT scored.** Nothing here says whether AWQ or FP8 hurt Thai output. The raw answers
  for all four configs are in `results/run2/answers_readable.md`, waiting for a Thai-speaking reviewer.
- **TTFT** is the time to the first streamed text chunk. The gap p50 figure in the saved `.txt`
  files is the gap between streamed chunks, not true inter-token latency.
- **Small sample:** 64 requests per level from 23 prompts. Treat p95 as rough.
- **Run to run variation exists.** Qwen3 BF16 at concurrency 32 gave 1,386 tok/s in run 1 and 1,044 in
  run 2. The caps differed (256 and 1,024), and I have not isolated the cause. One run per config.
- **Prefix caching** was on in all four. Logged hit rates reached 36.9% for the Qwen3 configs and 58.5%
  for Typhoon2. I have not measured its effect on the results. One server handled the warm-up and then
  concurrency 1, 8 and 32 in order, with the same 23 prompts repeating, so the 8 and 32 levels started
  with a warm prefix cache. These are warm-cache numbers, not cold-start numbers.
- **Not fully deterministic.** At temperature 0, 2 of 23 prompts gave different answers across repeats
  for q3-bf16 and 10 of 23 for typhoon-bf16 (see `results/run2/CHECKS.md`). I have not found the cause.
- **"64/64 OK"** means each request returned text and a usage count without an error. It does not
  check for a clean finish reason.
- **Not pinned.** Models were pulled from the Hugging Face `main` branch and no dependency lockfile is
  included, so a rerun may use different model files or library versions.
- **Cost** is GPU rental only, output tokens only. It excludes load time, idle time and storage.
  Figures are computed from unrounded tok/s, so they can differ by a cent or two from the rounded
  tok/s shown.

## Run 1 (256-token cap, superseded)

Kept in `results/run1/RESULTS.md`. A cap of 256 tokens cut off about 58 to 67% of Qwen3 answers and
about 27% of Typhoon2 answers. That is not a fair way to judge answers or compare models. I treated
it as a failed first attempt and reran with 1,024.
