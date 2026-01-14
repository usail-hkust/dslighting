"""
Context Management Utilities for Web UI

Provides intelligent truncation of long outputs (errors, stdout, stderr)
to prevent overflowing agent context windows, following DSAT's approach.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Use character count as a simple, fast proxy for token count
# These limits match DSAT's context management
MAX_ERROR_CHARS = 8000      # Maximum characters for error messages
MAX_OUTPUT_CHARS = 16000   # Maximum characters for execution output (stdout/stderr)

__all__ = [
    'truncate_error',
    'truncate_output',
    'format_error_for_agent',
    'extract_essential_error_info',
    'truncate_context',
    'MAX_ERROR_CHARS',
    'MAX_OUTPUT_CHARS'
]


def truncate_error(stderr: str, exc_type: Optional[str] = None) -> str:
    """
    Intelligently truncates long error messages to fit within context budget.

    Strategy:
    - If error is short enough, return as-is
    - If error is too long, keep the head and tail, replace middle with [...]
    - This preserves both the error type and the final error message

    Args:
        stderr: The error/traceback message
        exc_type: Optional exception type name

    Returns:
        Truncated error message with context
    """
    if not stderr:
        return "No error output."

    # Build summary with exception type if available
    summary = f"Exception Type: {exc_type}\n\n" if exc_type else ""

    if len(stderr) > MAX_ERROR_CHARS:
        # Keep the beginning (stack frames) and the end (final error)
        head = stderr[:MAX_ERROR_CHARS // 2]
        tail = stderr[-MAX_ERROR_CHARS // 2:]
        summary += f"Traceback (truncated, total {len(stderr)} chars):\n{head}\n\n[... {len(stderr) - MAX_ERROR_CHARS} chars omitted ...]\n\n{tail}"
        logger.warning(f"Error context truncated from {len(stderr)} to {MAX_ERROR_CHARS} chars")
    else:
        summary += f"Traceback:\n{stderr}"

    return summary


def truncate_output(output: str, output_type: str = "output") -> str:
    """
    Intelligently truncates long execution output (stdout/stderr).

    Strategy:
    - Prioritize the beginning (initial output) and end (final status)
    - For structured output (like data frames), try to preserve structure

    Args:
        output: The execution output
        output_type: Type of output ("stdout", "stderr", etc.)

    Returns:
        Truncated output with context indicator
    """
    if not output:
        return f"No {output_type} output."

    if len(output) <= MAX_OUTPUT_CHARS:
        return output

    # Try to preserve structure by splitting on lines
    lines = output.split('\n')

    # Keep first 60% and last 40% of lines
    total_lines = len(lines)
    head_line_count = int(total_lines * 0.6)
    tail_line_count = int(total_lines * 0.4)

    head_lines = lines[:head_line_count]
    tail_lines = lines[-tail_line_count:] if tail_line_count > 0 else []

    head = '\n'.join(head_lines)
    tail = '\n'.join(tail_lines)

    truncated = f"{head}\n\n[... {len(lines) - head_line_count - tail_line_count} lines omitted ({len(output) - MAX_OUTPUT_CHARS} chars) ...]\n\n{tail}"

    logger.info(f"{output_type} truncated from {len(output)} chars to ~{MAX_OUTPUT_CHARS} chars")
    return truncated


def extract_essential_error_info(stderr: str) -> dict:
    """
    Extracts the most important error information for agent debugging.

    Looks for:
    - Exception type
    - Error message (last line of traceback)
    - File and line number of the error
    - Common error patterns

    Args:
        stderr: The error/traceback message

    Returns:
        Dictionary with essential error info
    """
    info = {
        "exception_type": None,
        "error_message": None,
        "file_line": None,
        "suggestion": None
    }

    if not stderr:
        return info

    lines = stderr.split('\n')

    # Extract exception type (e.g., "ValueError", "NameError")
    exc_match = re.search(r'(\w+Error):', stderr)
    if exc_match:
        info["exception_type"] = exc_match.group(1)

    # Extract error message (usually the last meaningful line)
    for line in reversed(lines):
        line = line.strip()
        if line and not line.startswith('File') and not line.startswith('Traceback') and not line.startswith('During'):
            info["error_message"] = line
            break

    # Extract file and line number (e.g., "File 'script.py', line 42")
    file_line_match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+)', stderr)
    if file_line_match:
        info["file_line"] = f"{file_line_match.group(1)}:{file_line_match.group(2)}"

    # Generate suggestion based on error type
    if info["exception_type"]:
        suggestions = {
            "NameError": "Check for typos in variable names or ensure variables are defined before use.",
            "ValueError": "Check if the input data format is correct or if values are within expected ranges.",
            "TypeError": "Check if you're using the correct data types for operations.",
            "KeyError": "Check if the key exists in the dictionary or DataFrame.",
            "AttributeError": "Check if the object has the attribute you're trying to access.",
            "IndexError": "Check if the index is within the valid range.",
            "ImportError": "Check if the module is installed or if there's a circular import.",
            "SyntaxError": "Check for syntax errors like missing colons, brackets, or quotes.",
            "MemoryError": "The operation ran out of memory. Try processing data in smaller chunks.",
            "ZeroDivisionError": "Check for division by zero. Add guards to handle zero values."
        }
        info["suggestion"] = suggestions.get(info["exception_type"], "Review the error traceback for details.")

    return info


def format_error_for_agent(stderr: str, exc_type: Optional[str] = None) -> str:
    """
    Formats error message for agent consumption with context and suggestions.

    Combines:
    1. Essential error info (exception type, message, file/line)
    2. Truncated traceback
    3. Actionable suggestion

    Args:
        stderr: The error/traceback message
        exc_type: Optional exception type name

    Returns:
        Formatted error message ready for agent prompt
    """
    essential = extract_essential_error_info(stderr)
    truncated = truncate_error(stderr, exc_type)

    parts = []
    if essential["exception_type"]:
        parts.append(f"**Exception Type:** {essential['exception_type']}")
    if essential["error_message"]:
        parts.append(f"**Error Message:** {essential['error_message']}")
    if essential["file_line"]:
        parts.append(f"**Location:** {essential['file_line']}")
    if essential["suggestion"]:
        parts.append(f"**Suggestion:** {essential['suggestion']}")

    formatted = "\n".join(parts) + "\n\n**Full Traceback:**\n" + truncated

    return formatted


# Convenience function for quick truncation
def truncate_context(text: str, max_chars: int = MAX_ERROR_CHARS, text_type: str = "text") -> str:
    """
    Generic truncation function for any text content.

    Args:
        text: Text to truncate
        max_chars: Maximum characters to keep
        text_type: Type of text (for logging)

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_chars:
        return text

    head = text[:max_chars // 2]
    tail = text[-max_chars // 2:]
    omitted = len(text) - max_chars

    result = f"{head}\n\n[... {omitted} chars omitted ...]\n\n{tail}"
    logger.info(f"{text_type} truncated from {len(text)} to {max_chars} chars")

    return result
