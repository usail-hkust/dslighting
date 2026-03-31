"""Core data models for structured debug observability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DebugSessionConfig:
    enabled: bool
    profile: str = "full"
    console_output: bool = True
    output_dir: Path | None = None
    console_formatter: str = "human_structured"
    archive_formatter: str = "jsonl_lossless"
    dedupe_payloads: bool = True
    redact_secrets: bool = True
    max_inline_chars: int = 12000
    partial_flush_timeout_seconds: float = 5.0
    use_color: bool = True
    schema_version: int = 1


@dataclass(frozen=True)
class RunDebugContext:
    session_id: str
    run_id: str
    task_id: str | None = None
    workflow_name: str | None = None
    benchmark_source: str | None = None
    benchmark_preset: str | None = None


@dataclass(frozen=True)
class NodeDebugContext:
    node_id: str | None = None
    operator_name: str | None = None
    op_type: str | None = None
    node_attempt: int | None = None


@dataclass(frozen=True)
class LLMCallContext:
    logical_call_id: str
    model: str
    provider: str | None = None
    response_mode: str = "text"
    semantic_attempt: int = 1
    transport_attempt: int = 1
    validation_attempt: int = 0


@dataclass(frozen=True)
class PayloadRef:
    ref: str
    sha256: str
    kind: str
    bytes_len: int
    chars_len: int
    reused: bool = False
    preview: str | None = None
    section_map_ref: str | None = None
