"""Shared mapping helpers for task execution outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dslighting.core.interfaces import AgentResult


def map_execution_result(
    *,
    raw_output: Any,
    total_cost: Any,
    usage: dict[str, Any] | None,
    workflow_name: str,
    task_id: str,
    duration: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> AgentResult:
    """Normalize raw runner outputs into a stable AgentResult."""
    score: float | None = None
    error: str | None = None
    output_value: Any = raw_output
    success = True

    if isinstance(raw_output, dict):
        score = raw_output.get("score")
        error = raw_output.get("error")
        output_value = raw_output.get("submission_path") or raw_output.get("output") or raw_output
        success = error is None
    elif isinstance(raw_output, str) and raw_output.startswith("[ERROR]"):
        success = False
        error = raw_output
    elif isinstance(raw_output, Path):
        output_value = str(raw_output)

    if score is not None:
        try:
            score = float(score)
        except (TypeError, ValueError):
            pass

    merged_metadata: dict[str, Any] = {
        "usage": usage or {},
        "workflow": workflow_name,
        "task_id": task_id,
    }
    if metadata:
        merged_metadata.update(metadata)

    try:
        normalized_cost = float(total_cost) if total_cost is not None else 0.0
    except (TypeError, ValueError):
        normalized_cost = 0.0

    try:
        normalized_duration = max(0.0, float(duration))
    except (TypeError, ValueError):
        normalized_duration = 0.0

    return AgentResult(
        success=success,
        output=output_value,
        score=score,
        cost=normalized_cost,
        duration=normalized_duration,
        error=error,
        metadata=merged_metadata,
    )
