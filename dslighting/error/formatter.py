"""
Error Message Formatter for DSLighting

This module provides comprehensive error formatting capabilities with:
- Error registry with predefined error definitions
- Formatted error output with suggestions and documentation links
- Integration with DSLighting exception system
- Internationalization support (extensible)
- Backward compatibility with ErrorFormatter

Usage:
    # Recommended: Use DSLightingError.format() directly
    from dslighting.error import ConfigurationError

    error = ConfigurationError(
        "Invalid model",
        error_code="CFG-001",
        details={"model": "gpt-5"}
    )
    print(error.format())

    # Legacy: Use ErrorFormatter (deprecated but still supported)
    from dslighting.error import ErrorFormatter

    formatter = ErrorFormatter()
    formatted = formatter.format(exception)
    print(formatted.message)
"""

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union

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


# =============================================================================
# Main Error Formatter Class
# =============================================================================

class ErrorFormatter:
    """Formats exceptions into detailed, actionable error messages.

    .. deprecated::
        The ErrorFormatter class is deprecated and will be removed in version 3.0.0.
        New code should use the :meth:`DSLightingError.format()` method directly
        for simpler and more consistent error formatting.

        Legacy code should migrate to:
        - Use ``error.format()`` instead of ``ErrorFormatter().format(error)``
        - Use ``FormattedError`` attributes directly from the exception

    The ErrorFormatter provides:
    - Lookup of error definitions by error code
    - Message formatting with context variables
    - Automatic suggestion generation
    - Documentation link generation
    - Integration with DSLighting exception system
    - Internationalization support

    Migration Example:
        >>> # OLD (deprecated)
        >>> formatter = ErrorFormatter()
        >>> formatted = formatter.format(error)
        >>> print(formatted.message)

        >>> # NEW (recommended)
        >>> print(error.format())

    This class is maintained for backward compatibility and will be removed
    in version 3.0.0.
    """

    BASE_DOC_URL = "https://docs.dslighting.io/errors"
    DEFAULT_ERROR_CODE = "DSL-000"

    def __init__(
        self,
        registry: Optional[ErrorRegistry] = None,
        base_doc_url: Optional[str] = None,
        enable_i18n: bool = False,
        lang: Optional[str] = None,
    ) -> None:
        """Initialize error formatter.

        Args:
            registry: Custom error registry. Uses default if None.
            base_doc_url: Base URL for documentation links.
            enable_i18n: Enable internationalization support.
            lang: Language for error messages ('en' or 'zh'). If None, uses current global setting.
        """
        self.registry = registry or create_default_registry()
        self.base_doc_url = base_doc_url or self.BASE_DOC_URL
        self.enable_i18n = enable_i18n
        self._lang = lang
        self._custom_suggestions: Dict[str, str] = {}

        # Issue deprecation warning
        warnings.warn(
            "ErrorFormatter is partially deprecated. Use DSLightingError.format() for new code. "
            "ErrorFormatter will be fully deprecated in version 3.0.0.",
            DeprecationWarning,
            stacklevel=2
        )

    @property
    def lang(self) -> str:
        """Get current language setting."""
        return self._lang if self._lang is not None else get_error_language()

    @lang.setter
    def lang(self, value: str) -> None:
        """Set the language for error messages."""
        if value in SUPPORTED_ERROR_LANGUAGES:
            self._lang = value
        else:
            self._lang = DEFAULT_ERROR_LANGUAGE

    def set_lang(self, lang: str) -> bool:
        """Set the language for error messages.

        Args:
            lang: Language code ('en' or 'zh').

        Returns:
            True if language was set successfully, False if invalid.
        """
        if lang in SUPPORTED_ERROR_LANGUAGES:
            self._lang = lang
            return True
        return False

    def register_error(self, error_code: str, definition: ErrorDefinition) -> None:
        """Register a new error definition.

        Args:
            error_code: Unique error code.
            definition: ErrorDefinition instance.
        """
        self.registry.register(error_code, definition)

    def add_custom_suggestion(self, error_code: str, suggestion: str) -> None:
        """Add a custom suggestion for a specific error code.

        This overrides the default suggestion from the registry.

        Args:
            error_code: Error code to customize.
            suggestion: Custom suggestion text.
        """
        self._custom_suggestions[error_code] = suggestion

    def get_error_code(self, error: Exception) -> str:
        """Extract error code from an exception.

        Args:
            error: The exception to extract error code from.

        Returns:
            Error code string.
        """
        return self.registry.get_error_code(error)

    def get_error_def(self, error_code: str) -> Optional[ErrorDefinition]:
        """Get error definition by code.

        Args:
            error_code: The error code to look up.

        Returns:
            ErrorDefinition if found, default definition otherwise.
        """
        definition = self.registry.get(error_code)
        if definition is None:
            # Return a default definition for unknown error codes
            return ErrorDefinition(
                template=f"Unknown error code '{error_code}': {{message}}",
                suggestion="Check error documentation or report this issue.",
                category="UNKNOWN",
                severity="ERROR",
            )
        return definition

    def _format_template(
        self, template: str, details: Dict[str, Any], **context: Any
    ) -> str:
        """Format a message template with context variables.

        Args:
            template: The message template with placeholders.
            details: Additional details from the exception.
            **context: Additional context variables.

        Returns:
            Formatted message string.
        """
        # Merge details and context
        all_vars = {**details, **context}

        try:
            return template.format(**all_vars)
        except KeyError as e:
            # If formatting fails, return original template with note
            missing_keys = ", ".join(str(arg) for arg in e.args)
            return f"{template} (Note: could not format {missing_keys})"

    def format(
        self,
        error: Exception,
        **context: Any,
    ) -> FormattedError:
        """Format an exception into a detailed error message.

        Args:
            error: The exception to format.
            **context: Additional context variables for message formatting.

        Returns:
            FormattedError instance with all relevant information.
        """
        error_code = self.get_error_code(error)
        error_def = self.get_error_def(error_code)

        # Get details from the exception
        details = {}
        if isinstance(error, DSLightingError):
            details = getattr(error, "details", {}) or {}
            suggestion = getattr(error, "suggestion", None)
            if suggestion:
                # Use suggestion from exception if provided
                pass
            else:
                suggestion = self._custom_suggestions.get(
                    error_code,
                    error_def.suggestion if error_def else "",
                )
        else:
            suggestion = self._custom_suggestions.get(
                error_code,
                error_def.suggestion if error_def else "",
            )

        # Get the template - use i18n translation if enabled
        template = error_def.template
        if self.enable_i18n:
            lang = self.lang
            translated_template = get_error_message(error_code, lang, **context)
            if translated_template:
                template = translated_template
            translated_suggestion = get_error_suggestion(error_code, lang)
            if translated_suggestion and not self._custom_suggestions.get(error_code):
                suggestion = translated_suggestion

        # Format message
        message = self._format_template(template, details, **context)

        # Generate documentation URL
        if error_def and error_def.doc_url:
            doc_url = error_def.doc_url
        else:
            doc_url = f"{self.base_doc_url}/{error_code}"

        return FormattedError(
            code=error_code,
            message=message,
            suggestion=suggestion,
            doc_url=doc_url,
            details=details,
            severity=error_def.severity if error_def else "ERROR",
            category=error_def.category if error_def else "GENERAL",
        )

    def format_with_cause(
        self,
        error: Exception,
        include_traceback: bool = False,
        **context: Any,
    ) -> str:
        """Format an error with its cause chain.

        Args:
            error: The exception to format.
            include_traceback: Include traceback in output.
            **context: Additional context variables.

        Returns:
            Formatted string representation.
        """
        formatted = self.format(error, **context)
        lines = [str(formatted)]

        if include_traceback:
            import traceback
            lines.append(f"\nTraceback:\n{traceback.format_exc()}")

        # Handle chained exceptions
        if isinstance(error, DSLightingError) and error.cause:
            lines.append(f"\nCaused by: {error.cause}")

        return "\n".join(lines)

    def try_format(
        self, error: Exception, default_message: str = "Unknown error", **context: Any
    ) -> FormattedError:
        """Try to format an error, falling back to default if lookup fails.

        This is useful when you want to handle both known and unknown errors.

        Args:
            error: The exception to format.
            default_message: Default message if formatting fails.
            **context: Additional context variables.

        Returns:
            FormattedError instance.
        """
        try:
            return self.format(error, **context)
        except Exception:
            # Fallback for any unexpected formatting errors
            return FormattedError(
                code="DSL-000",
                message=default_message,
                suggestion="An unexpected error occurred during error formatting.",
                doc_url=f"{self.base_doc_url}/DSL-000",
                details={"original_error": str(error)},
                severity="ERROR",
                category="GENERAL",
            )

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about error registry.

        Returns:
            Dictionary with registry statistics.
        """
        codes = self.registry.list_codes()
        categories = {}
        for code in codes:
            definition = self.registry.get(code)
            if definition:
                cat = definition.category
                categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_errors": len(codes),
            "categories": categories,
            "i18n_enabled": self.enable_i18n,
        }


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
    formatter = ErrorFormatter(enable_i18n=enable_i18n, lang=lang)
    return formatter.format(error, **context)


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
    formatter = ErrorFormatter(enable_i18n=enable_i18n, lang=lang)
    formatted = formatter.try_format(error, default_message, **context)
    return str(formatted)


__all__ = [
    "ErrorFormatter",
    "FormattedError",
    "ErrorRegistry",
    "ErrorDefinition",
    "create_default_registry",
    "format_error",
    "safe_format",
]
