"""Public unified logging entrypoint."""

from __future__ import annotations

import logging

from dslighting.logging.config import LoggingConfig
from dslighting.logging.controller import LoggingController
from dslighting.logging.stdlib import install_stdlib_handlers
from dslighting.logging.trace import install_trace_runtime


_logger = logging.getLogger("dslighting.logging")
_global_controller: LoggingController | None = None


def configure_logging(
    *,
    level: str | None = None,
    format: str | None = None,
    console: bool | None = None,
    file: str | None = None,
    trace_llm: bool | None = None,
    trace_tools: bool | None = None,
    trace_sandbox: bool | None = None,
    output_dir: str | None = None,
    provider_raw: bool | None = None,
    force: bool = False,
) -> LoggingController:
    global _global_controller

    env_config = LoggingConfig.from_env()
    config = LoggingConfig(
        level=level if level is not None else env_config.level,
        format=format if format is not None else env_config.format,
        console=console if console is not None else env_config.console,
        file=file if file is not None else env_config.file,
        trace_llm=trace_llm if trace_llm is not None else env_config.trace_llm,
        trace_tools=trace_tools if trace_tools is not None else env_config.trace_tools,
        trace_sandbox=trace_sandbox if trace_sandbox is not None else env_config.trace_sandbox,
        output_dir=output_dir if output_dir is not None else env_config.output_dir,
        provider_raw=provider_raw if provider_raw is not None else env_config.provider_raw,
        force=force,
    )
    config.validate()

    if _global_controller is not None and not _global_controller.closed:
        if not force:
            _logger.warning("configure_logging() called again without force=True; reusing current configuration")
            return _global_controller
        _global_controller.close()

    handlers, target_logger_names = install_stdlib_handlers(config)
    session = install_trace_runtime(config)
    if not config.console and config.file is None and config.output_dir is None:
        _logger.warning("configure_logging() produced no visible or persisted outputs")

    session_path = str(session.output_dir) if session is not None and session.output_dir is not None else None
    controller = LoggingController(
        debug_session=session,
        installed_handlers=handlers,
        session_path=session_path,
        target_logger_names=target_logger_names,
        config=config,
    )
    _global_controller = controller
    return controller


def get_logging_controller() -> LoggingController | None:
    return _global_controller
