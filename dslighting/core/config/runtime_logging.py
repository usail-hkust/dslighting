"""Helpers for logging resolved runtime configuration from DSLightingConfig."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dslighting.config import DSLightingConfig


def log_resolved_runtime_config(
    logger: logging.Logger,
    *,
    config: "DSLightingConfig",
    source: str,
    task_id: str | None = None,
) -> None:
    """Log runtime configuration from the resolved config, not constructor defaults."""
    if not logger.isEnabledFor(logging.DEBUG):
        return

    suffix = f" for task '{task_id}'" if task_id else ""
    logger.debug("%s runtime resolved from config%s", source, suffix)
    logger.debug("  - Workflow: %s", getattr(config.workflow, "name", "N/A"))

    llm = getattr(config, "llm", None)
    if llm is not None:
        logger.debug("  - Model: %s", getattr(llm, "model", "N/A"))
        provider = getattr(llm, "provider", None)
        if provider:
            logger.debug("  - Provider: %s", provider)
        api_base = getattr(llm, "api_base", None)
        if api_base:
            logger.debug("  - API Base: %s", api_base)

    sandbox = getattr(config, "sandbox", None)
    if sandbox is not None:
        logger.debug("  - Timeout: %ss", getattr(sandbox, "timeout", "N/A"))

    data_analysis = getattr(config, "data_analysis", None)
    if data_analysis is not None:
        logger.debug("  - Data analyzer enabled: %s", getattr(data_analysis, "enabled", True))
        logger.debug("  - Data analyzer cache: %s", getattr(data_analysis, "cache_enabled", True))
        logger.debug("  - Data report budget: %s", getattr(data_analysis, "max_report_chars", None))

    run = getattr(config, "run", None)
    if run is not None:
        logger.debug("  - Keep workspace: %s", getattr(run, "keep_all_workspaces", False))
        logger.debug(
            "  - Keep workspace on failure: %s",
            getattr(run, "keep_workspace_on_failure", False),
        )
