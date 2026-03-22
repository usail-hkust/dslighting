"""Structured debug event schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dslighting.debug.models import LLMCallContext, NodeDebugContext, PayloadRef, RunDebugContext


@dataclass(frozen=True)
class DebugEvent:
    schema_version: int
    event_id: str
    timestamp_utc: str
    event_type: str
    summary: str
    run: RunDebugContext | None = None
    node: NodeDebugContext | None = None
    llm: LLMCallContext | None = None
    payload_refs: dict[str, PayloadRef] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
