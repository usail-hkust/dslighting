"""
Utility modules for DSLighting.
"""

from dslighting.utils.defaults import (
    DEFAULT_WORKFLOW,
    DEFAULT_LLM_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_ITERATIONS,
    WORKFLOW_RECOMMENDATIONS,
)

# Re-export dsat.utils.context for backward compatibility
try:
    from dsat.utils.context import (
        ContextManager,
        summarize_repetitive_logs,
    )
    _has_context = True
except ImportError:
    _has_context = False
    ContextManager = None
    summarize_repetitive_logs = None

__all__ = [
    "DEFAULT_WORKFLOW",
    "DEFAULT_LLM_MODEL",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_ITERATIONS",
    "WORKFLOW_RECOMMENDATIONS",
    # Context utilities
    "ContextManager",
    "summarize_repetitive_logs",
]
