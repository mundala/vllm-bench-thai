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

start= time.perf_counter()
first = None
chunks = 0
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
        chunks += 1
        times.append(time.perf_counter())

end = time.perf_counter()
print(f"TTFT: {(first - start) * 1000:.02f} ms")
print(f"chunks: {chunks}, total: {end - start:.2f} s")
gaps = [(b - a) * 1000 for a, b in zip(times, times[1:])]
print(f"avg gap between chunks: {sum(gaps) / len(gaps):.02f} ms")
print(f"token: {usage['completion_tokens'] if usage else 'not sent'}")
