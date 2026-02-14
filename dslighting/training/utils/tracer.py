"""
Trace Collection Utilities

Utilities for collecting and managing execution traces during training.
"""
from typing import Any, Dict, List


class TraceCollector:
    """
    Collector for storing and managing execution traces.

    Provides simple in-memory storage for trace data collected
    during training runs.
    """

    def __init__(self):
        self.traces: List[Dict[str, Any]] = []

    def add_trace(self, trace: Dict[str, Any]) -> None:
        """Add a trace entry to the collector."""
        self.traces.append(trace)

    def get_traces(self) -> List[Dict[str, Any]]:
        """Retrieve all collected traces."""
        return self.traces

    def clear(self) -> None:
        """Clear all collected traces."""
        self.traces.clear()


__all__ = ["TraceCollector"]
