from __future__ import annotations


class InvalidSubmissionError(Exception):
    """Raised when a task-local grader determines the submission is invalid."""


class SubmissionValidationError(Exception):
    """Raised when framework-level artifact validation fails before grading."""


class GradingExecutionError(Exception):
    """Raised when grading cannot be completed due to runtime execution failures."""
