"""A portable record of one benchmark run."""

from dataclasses import asdict, dataclass
import json


@dataclass
class RunResult:
    model: str
    quantisation: str
    concurrency: int
    ttft_ms_median: float
    tpot_ms_median: float
    output_tok_per_s: float
    vram_gb: float
    gpu: str
    gpu_usd_per_hr: float
    vllm_version: str

    def cost_per_million_tokens(self) -> float:
        if self.output_tok_per_s <= 0:
            raise ValueError("output token throughput must be positive")
        return self.gpu_usd_per_hr * 1_000_000 / (self.output_tok_per_s * 3600)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
