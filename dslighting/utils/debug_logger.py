"""Compatibility exports for the legacy debug logger API."""

from dslighting.debug.compat import DebugLevel, LLMDebugLogger, get_debug_logger, init_debug_logger

__all__ = [
    "DebugLevel",
    "LLMDebugLogger",
    "get_debug_logger",
    "init_debug_logger",
]
