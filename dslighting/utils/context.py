"""
DSLighting Utils - Context Utilities

This module re-exports all context-related utilities from dsat.utils.context
for easy access through the dslighting namespace.
"""

# Re-export all context utilities from dsat.utils.context
try:
    from dsat.utils.context import (
        ContextManager,
        summarize_repetitive_logs,
    )
    _has_dsat_context = True
except ImportError:
    _has_dsat_context = False
    ContextManager = None
    summarize_repetitive_logs = None

__all__ = [
    "ContextManager",
    "summarize_repetitive_logs",
]
