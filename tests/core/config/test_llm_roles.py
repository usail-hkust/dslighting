from __future__ import annotations

import json

import pytest

from dslighting.core.config.llm_roles import (
    DEFAULT_IMAGE_JUDGE_MODEL,
    DEFAULT_TEXT_JUDGE_MODEL,
    ENV_JUDGE_IMAGE_MODEL,
    ENV_JUDGE_MODEL,
    resolve_image_judge_llm_config,
    resolve_primary_llm_config,
    resolve_role_model_name,
    resolve_text_judge_llm_config,
)
from dslighting.utils.defaults import ENV_LLM_MODEL


def test_explicit_model_beats_role_and_global_env(monkeypatch) -> None:
    monkeypatch.setenv(ENV_LLM_MODEL, "global-model")
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    resolved = resolve_role_model_name("image_judge", model="explicit-model")

    assert resolved == "explicit-model"


def test_role_env_beats_global_env_for_image_judge(monkeypatch) -> None:
    monkeypatch.setenv(ENV_LLM_MODEL, "global-model")
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    resolved = resolve_role_model_name("image_judge")

    assert resolved == "judge-image-model"


def test_global_env_beats_role_default_when_role_env_missing(monkeypatch) -> None:
    monkeypatch.delenv(ENV_JUDGE_MODEL, raising=False)
    monkeypatch.setenv(ENV_LLM_MODEL, "global-model")

    resolved = resolve_role_model_name("text_judge")

    assert resolved == "global-model"


def test_role_default_used_when_no_env_or_explicit_model(monkeypatch) -> None:
    monkeypatch.delenv(ENV_LLM_MODEL, raising=False)
    monkeypatch.delenv(ENV_JUDGE_IMAGE_MODEL, raising=False)
    monkeypatch.delenv(ENV_JUDGE_MODEL, raising=False)

    assert resolve_role_model_name("image_judge") == DEFAULT_IMAGE_JUDGE_MODEL
    assert resolve_role_model_name("text_judge") == DEFAULT_TEXT_JUDGE_MODEL


def test_image_judge_role_uses_model_overrides(monkeypatch) -> None:
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps(
            {
                "judge-image-model": {
                    "api_keys": ["key-1", "key-2"],
                    "api_base": "https://judge.example/v1",
                    "provider": "siliconflow",
                    "temperature": 0.15,
                }
            }
        ),
    )

    config = resolve_image_judge_llm_config()

    assert config.model == "judge-image-model"
    assert config.api_key is None
    assert config.api_keys == ["key-1", "key-2"]
    assert config.api_base == "https://judge.example/v1"
    assert config.provider == "siliconflow"
    assert config.temperature == pytest.approx(0.15)


def test_explicit_params_still_override_role_config(monkeypatch) -> None:
    monkeypatch.setenv(ENV_JUDGE_MODEL, "judge-text-model")
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps(
            {
                "judge-text-model": {
                    "api_key": "model-key",
                    "api_base": "https://judge.example/v1",
                    "provider": "siliconflow",
                    "temperature": 0.2,
                }
            }
        ),
    )

    config = resolve_text_judge_llm_config(
        model="explicit-text-model",
        api_key="manual-key",
        api_base="https://manual.example/v1",
        provider="manual-provider",
        temperature=0.9,
    )

    assert config.model == "explicit-text-model"
    assert config.api_key == "manual-key"
    assert config.api_keys is None
    assert config.api_base == "https://manual.example/v1"
    assert config.provider == "manual-provider"
    assert config.temperature == pytest.approx(0.9)


def test_primary_role_still_uses_global_chain(monkeypatch) -> None:
    monkeypatch.setenv(ENV_LLM_MODEL, "primary-model")

    config = resolve_primary_llm_config()

    assert config.model == "primary-model"
