import json
import statistics
import time
import urllib.request
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:11434/v1/chat/completions")
parser.add_argument("--model", default="qwen2.5:7b")
parser.add_argument("--runs", type=int,default=5)
args = parser.parse_args()

URL = args.url
MODEL = args.model
PROMPT = "ทำไมน้ำทะเลจึงเค็ม อธิบายสั้น ๆ"

body = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": PROMPT}],
    "stream": True,
    "stream_options": {"include_usage": True},
    "temperature": 0,
    "max_tokens": 150
}).encode()

req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})

def run():
    start = time.perf_counter()
    first = None
    times = []
    usage = None
    with urllib.request.urlopen(req) as res:
        for line in res:
            line = line.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            payload = json.loads(line[6:])
            if payload.get("usage"):
                usage = payload["usage"]
            if first is None:
                first = time.perf_counter()
            times.append(time.perf_counter())
    ttft = (first - start) * 1000
    gaps = [(b - a) * 1000 for a, b in zip(times, times[1:])]
    avg_gap = sum(gaps) / len(gaps)
    tokens = usage["completion_tokens"] if usage else len(times)
    return ttft, avg_gap, tokens


print("warm-up run (not counted)...")
run()

results = []
for i in range(args.runs):
    r = run()
    results.append(r)
    print(f"run {i + 1}: TTFT {r[0]:.0f} ms, gap {r[1]:.0f} ms, tokens {r[2]}")

avg_ttft = sum(r[0] for r in results) / len(results)
med_ttft = statistics.median(r[0] for r in results)
med_gap = statistics.median(r[1] for r in results)
print(f"median TTFT: {med_ttft:.0f} ms")
print(f"median gap: {med_gap:.0f} ms, about {1000 / med_gap:.1f} tokens/s")
      
with open("results.json", "w") as f:
    json.dump({"model": MODEL, "runs": results}, f, indent=2)