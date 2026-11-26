# Run 1: RTX 4090 24 GB (Ada), vLLM 0.34.0, Secure Cloud $0.89/hr, 25 Nov 2026
Flags: --max-model-len 4096 --gpu-memory-utilization 0.90. 64 requests per level, max_tokens 256, temp 0, 23 Thai prompts.
Qwen3 runs use thinking off. Benchmark client ran on the pod (no network latency in TTFT).

| config | conc | tok/s | TTFT p50 ms | TTFT p95 ms | req tok/s | $/1M tok | $/1M Thai chars |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3-8B BF16 | 1 | 58 | 39 | 50 | 59 | 4.26 | 3.01 |
| Qwen3-8B BF16 | 8 | 409 | 56 | 69 | 56 | 0.60 | 0.43 |
| Qwen3-8B BF16 | 32 | 1386 | 137 | 173 | 52 | 0.18 | 0.13 |
| Qwen3-8B FP8 | 1 | 96 | 30 | 35 | 98 | 2.56 | 1.81 |
| Qwen3-8B FP8 | 8 | 707 | 34 | 60 | 96 | 0.35 | 0.25 |
| Qwen3-8B FP8 | 32 | 2288 | 111 | 179 | 86 | 0.11 | 0.08 |
| Qwen3-8B AWQ | 1 | 147 | 30 | 35 | 150 | 1.68 | 1.18 |
| Qwen3-8B AWQ | 8 | 1053 | 35 | 51 | 143 | 0.23 | 0.16 |
| Qwen3-8B AWQ | 32 | 3185 | 79 | 158 | 123 | 0.08 | 0.05 |
| Typhoon2-Qwen2.5-7B BF16 | 1 | 63 | 38 | 45 | 64 | 3.93 | 2.52 |
| Typhoon2-Qwen2.5-7B BF16 | 8 | 453 | 51 | 71 | 62 | 0.55 | 0.35 |
| Typhoon2-Qwen2.5-7B BF16 | 32 | 1270 | 71 | 164 | 55 | 0.19 | 0.12 |

Kernels from server logs: BF16 = FlashAttention backend, plain GEMM. FP8 = MarlinFP8ScaledMMLinearKernel (weight-only FP8, log warns no native FP8 compute). AWQ = MarlinLinearKernel (AutoAWQMarlin). All: FLASH_ATTN attention.
Replies hitting the 256-token cap: Qwen3 about 58-67% of requests, Typhoon about 27%. Cost is GPU-only, output tokens only.
Agreement with Qwen3 BF16 (greedy, 23 prompts): AWQ identical 2/23, FP8 identical 3/23. Exact match is a weak quality signal; it needs Thai review.
Quality is NOT scored yet. Jean to review answers (exploratory only).
