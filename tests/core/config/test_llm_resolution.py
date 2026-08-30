from __future__ import annotations

import json

import pytest

from dslighting.core import ConfigBuilder
from dslighting.error import ConfigurationError


def test_model_override_beats_global_env(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "global-key")
    monkeypatch.setenv("API_BASE", "https://global.example/v1")
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps(
            {
                "model-a": {
                    "api_key": ["key-1", "key-2"],
                    "api_base": "https://override.example/v1",
                    "provider": "siliconflow",
                    "temperature": 0.1,
                }
            }
        ),
    )

    config = ConfigBuilder().build_config(model="model-a")

    assert config.llm.model == "model-a"
    assert config.llm.api_key is None
    assert config.llm.api_keys == ["key-1", "key-2"]
    assert config.llm.api_base == "https://override.example/v1"
    assert config.llm.provider == "siliconflow"
    assert config.llm.temperature == pytest.approx(0.1)


def test_explicit_params_beat_model_override(monkeypatch) -> None:
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps(
            {
                "model-a": {
                    "api_key": ["key-1", "key-2"],
                    "api_base": "https://override.example/v1",
                    "provider": "siliconflow",
                    "temperature": 0.1,
                }
            }
        ),
    )

    config = ConfigBuilder().build_config(
        model="model-a",
        api_key="manual-key",
        api_base="https://manual.example/v1",
        provider="manual-provider",
        default_headers={"x-foo": "true"},
        temperature=0.9,
    )

    assert config.llm.model == "model-a"
    assert config.llm.api_key == "manual-key"
    assert config.llm.api_keys is None
    assert config.llm.api_base == "https://manual.example/v1"
    assert config.llm.provider == "manual-provider"
    assert config.llm.default_headers == {"x-foo": "true"}
    assert config.llm.temperature == pytest.approx(0.9)


def test_api_key_list_is_normalized_to_api_keys() -> None:
    config = ConfigBuilder().build_config(model="model-a", api_key=["key-1", "key-2"])

    assert config.llm.api_key is None
    assert config.llm.api_keys == ["key-1", "key-2"]


def test_build_config_rejects_conflicting_api_key_and_api_keys() -> None:
    with pytest.raises(ConfigurationError, match="Only one of `api_key` or `api_keys`"):
        ConfigBuilder().build_config(model="model-a", api_key="k1", api_keys=["k2"])
