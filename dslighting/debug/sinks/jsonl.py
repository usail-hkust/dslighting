"""JSONL archive sink for structured debug events."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path


class JsonlSink:
    def __init__(self, *, output_dir: Path, formatter) -> None:
        self.output_dir = output_dir
        self.formatter = formatter
        self._event_path = self.output_dir / "events.jsonl"
        self._payload_path = self.output_dir / "payloads.jsonl"
        self._payloads_written: set[str] = set()
        self._lock = asyncio.Lock()
        self._payload_store = None

    async def handle(self, event, payload_store) -> None:
        self._payload_store = payload_store
        async with self._lock:
            for payload_ref in event.payload_refs.values():
                if payload_ref.ref in self._payloads_written:
                    continue
                payload_body = payload_store.get(payload_ref.ref)
                payload_entry = self.formatter.format_payload(payload_ref, payload_body)
                await asyncio.to_thread(self._append_jsonl, self._payload_path, payload_entry)
                self._payloads_written.add(payload_ref.ref)
            event_entry = self.formatter.format_event(event)
            await asyncio.to_thread(self._append_jsonl, self._event_path, event_entry)

    async def close(self) -> None:
        return None

    @staticmethod
    def _append_jsonl(path: Path, entry: dict) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
