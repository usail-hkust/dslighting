"""Async event dispatch for debug sinks."""

from __future__ import annotations

from dslighting.debug.events import DebugEvent
from dslighting.debug.payload_store import PayloadStore
from dslighting.debug.sinks.base import DebugSink


class DebugEventBus:
    def __init__(self, sinks: list[DebugSink], payload_store: PayloadStore) -> None:
        self._sinks = sinks
        self._payload_store = payload_store

    async def emit(self, event: DebugEvent) -> None:
        for sink in self._sinks:
            await sink.handle(event, self._payload_store)

    async def close(self) -> None:
        for sink in self._sinks:
            await sink.close()
