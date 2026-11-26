#!/usr/bin/env bash
set -o pipefail
# Run ON the GPU pod (so network latency is not part of TTFT).
# Usage: [MAXTOK=1024] ./run_all.sh <config> <gpu_usd_per_hr>   (MAXTOK default 256)
# configs: q3-bf16 | q3-awq | q3-fp8 | typhoon-bf16
# Starts vLLM with locked flags, waits for it, benchmarks, saves the server log, stops it.
CFG="${1:?config}"; RATE="${2:?gpu usd per hr}"
EXTRA=""
case "$CFG" in
  q3-bf16)       MODEL="Qwen/Qwen3-8B"; EXTRA="--no-think" ;;
  q3-awq)        MODEL="Qwen/Qwen3-8B-AWQ"; EXTRA="--no-think" ;;
  q3-fp8)        MODEL="Qwen/Qwen3-8B-FP8"; EXTRA="--no-think" ;;
  typhoon-bf16)  MODEL="typhoon-ai/typhoon2-qwen2.5-7b-instruct" ;;
  *) echo "unknown config"; exit 1 ;;
esac
mkdir -p results
# Fairness locks: identical for every config.
vllm serve "$MODEL" --max-model-len 4096 --gpu-memory-utilization 0.90 --port 8000 \
  > "results/$CFG.server.log" 2>&1 &
SPID=$!
READY=0
for i in $(seq 1 120); do
  curl -sf localhost:8000/health >/dev/null && { READY=1; break; }
  kill -0 $SPID 2>/dev/null || { echo "server died, see results/$CFG.server.log"; exit 1; }
  sleep 10
done
[ $READY = 1 ] || { echo "health timeout"; kill $SPID; exit 1; }
curl -s localhost:8000/v1/models | grep -q "$MODEL" || { echo "wrong model served"; kill $SPID; exit 1; }
python3 script/bench.py --url "http://localhost:8000/v1/chat/completions" --model "$MODEL" \
  --max-tokens "${MAXTOK:-256}" --label "$CFG" --gpu-usd-hr "$RATE" --out "results/$CFG.json" $EXTRA | tee "results/$CFG.txt"
kill $SPID; wait $SPID 2>/dev/null
echo "done $CFG"
