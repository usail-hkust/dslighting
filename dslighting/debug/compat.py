"""Legacy compatibility layer for the deprecated ``debug_logger`` API.

This module exists only to preserve older imports while the public logging API
has moved to ``dslighting.configure_logging(...)``. New code should not build
on the wrappers defined here.
"""

from __future__ import annotations

import asyncio
import logging
import warnings
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from dslighting.debug.api import get_debug_session, init_debug
from dslighting.debug.context import get_effective_debug_context
from dslighting.debug.events import DebugEvent
from dslighting.debug.models import LLMCallContext

debug_logger = logging.getLogger("dslighting.debug")


class DebugLevel(Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    VERBOSE = "verbose"


class LLMDebugLogger:
    """Legacy wrapper around ``DebugSession`` kept for backward compatibility.

    The preferred entrypoint for new code is ``configure_logging(...)``. This
    class intentionally preserves the old object shape for callers that still
    depend on the deprecated debug logger API.
    """

    def __init__(
        self,
        *,
        enabled: bool = False,
        level: DebugLevel = DebugLevel.BASIC,
        output_dir: Optional[Path] = None,
        console_output: bool = True,
    ) -> None:
        profile = _profile_from_level(level)
        self.level = level
        self.console_output = console_output
        self.output_dir = output_dir
        self._session = init_debug(
            enabled=enabled,
            profile=profile,
            output_dir=str(output_dir) if output_dir else None,
            console_output=console_output,
        )

    @property
    def enabled(self) -> bool:
        return bool(self._session and self._session.enabled)

    @property
    def log_file(self) -> Path | None:
        if self._session is None or self._session.output_dir is None:
            return None
        return self._session.output_dir / "events.jsonl"

    def log_request(
        self,
        request_id: str,
        model: str,
        messages: list,
        parameters: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        session = self._session
        if session is None or not session.enabled:
            return
        request_ref = session.store_payload(kind="request_messages", body=messages)
        context = get_effective_debug_context(session.session_id)
        event = DebugEvent(
            schema_version=session.config.schema_version,
            event_id=f"legacy_req_{request_id}",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            event_type="llm.request.prepared",
            summary="Legacy debug request",
            run=context.run,
            node=context.node,
            llm=LLMCallContext(logical_call_id=request_id, model=model),
            payload_refs={"request_messages": request_ref},
            tags={"parameters": parameters, "metadata": metadata or {}},
        )
        _schedule_emit(session.emit(event))

    def log_response(
        self,
        request_id: str,
        model: str,
        response: dict[str, Any],
        duration: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        session = self._session
        if session is None or not session.enabled:
            return
        response_ref = session.store_payload(kind="response_body", body=response)
        context = get_effective_debug_context(session.session_id)
        event = DebugEvent(
            schema_version=session.config.schema_version,
            event_id=f"legacy_resp_{request_id}",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            event_type="llm.call.completed",
            summary="Legacy debug response",
            run=context.run,
            node=context.node,
            llm=LLMCallContext(logical_call_id=request_id, model=model),
            payload_refs={"response_body": response_ref},
            metrics={"duration_seconds": duration},
            tags={"metadata": metadata or {}},
        )
        _schedule_emit(session.emit(event))

    def log_error(
        self,
        request_id: str,
        model: str,
        error: Exception,
        duration: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        session = self._session
        if session is None or not session.enabled:
            return
        error_ref = session.store_payload(kind="error_body", body={"error": str(error), "repr": repr(error)})
        context = get_effective_debug_context(session.session_id)
        event = DebugEvent(
            schema_version=session.config.schema_version,
            event_id=f"legacy_err_{request_id}",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            event_type="llm.call.failed",
            summary="Legacy debug error",
            run=context.run,
            node=context.node,
            llm=LLMCallContext(logical_call_id=request_id, model=model),
            payload_refs={"error_body": error_ref},
            metrics={"duration_seconds": duration},
            tags={"metadata": metadata or {}},
            error={"type": type(error).__name__, "message": str(error)},
        )
        _schedule_emit(session.emit(event))

    def get_statistics(self) -> dict[str, Any]:
        if self._session is None:
            return {}
        return self._session.get_statistics()

    def print_statistics(self) -> None:
        stats = self.get_statistics()
        debug_logger.info("=" * 50)
        debug_logger.info("LLM Debug Session Statistics")
        debug_logger.info("=" * 50)
        for key, value in stats.items():
            debug_logger.info("%s: %s", key, value)
        debug_logger.info("=" * 50)


_global_debug_logger: Optional[LLMDebugLogger] = None


def get_debug_logger() -> Optional[LLMDebugLogger]:
    return _global_debug_logger


def init_debug_logger(
    enabled: bool = False,
    level: str = "basic",
    output_dir: Optional[str] = None,
    console_output: bool = True,
) -> LLMDebugLogger:
    """Initialize the deprecated legacy debug logger wrapper.

    New code should use ``configure_logging(trace_llm=...)`` instead.
    """
    warnings.warn(
        "init_debug_logger() is deprecated; use configure_logging(trace_llm=...) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _global_debug_logger
    _global_debug_logger = LLMDebugLogger(
        enabled=enabled,
        level=DebugLevel(level),
        output_dir=Path(output_dir) if output_dir else None,
        console_output=console_output,
    )
    return _global_debug_logger


def _profile_from_level(level: DebugLevel) -> str:
    if level == DebugLevel.BASIC:
        return "summary"
    if level == DebugLevel.DETAILED:
        return "detailed"
    return "full"


def _schedule_emit(coro) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
    else:
        loop.create_task(coro)
