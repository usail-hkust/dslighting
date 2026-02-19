"""
DSLighting Exception Hierarchy with Built-in Formatting

This module defines a unified exception hierarchy for DSLighting errors,
providing consistent error codes, structured error information, and built-in
formatting capabilities.

Error Codes:
    - DSL-000: General DSLighting error (base)
    - CFG: Configuration-related errors
    - WRK: Workflow execution errors
    - BMK: Benchmark-related errors
    - LLM: LLM service errors
    - TSK: Task-related errors
    - WSP: Workspace errors

Example Usage:
    >>> try:
    ...     raise ConfigurationError(
    ...         "Invalid model configuration",
    ...         error_code="CFG-001",
    ...         details={"model": "invalid", "provider": "openai"},
    ...         suggestion="Check supported models at https://docs.dslighting.io/providers"
    ...     )
    ... except ConfigurationError as e:
    ...     print(e.error_code)  # CFG-001
    ...     print(e.format())    # Full formatted message with suggestion
    ...     print(e.suggestion)  # Check supported models...
"""

from typing import Any, Dict, Optional
from datetime import datetime


class DSLightingError(Exception):
    """Base exception for all DSLighting errors.

    This exception class provides built-in formatting capabilities and
    structured error information including error codes, suggestions,
    documentation links, and context details.

    Attributes:
        error_code: Unique error code in format 'DOMAIN-XXX' or short code like 'CFG'.
        message: Human-readable error message.
        details: Additional error details (optional).
        suggestion: Actionable suggestion for resolving (optional).
        cause: The underlying exception that caused this error (optional).
        timestamp: When the error occurred (auto-generated).
        context: Additional context information (optional).
        doc_url: Documentation URL for this error (auto-generated if not provided).

    Example:
        >>> error = DSLightingError(
        ...     "Something went wrong",
        ...     error_code="DSL-001",
        ...     suggestion="Try restarting the service"
        ... )
        >>> print(error.format())
    """

    error_code: str = "DSL-000"
    _error_count: int = 0

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        cause: Optional[Exception] = None,
        doc_url: Optional[str] = None,
    ) -> None:
        self.message = message or "An unspecified error occurred in DSLighting."
        self.error_code = error_code if error_code is not None else type(self).error_code
        self.details = details or {}
        self.suggestion = suggestion
        self.cause = cause
        self.doc_url = doc_url
        self.timestamp = datetime.utcnow()
        self.context: Dict[str, Any] = {}
        DSLightingError._error_count += 1
        super().__init__(self._format_message())

    def __str__(self) -> str:
        """Return formatted error string."""
        return self._format_message()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r}, "
            f"suggestion={self.suggestion!r}"
            ")"
        )

    def _format_message(self) -> str:
        """Format the error message with all components."""
        parts = [f"[{self.error_code}] {self.message}"]

        if self.details:
            details_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        return " | ".join(parts)

    def format(
        self,
        include_doc_url: bool = True,
        include_timestamp: bool = False,
        include_context: bool = False,
    ) -> str:
        """Format the error with additional options.

        Args:
            include_doc_url: Include documentation URL in output.
            include_timestamp: Include timestamp in output.
            include_context: Include context dictionary in output.

        Returns:
            Formatted error string.
        """
        lines = [f"[{self.error_code}] {self.message}"]

        if self.details and include_context:
            details_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            lines.append(f"Details: {details_str}")

        if self.suggestion:
            lines.append(f"Suggestion: {self.suggestion}")

        if include_doc_url:
            doc_url = self.doc_url or f"https://docs.dslighting.io/errors/{self.error_code}"
            lines.append(f"Documentation: {doc_url}")

        if include_timestamp:
            lines.append(f"Timestamp: {self.timestamp.isoformat()}")

        if self.context and include_context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            lines.append(f"Context: {ctx_str}")

        return "\n".join(lines)

    def with_context(self, **context: Any) -> "DSLightingError":
        """Add context information to the exception.

        Args:
            **context: Key-value pairs of context information.

        Returns:
            Self for method chaining.

        Example:
            >>> error = ConfigurationError("Invalid config")
            >>> error.with_context(file="config.yaml", line=42)
        """
        self.context.update(context)
        return self

    def with_suggestion(self, suggestion: str) -> "DSLightingError":
        """Add a suggestion to the exception.

        Args:
            suggestion: Actionable suggestion for resolving the error.

        Returns:
            Self for method chaining.

        Example:
            >>> error = ConfigurationError("Invalid config")
            >>> error.with_suggestion("Check the documentation")
        """
        self.suggestion = suggestion
        return self

    def with_doc_url(self, doc_url: str) -> "DSLightingError":
        """Set the documentation URL for this error.

        Args:
            doc_url: URL to the documentation.

        Returns:
            Self for method chaining.
        """
        self.doc_url = doc_url
        return self

    @classmethod
    def get_error_count(cls) -> int:
        """Get the total number of DSLightingError instances created."""
        return cls._error_count


class ConfigurationError(DSLightingError):
    """Raised when configuration is invalid or cannot be loaded.

    This includes errors related to:
        - YAML config file parsing
        - Environment variable validation
        - Pydantic model validation
        - Missing required configuration keys
        - Invalid configuration values
    """

    error_code: str = "CFG"


class WorkflowError(DSLightingError):
    """Raised when workflow execution fails.

    This includes errors related to:
        - Workflow initialization
        - Task execution
        - Workflow state management
        - Invalid workflow configurations
    """

    error_code: str = "WRK"


class BenchmarkError(DSLightingError):
    """Raised when benchmark operations fail.

    This includes errors related to:
        - Benchmark task loading
        - Submission validation
        - Grading/scoring
        - Leaderboard operations
    """

    error_code: str = "BMK"


class LLMServiceError(DSLightingError):
    """Raised when LLM service operations fail.

    This includes errors related to:
        - API key management
        - Model provider calls
        - Response parsing
        - Rate limiting
        - Cost tracking
    """

    error_code: str = "LLM"


class TaskError(DSLightingError):
    """Raised when task operations fail.

    This includes errors related to:
        - Task definition parsing
        - Task data loading
        - Task validation
    """

    error_code: str = "TSK"


class WorkspaceError(DSLightingError):
    """Raised when workspace operations fail.

    This includes errors related to:
        - Workspace creation/deletion
        - File operations
        - Path resolution
        - Directory management
    """

    error_code: str = "WSP"


class DynamicImportError(DSLightingError):
    """Raised when a dynamic import fails."""

    error_code: str = "IMP"


# Export all exception classes for convenient imports
__all__ = [
    "DSLightingError",
    "ConfigurationError",
    "WorkflowError",
    "BenchmarkError",
    "LLMServiceError",
    "TaskError",
    "WorkspaceError",
    "DynamicImportError",
]
