"""Debug sinks."""

from dslighting.debug.sinks.base import DebugSink
from dslighting.debug.sinks.console import ConsoleSink
from dslighting.debug.sinks.jsonl import JsonlSink

__all__ = ["ConsoleSink", "DebugSink", "JsonlSink"]
