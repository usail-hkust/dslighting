"""Structured runtime event helpers for unified logging."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from dslighting.debug.api import get_debug_session
from dslighting.debug.context import get_effective_debug_context
from dslighting.debug.events import DebugEvent
from dslighting.logging.setup import get_logging_controller


def _controller_trace_enabled(flag_name: str) -> bool:
    controller = get_logging_controller()
    if controller is None or controller.closed or controller.config is None:
        return False
    return bool(getattr(controller.config, flag_name, False))


def is_tool_trace_enabled() -> bool:
    return _controller_trace_enabled("trace_tools")


def is_sandbox_trace_enabled() -> bool:
    return _controller_trace_enabled("trace_sandbox")


def emit_runtime_event(
    event_type: str,
    summary: str,
    *,
    tags: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    payloads: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    session = get_debug_session()
    if session is None or not session.enabled:
        return

    context = get_effective_debug_context(session.session_id)
    payload_refs = {}
    for label, body in (payloads or {}).items():
        payload_refs[label] = session.store_payload(kind=label, body=body)

    event = DebugEvent(
        schema_version=session.config.schema_version,
        event_id=f"{event_type.replace('.', '_')}_{uuid4().hex[:12]}",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        event_type=event_type,
        summary=summary,
        run=context.run,
        node=context.node,
        payload_refs=payload_refs,
        metrics=metrics or {},
        tags=tags or {},
        error=error,
    )
    _schedule_emit(session.emit(event))


def _schedule_emit(coro) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
    else:
        loop.create_task(coro)
