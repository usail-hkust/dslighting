from __future__ import annotations


class TaskLayoutResolutionError(ValueError):
    """Raised when the task registry/data layout cannot be resolved safely."""


class TaskExecutionSpecError(ValueError):
    """Raised when a task payload cannot be converted into a runtime execution spec."""
