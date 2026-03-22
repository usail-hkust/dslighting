"""LiteLLM callback bridge for provider-aware debug traces."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from litellm.integrations.custom_logger import CustomLogger

from dslighting.debug.context import get_current_debug_context, get_effective_debug_context
from dslighting.debug.events import DebugEvent
from dslighting.debug.models import LLMCallContext
from dslighting.debug.session import DebugSession


class DSLightingLiteLLMLogger(CustomLogger):
    """Bridge LiteLLM callback hooks into DSLighting debug events when needed."""

    def __init__(self, *, provider_raw: bool = False) -> None:
        super().__init__(turn_off_message_logging=False)
        self.provider_raw = provider_raw

    async def async_log_pre_api_call(self, model, messages, kwargs):
        await self._emit_provider_event(
            session=self._get_session(),
            event_type="llm.provider.pre_api_call",
            summary="LiteLLM prepared provider request",
            model=model,
            kwargs=kwargs,
            payloads={"provider_request_messages": ("request_messages", messages)},
        )

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        payloads: dict[str, tuple[str, Any]] = {}
        if response_obj is not None:
            payloads["provider_response_body"] = ("response_body", self._serialize_response(response_obj))
        await self._emit_provider_event(
            session=self._get_session(),
            event_type="llm.provider.success",
            summary="LiteLLM received provider response",
            kwargs=kwargs,
            payloads=payloads,
            metrics={"provider_duration_seconds": self._duration_seconds(start_time, end_time)},
        )

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        error_payload = None
        exception = None
        if isinstance(kwargs, dict):
            exception = (
                kwargs.get("exception")
                or kwargs.get("error")
                or kwargs.get("original_exception")
            )
        if response_obj is not None:
            error_payload = response_obj
        elif exception is not None:
            error_payload = {"message": str(exception), "repr": repr(exception)}

        payloads: dict[str, tuple[str, Any]] = {}
        if error_payload is not None:
            payloads["provider_error_body"] = ("error_body", error_payload)

        await self._emit_provider_event(
            session=self._get_session(),
            event_type="llm.provider.failure",
            summary="LiteLLM observed provider failure",
            kwargs=kwargs,
            payloads=payloads,
            metrics={"provider_duration_seconds": self._duration_seconds(start_time, end_time)},
            error=self._build_error(exception or response_obj),
        )

    def _get_session(self) -> DebugSession | None:
        from dslighting.debug.api import get_debug_session

        session = get_debug_session()
        if session is None or not session.enabled or not self.provider_raw:
            return None
        return session

    async def _emit_provider_event(
        self,
        *,
        session: DebugSession | None,
        event_type: str,
        summary: str,
        model: str | None = None,
        kwargs: dict[str, Any] | None = None,
        payloads: dict[str, tuple[str, Any]] | None = None,
        metrics: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        if session is None:
            return

        payload_refs = {}
        for label, (kind, body) in (payloads or {}).items():
            payload_refs[label] = session.store_payload(kind=kind, body=body)

        context = get_current_debug_context()
        if context.run is None:
            context = get_effective_debug_context(session.session_id)

        llm_context = context.llm or self._extract_llm_context(kwargs=kwargs, model=model)
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
            tags=self._extract_tags(kwargs),
            error=error,
        )
        await session.emit(event)

    @staticmethod
    def _extract_llm_context(*, kwargs: dict[str, Any] | None, model: str | None) -> LLMCallContext:
        metadata = {}
        if isinstance(kwargs, dict):
            metadata = kwargs.get("metadata") or {}
        debug_meta = metadata.get("dslighting_debug") if isinstance(metadata, dict) else None
        if isinstance(debug_meta, dict):
            return LLMCallContext(
                logical_call_id=str(debug_meta.get("logical_call_id") or uuid.uuid4().hex[:12]),
                model=str(debug_meta.get("model") or model or kwargs.get("model") or "unknown"),
                provider=debug_meta.get("provider"),
                response_mode=str(debug_meta.get("response_mode") or "text"),
                semantic_attempt=int(debug_meta.get("semantic_attempt") or 1),
                transport_attempt=int(debug_meta.get("transport_attempt") or 1),
                validation_attempt=int(debug_meta.get("validation_attempt") or 0),
            )
        inferred_model = "unknown"
        inferred_provider = None
        if isinstance(kwargs, dict):
            inferred_model = str(kwargs.get("model") or model or "unknown")
            inferred_provider = kwargs.get("custom_llm_provider")
        return LLMCallContext(logical_call_id=uuid.uuid4().hex[:12], model=inferred_model, provider=inferred_provider)

    @staticmethod
    def _extract_tags(kwargs: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(kwargs, dict):
            return {}
        tags = {
            "provider": kwargs.get("custom_llm_provider"),
            "api_base": kwargs.get("api_base"),
            "temperature": kwargs.get("temperature"),
            "response_format": kwargs.get("response_format"),
        }
        return {key: value for key, value in tags.items() if value is not None}

    @staticmethod
    def _serialize_response(response_obj: Any) -> Any:
        if response_obj is None:
            return None
        model_dump = getattr(response_obj, "model_dump", None)
        if callable(model_dump):
            try:
                return model_dump()
            except Exception:
                pass
        if isinstance(response_obj, dict):
            return response_obj
        return {"repr": repr(response_obj)}

    @staticmethod
    def _duration_seconds(start_time: Any, end_time: Any) -> float | None:
        try:
            if start_time is None or end_time is None:
                return None
            return round((end_time - start_time).total_seconds(), 4)
        except Exception:
            return None

    @staticmethod
    def _build_error(error_obj: Any) -> dict[str, Any] | None:
        if error_obj is None:
            return None
        if isinstance(error_obj, Exception):
            return {"type": type(error_obj).__name__, "message": str(error_obj)}
        if isinstance(error_obj, dict):
            return error_obj
        return {"type": type(error_obj).__name__, "message": str(error_obj)}
