"""Public API for debug observability."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dslighting.debug.context import debug_scope
from dslighting.debug.models import DebugSessionConfig
from dslighting.debug.session import DebugSession

if TYPE_CHECKING:
    from dslighting.debug.litellm_bridge import DSLightingLiteLLMLogger

_global_debug_session: Optional[DebugSession] = None
_debug_logger = logging.getLogger("dslighting.debug")
_HANDLER_MARKER = "_dslighting_debug_handler"
_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "httpcore.connection",
    "httpcore.http11",
    "httpcore.connection_pool",
    "openai",
)
_LITELLM_LOGGERS = ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy")
_litellm_bridge: "DSLightingLiteLLMLogger | None" = None


def init_debug(
    *,
    enabled: bool = False,
    profile: str = "full",
    output_dir: str | None = None,
    console_output: bool = True,
) -> DebugSession:
    global _global_debug_session

    _dispose_previous_session()
    _configure_provider_debug_policy(enabled=enabled, profile=profile)
    _configure_debug_logger(console_output=console_output)
    _global_debug_session = DebugSession(
        DebugSessionConfig(
            enabled=enabled,
            profile=profile,
            console_output=console_output,
            output_dir=Path(output_dir) if output_dir else None,
        )
    )
    if enabled:
        _debug_logger.info("LLM debug enabled (profile=%s)", profile)
        if _global_debug_session.output_dir is not None:
            _debug_logger.info("Debug output dir: %s", _global_debug_session.output_dir)
    return _global_debug_session


def get_debug_session() -> Optional[DebugSession]:
    return _global_debug_session


async def emit_debug_event(event) -> None:
    session = get_debug_session()
    if session is None:
        return
    await session.emit(event)


def _configure_debug_logger(*, console_output: bool) -> None:
    _debug_logger.setLevel(logging.INFO)
    _debug_logger.propagate = False
    for handler in list(_debug_logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            _debug_logger.removeHandler(handler)
    if console_output:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(message)s"))
        setattr(handler, _HANDLER_MARKER, True)
        _debug_logger.addHandler(handler)


def _configure_provider_debug_policy(*, enabled: bool, profile: str) -> None:
    provider_raw = enabled and _provider_raw_enabled(profile)
    os.environ["LITELLM_LOG"] = "DEBUG" if provider_raw else "WARNING"
    _configure_standard_loggers(provider_raw=provider_raw)
    _configure_litellm_runtime(enabled=enabled, provider_raw=provider_raw)


def _provider_raw_enabled(profile: str) -> bool:
    return profile in {"provider_raw", "provider-debug", "raw"}


def _configure_standard_loggers(*, provider_raw: bool) -> None:
    third_party_level = logging.WARNING
    litellm_level = logging.DEBUG if provider_raw else logging.WARNING
    for name in _NOISY_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(third_party_level)
        for handler in logger.handlers:
            handler.setLevel(third_party_level)
    for name in _LITELLM_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(litellm_level)
        logger.propagate = False
        for handler in logger.handlers:
            handler.setLevel(litellm_level)


def _configure_litellm_runtime(*, enabled: bool, provider_raw: bool) -> None:
    global _litellm_bridge

    try:
        import litellm
        from dslighting.debug.litellm_bridge import DSLightingLiteLLMLogger
    except Exception:
        _litellm_bridge = None
        return

    litellm.telemetry = False
    litellm.turn_off_message_logging = False
    litellm.log_raw_request_response = provider_raw

    bridge = DSLightingLiteLLMLogger(provider_raw=provider_raw)
    _remove_litellm_bridge(litellm)
    if enabled:
        litellm.callbacks.append(bridge)
        _litellm_bridge = bridge
    else:
        _litellm_bridge = None


def _remove_litellm_bridge(litellm_module) -> None:
    from dslighting.debug.litellm_bridge import DSLightingLiteLLMLogger

    callback_attrs = [
        "callbacks",
        "input_callback",
        "success_callback",
        "failure_callback",
        "_async_input_callback",
        "_async_success_callback",
        "_async_failure_callback",
    ]
    for attr in callback_attrs:
        callbacks = getattr(litellm_module, attr, None)
        if not isinstance(callbacks, list):
            continue
        callbacks[:] = [cb for cb in callbacks if not isinstance(cb, DSLightingLiteLLMLogger)]


def _dispose_previous_session() -> None:
    global _global_debug_session
    if _global_debug_session is None:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_global_debug_session.close())
    else:
        loop.create_task(_global_debug_session.close())
    _global_debug_session = None


__all__ = [
    "debug_scope",
    "emit_debug_event",
    "get_debug_session",
    "init_debug",
]
