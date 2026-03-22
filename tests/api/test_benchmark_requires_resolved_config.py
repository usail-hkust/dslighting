from __future__ import annotations

import json

import pytest

pytest.importorskip("diskcache")

from dslighting.api.benchmark import DSBenchmark
from dslighting.config import DSLightingConfig
from dslighting.core import ConfigBuilder
from dslighting.error import ConfigurationError


def _make_benchmark(tmp_path) -> DSBenchmark:
    data_dir = tmp_path / "data"
    vendor_dir = tmp_path / "vendor"
    data_dir.mkdir()
    vendor_dir.mkdir()
    return DSBenchmark(
        benchmark_type="custom",
        data_dir=str(data_dir),
        vendor_comp_dir=str(vendor_dir),
        competitions=["task-1"],
    )


def test_benchmark_requires_resolved_config_even_when_env_exists(monkeypatch, tmp_path) -> None:
    benchmark = _make_benchmark(tmp_path)

    monkeypatch.setenv("API_KEY", "env-key")
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps(
            {
                "gpt-4o-mini": {
                    "api_key": ["env-1", "env-2"],
                }
            }
        ),
    )

    with pytest.raises(ConfigurationError, match="fully resolved LLM config"):
        benchmark.run(config=DSLightingConfig())


def test_benchmark_accepts_config_built_by_config_builder(monkeypatch, tmp_path) -> None:
    benchmark = _make_benchmark(tmp_path)
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps(
            {
                "model-a": {
                    "api_key": ["env-1", "env-2"],
                    "provider": "siliconflow",
                }
            }
        ),
    )

    config = ConfigBuilder().build_config(model="model-a")
    captured = {}
    benchmark._build_runtime_options = lambda cfg: {"ok": True}

    def _fake_execute(config, runtime_options, log_path=None, verbose=True):
        captured["config"] = config
        captured["runtime_options"] = runtime_options
        captured["log_path"] = log_path
        captured["verbose"] = verbose
        return "ok"

    benchmark._execute_benchmark = _fake_execute

    result = benchmark.run(config=config, verbose=False)

    assert result == "ok"
    assert captured["config"].llm.api_keys == ["env-1", "env-2"]
    assert captured["config"].scheduler.exp_name == benchmark.name
    assert captured["runtime_options"] == {"ok": True}
