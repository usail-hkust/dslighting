"""Session orchestration for structured debug observability."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dslighting.debug.bus import DebugEventBus
from dslighting.debug.formatters.human import HumanStructuredFormatter
from dslighting.debug.formatters.jsonl import JsonlFormatter
from dslighting.debug.models import DebugSessionConfig, PayloadRef
from dslighting.debug.payload_store import PayloadStore
from dslighting.debug.redaction import RedactionPolicy
from dslighting.debug.sinks.console import ConsoleSink
from dslighting.debug.sinks.jsonl import JsonlSink


class DebugSession:
    def __init__(self, config: DebugSessionConfig) -> None:
        self.config = config
        self.session_id = f"dbg_{uuid4().hex[:12]}"
        self.started_at_utc = datetime.now(timezone.utc).isoformat()
        self.enabled = config.enabled
        self.output_dir = self._prepare_output_dir(config.output_dir)
        self._payload_store = PayloadStore(
            output_dir=self.output_dir,
            redaction_policy=RedactionPolicy(),
            dedupe_enabled=config.dedupe_payloads,
        )
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_duration": 0.0,
        }
        sinks = []
        if self.enabled and config.console_output:
            sinks.append(
                ConsoleSink(
                    formatter=HumanStructuredFormatter(
                        profile=config.profile,
                        max_inline_chars=config.max_inline_chars,
                        use_color=config.use_color,
                    ),
                    partial_flush_timeout_seconds=config.partial_flush_timeout_seconds,
                )
            )
        if self.enabled and self.output_dir is not None:
            sinks.append(JsonlSink(output_dir=self.output_dir, formatter=JsonlFormatter()))
        self._bus = DebugEventBus(sinks=sinks, payload_store=self._payload_store)

    def store_payload(self, *, kind: str, body: object) -> PayloadRef:
        return self._payload_store.store(kind=kind, body=body)

    async def emit(self, event) -> None:
        if not self.enabled:
            return
        self._update_stats(event)
        await self._bus.emit(event)

    async def close(self) -> None:
        await self._bus.close()
        self._payload_store.flush()

    def get_statistics(self) -> dict[str, float]:
        stats = dict(self._stats)
        total_requests = stats["total_requests"]
        if total_requests:
            stats["average_duration"] = stats["total_duration"] / total_requests
            stats["success_rate"] = stats["successful_requests"] / total_requests
        return stats

    @staticmethod
    def _prepare_output_dir(output_dir: Path | None) -> Path | None:
        if output_dir is None:
            return None
        session_dir = output_dir / f"debug_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def _update_stats(self, event) -> None:
        if event.event_type == "llm.call.started":
            self._stats["total_requests"] += 1
            return
        if event.event_type == "llm.call.completed":
            self._stats["successful_requests"] += 1
            self._stats["total_duration"] += float(event.metrics.get("duration_seconds", 0.0) or 0.0)
            self._stats["total_tokens"] += int(event.metrics.get("total_tokens", 0) or 0)
            return
        if event.event_type == "llm.call.failed":
            self._stats["failed_requests"] += 1
            self._stats["total_duration"] += float(event.metrics.get("duration_seconds", 0.0) or 0.0)
