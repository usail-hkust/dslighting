"""Role-based LLM configuration resolution helpers."""

from __future__ import annotations

import os
from typing import Literal, Optional, Sequence, Union

from dslighting.config import LLMConfig
from dslighting.core.config.llm_resolution import build_llm_config
from dslighting.utils.defaults import DEFAULT_LLM_MODEL, ENV_LLM_MODEL

ENV_JUDGE_MODEL = "JUDGE_MODEL"
ENV_JUDGE_IMAGE_MODEL = "JUDGE_IMAGE_MODEL"

ROLE_PRIMARY = "primary"
ROLE_TEXT_JUDGE = "text_judge"
ROLE_IMAGE_JUDGE = "image_judge"
LLMRole = Literal["primary", "text_judge", "image_judge"]

DEFAULT_PRIMARY_MODEL = DEFAULT_LLM_MODEL
DEFAULT_TEXT_JUDGE_MODEL = "openai/deepseek-ai/DeepSeek-V3.1-Terminus"
DEFAULT_IMAGE_JUDGE_MODEL = "openai/Qwen/Qwen2-VL-72B-Instruct"

_ROLE_ENV_MODEL_VARS: dict[LLMRole, str | None] = {
    ROLE_PRIMARY: None,
    ROLE_TEXT_JUDGE: ENV_JUDGE_MODEL,
    ROLE_IMAGE_JUDGE: ENV_JUDGE_IMAGE_MODEL,
}

_ROLE_DEFAULT_MODELS: dict[LLMRole, str] = {
    ROLE_PRIMARY: DEFAULT_PRIMARY_MODEL,
    ROLE_TEXT_JUDGE: DEFAULT_TEXT_JUDGE_MODEL,
    ROLE_IMAGE_JUDGE: DEFAULT_IMAGE_JUDGE_MODEL,
}


def resolve_role_model_name(
    role: LLMRole,
    *,
    model: str | None = None,
) -> str:
    """Resolve the effective model name for a given logical LLM role."""
    if model is not None and str(model).strip():
        return str(model).strip()

    role_env_var = _ROLE_ENV_MODEL_VARS[role]
    if role_env_var:
        role_model = os.getenv(role_env_var)
        if role_model and role_model.strip():
            return role_model.strip()

    global_model = os.getenv(ENV_LLM_MODEL)
    if global_model and global_model.strip():
        return global_model.strip()

    return _ROLE_DEFAULT_MODELS[role]


def resolve_llm_config_for_role(
    role: LLMRole,
    *,
    model: str | None = None,
    api_key: Optional[Union[str, Sequence[str]]] = None,
    api_keys: Optional[Sequence[str]] = None,
    api_base: str | None = None,
    provider: str | None = None,
    temperature: float | None = None,
) -> LLMConfig:
    """Resolve an `LLMConfig` using shared precedence rules for a logical role."""
    resolved_model = resolve_role_model_name(role, model=model)
    return build_llm_config(
        model=resolved_model,
        api_key=api_key,
        api_keys=api_keys,
        api_base=api_base,
        provider=provider,
        temperature=temperature,
    )


def resolve_primary_llm_config(
    *,
    model: str | None = None,
    api_key: Optional[Union[str, Sequence[str]]] = None,
    api_keys: Optional[Sequence[str]] = None,
    api_base: str | None = None,
    provider: str | None = None,
    temperature: float | None = None,
) -> LLMConfig:
    return resolve_llm_config_for_role(
        ROLE_PRIMARY,
        model=model,
        api_key=api_key,
        api_keys=api_keys,
        api_base=api_base,
        provider=provider,
        temperature=temperature,
    )


def resolve_text_judge_llm_config(
    *,
    model: str | None = None,
    api_key: Optional[Union[str, Sequence[str]]] = None,
    api_keys: Optional[Sequence[str]] = None,
    api_base: str | None = None,
    provider: str | None = None,
    temperature: float | None = None,
) -> LLMConfig:
    return resolve_llm_config_for_role(
        ROLE_TEXT_JUDGE,
        model=model,
        api_key=api_key,
        api_keys=api_keys,
        api_base=api_base,
        provider=provider,
        temperature=temperature,
    )


def resolve_image_judge_llm_config(
    *,
    model: str | None = None,
    api_key: Optional[Union[str, Sequence[str]]] = None,
    api_keys: Optional[Sequence[str]] = None,
    api_base: str | None = None,
    provider: str | None = None,
    temperature: float | None = None,
) -> LLMConfig:
    return resolve_llm_config_for_role(
        ROLE_IMAGE_JUDGE,
        model=model,
        api_key=api_key,
        api_keys=api_keys,
        api_base=api_base,
        provider=provider,
        temperature=temperature,
    )


__all__ = [
    "DEFAULT_IMAGE_JUDGE_MODEL",
    "DEFAULT_PRIMARY_MODEL",
    "DEFAULT_TEXT_JUDGE_MODEL",
    "ENV_JUDGE_IMAGE_MODEL",
    "ENV_JUDGE_MODEL",
    "ROLE_IMAGE_JUDGE",
    "ROLE_PRIMARY",
    "ROLE_TEXT_JUDGE",
    "resolve_image_judge_llm_config",
    "resolve_llm_config_for_role",
    "resolve_primary_llm_config",
    "resolve_role_model_name",
    "resolve_text_judge_llm_config",
]
