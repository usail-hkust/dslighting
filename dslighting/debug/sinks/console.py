"""Console sink with call-level buffering."""

from __future__ import annotations

import asyncio
import logging

debug_logger = logging.getLogger("dslighting.debug")


class ConsoleSink:
    def __init__(
        self,
        *,
        formatter,
        partial_flush_timeout_seconds: float = 5.0,
    ) -> None:
        self.formatter = formatter
        self.partial_flush_timeout_seconds = partial_flush_timeout_seconds
        self._buffers: dict[str, list] = {}
        self._opened_at: dict[str, float] = {}
        self._printed_payload_refs: set[str] = set()
        self._lock = asyncio.Lock()
        self._payload_store = None

    async def handle(self, event, payload_store) -> None:
        self._payload_store = payload_store
        if event.llm is None or not event.llm.logical_call_id:
            block = self.formatter.format_generic_event(
                event,
                payload_store,
                printed_payload_refs=self._printed_payload_refs,
            )
            if block:
                debug_logger.info(block)
            return
        logical_call_id = event.llm.logical_call_id
        expired_to_flush: list[str] = []
        should_flush = False
        loop = asyncio.get_running_loop()
        async with self._lock:
            now = loop.time()
            for call_id, opened_at in list(self._opened_at.items()):
                if now - opened_at >= self.partial_flush_timeout_seconds and call_id != logical_call_id:
                    expired_to_flush.append(call_id)

            self._buffers.setdefault(logical_call_id, []).append(event)
            self._opened_at.setdefault(logical_call_id, now)
            should_flush = event.event_type in {"llm.call.completed", "llm.call.failed"}

        for call_id in expired_to_flush:
            await self.flush_call(call_id, payload_store)
        if should_flush:
            await self.flush_call(logical_call_id, payload_store)

    async def flush_call(self, logical_call_id: str, payload_store=None) -> None:
        store = payload_store or self._payload_store
        if store is None:
            return
        async with self._lock:
            events = self._buffers.pop(logical_call_id, [])
            self._opened_at.pop(logical_call_id, None)
            if not events:
                return
            block = self.formatter.format_call_block(
                events,
                store,
                printed_payload_refs=self._printed_payload_refs,
            )
            debug_logger.info(block)

    async def flush_expired(self, payload_store=None) -> None:
        store = payload_store or self._payload_store
        if store is None:
            return
        async with self._lock:
            call_ids = list(self._buffers.keys())
        for call_id in call_ids:
            await self.flush_call(call_id, store)

    async def close(self) -> None:
        await self.flush_expired()
