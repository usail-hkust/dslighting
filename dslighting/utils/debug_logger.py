"""Legacy compatibility exports for the deprecated debug logger API.

New integrations should use ``dslighting.configure_logging(...)`` instead of
importing symbols from this module. This file remains only to avoid breaking
older code paths that still import the legacy debug logger helpers.
"""

from dslighting.debug.compat import DebugLevel, LLMDebugLogger, get_debug_logger, init_debug_logger

__all__ = [
    "DebugLevel",
    "LLMDebugLogger",
    "get_debug_logger",
    "init_debug_logger",
]
