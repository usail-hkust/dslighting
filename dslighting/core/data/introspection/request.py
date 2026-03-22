"""Runtime request model for data perception."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from dslighting.core.types.task import TaskType


@dataclass(frozen=True)
class DataPerceptionRequest:
    data_dir: Path
    task_type: Optional[TaskType] = None
    task_id: Optional[str] = None
    submission_context: Dict[str, Any] = field(default_factory=dict)
    profile: str = "balanced"
    max_artifacts: int = 12
    max_report_chars: Optional[int] = 14000
    document_preview_lines: int = 12
    enable_document_inspection: bool = True
    enable_database_inspection: bool = True
    tabular_tolerant_fallback: bool = True
