"""Document and schema artifact sampling."""

from __future__ import annotations

import json

from ..models import ArtifactDescriptor, ArtifactSummary
from .json_document import JsonDocumentInspector, render_json_inspection


class DocumentSampler:
    CSV_ENCODINGS = ("utf-8", "utf-8-sig", "gbk", "latin1")

    def __init__(self, *, preview_lines: int = 12) -> None:
        self.preview_lines = max(1, int(preview_lines))
        self._json_inspector = JsonDocumentInspector(preview_lines=self.preview_lines)

    def summarize(self, descriptor: ArtifactDescriptor) -> ArtifactSummary:
        text, encoding = self._read_text_document(descriptor)
        lowered = text.lower()

        if descriptor.suffix.lower() in {".json", ".jsonl"}:
            detail_lines = self._summarize_json_document(text, suffix=descriptor.suffix.lower())
        elif "## table:" in lowered or "# database schema" in lowered:
            detail_lines = self._summarize_schema_document(text)
        else:
            detail_lines = self._summarize_generic_document(text)

        detail_lines.insert(1, f"Encoding Used: {encoding}")
        return ArtifactSummary(
            descriptor=descriptor,
            status="ok",
            detail_lines=detail_lines,
        )

    def _read_text_document(self, descriptor: ArtifactDescriptor) -> tuple[str, str]:
        last_error = None
        for encoding in self.CSV_ENCODINGS:
            try:
                return descriptor.path.read_text(encoding=encoding), encoding
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode document")

    def _summarize_schema_document(self, text: str) -> list[str]:
        lines = [line.rstrip() for line in text.splitlines()]
        table_names: list[str] = []
        column_counts: dict[str, int] = {}
        current_table: str | None = None

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Table:"):
                current_table = stripped.split(":", 1)[1].strip()
                table_names.append(current_table)
                column_counts[current_table] = 0
                continue
            if current_table and stripped.startswith("- ") and ":" in stripped:
                column_counts[current_table] += 1

        preview_lines = [line for line in lines if line.strip()][: self.preview_lines]
        summary = ["Kind: schema document"]
        if table_names:
            summary.append(f"Detected Tables ({len(table_names)}):")
            summary.extend(
                f"- {table_name} ({column_counts.get(table_name, 0)} columns)"
                for table_name in table_names[:8]
            )
        if preview_lines:
            summary.append("Preview:")
            summary.extend(preview_lines)
        return summary

    def _summarize_json_document(self, text: str, *, suffix: str) -> list[str]:
        inspection = self._json_inspector.inspect(text=text, suffix=suffix)
        return render_json_inspection(inspection)

    def _summarize_generic_document(self, text: str) -> list[str]:
        lines = [line.rstrip() for line in text.splitlines()]
        headings = [line.strip() for line in lines if line.strip().startswith("#")]
        non_empty = [line for line in lines if line.strip()]
        summary = ["Kind: text document"]
        if headings:
            summary.append(f"Headings Detected ({min(len(headings), 6)} shown):")
            summary.extend(f"- {heading}" for heading in headings[:6])
        if non_empty:
            summary.append("Preview:")
            summary.extend(non_empty[: self.preview_lines])
        return summary
