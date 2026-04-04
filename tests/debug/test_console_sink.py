from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dslighting.debug.events import DebugEvent
from dslighting.debug.formatters.human import HumanStructuredFormatter
from dslighting.debug.models import LLMCallContext, RunDebugContext
from dslighting.debug.payload_store import PayloadStore
from dslighting.debug.redaction import RedactionPolicy
from dslighting.debug.sinks import console as console_module
from dslighting.debug.sinks.console import ConsoleSink


def _event(
    event_type: str,
    call_id: str,
    *,
    payload_refs=None,
) -> DebugEvent:
    return DebugEvent(
        schema_version=1,
        event_id=f"{call_id}_{event_type}",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        event_type=event_type,
        summary=event_type,
        run=RunDebugContext(session_id="dbg", run_id="run1", task_id="task1", workflow_name="aide"),
        llm=LLMCallContext(logical_call_id=call_id, model="gpt-test"),
        payload_refs=payload_refs or {},
    )


@pytest.mark.asyncio
async def test_console_sink_marks_reused_payloads(monkeypatch) -> None:
    blocks: list[str] = []
    monkeypatch.setattr(console_module.debug_logger, "info", lambda message, *args, **kwargs: blocks.append(message))

    store = PayloadStore(output_dir=None, redaction_policy=RedactionPolicy(), dedupe_enabled=True)
    sink = ConsoleSink(formatter=HumanStructuredFormatter(), partial_flush_timeout_seconds=60.0)

    first_ref = store.store(kind="request_messages", body=[{"role": "user", "content": "hello"}])
    second_ref = store.store(kind="request_messages", body=[{"role": "user", "content": "hello"}])

    await sink.handle(_event("llm.call.started", "call_1"), store)
    await sink.handle(
        _event("llm.request.prepared", "call_1", payload_refs={"request_messages": first_ref}),
        store,
    )
    await sink.handle(_event("llm.call.completed", "call_1"), store)

    await sink.handle(_event("llm.call.started", "call_2"), store)
    await sink.handle(
        _event("llm.request.prepared", "call_2", payload_refs={"request_messages": second_ref}),
        store,
    )
    await sink.handle(_event("llm.call.completed", "call_2"), store)

    assert len(blocks) == 2
    assert "request_messages: payload=" in blocks[0]
    assert "reused" in blocks[1]


@pytest.mark.asyncio
async def test_console_sink_renders_litellm_style_fields(monkeypatch) -> None:
    blocks: list[str] = []
    monkeypatch.setattr(console_module.debug_logger, "info", lambda message, *args, **kwargs: blocks.append(message))

    store = PayloadStore(output_dir=None, redaction_policy=RedactionPolicy(), dedupe_enabled=True)
    sink = ConsoleSink(formatter=HumanStructuredFormatter(use_color=False), partial_flush_timeout_seconds=60.0)

    request_ref = store.store(kind="request_messages", body=[{"role": "user", "content": "hello"}])
    event = DebugEvent(
        schema_version=1,
        event_id="call_1_req",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        event_type="llm.request.prepared",
        summary="Prepared LLM request",
        run=RunDebugContext(session_id="dbg", run_id="run1", task_id="task1", workflow_name="aide"),
        llm=LLMCallContext(logical_call_id="call_1", model="gpt-test"),
        payload_refs={"request_messages": request_ref},
        tags={
            "provider": "openai",
            "api_base": "https://example.com/v1",
            "temperature": 1.0,
        },
    )

    await sink.handle(_event("llm.call.started", "call_1"), store)
    await sink.handle(event, store)
    await sink.handle(_event("llm.call.completed", "call_1"), store)

    assert len(blocks) == 1
    assert "Provider: openai" in blocks[0]
    assert "API Base: https://example.com/v1" in blocks[0]
    assert "Temperature: 1.0" in blocks[0]
