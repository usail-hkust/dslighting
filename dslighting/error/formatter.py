"""
Error Message Formatter for DSLighting

This module provides comprehensive error formatting capabilities with:
- Error registry with predefined error definitions
- Formatted error output with suggestions and documentation links
- Integration with DSLighting exception system
- Internationalization support (extensible)

Usage:
    # Recommended: Use DSLightingError.format() directly
    from dslighting.error import ConfigurationError

    error = ConfigurationError(
        "Invalid model",
        error_code="CFG-001",
        details={"model": "gpt-5"}
    )
    print(error.format())

    from dslighting.error import format_error
    formatted = format_error(exception)
    print(formatted.message)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dslighting.error.exceptions import (
    DSLightingError,
    ConfigurationError,
    WorkflowError,
    BenchmarkError,
    LLMServiceError,
    TaskError,
    WorkspaceError,
)
from dslighting.error.i18n import (
    get_error_message,
    get_error_suggestion,
    set_error_language,
    get_error_language,
    SUPPORTED_ERROR_LANGUAGES,
    DEFAULT_ERROR_LANGUAGE,
    ERROR_MESSAGE_TEMPLATES,
    ERROR_SUGGESTION_TEMPLATES,
)


# =============================================================================
# Formatted Error Data Class
# =============================================================================

@dataclass
class FormattedError:
    """Represents a formatted error with all relevant information.

    Attributes:
        code: Unique error code (e.g., 'CFG-001', 'LLM-001').
        message: Human-readable error message with placeholders filled.
        suggestion: Actionable suggestion for resolving the error.
        doc_url: URL to the documentation for this error.
        details: Additional context details passed during formatting.
        severity: Error severity level (INFO, WARNING, ERROR, CRITICAL).
        category: Error category for grouping (CONFIG, RUNTIME, DATA, etc.).
    """

    code: str
    message: str
    suggestion: str
    doc_url: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "ERROR"
    category: str = "GENERAL"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
            "doc_url": self.doc_url,
            "details": self.details,
            "severity": self.severity,
            "category": self.category,
        }

    def __str__(self) -> str:
        """Format for display."""
        lines = [
            f"[{self.code}] {self.message}",
            f"Severity: {self.severity}",
        ]
        if self.suggestion:
            lines.append(f"Suggestion: {self.suggestion}")
        lines.append(f"Documentation: {self.doc_url}")
        if self.details:
            lines.append(f"Details: {self.details}")
        return "\n".join(lines)


# =============================================================================
# Error Definition Types
# =============================================================================

ErrorTemplate = str
ErrorSuggestion = str
ErrorCategory = str


@dataclass
class ErrorDefinition:
    """Defines an error with template, suggestion, and metadata.

    Attributes:
        template: Message template with placeholders like {file}, {value}, etc.
        suggestion: Actionable suggestion for resolving the error.
        category: Error category (CONFIG, RUNTIME, DATA, LLM, WORKFLOW).
        severity: Error severity (INFO, WARNING, ERROR, CRITICAL).
        doc_url: Override documentation URL (uses default if not provided).
    """

    template: str
    suggestion: str
    category: str = "GENERAL"
    severity: str = "ERROR"
    doc_url: Optional[str] = None


# =============================================================================
# Error Registry
# =============================================================================

class ErrorRegistry:
    """Registry for error definitions with lookup capabilities."""

    def __init__(self) -> None:
        self._errors: Dict[str, ErrorDefinition] = {}

    def register(self, error_code: str, definition: ErrorDefinition) -> None:
        """Register an error definition.

        Args:
            error_code: Unique error code (e.g., 'CFG-001').
            definition: ErrorDefinition instance.
        """
        self._errors[error_code] = definition

    def get(self, error_code: str) -> Optional[ErrorDefinition]:
        """Get error definition by code.

        Args:
            error_code: The error code to look up.

        Returns:
            ErrorDefinition if found, None otherwise.
        """
        return self._errors.get(error_code)

    def get_error_code(self, exception: Exception) -> str:
        """Extract error code from an exception.

        Args:
            exception: The exception to extract error code from.

        Returns:
            Error code string.
        """
        if isinstance(exception, DSLightingError):
            return getattr(exception, "error_code", "DSL-000")
        # Try to extract code from exception class name
        exception_name = exception.__class__.__name__
        if exception_name.endswith("Error"):
            prefix = exception_name[:-5].upper()
            return f"{prefix}-000"
        return "DSL-000"

    def list_codes(self) -> List[str]:
        """List all registered error codes."""
        return list(self._errors.keys())

    def __contains__(self, error_code: str) -> bool:
        return error_code in self._errors

    def __len__(self) -> int:
        return len(self._errors)


# =============================================================================
# Default Error Registry with Predefined Errors
# =============================================================================

def _get_error_category(error_code: str) -> str:
    """Determine error category from error code prefix."""
    prefix = error_code.split('-')[0] if '-' in error_code else error_code
    categories = {
        "CFG": "CONFIG",
        "WRK": "WORKFLOW",
        "LLM": "LLM",
        "DAT": "DATA",
        "BMK": "BENCHMARK",
        "WSP": "WORKSPACE",
        "TSK": "TASK",
    }
    return categories.get(prefix, "GENERAL")


def _get_error_severity(error_code: str) -> str:
    """Determine default error severity from error code.

    Rules:
    - XXX-001, XXX-002, XXX-003: ERROR
    - XXX-004 and above: varies
    """
    # Extract numeric part if available
    if '-' in error_code:
        suffix = error_code.split('-')[1]
        try:
            num = int(suffix)
            # First three error codes are typically ERROR severity
            if num <= 3:
                return "ERROR"
            # CFG-004 is CRITICAL (API key missing)
            if error_code == "CFG-004":
                return "CRITICAL"
            # WRK-003 is timeout (WARNING)
            if error_code == "WRK-003":
                return "WARNING"
            # DAT-003 is memory error (CRITICAL)
            if error_code == "DAT-003":
                return "CRITICAL"
            # LLM-002 is rate limit (WARNING)
            if error_code == "LLM-002":
                return "WARNING"
            return "ERROR"
        except ValueError:
            pass
    return "ERROR"


def create_default_registry() -> ErrorRegistry:
    """Create the default error registry with predefined errors.

    Error definitions are dynamically loaded from i18n.py to avoid code duplication.
    This ensures consistency between translation templates and error definitions.

    Returns:
        ErrorRegistry with all DSLighting errors registered.
    """
    registry = ErrorRegistry()

    # Dynamically create ErrorDefinitions from i18n templates
    for error_code in ERROR_MESSAGE_TEMPLATES:
        # Get English template (fallback) and suggestion
        template_en = ERROR_MESSAGE_TEMPLATES[error_code].get('en', '')
        suggestion_en = ERROR_SUGGESTION_TEMPLATES.get(error_code, {}).get('en', '')

        registry.register(
            error_code,
            ErrorDefinition(
                template=template_en,
                suggestion=suggestion_en,
                category=_get_error_category(error_code),
                severity=_get_error_severity(error_code),
            ),
        )

    return registry


BASE_DOC_URL = "https://docs.dslighting.io/errors"


def _format_template(template: str, details: Dict[str, Any], **context: Any) -> str:
    """Format a message template with context variables."""
    all_vars = {**details, **context}
    try:
        return template.format(**all_vars)
    except KeyError as e:
        missing_keys = ", ".join(str(arg) for arg in e.args)
        return f"{template} (Note: could not format {missing_keys})"


def _format_error_internal(
    error: Exception,
    *,
    registry: Optional[ErrorRegistry] = None,
    base_doc_url: str = BASE_DOC_URL,
    enable_i18n: bool = False,
    lang: Optional[str] = None,
    default_message: Optional[str] = None,
    **context: Any,
) -> FormattedError:
    """Core formatter used by public convenience functions."""
    active_registry = registry or create_default_registry()
    error_code = active_registry.get_error_code(error)
    error_def = active_registry.get(error_code)

    if error_def is None:
        fallback_message = default_message or f"Unknown error code '{error_code}': {error}"
        return FormattedError(
            code=error_code,
            message=fallback_message,
            suggestion="Check error documentation or report this issue.",
            doc_url=f"{base_doc_url}/{error_code}",
            details={"original_error": str(error)},
            severity="ERROR",
            category="UNKNOWN",
        )

    details = {}
    suggestion = error_def.suggestion
    if isinstance(error, DSLightingError):
        details = getattr(error, "details", {}) or {}
        suggestion = getattr(error, "suggestion", None) or suggestion

    template = error_def.template
    if enable_i18n:
        effective_lang = lang if lang in SUPPORTED_ERROR_LANGUAGES else get_error_language()
        translated_template = get_error_message(error_code, effective_lang, **context)
        if translated_template:
            template = translated_template
        translated_suggestion = get_error_suggestion(error_code, effective_lang)
        if translated_suggestion and not getattr(error, "suggestion", None):
            suggestion = translated_suggestion

    message = _format_template(template, details, **context)
    doc_url = error_def.doc_url or f"{base_doc_url}/{error_code}"
    return FormattedError(
        code=error_code,
        message=message,
        suggestion=suggestion,
        doc_url=doc_url,
        details=details,
        severity=error_def.severity,
        category=error_def.category,
    )


# =============================================================================
# Convenience Functions
# =============================================================================

def format_error(
    error: Exception,
    enable_i18n: bool = False,
    lang: Optional[str] = None,
    **context: Any,
) -> FormattedError:
    """Convenience function to format an error.

    Args:
        error: The exception to format.
        enable_i18n: Enable internationalization support.
        lang: Language for error messages ('en' or 'zh').
        **context: Additional context variables.

    Returns:
        FormattedError instance.
    """
    return _format_error_internal(
        error,
        enable_i18n=enable_i18n,
        lang=lang,
        **context,
    )


def safe_format(
    error: Exception,
    default_message: str = "Unknown error",
    enable_i18n: bool = False,
    lang: Optional[str] = None,
    **context: Any,
) -> str:
    """Safely format an error, returning a string.

    This function always returns a string, even if formatting fails.

    Args:
        error: The exception to format.
        default_message: Default message if formatting fails.
        enable_i18n: Enable internationalization support.
        lang: Language for error messages ('en' or 'zh').
        **context: Additional context variables.

    Returns:
        Formatted error string.
    """
    formatted = _format_error_internal(
        error,
        enable_i18n=enable_i18n,
        lang=lang,
        default_message=default_message,
        **context,
    )
    return str(formatted)


__all__ = [
    "FormattedError",
    "ErrorRegistry",
    "ErrorDefinition",
    "create_default_registry",
    "format_error",
    "safe_format",
]
