"""Stable jsonl formatter for debug events and payloads."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


class JsonlFormatter:
    def format_event(self, event) -> dict[str, Any]:
        return self._normalize(event)

    def format_payload(self, ref, body: Any) -> dict[str, Any]:
        entry = self._normalize(ref)
        entry["body"] = self._normalize(body)
        return entry

    def _normalize(self, value: Any) -> Any:
        if is_dataclass(value):
            return {key: self._normalize(val) for key, val in asdict(value).items()}
        if isinstance(value, dict):
            return {str(key): self._normalize(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._normalize(item) for item in value]
        return value
