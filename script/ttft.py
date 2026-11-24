import json
import time
import urllib.request

URL = "http://127.0.0.1:11434/v1/chat/completions"
MODEL = "qwen2.5:7b"
PROMPT = "ทำไมน้ำทะเลจึงเค็ม อธิบายสั้น ๆ"

body = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": PROMPT}],
    "stream": True,
    "stream_options": {"include_usage": True}
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
for i in range(5):
    r = run()
    results.append(r)
    print(f"run {i + 1}: TTFT {r[0]:.0f} ms, gap {r[1]:.0f} ms, tokens {r[2]}")

avg_ttft = sum(r[0] for r in results) / len(results)
avg_gap = sum(r[1] for r in results) / len(results)
print(f"average TTFT: {avg_ttft:.0f} ms")
print(f"average gap: {avg_gap:.0f} ms, about {1000 / avg_gap:.1f} tokens/s")