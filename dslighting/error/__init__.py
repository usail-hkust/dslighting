"""
DSLighting Error Handling Module

This module provides unified error handling with:
- DSLightingError hierarchy with built-in formatting
- ErrorRegistry for predefined error definitions
- Internationalization support for error messages
- FormattedError dataclass for structured error output

Usage:
    # Recommended: Use DSLightingError with built-in formatting
    from dslighting.error import DSLightingError, ConfigurationError

    raise ConfigurationError(
        "Invalid model configuration",
        error_code="CFG-001",
        details={"model": "gpt-5", "provider": "openai"},
        suggestion="Check supported models at https://docs.dslighting.io/providers"
    )

    from dslighting.error import format_error
    formatted = format_error(exception)
"""

# Core exception hierarchy with built-in formatting
from dslighting.error.exceptions import (
    DSLightingError,
    ConfigurationError,
    WorkflowError,
    BenchmarkError,
    LLMServiceError,
    TaskError,
    WorkspaceError,
    DynamicImportError,
)

# Error formatting and registry
from dslighting.error.formatter import (
    FormattedError,
    ErrorRegistry,
    ErrorDefinition,
    format_error,
    safe_format,
)

# Internationalization support
from dslighting.error.i18n import (
    get_error_message,
    get_error_suggestion,
    set_error_language,
    get_error_language,
    SUPPORTED_ERROR_LANGUAGES,
    DEFAULT_ERROR_LANGUAGE,
)

__all__ = [
    # Exception hierarchy
    "DSLightingError",
    "ConfigurationError",
    "WorkflowError",
    "BenchmarkError",
    "LLMServiceError",
    "TaskError",
    "WorkspaceError",
    "DynamicImportError",
    # Error formatting
    "FormattedError",
    "ErrorRegistry",
    "ErrorDefinition",
    "format_error",
    "safe_format",
    # Internationalization
    "get_error_message",
    "get_error_suggestion",
    "set_error_language",
    "get_error_language",
    "SUPPORTED_ERROR_LANGUAGES",
    "DEFAULT_ERROR_LANGUAGE",
]
