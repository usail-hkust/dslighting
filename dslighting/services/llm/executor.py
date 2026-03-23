"""Unified execution and debug event emission for LLM calls."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from dslighting.debug.context import get_effective_debug_context
from dslighting.debug.api import get_debug_session
from dslighting.debug.context import debug_scope
from dslighting.debug.events import DebugEvent
from dslighting.debug.models import LLMCallContext
from dslighting.error import LLMServiceError

if TYPE_CHECKING:
    from dslighting.services.llm.service import LLMService


@dataclass(frozen=True)
class LLMCallSpec:
    messages: list[dict[str, Any]]
    response_format: dict[str, Any] | None = None
    output_model: type[BaseModel] | None = None
    response_mode: str = "text"
    max_transport_retries: int = 3
    max_validation_retries: int = 1
    base_delay: float = 1.0


class LLMCallExecutor:
    def __init__(self, service: "LLMService") -> None:
        self._service = service

    async def execute(self, spec: LLMCallSpec) -> Any:
        logical_call_id = uuid.uuid4().hex
        overall_started = time.perf_counter()
        effective_response_format = spec.response_format
        if effective_response_format and not self._service._supports_response_format():
            effective_response_format = None

        await self._emit_started(
            LLMCallContext(
                logical_call_id=logical_call_id,
                model=self._service.config.model,
                provider=self._service.config.provider,
                response_mode=spec.response_mode,
            ),
            summary="LLM call started",
        )

        last_error: Exception | None = None
        validation_attempts = max(1, spec.max_validation_retries if spec.response_mode == "json" else 1)

        for semantic_attempt in range(1, validation_attempts + 1):
            try:
                response = await self._execute_transport_attempt(
                    spec=LLMCallSpec(
                        messages=spec.messages,
                        response_format=effective_response_format,
                        output_model=spec.output_model,
                        response_mode=spec.response_mode,
                        max_transport_retries=max(1, spec.max_transport_retries),
                        max_validation_retries=spec.max_validation_retries,
                        base_delay=spec.base_delay,
                    ),
                    logical_call_id=logical_call_id,
                    semantic_attempt=semantic_attempt,
                )
            except Exception as exc:
                last_error = exc
                await self._emit_failed(
                    LLMCallContext(
                        logical_call_id=logical_call_id,
                        model=self._service.config.model,
                        provider=self._service.config.provider,
                        response_mode=spec.response_mode,
                        semantic_attempt=semantic_attempt,
                    ),
                    error=exc,
                    duration=time.perf_counter() - overall_started,
                )
                if isinstance(exc, LLMServiceError):
                    raise
                raise LLMServiceError(f"LLM call failed: {exc}") from exc

            if spec.output_model is None:
                await self._emit_validated(
                    LLMCallContext(
                        logical_call_id=logical_call_id,
                        model=self._service.config.model,
                        provider=self._service.config.provider,
                        response_mode=spec.response_mode,
                        semantic_attempt=semantic_attempt,
                    ),
                    summary="Text response validated",
                )
                await self._emit_completed(
                    LLMCallContext(
                        logical_call_id=logical_call_id,
                        model=self._service.config.model,
                        provider=self._service.config.provider,
                        response_mode=spec.response_mode,
                        semantic_attempt=semantic_attempt,
                    ),
                    response=response,
                    duration=time.perf_counter() - overall_started,
                )
                return response

            response_content = self._extract_content(response)
            try:
                parsed = spec.output_model.model_validate_json(response_content)
            except ValidationError as exc:
                last_error = exc
                call_context = LLMCallContext(
                    logical_call_id=logical_call_id,
                    model=self._service.config.model,
                    provider=self._service.config.provider,
                    response_mode=spec.response_mode,
                    semantic_attempt=semantic_attempt,
                    validation_attempt=semantic_attempt,
                )
                await self._emit_validation_failed(call_context, response_content=response_content, error=exc)
                if semantic_attempt < validation_attempts:
                    await self._emit_retry_scheduled(
                        call_context,
                        reason="validation_failed",
                        next_semantic_attempt=semantic_attempt + 1,
                    )
                    continue
                terminal_error = LLMServiceError(
                    f"LLM returned invalid JSON that could not be parsed: {exc}",
                    error_code="LLM-002",
                    details={"validation_error": str(exc)},
                    suggestion="Check the JSON schema and ensure the LLM response matches the expected format",
                )
                await self._emit_failed(
                    call_context,
                    error=terminal_error,
                    duration=time.perf_counter() - overall_started,
                )
                raise terminal_error from exc

            await self._emit_validated(
                LLMCallContext(
                    logical_call_id=logical_call_id,
                    model=self._service.config.model,
                    provider=self._service.config.provider,
                    response_mode=spec.response_mode,
                    semantic_attempt=semantic_attempt,
                    validation_attempt=semantic_attempt,
                ),
                summary="JSON response validated",
            )
            await self._emit_completed(
                LLMCallContext(
                    logical_call_id=logical_call_id,
                    model=self._service.config.model,
                    provider=self._service.config.provider,
                    response_mode=spec.response_mode,
                    semantic_attempt=semantic_attempt,
                    validation_attempt=semantic_attempt,
                ),
                response=response,
                duration=time.perf_counter() - overall_started,
            )
            return parsed

        if isinstance(last_error, LLMServiceError):
            raise last_error
        raise LLMServiceError(f"LLM call failed: {last_error}") from last_error

    async def _execute_transport_attempt(
        self,
        *,
        spec: LLMCallSpec,
        logical_call_id: str,
        semantic_attempt: int,
    ) -> Any:
        import litellm
        import litellm.exceptions as litellm_exceptions

        last_exception: Exception | None = None
        exhausted_keys: set[str] = set()
        max_key_attempts = max(1, len(self._service.config.get_api_keys()))

        for _ in range(max_key_attempts):
            api_key = await self._service._key_pool.acquire_key(excluded_keys=exhausted_keys)
            if api_key is None:
                break

            rotate_key = False
            try:
                for transport_attempt in range(1, max(1, spec.max_transport_retries) + 1):
                    llm_context = LLMCallContext(
                        logical_call_id=logical_call_id,
                        model=self._service.config.model,
                        provider=self._service.config.provider,
                        response_mode=spec.response_mode,
                        semantic_attempt=semantic_attempt,
                        transport_attempt=transport_attempt,
                    )
                    call_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    perf_start = time.perf_counter()
                    await self._emit_request_prepared(llm_context, spec=spec)
                    try:
                        kwargs = self._service._build_completion_kwargs(
                            messages=spec.messages,
                            response_format=spec.response_format,
                            api_key=api_key,
                        )
                        self._attach_debug_metadata(kwargs=kwargs, llm_context=llm_context)
                        await self._emit_request_sent(llm_context, message_count=len(spec.messages))

                        with debug_scope(llm=llm_context):
                            async with self._service._concurrency_guard():
                                response = await litellm.acompletion(**kwargs)

                        content = self._extract_content(response)
                        duration = time.perf_counter() - perf_start
                        if not content.strip():
                            raise LLMServiceError("LLM returned an empty response.")

                        await self._emit_response_received(
                            llm_context,
                            response=response,
                            duration=duration,
                        )
                        self._service._record_successful_call(
                            call_id=f"{logical_call_id}:{semantic_attempt}:{transport_attempt}",
                            call_started_at=call_started_at,
                            duration=duration,
                            messages=spec.messages,
                            response=response,
                            content=content,
                            response_format=spec.response_format,
                        )
                        self._service._key_pool.mark_key_success(api_key)
                        return response
                    except Exception as exc:
                        last_exception = exc
                        if isinstance(exc, litellm_exceptions.RateLimitError):
                            self._record_rate_limit()

                        action = self._service._classify_error_action(exc)
                        if self._is_retryable_transport_error(exc) and transport_attempt < max(1, spec.max_transport_retries):
                            await self._emit_retry_scheduled(
                                llm_context,
                                reason=str(exc),
                                next_transport_attempt=transport_attempt + 1,
                            )
                            delay = spec.base_delay * (3 ** (transport_attempt - 1)) + (asyncio.get_event_loop().time() % 1)
                            await asyncio.sleep(delay)
                            continue

                        if action == "retry_next_key":
                            exhausted_keys.add(api_key)
                            self._service._key_pool.mark_key_failed(
                                api_key,
                                reason=type(exc).__name__,
                                cooldown_seconds=self._service._cooldown_seconds_for_error(exc),
                            )
                            rotate_key = True
                            await self._emit_retry_scheduled(
                                llm_context,
                                reason=f"rotate_api_key:{type(exc).__name__}",
                            )
                            break

                        if action == "fail_fast":
                            raise LLMServiceError(f"LLM call failed with non-retryable error: {exc}") from exc

                        raise LLMServiceError(
                            f"LLM call failed after {spec.max_transport_retries} transport attempts. Last error: {exc}"
                        ) from exc
            finally:
                self._service._key_pool.release_key(api_key)

            if not rotate_key:
                break

        if exhausted_keys:
            raise LLMServiceError(
                f"LLM call failed after exhausting {len(exhausted_keys)} API key(s). Last error: {last_exception}"
            ) from last_exception
        raise LLMServiceError(
            f"LLM call failed after {spec.max_transport_retries} transport attempts. Last error: {last_exception}"
        ) from last_exception

    def _extract_content(self, response: Any) -> str:
        if not response or not hasattr(response, "choices") or not response.choices:
            raise LLMServiceError("Invalid response structure: missing choices")
        try:
            content = response.choices[0].message.content
        except (IndexError, AttributeError) as exc:
            raise LLMServiceError(f"Invalid response structure: {exc}") from exc
        if content is None:
            return ""
        return str(content)

    def _is_retryable_transport_error(self, error: Exception) -> bool:
        if isinstance(error, LLMServiceError):
            return True
        return self._service._classify_error_action(error) == "retry_same_key"

    def _record_rate_limit(self) -> None:
        try:
            from dslighting.monitoring.monitoring import get_global_monitor

            monitor = get_global_monitor()
            if monitor is not None:
                monitor.increment_rate_limited_count()
        except Exception:
            pass

    async def _emit_started(self, llm_context: LLMCallContext, *, summary: str) -> None:
        await self._emit_event("llm.call.started", summary, llm_context=llm_context)

    async def _emit_request_prepared(self, llm_context: LLMCallContext, *, spec: LLMCallSpec) -> None:
        await self._emit_event(
            "llm.request.prepared",
            "Prepared LLM request",
            llm_context=llm_context,
            payloads={"request_messages": ("request_messages", spec.messages)},
            tags={
                "temperature": self._service.config.temperature,
                "api_base": self._service.config.api_base,
                "provider": self._service.config.provider,
                "response_format": spec.response_format,
            },
        )

    async def _emit_request_sent(self, llm_context: LLMCallContext, *, message_count: int) -> None:
        await self._emit_event(
            "llm.request.sent",
            "Sent LLM request",
            llm_context=llm_context,
            metrics={"message_count": message_count},
        )

    async def _emit_response_received(self, llm_context: LLMCallContext, *, response: Any, duration: float) -> None:
        serialized = self._service._serialize_response_for_debug(response)
        usage = self._service._extract_usage(response)
        metrics = {"duration_seconds": round(duration, 4)}
        metrics.update({key: value for key, value in usage.items() if value is not None})
        await self._emit_event(
            "llm.response.received",
            "Received LLM response",
            llm_context=llm_context,
            payloads={"response_body": ("response_body", serialized)},
            metrics=metrics,
        )

    async def _emit_validated(self, llm_context: LLMCallContext, *, summary: str) -> None:
        await self._emit_event("llm.response.validated", summary, llm_context=llm_context)

    async def _emit_validation_failed(
        self,
        llm_context: LLMCallContext,
        *,
        response_content: str,
        error: Exception,
    ) -> None:
        await self._emit_event(
            "llm.validation.failed",
            "Validation failed for LLM response",
            llm_context=llm_context,
            payloads={"response_text": ("response_body", response_content)},
            error={"type": type(error).__name__, "message": str(error)},
        )

    async def _emit_retry_scheduled(
        self,
        llm_context: LLMCallContext,
        *,
        reason: str,
        next_transport_attempt: int | None = None,
        next_semantic_attempt: int | None = None,
    ) -> None:
        tags: dict[str, Any] = {"reason": reason}
        if next_transport_attempt is not None:
            tags["next_transport_attempt"] = next_transport_attempt
        if next_semantic_attempt is not None:
            tags["next_semantic_attempt"] = next_semantic_attempt
        await self._emit_event(
            "llm.retry.scheduled",
            "Scheduled retry for LLM call",
            llm_context=llm_context,
            tags=tags,
        )

    async def _emit_completed(self, llm_context: LLMCallContext, *, response: Any, duration: float) -> None:
        usage = self._service._extract_usage(response)
        metrics = {"duration_seconds": round(duration, 4)}
        if usage:
            metrics.update({key: value for key, value in usage.items() if value is not None})
            total_tokens = usage.get("total_tokens")
            if total_tokens is not None:
                metrics["total_tokens"] = total_tokens
        await self._emit_event(
            "llm.call.completed",
            "LLM call completed",
            llm_context=llm_context,
            metrics=metrics,
        )

    async def _emit_failed(self, llm_context: LLMCallContext, *, error: Exception, duration: float) -> None:
        await self._emit_event(
            "llm.call.failed",
            "LLM call failed",
            llm_context=llm_context,
            payloads={"error_body": ("error_body", {"message": str(error), "repr": repr(error)})},
            metrics={"duration_seconds": round(duration, 4)},
            error={"type": type(error).__name__, "message": str(error)},
        )

    async def _emit_event(
        self,
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
        if session is None or not session.enabled:
            return
        payload_refs = {}
        for label, (kind, body) in (payloads or {}).items():
            payload_refs[label] = session.store_payload(kind=kind, body=body)
        context = get_effective_debug_context(session.session_id)
        event = DebugEvent(
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
        await session.emit(event)

    def _attach_debug_metadata(self, *, kwargs: dict[str, Any], llm_context: LLMCallContext) -> None:
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
