"""Shared runtime configuration normalizers.

These helpers intentionally use framework-level names. Workflow-specific
adapters can consume the resulting config, but public parameters should remain
under ``agent_runtime`` and ``output_contract``.
"""

from __future__ import annotations

from typing import Any

AGENT_RUNTIME_ALLOWED_KEYS = frozenset({"max_steps", "observation", "context"})
AGENT_RUNTIME_OBSERVATION_ALLOWED_KEYS = frozenset(
    {"max_tokens", "head_tokens", "tail_tokens", "max_chars"}
)
AGENT_RUNTIME_CONTEXT_ALLOWED_STRATEGIES = frozenset(
    {"recent_turns", "summarize_old_turns", "hybrid"}
)
AGENT_RUNTIME_CONTEXT_ALLOWED_KEYS = frozenset(
    {
        "strategy",
        "max_history_chars",
        "keep_recent_turns",
        "max_observation_chars",
        "summary_trigger_turns",
        "summary_max_chars",
        "keep_latest_feedback_only",
        "max_feedback_retries",
        "recent_observation_window",
        "max_feedback_chars",
    }
)
OUTPUT_CONTRACT_ALLOWED_KEYS = frozenset(
    {
        "require_output_before_completion",
        "missing_output_feedback_retries",
        "max_preview_rows",
        "max_candidate_files",
        "allow_runner_fallback",
    }
)

# Old public names that should now fail with an explicit migration hint.
LEGACY_REACT_RUNTIME_KEYS = frozenset(
    {"max_steps", "obs_max_tokens", "obs_head_tokens", "obs_tail_tokens", "context"}
)


def _coerce_bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise ValueError(f"`{field_name}` must be a boolean")


def _coerce_int(
    value: Any,
    *,
    field_name: str,
    minimum: int,
) -> int:
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"`{field_name}` must be an integer") from exc
    if coerced < minimum:
        comparator = ">=" if minimum == 0 else ">"
        target = minimum if minimum == 0 else minimum - 1
        raise ValueError(f"`{field_name}` must be {comparator} {target}")
    return coerced


def normalize_agent_runtime_context_params(
    params: dict[str, Any] | None,
    *,
    source: str = "agent_runtime.context",
) -> dict[str, Any]:
    if params is None:
        return {}
    if not isinstance(params, dict):
        raise TypeError(f"`{source}` must be a dictionary")

    unknown = sorted(key for key in params if key not in AGENT_RUNTIME_CONTEXT_ALLOWED_KEYS)
    if unknown:
        raise ValueError(
            f"Unknown agent runtime context parameters in `{source}`: {unknown}. "
            f"Allowed keys: {sorted(AGENT_RUNTIME_CONTEXT_ALLOWED_KEYS)}"
        )

    normalized: dict[str, Any] = {}
    for key, value in params.items():
        field_name = f"{source}.{key}"
        if key == "strategy":
            strategy = str(value).strip()
            if strategy not in AGENT_RUNTIME_CONTEXT_ALLOWED_STRATEGIES:
                raise ValueError(
                    f"`{field_name}` must be one of: "
                    f"{sorted(AGENT_RUNTIME_CONTEXT_ALLOWED_STRATEGIES)}"
                )
            normalized[key] = strategy
        elif key == "keep_latest_feedback_only":
            normalized[key] = _coerce_bool(value, field_name=field_name)
        elif key == "max_feedback_retries":
            normalized[key] = _coerce_int(value, field_name=field_name, minimum=0)
        else:
            normalized[key] = _coerce_int(value, field_name=field_name, minimum=1)
    return normalized


def normalize_agent_runtime_params(
    params: dict[str, Any] | None,
    *,
    source: str = "agent_runtime",
) -> dict[str, Any]:
    if params is None:
        return {}
    if not isinstance(params, dict):
        raise TypeError(f"`{source}` must be a dictionary")

    unknown = sorted(key for key in params if key not in AGENT_RUNTIME_ALLOWED_KEYS)
    if unknown:
        raise ValueError(
            f"Unknown agent runtime parameters in `{source}`: {unknown}. "
            f"Allowed keys: {sorted(AGENT_RUNTIME_ALLOWED_KEYS)}"
        )

    normalized: dict[str, Any] = {}
    if "max_steps" in params:
        normalized["max_steps"] = _coerce_int(
            params["max_steps"],
            field_name=f"{source}.max_steps",
            minimum=1,
        )

    observation = params.get("observation")
    if observation is not None:
        if not isinstance(observation, dict):
            raise TypeError(f"`{source}.observation` must be a dictionary")
        unknown_observation = sorted(
            key for key in observation if key not in AGENT_RUNTIME_OBSERVATION_ALLOWED_KEYS
        )
        if unknown_observation:
            raise ValueError(
                f"Unknown agent runtime observation parameters in `{source}.observation`: "
                f"{unknown_observation}. Allowed keys: "
                f"{sorted(AGENT_RUNTIME_OBSERVATION_ALLOWED_KEYS)}"
            )

        normalized_observation: dict[str, Any] = {}
        for key, value in observation.items():
            normalized_observation[key] = _coerce_int(
                value,
                field_name=f"{source}.observation.{key}",
                minimum=1,
            )
        max_tokens = normalized_observation.get("max_tokens", 4000)
        head_tokens = normalized_observation.get("head_tokens", 2000)
        tail_tokens = normalized_observation.get("tail_tokens", 2000)
        if head_tokens + tail_tokens > max_tokens:
            raise ValueError(
                f"`{source}.observation.head_tokens + "
                f"{source}.observation.tail_tokens` must be <= "
                f"`{source}.observation.max_tokens`"
            )
        normalized["observation"] = normalized_observation

    if "context" in params:
        normalized["context"] = normalize_agent_runtime_context_params(
            params["context"],
            source=f"{source}.context",
        )

    return normalized


def normalize_output_contract_params(
    params: dict[str, Any] | None,
    *,
    source: str = "output_contract",
) -> dict[str, Any]:
    if params is None:
        return {}
    if not isinstance(params, dict):
        raise TypeError(f"`{source}` must be a dictionary")

    unknown = sorted(key for key in params if key not in OUTPUT_CONTRACT_ALLOWED_KEYS)
    if unknown:
        raise ValueError(
            f"Unknown output contract parameters in `{source}`: {unknown}. "
            f"Allowed keys: {sorted(OUTPUT_CONTRACT_ALLOWED_KEYS)}"
        )

    normalized: dict[str, Any] = {}
    for key, value in params.items():
        field_name = f"{source}.{key}"
        if key in {"require_output_before_completion", "allow_runner_fallback"}:
            normalized[key] = _coerce_bool(value, field_name=field_name)
        elif key == "missing_output_feedback_retries":
            normalized[key] = _coerce_int(value, field_name=field_name, minimum=0)
        else:
            normalized[key] = _coerce_int(value, field_name=field_name, minimum=1)
    return normalized


__all__ = [
    "AGENT_RUNTIME_ALLOWED_KEYS",
    "AGENT_RUNTIME_CONTEXT_ALLOWED_KEYS",
    "AGENT_RUNTIME_CONTEXT_ALLOWED_STRATEGIES",
    "AGENT_RUNTIME_OBSERVATION_ALLOWED_KEYS",
    "LEGACY_REACT_RUNTIME_KEYS",
    "OUTPUT_CONTRACT_ALLOWED_KEYS",
    "normalize_agent_runtime_context_params",
    "normalize_agent_runtime_params",
    "normalize_output_contract_params",
]
