import json

import pytest

from vllm_bench.schema import RunResult


def test_cost_and_json():
    result = RunResult("model", "fp16", 8, 100.0, 20.0, 1000.0, 20.0, "GPU", 0.69, "test")
    assert result.cost_per_million_tokens() == pytest.approx(0.1916667)
    assert json.loads(result.to_json())["concurrency"] == 8


def test_zero_throughput_has_no_valid_cost():
    result = RunResult("model", "fp16", 1, 0, 0, 0, 0, "GPU", 0.69, "test")
    with pytest.raises(ValueError, match="throughput"):
        result.cost_per_million_tokens()
