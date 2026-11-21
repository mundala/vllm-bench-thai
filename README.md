# vllm-bench-thai

Benchmarking one open-weight model, Qwen2.5-7B-Instruct, on vLLM:
full precision (FP16) against quantised versions (AWQ, and FP8 where the GPU supports it),
on a single rented Runpod GPU.

**Status:** work in progress. No results yet.

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

Coming soon: GPU, vLLM version, every command I ran.

## Results

Coming soon.

## What failed

Coming soon. Failures go here too.

## AI assistance

Some scripts were written with help from AI coding assistants (Claude Code, Codex).
I ran every benchmark myself and checked every number in this repo.
