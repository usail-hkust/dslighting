"""Structured inspection helpers for JSON-family documents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class JsonInspectionResult:
    kind: Literal["json", "jsonl", "json_like"]
    parsed_ok: bool
    top_level_type: str | None
    keys: tuple[str, ...]
    record_count: int | None
    failed_record_count: int | None
    preview_lines: tuple[str, ...]


def render_json_inspection(result: JsonInspectionResult) -> list[str]:
    if result.kind == "json":
        summary = ["Kind: json document"]
        if result.top_level_type == "dict":
            summary.append(f"Top-level keys ({len(result.keys)}): {list(result.keys[:12])}")
        elif result.top_level_type == "list":
            count = result.record_count if result.record_count is not None else "unknown"
            summary.append(f"Top-level type: list (length={count})")
        elif result.top_level_type:
            summary.append(f"Top-level type: {result.top_level_type}")
    elif result.kind == "jsonl":
        summary = ["Kind: jsonl document"]
        if result.record_count is not None:
            summary.append(f"Records: {result.record_count}")
        if result.failed_record_count:
            summary.append(f"Failed lines: {result.failed_record_count}")
        if result.keys:
            summary.append(f"Record keys ({len(result.keys)}): {list(result.keys[:12])}")
    else:
        summary = ["Kind: json-like document", "Parse Status: failed"]

    if result.preview_lines:
        summary.append("Preview:")
        summary.extend(result.preview_lines)
    return summary


class JsonDocumentInspector:
    def __init__(self, *, preview_lines: int = 12) -> None:
        self.preview_lines = max(1, int(preview_lines))

    def inspect(self, *, text: str, suffix: str) -> JsonInspectionResult:
        suffix_value = str(suffix or "").strip().lower()
        json_result = self._inspect_json(text)
        if suffix_value == ".jsonl":
            jsonl_result = self._inspect_jsonl(text, min_records=1, allow_partial=True)
            if jsonl_result is not None:
                return jsonl_result
            if json_result is not None:
                return json_result
        else:
            if json_result is not None:
                return json_result
            jsonl_result = self._inspect_jsonl(text, min_records=2, allow_partial=False)
            if jsonl_result is not None:
                return jsonl_result
        return self._inspect_json_like(text)

    def _inspect_json(self, text: str) -> JsonInspectionResult | None:
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

        keys: tuple[str, ...] = ()
        record_count: int | None = None
        top_level_type = type(parsed).__name__
        if isinstance(parsed, dict):
            keys = tuple(str(key) for key in parsed.keys())
        elif isinstance(parsed, list):
            record_count = len(parsed)

        return JsonInspectionResult(
            kind="json",
            parsed_ok=True,
            top_level_type=top_level_type,
            keys=keys,
            record_count=record_count,
            failed_record_count=None,
            preview_lines=self._preview(text),
        )

    def _inspect_jsonl(
        self,
        text: str,
        *,
        min_records: int,
        allow_partial: bool,
    ) -> JsonInspectionResult | None:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            return None

        parsed_records: list[Any] = []
        failed_lines = 0
        for line in lines:
            try:
                parsed_records.append(json.loads(line))
            except (json.JSONDecodeError, ValueError, TypeError):
                failed_lines += 1

        if len(parsed_records) < min_records:
            return None
        if failed_lines and not allow_partial:
            return None

        first = parsed_records[0]
        keys: tuple[str, ...] = ()
        if isinstance(first, dict):
            keys = tuple(str(key) for key in first.keys())

        return JsonInspectionResult(
            kind="jsonl",
            parsed_ok=failed_lines == 0,
            top_level_type="record_stream",
            keys=keys,
            record_count=len(parsed_records),
            failed_record_count=failed_lines or None,
            preview_lines=self._preview(text),
        )

    def _inspect_json_like(self, text: str) -> JsonInspectionResult:
        return JsonInspectionResult(
            kind="json_like",
            parsed_ok=False,
            top_level_type=None,
            keys=(),
            record_count=None,
            failed_record_count=None,
            preview_lines=self._preview(text),
        )

    def _preview(self, text: str) -> tuple[str, ...]:
        return tuple(text.splitlines()[: self.preview_lines])
