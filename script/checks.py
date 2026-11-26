"""Objective, non-quality checks on run 2 saved answers.

Reads results/run2/<config>.json (written by script/bench.py) and prints a
markdown table plus a cost table. These are surface statistics only.
They are NOT a quality score.

Usage: python3 -I script/checks.py [run2_dir]
"""
import json
import os
import sys
from collections import Counter, defaultdict

CONFIGS = ["q3-bf16", "q3-fp8", "q3-awq", "typhoon-bf16"]
THAI_RE_RANGE = (0x0E00, 0x0E7F)
CJK_RANGE = (0x4E00, 0x9FFF)
WINDOW = 20
REPEAT_MIN = 3


def in_range(ch, rng):
    return rng[0] <= ord(ch) <= rng[1]


def has_repeat(text):
    """True if some 20-character window (code points, overlapping) occurs 3+ times."""
    counts = Counter(text[i:i + WINDOW] for i in range(len(text) - WINDOW + 1))
    return any(c >= REPEAT_MIN for c in counts.values())


def check_config(run_dir, cfg):
    path = os.path.join(run_dir, f"{cfg}.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    answers = d["answers"]
    lvl = d["levels"]["1"]  # answers are saved only from the concurrency-1 level
    n = len(answers)

    total_chars = 0
    thai_chars = 0
    cjk_answers = 0
    repeat_answers = 0
    per_prompt = defaultdict(list)
    for a in answers:
        t = a["text"]
        total_chars += len(t)
        th = sum(1 for ch in t if in_range(ch, THAI_RE_RANGE))
        thai_chars += th
        if any(in_range(ch, CJK_RANGE) for ch in t):
            cjk_answers += 1
        if has_repeat(t):
            repeat_answers += 1
        per_prompt[a["prompt"]].append(t)

    # Identical answers: an answer is "identical" if it equals the modal answer
    # for its prompt. Prompts with a single request count as trivially identical.
    same = 0
    prompts_multi_distinct = 0
    for prompt, texts in per_prompt.items():
        c = Counter(texts)
        same += c.most_common(1)[0][1]
        if len(c) > 1:
            prompts_multi_distinct += 1
    repeat_counts = Counter(len(v) for v in per_prompt.values())

    # Cost: GPU $/hr is the rate recorded by bench.py. Single-stream wall time
    # for the 64 conc-1 requests is lvl["wall_s"].
    rate = d["gpu_usd_hr"]
    wall = lvl["wall_s"]
    thai_per_s = thai_chars / wall
    usd_per_1m_thai = rate / 3600 / thai_per_s * 1e6

    return {
        "cfg": cfg,
        "n": n,
        "capped": lvl["hit_max_tokens"],
        "capped_share": lvl["hit_max_tokens"] / lvl["ok"],
        "thai_share": thai_chars / total_chars,
        "thai_mean": thai_chars / n,
        "cjk_share": cjk_answers / n,
        "repeat_share": repeat_answers / n,
        "identical_share": same / n,
        "prompts_multi_distinct": prompts_multi_distinct,
        "prompts": len(per_prompt),
        "repeat_counts": dict(sorted(repeat_counts.items())),
        "total_thai": thai_chars,
        "wall": wall,
        "rate": rate,
        "usd_1m_thai": usd_per_1m_thai,
        "usd_1m_thai_stored": lvl["usd_per_1m_thai_chars"],
        "thai_chars_s_stored": lvl["thai_chars_s"],
        "thai_chars_s_recalc": thai_per_s,
    }


def pct(x):
    return f"{100 * x:.1f}%"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    run_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "results", "run2")
    run_dir = os.path.abspath(run_dir)
    rows = [check_config(run_dir, c) for c in CONFIGS]

    print(f"Run dir: {run_dir}")
    print("NOT a quality score. Surface statistics only.")
    print()
    print("| config | answers | hit 1,024 cap | Thai-block share of chars | mean Thai chars/answer | any CJK | 20-char repeat 3+x | identical to prompt modal answer | prompts with >1 distinct answer |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['cfg']} | {r['n']} | {r['capped']}/{r['n']} ({pct(r['capped_share'])}) | "
              f"{pct(r['thai_share'])} | {r['thai_mean']:.1f} | {pct(r['cjk_share'])} | "
              f"{pct(r['repeat_share'])} | {pct(r['identical_share'])} | "
              f"{r['prompts_multi_distinct']}/{r['prompts']} |")
    print()
    print("Requests per prompt (count of prompts with that many requests): ")
    for r in rows:
        print(f"  {r['cfg']}: {r['repeat_counts']}")
    print()
    print("| config | GPU $/hr | conc-1 wall s | total Thai chars | Thai chars/s (recalc) | Thai chars/s (stored) | $/1M Thai chars (recalc) | $/1M Thai chars (stored) |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['cfg']} | {r['rate']:.2f} | {r['wall']:.1f} | {r['total_thai']} | "
              f"{r['thai_chars_s_recalc']:.2f} | {r['thai_chars_s_stored']:.2f} | "
              f"{r['usd_1m_thai']:.2f} | {r['usd_1m_thai_stored']:.2f} |")


if __name__ == "__main__":
    main()
