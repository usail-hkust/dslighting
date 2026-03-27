"""Bridge unified logging configuration to the existing debug runtime."""

from __future__ import annotations

import logging

from dslighting.debug.api import init_debug
from dslighting.debug.session import DebugSession
from dslighting.logging.config import LoggingConfig


_logger = logging.getLogger("dslighting.logging")


def install_trace_runtime(config: LoggingConfig) -> DebugSession | None:
    enabled = config.trace_llm or config.trace_tools or config.trace_sandbox
    if not enabled:
        return init_debug(enabled=False, console_output=False)

    profile = "raw" if config.provider_raw else "full"
    output_dir = config.resolved_output_dir()
    session = init_debug(
        enabled=True,
        profile=profile,
        output_dir=str(output_dir) if output_dir is not None else None,
        console_output=config.console,
    )
    return session
