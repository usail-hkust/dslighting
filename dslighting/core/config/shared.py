"""
Shared configuration utilities for DSLighting.

This module provides common configuration building utilities used across
ConfigBuilder and API entrypoints to avoid code duplication.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


# Valid workflow names - shared constant
VALID_WORKFLOW_NAMES = frozenset({
    "aide", "autokaggle", "data_interpreter",
    "automind", "dsagent", "deepanalyze"
})

# Workflow to config key mapping - shared constant
WORKFLOW_TO_CONFIG_KEY = {
    "autokaggle": "agent.autokaggle",
    "aide": "agent.search",
    "data_interpreter": "agent.search",
    "deepanalyze": "agent.search",
    "automind": "workflow.params",
    "dsagent": "workflow.params",
}


def is_valid_workflow_name(workflow: str) -> bool:
    """
    Check if a workflow name is valid.

    Args:
        workflow: Workflow name to validate

    Returns:
        True if workflow is valid, False otherwise
    """
    return workflow in VALID_WORKFLOW_NAMES


def get_config_key_for_workflow(workflow: str) -> str:
    """
    Get the config key for a given workflow name.

    Args:
        workflow: Workflow name

    Returns:
        Config key path (e.g., "agent.search")

    Raises:
        ValueError: If workflow is not recognized
    """
    if workflow not in WORKFLOW_TO_CONFIG_KEY:
        raise ValueError(
            f"Unknown workflow: {workflow}. "
            f"Valid workflows: {', '.join(sorted(VALID_WORKFLOW_NAMES))}"
        )
    return WORKFLOW_TO_CONFIG_KEY[workflow]


def deep_merge(
    base: Dict[str, Any],
    override: Dict[str, Any],
    path: str = ""
) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with override values
        path: Current path (for error messages)

    Returns:
        Merged dictionary

    Example:
        >>> base = {"a": {"b": 1, "c": 2}}
        >>> override = {"a": {"b": 10}, "d": 3}
        >>> deep_merge(base, override)
        {"a": {"b": 10, "c": 2}, "d": 3}
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(
                result[key],
                value,
                f"{path}.{key}" if path else key
            )
        else:
            result[key] = value

    return result


def get_workflow_for_benchmark(benchmark_name: str, default: str = "aide") -> str:
    """
    Get the recommended workflow for a benchmark type.

    Args:
        benchmark_name: Name of the benchmark
        default: Default workflow if no match

    Returns:
        Recommended workflow name
    """
    benchmark_lower = benchmark_name.lower()

    if "mle" in benchmark_lower or "kaggle" in benchmark_lower:
        return "autokaggle"
    elif "science" in benchmark_lower:
        return "data_interpreter"
    elif "da" in benchmark_lower:
        return "dsagent"

    return default


def apply_env_overrides(
    config: Dict[str, Any],
    env_mapping: Dict[str, tuple]
) -> Dict[str, Any]:
    """
    Apply environment variable overrides to config.

    Args:
        config: Base configuration dictionary
        env_mapping: Mapping of env var names to (config_path, converter) tuples
                    where config_path is a dot-separated path and converter
                    is a function to convert the string value

    Returns:
        Configuration with environment overrides applied

    Example:
        >>> env_mapping = {
        ...     "LLM_MODEL": ("llm.model", str),
        ...     "LLM_TEMPERATURE": ("llm.temperature", float),
        ... }
        >>> apply_env_overrides({"llm": {}}, env_mapping)
    """
    import os

    result = config.copy()

    for env_var, (config_path, converter) in env_mapping.items():
        value = os.getenv(env_var)
        if value is None:
            continue

        # Navigate to the target location
        parts = config_path.split(".")
        current = result

        # Create nested dicts if needed
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                logger.warning(
                    f"Cannot apply env override: {'.'.join(parts[:-1])} is not a dict"
                )
                break
            current = current[part]
        else:
            # Apply the value
            try:
                converted_value = converter(value)
                current[parts[-1]] = converted_value
                logger.debug(
                    f"Applied env override: {config_path} = {converted_value} "
                    f"(from {env_var})"
                )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Failed to convert env var {env_var}={value!r}: {e}"
                )

    return result
