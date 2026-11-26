"""Concurrency benchmark for an OpenAI-compatible server (vLLM).

Per request: TTFT, inter-chunk gap, output tokens, Thai characters.
Per concurrency level: throughput (tokens/s and Thai chars/s) and, if
--gpu-usd-hr is given, cost per 1M output tokens and per 1M Thai chars.
"""
import argparse, json, re, statistics, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

p = argparse.ArgumentParser()
p.add_argument("--url", required=True)            # e.g. http://POD:8000/v1/chat/completions
p.add_argument("--model", required=True)
p.add_argument("--prompts", default="results/thai_prompts.md")
p.add_argument("--levels", default="1,8,32")
p.add_argument("--requests-per-level", type=int, default=64)
p.add_argument("--max-tokens", type=int, default=256)
p.add_argument("--gpu-usd-hr", type=float, default=0.0)
p.add_argument("--label", default="run")
p.add_argument("--out", default="results/bench.json")
p.add_argument("--no-think", action="store_true")  # Qwen3: disable thinking
args = p.parse_args()

text = open(args.prompts, encoding="utf-8").read().split("## Rubric")[0]
prompts = [m.group(1) for l in text.splitlines()
           if (m := re.match(r"^\d+\.\s+(.*\S)", l))]
THAI = re.compile(r"[฀-๿]")

def one(prompt):
    body = {"model": args.model, "messages": [{"role": "user", "content": prompt}],
            "stream": True, "stream_options": {"include_usage": True},
            "temperature": 0, "max_tokens": args.max_tokens}
    if args.no_think:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(args.url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter(); first = None; stamps = []; text = ""; usage = None; fin = None
    try:
        with urllib.request.urlopen(req, timeout=300) as res:
            for line in res:
                line = line.decode().strip()
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                j = json.loads(line[6:])
                if j.get("usage"): usage = j["usage"]
                for c in j.get("choices", []):
                    if c.get("finish_reason"): fin = c["finish_reason"]
                    d = c.get("delta", {}).get("content")
                    if d:
                        now = time.perf_counter()
                        if first is None: first = now
                        stamps.append(now); text += d
    except Exception as e:
        return {"error": str(e)}
    end = time.perf_counter()
    if first is None: return {"error": "no output"}
    if not usage: return {"error": "no usage from server"}  # never fall back to chunk counts
    gaps = [(b - a) * 1000 for a, b in zip(stamps, stamps[1:])]
    return {"ttft_ms": (first - t0) * 1000,
            "gap_ms": statistics.median(gaps) if gaps else None,
            "e2e_ms": (end - t0) * 1000, "finish": fin,
            "prompt_tokens": usage["prompt_tokens"],
            "tokens": usage["completion_tokens"],
            "req_tok_s": usage["completion_tokens"] / (end - first) if end > first else None,
            "thai_chars": len(THAI.findall(text)), "text": text}

def pct(v, q):
    v = sorted(v); return v[min(len(v) - 1, int(q * len(v)))]

print(f"warm-up (not counted), {len(prompts)} prompts loaded")
for pr in prompts[:3]: one(pr)

out = {"label": args.label, "model": args.model, "gpu_usd_hr": args.gpu_usd_hr, "levels": {}}
print("| label | conc | ok/fail | TTFT p50 | TTFT p95 | gap p50 | tok/s | Thai chars/s | chars/tok | $/1M tok | $/1M Thai chars | e2e | per-req | capped |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for conc in [int(x) for x in args.levels.split(",")]:
    work = [prompts[i % len(prompts)] for i in range(args.requests_per_level)]
    t0 = time.perf_counter()
    with ThreadPoolExecutor(conc) as ex:
        res = list(ex.map(one, work))
    wall = time.perf_counter() - t0
    ok = [r for r in res if "error" not in r]
    fail = len(res) - len(ok)
    if not ok:
        print(f"| {args.label} | {conc} | 0/{fail} | - | - | - | - | - | - | - | - |"); continue
    toks = sum(r["tokens"] for r in ok); chars = sum(r["thai_chars"] for r in ok)
    tps, cps = toks / wall, chars / wall
    usd_tok = args.gpu_usd_hr / 3600 / tps * 1e6 if args.gpu_usd_hr and tps else float("nan")
    usd_chr = args.gpu_usd_hr / 3600 / cps * 1e6 if args.gpu_usd_hr and cps else float("nan")
    gaps = [r["gap_ms"] for r in ok if r["gap_ms"] is not None]
    rts = [r["req_tok_s"] for r in ok if r["req_tok_s"]]
    capped = sum(r["finish"] == "length" for r in ok)
    ttfts = [r["ttft_ms"] for r in ok]
    row = {"ok": len(ok), "fail": fail, "wall_s": wall, "tok_s": tps, "thai_chars_s": cps,
           "chars_per_tok": chars / toks, "ttft_p50": statistics.median(ttfts),
           "ttft_p95": pct(ttfts, .95), "gap_p50": statistics.median(gaps) if gaps else None,
           "e2e_p50": statistics.median(r["e2e_ms"] for r in ok),
           "e2e_p95": pct([r["e2e_ms"] for r in ok], .95),
           "req_tok_s_p50": statistics.median(rts) if rts else None,
           "prompt_tok_mean": statistics.mean(r["prompt_tokens"] for r in ok),
           "out_tok_mean": toks / len(ok), "hit_max_tokens": capped,
           "usd_per_1m_tok": usd_tok, "usd_per_1m_thai_chars": usd_chr}
    out["levels"][conc] = row
    print(f"| {args.label} | {conc} | {len(ok)}/{fail} | {row['ttft_p50']:.0f} | {row['ttft_p95']:.0f} | "
          f"{row['gap_p50'] or 0:.0f} | {tps:.0f} | {cps:.0f} | {row['chars_per_tok']:.2f} | "
          f"{usd_tok:.2f} | {usd_chr:.2f} | e2e50 {row['e2e_p50']:.0f} | req tok/s {row['req_tok_s_p50'] or 0:.0f} | capped {capped}/{len(ok)} |")
    if conc == 1:  # keep the quality answers for later scoring
        out["answers"] = [{"prompt": w, "text": r["text"]} for w, r in zip(work, res) if "text" in r]

json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", args.out)
