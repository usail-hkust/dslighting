# cost.py

"""
Cost tracking and model pricing configuration for LLM services.

Provides:
- Custom model pricing loading from YAML configuration
- Cost-related utilities

Usage:
    Call init_model_pricing() to load custom model pricing during application startup.
    The pricing is automatically applied to LiteLLM when using LLMService.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Global storage for custom model pricing
CUSTOM_MODEL_PRICING: dict[str, Any] = {}


def load_custom_model_pricing(config_path: str | None = None) -> dict[str, Any]:
    """
    Load custom model pricing configuration from config.yaml file.

    Args:
        config_path: Optional path to config.yaml. If not provided,
                    defaults to the project's config.yaml.

    Returns:
        Dictionary of custom model pricing configurations
    """
    try:
        if config_path is None:
            # Get the path to the config.yaml file relative to this module
            current_dir = Path(__file__).parent
            framework_dir = current_dir.parent.parent  # Go up to dslighting
            config_yaml_path = framework_dir / "config.yaml"
        else:
            config_yaml_path = Path(config_path)

        if config_yaml_path.exists():
            with open(config_yaml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("custom_model_pricing", {})
        else:
            # Changed to debug to avoid confusing warnings for pip-installed packages
            logger.debug(
                f"Config file not found at {config_yaml_path} (this is expected for pip-installed packages)"
            )
            return {}
    except Exception as e:
        logger.error(f"Failed to load cost configuration: {e}")
        return {}


def apply_custom_model_pricing(pricing: dict[str, Any] | None = None) -> None:
    """
    Apply custom model pricing to LiteLLM.

    Args:
        pricing: Dictionary of custom model pricing. If None, loads from default config.
    """
    global CUSTOM_MODEL_PRICING

    if pricing is None:
        pricing = load_custom_model_pricing()

    CUSTOM_MODEL_PRICING = pricing

    if CUSTOM_MODEL_PRICING:
        import litellm

        litellm.model_cost.update(CUSTOM_MODEL_PRICING)
        logger.info(
            f"Loaded custom model pricing for {len(CUSTOM_MODEL_PRICING)} models"
        )


def init_model_pricing() -> dict[str, Any]:
    """
    Initialize custom model pricing from config.

    This function should be called during application startup to ensure
    custom pricing is applied before any LLM calls are made.

    Returns:
        The loaded custom model pricing dictionary.
    """
    pricing = load_custom_model_pricing()
    if pricing:
        apply_custom_model_pricing(pricing)
    return pricing
