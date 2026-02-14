"""
Debug Logger for DSLighting - Capture detailed LLM interactions

This module provides debug logging functionality for monitoring LLM inputs/outputs
with support for different detail levels and output formats.
"""

import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

# Configure debug logger
debug_logger = logging.getLogger("dslighting.debug")


class DebugLevel(Enum):
    """Debug detail levels"""
    BASIC = "basic"          # Only request/response summary
    DETAILED = "detailed"    # Include prompts, parameters, metadata
    VERBOSE = "verbose"      # Everything including raw data


class LLMDebugLogger:
    """
    Logger for capturing detailed LLM interaction data.

    Features:
    - Multiple detail levels (basic, detailed, verbose)
    - File and console output
    - Request ID tracking
    - Timing and token statistics
    - JSON formatted output for analysis
    """

    def __init__(
        self,
        enabled: bool = False,
        level: DebugLevel = DebugLevel.BASIC,
        output_dir: Optional[Path] = None,
        console_output: bool = True
    ):
        """
        Initialize the LLM Debug Logger.

        Args:
            enabled: Whether debug logging is enabled
            level: Detail level for logging
            output_dir: Directory to save debug logs (None = no file output)
            console_output: Whether to output to console
        """
        self.enabled = enabled
        self.level = level
        self.output_dir = Path(output_dir) if output_dir else None
        self.console_output = console_output
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_duration": 0.0
        }

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.output_dir / f"llm_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

    def log_request(
        self,
        request_id: str,
        model: str,
        messages: list,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log LLM request details"""
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        log_entry = {
            "type": "request",
            "request_id": request_id,
            "timestamp": timestamp,
            "model": model,
        }

        if self.level in [DebugLevel.DETAILED, DebugLevel.VERBOSE]:
            log_entry.update({
                "messages": messages,
                "parameters": parameters,
            })

        if self.level == DebugLevel.VERBOSE and metadata:
            log_entry["metadata"] = metadata

        self._write_log(log_entry)

    def log_response(
        self,
        request_id: str,
        model: str,
        response: Dict[str, Any],
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log LLM response details"""
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        log_entry = {
            "type": "response",
            "request_id": request_id,
            "timestamp": timestamp,
            "model": model,
            "duration": duration,
            "success": True
        }

        if self.level in [DebugLevel.DETAILED, DebugLevel.VERBOSE]:
            # Extract response content
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                log_entry["content"] = choice.get("message", {}).get("content", "")

            # Token usage
            if "usage" in response:
                usage = response["usage"]
                log_entry["tokens"] = {
                    "prompt": usage.get("prompt_tokens", 0),
                    "completion": usage.get("completion_tokens", 0),
                    "total": usage.get("total_tokens", 0)
                }

        if self.level == DebugLevel.VERBOSE:
            log_entry["raw_response"] = response
            if metadata:
                log_entry["metadata"] = metadata

        # Update statistics
        self.stats["total_requests"] += 1
        self.stats["successful_requests"] += 1
        if "tokens" in log_entry:
            self.stats["total_tokens"] += log_entry["tokens"]["total"]
        self.stats["total_duration"] += duration

        self._write_log(log_entry)

    def log_error(
        self,
        request_id: str,
        model: str,
        error: Exception,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log LLM error details"""
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        log_entry = {
            "type": "error",
            "request_id": request_id,
            "timestamp": timestamp,
            "model": model,
            "duration": duration,
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__
        }

        if self.level == DebugLevel.VERBOSE:
            log_entry["raw_error"] = repr(error)

        # Update statistics
        self.stats["total_requests"] += 1
        self.stats["failed_requests"] += 1
        self.stats["total_duration"] += duration

        self._write_log(log_entry)

    def _write_log(self, log_entry: Dict[str, Any]):
        """Write log entry to file and/or console"""
        # Console output
        if self.console_output:
            self._console_log(log_entry)

        # File output
        if self.output_dir:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _console_log(self, log_entry: Dict[str, Any]):
        """Pretty print to console"""
        log_type = log_entry.get("type", "unknown")
        request_id = log_entry.get("request_id", "")[:8]

        if log_type == "request":
            if self.level == DebugLevel.BASIC:
                debug_logger.info(f"🔵 LLM Request [{request_id}] - Model: {log_entry.get('model')}")
            else:
                debug_logger.info(f"🔵 LLM Request [{request_id}]")
                debug_logger.info(f"  Model: {log_entry.get('model')}")
                if "parameters" in log_entry:
                    debug_logger.info(f"  Parameters: {log_entry['parameters']}")
                if "messages" in log_entry:
                    messages = log_entry["messages"]
                    debug_logger.info(f"  Messages: {len(messages)} messages")
                    for i, msg in enumerate(messages):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        if self.level == DebugLevel.DETAILED:
                            debug_logger.info(f"    [{i+1}] {role}:\n{content}")
                        else:
                            debug_logger.info(f"    [{i+1}] {role}:\n{content}")

        elif log_type == "response":
            duration = log_entry.get("duration", 0)
            if self.level == DebugLevel.BASIC:
                tokens = log_entry.get("tokens", {}).get("total", "?")
                debug_logger.info(f"🟢 LLM Response [{request_id}] - {duration:.2f}s - {tokens} tokens")
            else:
                debug_logger.info(f"🟢 LLM Response [{request_id}]")
                debug_logger.info(f"  Duration: {duration:.2f}s")
                if "tokens" in log_entry:
                    debug_logger.info(f"  Tokens: {log_entry['tokens']}")
                if "content" in log_entry:
                    debug_logger.info(f"  Content:\n{log_entry['content']}")

        elif log_type == "error":
            duration = log_entry.get("duration", 0)
            error = log_entry.get("error", "Unknown error")
            debug_logger.error(f"🔴 LLM Error [{request_id}] - {duration:.2f}s - {error}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get debug session statistics"""
        stats = self.stats.copy()
        if stats["total_requests"] > 0:
            stats["average_duration"] = stats["total_duration"] / stats["total_requests"]
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
        return stats

    def print_statistics(self):
        """Print statistics summary"""
        stats = self.get_statistics()
        debug_logger.info("=" * 50)
        debug_logger.info("LLM Debug Session Statistics")
        debug_logger.info("=" * 50)
        debug_logger.info(f"Total Requests: {stats['total_requests']}")
        debug_logger.info(f"Successful: {stats['successful_requests']}")
        debug_logger.info(f"Failed: {stats['failed_requests']}")
        if stats['total_requests'] > 0:
            debug_logger.info(f"Success Rate: {stats.get('success_rate', 0)*100:.1f}%")
            debug_logger.info(f"Average Duration: {stats.get('average_duration', 0):.2f}s")
        debug_logger.info(f"Total Tokens: {stats['total_tokens']}")
        debug_logger.info("=" * 50)


# Global debug logger instance
_global_debug_logger: Optional[LLMDebugLogger] = None


def get_debug_logger() -> Optional[LLMDebugLogger]:
    """Get the global debug logger instance"""
    return _global_debug_logger


def init_debug_logger(
    enabled: bool = False,
    level: str = "basic",
    output_dir: Optional[str] = None,
    console_output: bool = True
) -> LLMDebugLogger:
    """
    Initialize the global debug logger.

    Args:
        enabled: Whether to enable debug logging
        level: Debug level ("basic", "detailed", "verbose")
        output_dir: Directory for log files
        console_output: Whether to output to console

    Returns:
        The initialized LLMDebugLogger instance
    """
    global _global_debug_logger

    debug_level = DebugLevel(level)
    _global_debug_logger = LLMDebugLogger(
        enabled=enabled,
        level=debug_level,
        output_dir=Path(output_dir) if output_dir else None,
        console_output=console_output
    )

    if enabled:
        debug_logger.info(f"🐛 LLM Debug Logger enabled (Level: {level})")
        if output_dir:
            debug_logger.info(f"📁 Log file: {_global_debug_logger.log_file}")

    return _global_debug_logger
