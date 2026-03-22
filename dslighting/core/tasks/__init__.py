"""Unified task resolution and adaptation primitives."""

from .adapters import (
    BaseTaskAdapter,
    DataScienceTaskAdapter,
    FileSubmissionTaskAdapter,
    OpenEndedTaskAdapter,
    QATaskAdapter,
    TaskAdapter,
)
from .errors import TaskExecutionSpecError, TaskLayoutResolutionError
from .models import ResolvedTaskLayout, TaskExecutionSpec
from .resolver import TaskResolver

__all__ = [
    "BaseTaskAdapter",
    "DataScienceTaskAdapter",
    "FileSubmissionTaskAdapter",
    "OpenEndedTaskAdapter",
    "QATaskAdapter",
    "ResolvedTaskLayout",
    "TaskAdapter",
    "TaskExecutionSpec",
    "TaskExecutionSpecError",
    "TaskLayoutResolutionError",
    "TaskResolver",
]
