# vllm-bench-thai

Benchmarking one open-weight model, Qwen2.5-7B-Instruct, on vLLM:
full precision (FP16) against quantised versions (AWQ, and FP8 where the GPU supports it),
on a single rented Runpod GPU.

**Status:**
Work in Progress. Ollama baseline done. vLLM runs not started.

## What I'm measuring

- Time to first token (TTFT)
- Inter-token latency (ITL)
- Output tokens per second at concurrency 1, 8 and 32
- GPU memory used
- Cost per million output tokens, from the hourly GPU price
- Thai quality: 20 Thai prompts, scored 1 to 5 against a written rubric, FP16 vs AWQ

## Why

I lead an LLM safety evaluation team and run quantised models locally on Ollama.
This is my first step into measuring inference speed and cost properly,
and checking whether quantisation hurts Thai output.

## Setup

The benchmark script is `script/ttft.py`. It streams one Thai prompt to any
OpenAI-compatible server and reports TTFT and the gap between chunks
(about one token each). The first request is a warm-up and isn't counted.
After that it reports the median, so one slow run doesn't skew the numbers.

```bash
python script/ttft.py --runs 5 --out results.json
```
Options: `--url`, `--model`, `--runs`, `--out`.

It only tests concurrency 1 for now. vLLM GPU and version details will go
here once I've run it.

## Results

Baseline on my laptop, Ollama, CPU only. Temperature 0, max_tokens 150.

| server | model | median TTFT (ms) | median gap (ms) | tokens/s |
| --- | --- | --- | --- | --- |
| Ollama (laptop, CPU) | qwen2.5:7b | 273 | 317 | 3.2 |

3.2 tokens/s is slow, yes. It's a laptop CPU. The vLLM rows are the real test.

## What failed

Coming soon. Failures go here too.

## AI assistance

Some scripts were written with help from AI coding assistants (Claude Code, Codex).
I ran every benchmark myself and checked every number in this repo.
