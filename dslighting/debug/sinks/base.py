"""Debug sink protocol."""

from __future__ import annotations

from typing import Protocol


class DebugSink(Protocol):
    async def handle(self, event, payload_store) -> None: ...

    async def close(self) -> None: ...
