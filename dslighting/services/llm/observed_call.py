"""Shared LiteLLM calling helpers with DSLighting observability hooks."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import time
import uuid
from typing import Any

from dslighting.debug.api import get_debug_session
from dslighting.debug.context import debug_scope, get_effective_debug_context
from dslighting.debug.events import DebugEvent
from dslighting.debug.models import LLMCallContext


@dataclass(frozen=True)
class ObservedCompletionResult:
    response: Any
    llm_context: LLMCallContext
    duration_seconds: float
    usage: dict[str, Any]
    serialized_response: dict[str, Any]


def build_llm_context(
    *,
    model: str,
    provider: str | None = None,
    response_mode: str = "text",
    semantic_attempt: int = 1,
    transport_attempt: int = 1,
    validation_attempt: int = 0,
    logical_call_id: str | None = None,
) -> LLMCallContext:
    return LLMCallContext(
        logical_call_id=logical_call_id or uuid.uuid4().hex,
        model=model,
        provider=provider,
        response_mode=response_mode,
        semantic_attempt=semantic_attempt,
        transport_attempt=transport_attempt,
        validation_attempt=validation_attempt,
    )


def serialize_response_for_debug(response: Any) -> dict[str, Any]:
    """Convert LiteLLM response objects into JSON-serializable payloads."""
    if response is None:
        return {}
    if isinstance(response, dict):
        return response

    for method_name in ("model_dump", "dict"):
        method = getattr(response, method_name, None)
        if callable(method):
            try:
                payload = method()
                if isinstance(payload, dict):
                    return payload
            except Exception:
                pass

    payload: dict[str, Any] = {}
    choices = getattr(response, "choices", None)
    if choices is not None:
        serialized_choices: list[dict[str, Any]] = []
        for choice in choices:
            if isinstance(choice, dict):
                message = choice.get("message", {})
                serialized_choices.append(
                    {
                        "message": {
                            "role": message.get("role", "assistant"),
                            "content": message.get("content", ""),
                        }
                    }
                )
                continue
            message = getattr(choice, "message", None)
            serialized_choices.append(
                {
                    "message": {
                        "role": getattr(message, "role", "assistant"),
                        "content": getattr(message, "content", ""),
                    }
                }
            )
        payload["choices"] = serialized_choices

    usage = extract_usage(response)
    if usage:
        payload["usage"] = usage

    return payload


def extract_usage(response: Any) -> dict[str, Any]:
    """Extract token usage fields from a LiteLLM response in a JSON-safe format."""
    usage = getattr(response, "usage", None)
    if not usage:
        return {}

    payload: dict[str, Any] = {
        "prompt_tokens": _safe_int(getattr(usage, "prompt_tokens", None)),
        "completion_tokens": _safe_int(getattr(usage, "completion_tokens", None)),
        "total_tokens": _safe_int(getattr(usage, "total_tokens", None)),
        "prompt_tokens_cost": _safe_float(getattr(usage, "prompt_tokens_cost", None)),
        "completion_tokens_cost": _safe_float(getattr(usage, "completion_tokens_cost", None)),
    }
    total_tokens_cost = _safe_float(getattr(usage, "total_tokens_cost", None))
    if total_tokens_cost is None:
        prompt_cost = payload.get("prompt_tokens_cost")
        completion_cost = payload.get("completion_tokens_cost")
        if prompt_cost is not None and completion_cost is not None:
            total_tokens_cost = prompt_cost + completion_cost
    payload["total_tokens_cost"] = total_tokens_cost
    return payload


def extract_response_content(response: Any) -> str:
    if not response or not hasattr(response, "choices") or not response.choices:
        raise ValueError("Invalid response structure: missing choices")
    try:
        content = response.choices[0].message.content
    except (IndexError, AttributeError) as exc:
        raise ValueError(f"Invalid response structure: {exc}") from exc
    return "" if content is None else str(content)


def attach_debug_metadata(*, kwargs: dict[str, Any], llm_context: LLMCallContext) -> None:
    metadata = kwargs.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        kwargs["metadata"] = metadata
    metadata["dslighting_debug"] = {
        "logical_call_id": llm_context.logical_call_id,
        "model": llm_context.model,
        "provider": llm_context.provider,
        "response_mode": llm_context.response_mode,
        "semantic_attempt": llm_context.semantic_attempt,
        "transport_attempt": llm_context.transport_attempt,
        "validation_attempt": llm_context.validation_attempt,
    }


def sanitize_messages_for_debug(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            sanitized.append(message)
            continue
        item = dict(message)
        item["content"] = _sanitize_message_content(item.get("content"))
        sanitized.append(item)
    return sanitized


async def emit_llm_event(
    event_type: str,
    summary: str,
    *,
    llm_context: LLMCallContext,
    payloads: dict[str, tuple[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
    tags: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    session = get_debug_session()
    event = _build_debug_event(
        session=session,
        event_type=event_type,
        summary=summary,
        llm_context=llm_context,
        payloads=payloads,
        metrics=metrics,
        tags=tags,
        error=error,
    )
    if session is None or event is None:
        return
    await session.emit(event)


def emit_llm_event_sync(
    event_type: str,
    summary: str,
    *,
    llm_context: LLMCallContext,
    payloads: dict[str, tuple[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
    tags: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    session = get_debug_session()
    event = _build_debug_event(
        session=session,
        event_type=event_type,
        summary=summary,
        llm_context=llm_context,
        payloads=payloads,
        metrics=metrics,
        tags=tags,
        error=error,
    )
    if session is None or event is None:
        return
    _schedule_emit(session.emit(event))


def completion_with_observability(
    *,
    model: str,
    provider: str | None,
    api_base: str | None,
    api_key: str | None,
    messages: list[dict[str, Any]],
    response_format: dict[str, Any] | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_mode: str = "text",
    llm_context: LLMCallContext | None = None,
    extra_tags: dict[str, Any] | None = None,
) -> ObservedCompletionResult:
    import litellm

    context = llm_context or build_llm_context(model=model, provider=provider, response_mode=response_mode)
    emit_llm_event_sync("llm.call.started", "LLM call started", llm_context=context)
    emit_llm_event_sync(
        "llm.request.prepared",
        "Prepared LLM request",
        llm_context=context,
        payloads={"request_messages": ("request_messages", sanitize_messages_for_debug(messages))},
        tags=_request_tags(
            provider=provider,
            api_base=api_base,
            temperature=temperature,
            response_format=response_format,
            max_tokens=max_tokens,
            extra_tags=extra_tags,
        ),
    )
    emit_llm_event_sync(
        "llm.request.sent",
        "Sent LLM request",
        llm_context=context,
        metrics={"message_count": len(messages)},
    )

    kwargs = _build_completion_kwargs(
        model=model,
        provider=provider,
        api_base=api_base,
        api_key=api_key,
        messages=messages,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    attach_debug_metadata(kwargs=kwargs, llm_context=context)

    perf_start = time.perf_counter()
    try:
        with debug_scope(llm=context):
            response = litellm.completion(**kwargs)
    except Exception as exc:
        duration = round(time.perf_counter() - perf_start, 4)
        emit_llm_event_sync(
            "llm.call.failed",
            "LLM call failed",
            llm_context=context,
            payloads={"error_body": ("error_body", {"message": str(exc), "repr": repr(exc)})},
            metrics={"duration_seconds": duration},
            error={"type": type(exc).__name__, "message": str(exc)},
        )
        raise

    duration = round(time.perf_counter() - perf_start, 4)
    usage = extract_usage(response)
    metrics = {"duration_seconds": duration}
    metrics.update({key: value for key, value in usage.items() if value is not None})
    serialized = serialize_response_for_debug(response)
    emit_llm_event_sync(
        "llm.response.received",
        "Received LLM response",
        llm_context=context,
        payloads={"response_body": ("response_body", serialized)},
        metrics=metrics,
    )
    return ObservedCompletionResult(
        response=response,
        llm_context=context,
        duration_seconds=duration,
        usage=usage,
        serialized_response=serialized,
    )


async def acompletion_with_observability(
    *,
    model: str,
    provider: str | None,
    api_base: str | None,
    api_key: str | None,
    messages: list[dict[str, Any]],
    response_format: dict[str, Any] | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_mode: str = "text",
    llm_context: LLMCallContext | None = None,
    extra_tags: dict[str, Any] | None = None,
) -> ObservedCompletionResult:
    import litellm

    context = llm_context or build_llm_context(model=model, provider=provider, response_mode=response_mode)
    await emit_llm_event("llm.call.started", "LLM call started", llm_context=context)
    await emit_llm_event(
        "llm.request.prepared",
        "Prepared LLM request",
        llm_context=context,
        payloads={"request_messages": ("request_messages", sanitize_messages_for_debug(messages))},
        tags=_request_tags(
            provider=provider,
            api_base=api_base,
            temperature=temperature,
            response_format=response_format,
            max_tokens=max_tokens,
            extra_tags=extra_tags,
        ),
    )
    await emit_llm_event(
        "llm.request.sent",
        "Sent LLM request",
        llm_context=context,
        metrics={"message_count": len(messages)},
    )

    kwargs = _build_completion_kwargs(
        model=model,
        provider=provider,
        api_base=api_base,
        api_key=api_key,
        messages=messages,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    attach_debug_metadata(kwargs=kwargs, llm_context=context)

    perf_start = time.perf_counter()
    try:
        with debug_scope(llm=context):
            response = await litellm.acompletion(**kwargs)
    except Exception as exc:
        duration = round(time.perf_counter() - perf_start, 4)
        await emit_llm_event(
            "llm.call.failed",
            "LLM call failed",
            llm_context=context,
            payloads={"error_body": ("error_body", {"message": str(exc), "repr": repr(exc)})},
            metrics={"duration_seconds": duration},
            error={"type": type(exc).__name__, "message": str(exc)},
        )
        raise

    duration = round(time.perf_counter() - perf_start, 4)
    usage = extract_usage(response)
    metrics = {"duration_seconds": duration}
    metrics.update({key: value for key, value in usage.items() if value is not None})
    serialized = serialize_response_for_debug(response)
    await emit_llm_event(
        "llm.response.received",
        "Received LLM response",
        llm_context=context,
        payloads={"response_body": ("response_body", serialized)},
        metrics=metrics,
    )
    return ObservedCompletionResult(
        response=response,
        llm_context=context,
        duration_seconds=duration,
        usage=usage,
        serialized_response=serialized,
    )


def _build_completion_kwargs(
    *,
    model: str,
    provider: str | None,
    api_base: str | None,
    api_key: str | None,
    messages: list[dict[str, Any]],
    response_format: dict[str, Any] | None,
    temperature: float | None,
    max_tokens: int | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if provider:
        kwargs["custom_llm_provider"] = provider
    if api_base:
        kwargs["api_base"] = api_base
    if api_key:
        kwargs["api_key"] = api_key
    if response_format is not None:
        kwargs["response_format"] = response_format
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return kwargs


def _request_tags(
    *,
    provider: str | None,
    api_base: str | None,
    temperature: float | None,
    response_format: dict[str, Any] | None,
    max_tokens: int | None,
    extra_tags: dict[str, Any] | None,
) -> dict[str, Any]:
    tags: dict[str, Any] = {}
    if provider is not None:
        tags["provider"] = provider
    if api_base is not None:
        tags["api_base"] = api_base
    if temperature is not None:
        tags["temperature"] = temperature
    if response_format is not None:
        tags["response_format"] = response_format
    if max_tokens is not None:
        tags["max_tokens"] = max_tokens
    if extra_tags:
        tags.update(extra_tags)
    return tags


def _sanitize_message_content(content: Any) -> Any:
    if isinstance(content, list):
        return [_sanitize_content_item(item) for item in content]
    if isinstance(content, dict):
        return {str(key): _sanitize_message_content(value) for key, value in content.items()}
    return content


def _sanitize_content_item(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    item_type = item.get("type")
    if item_type == "image_url":
        image_url = item.get("image_url")
        if isinstance(image_url, dict):
            url = image_url.get("url")
            if isinstance(url, str) and url.startswith("data:image/") and ";base64," in url:
                prefix, encoded = url.split(",", 1)
                mime_type = prefix[len("data:") :].split(";", 1)[0]
                return {
                    "type": "image_url",
                    "image_url": {
                        "kind": "inline_base64_image",
                        "mime_type": mime_type,
                        "approx_chars": len(url),
                        "preview": f"data:{mime_type};base64,<redacted>",
                        "encoded_chars": len(encoded),
                    },
                }
        return item
    if item_type == "text":
        return {"type": "text", "text": item.get("text", "")}
    return {str(key): _sanitize_message_content(value) for key, value in item.items()}


def _build_debug_event(
    *,
    session,
    event_type: str,
    summary: str,
    llm_context: LLMCallContext,
    payloads: dict[str, tuple[str, Any]] | None,
    metrics: dict[str, Any] | None,
    tags: dict[str, Any] | None,
    error: dict[str, Any] | None,
):
    if session is None or not session.enabled:
        return None

    # Check for an active section_map from DataPerceptionRuntime.analyze().
    from dslighting.debug.section_map_context import get_section_map
    section_map = get_section_map()

    payload_refs = {}
    for label, (kind, body) in (payloads or {}).items():
        payload_ref = session.store_payload(kind=kind, body=body)
        # If this is a request_messages payload and we have an active section_map,
        # store the section_map separately and link it via section_map_ref.
        if kind == "request_messages" and section_map is not None:
            from dataclasses import replace
            section_map_ref = session.store_payload(kind="section_map", body=section_map)
            payload_ref = replace(payload_ref, section_map_ref=section_map_ref.ref)
        payload_refs[label] = payload_ref

    context = get_effective_debug_context(session.session_id)
    return DebugEvent(
        schema_version=session.config.schema_version,
        event_id=uuid.uuid4().hex,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        event_type=event_type,
        summary=summary,
        run=context.run,
        node=context.node,
        llm=llm_context,
        payload_refs=payload_refs,
        metrics=metrics or {},
        tags=tags or {},
        error=error,
    )


def _schedule_emit(coro) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
    else:
        loop.create_task(coro)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "ObservedCompletionResult",
    "acompletion_with_observability",
    "attach_debug_metadata",
    "build_llm_context",
    "completion_with_observability",
    "emit_llm_event",
    "emit_llm_event_sync",
    "extract_response_content",
    "extract_usage",
    "sanitize_messages_for_debug",
    "serialize_response_for_debug",
]
