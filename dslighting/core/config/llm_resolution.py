"""Single-source LLM config resolution helpers."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence, Union

from dslighting.config import LLMConfig
from dslighting.error import ConfigurationError
from dslighting.utils.defaults import (
    DEFAULT_API_BASE,
    DEFAULT_LLM_MODEL,
    DEFAULT_TEMPERATURE,
    ENV_API_BASE,
    ENV_API_KEY,
    ENV_LLM_MODEL,
    ENV_LLM_MODEL_CONFIGS,
    ENV_LLM_PROVIDER,
    ENV_LLM_TEMPERATURE,
)

logger = logging.getLogger(__name__)

_PLACEHOLDER_KEYS = {"your_key", "your_api_key"}


def load_global_llm_env() -> Dict[str, Any]:
    """Load global LLM overrides from environment variables."""
    payload: Dict[str, Any] = {}

    api_key = os.getenv(ENV_API_KEY)
    if api_key:
        payload["api_key"] = api_key

    api_base = os.getenv(ENV_API_BASE)
    if api_base:
        payload["api_base"] = api_base

    model = os.getenv(ENV_LLM_MODEL)
    if model:
        payload["model"] = model

    provider = os.getenv(ENV_LLM_PROVIDER)
    if provider:
        payload["provider"] = provider

    temperature = os.getenv(ENV_LLM_TEMPERATURE)
    if temperature:
        coerced = _coerce_temperature(temperature, source=ENV_LLM_TEMPERATURE)
        if coerced is not None:
            payload["temperature"] = coerced

    return payload


def load_model_override_map() -> Dict[str, Dict[str, Any]]:
    """Load per-model overrides from LLM_MODEL_CONFIGS."""
    raw = os.getenv(ENV_LLM_MODEL_CONFIGS)
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except Exception as exc:
        logger.warning("Failed to parse LLM_MODEL_CONFIGS as JSON: %s", exc)
        return {}

    if not isinstance(parsed, dict):
        logger.warning("LLM_MODEL_CONFIGS must be a JSON object")
        return {}

    result: Dict[str, Dict[str, Any]] = {}
    for model_name, model_config in parsed.items():
        if not isinstance(model_name, str) or not isinstance(model_config, dict):
            logger.warning("Skipping invalid model config: %s", model_name)
            continue

        normalized = normalize_api_credentials(model_config.copy(), source=f"LLM_MODEL_CONFIGS[{model_name}]")
        if normalized is None:
            continue

        if "temperature" in normalized:
            coerced = _coerce_temperature(normalized["temperature"], source=f"LLM_MODEL_CONFIGS[{model_name}].temperature")
            if coerced is None:
                normalized.pop("temperature", None)
            else:
                normalized["temperature"] = coerced

        result[model_name] = normalized

    return result


def resolve_model_name(model: Optional[str]) -> str:
    """Resolve final model name from explicit input, env, or defaults."""
    if model is not None and str(model).strip():
        return str(model).strip()

    env_model = os.getenv(ENV_LLM_MODEL)
    if env_model and env_model.strip():
        return env_model.strip()

    return DEFAULT_LLM_MODEL


def normalize_api_credentials(payload: Dict[str, Any], *, source: str = "llm") -> Optional[Dict[str, Any]]:
    """Normalize api_key/api_keys fields and filter placeholders."""
    api_key_value = payload.get("api_key")
    api_keys_value = payload.get("api_keys")

    if api_key_value is not None and api_keys_value is not None:
        raise ConfigurationError(
            f"Only one of `api_key` or `api_keys` may be provided in {source}.",
            error_code="CFG-002",
        )

    if _is_sequence_of_keys(api_key_value):
        payload["api_keys"] = [k for k in _normalize_key_list(api_key_value) if k]
        payload.pop("api_key", None)
    elif api_key_value is not None:
        normalized_key = _normalize_single_key(api_key_value)
        if normalized_key is None:
            payload.pop("api_key", None)
        else:
            payload["api_key"] = normalized_key

    if api_keys_value is not None:
        normalized_keys = _normalize_key_list(api_keys_value)
        if normalized_keys:
            payload["api_keys"] = normalized_keys
        else:
            payload.pop("api_keys", None)

    if payload.get("api_keys") is not None:
        payload.pop("api_key", None)

    return payload


def build_llm_config(
    *,
    model: Optional[str] = None,
    api_key: Optional[Union[str, Sequence[str]]] = None,
    api_keys: Optional[Sequence[str]] = None,
    api_base: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
) -> LLMConfig:
    """Build a resolved LLMConfig from defaults, env, model overrides, and explicit params."""
    defaults: Dict[str, Any] = {
        "model": DEFAULT_LLM_MODEL,
        "temperature": DEFAULT_TEMPERATURE,
        "api_base": DEFAULT_API_BASE,
    }

    env_llm = load_global_llm_env()
    resolved_model = resolve_model_name(model)
    model_override = load_model_override_map().get(resolved_model, {})

    explicit: Dict[str, Any] = {
        "model": resolved_model,
        "api_key": api_key,
        "api_keys": list(api_keys) if api_keys is not None else None,
        "api_base": api_base,
        "provider": provider,
        "temperature": temperature,
    }

    merged = _merge_non_none(defaults, env_llm)
    merged = _merge_with_credential_override(merged, model_override)
    merged = _merge_with_credential_override(merged, explicit)
    merged["model"] = resolved_model
    normalized = normalize_api_credentials(merged, source="LLM config")
    return LLMConfig(**normalized)


def _merge_non_none(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if value is not None:
            result[key] = value
    return result


def _merge_with_credential_override(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    if override.get("api_key") is not None or override.get("api_keys") is not None:
        result.pop("api_key", None)
        result.pop("api_keys", None)
    return _merge_non_none(result, override)


def _coerce_temperature(value: Any, *, source: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning("Invalid temperature value from %s: %r", source, value)
        return None


def _is_sequence_of_keys(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _normalize_key_list(value: Any) -> List[str]:
    if not _is_sequence_of_keys(value):
        raise ConfigurationError(
            "`api_keys` must be a sequence of strings.",
            error_code="CFG-002",
        )

    normalized: List[str] = []
    for item in value:
        key = _normalize_single_key(item)
        if key is not None:
            normalized.append(key)
    return normalized


def _normalize_single_key(value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigurationError(
            "`api_key` entries must be strings.",
            error_code="CFG-002",
        )

    normalized = value.strip()
    if not normalized:
        return None
    if normalized.lower() in _PLACEHOLDER_KEYS:
        return None
    return normalized
