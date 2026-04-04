"""
Context Utilities for DSLighting

This module provides context management utilities for handling
conversation history, error messages, and knowledge documents.
"""

from itertools import groupby
import logging
from typing import List, Dict, Optional, Any

from dslighting.services.llm import LLMService

logger = logging.getLogger(__name__)

# Default character limits. These can be overridden per instance via the constructor.
DEFAULT_MAX_HISTORY_CHARS = 32000
DEFAULT_MAX_ERROR_CHARS = 8000
DEFAULT_MAX_KNOWLEDGE_CHARS = 8000
DEFAULT_MAX_OUTPUT_CHARS = 16000  # Maximum characters for execution output

# Backward compatibility aliases
MAX_HISTORY_CHARS = DEFAULT_MAX_HISTORY_CHARS
MAX_ERROR_CHARS = DEFAULT_MAX_ERROR_CHARS
MAX_KNOWLEDGE_CHARS = DEFAULT_MAX_KNOWLEDGE_CHARS
MAX_OUTPUT_CHARS = DEFAULT_MAX_OUTPUT_CHARS


class ContextManager:
    """
    A utility for intelligently building prompt context to prevent overflow.
    It uses summarization, windowing, and truncation to manage context size.

    All character limits are configurable via the constructor or by setting
    instance attributes after initialization.
    """
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        max_history_chars: int = DEFAULT_MAX_HISTORY_CHARS,
        max_error_chars: int = DEFAULT_MAX_ERROR_CHARS,
        max_knowledge_chars: int = DEFAULT_MAX_KNOWLEDGE_CHARS,
        max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    ):
        self.llm_service = llm_service
        self.max_history_chars = max_history_chars
        self.max_error_chars = max_error_chars
        self.max_knowledge_chars = max_knowledge_chars
        self.max_output_chars = max_output_chars

    def build_history_context(self, history: List[Dict[str, Any]], key_order: List[str]) -> str:
        """
        Builds a context string from a list of historical events using a windowing strategy.

        Args:
            history: A list of dictionary-like objects representing historical steps.
            key_order: The keys to extract from each history object and their order.

        Returns:
            A formatted string of the most recent history that fits within the budget.
        """
        if not history:
            return "No history available."

        context_parts = []
        total_chars = 0

        # Iterate backwards from the most recent history
        for item in reversed(history):
            part = "\n".join([f"{key.capitalize()}: {item.get(key, 'N/A')}" for key in key_order])
            part_len = len(part)

            if total_chars + part_len > self.max_history_chars:
                logger.warning("History context truncated to fit budget.")
                break

            context_parts.append(part)
            total_chars += part_len

        # Reverse again to restore chronological order
        final_context = "\n---\n".join(reversed(context_parts))

        if len(history) > len(context_parts):
            final_context = f"[... {len(history) - len(context_parts)} older steps summarized ...]\n\n{final_context}"

        return final_context

    def summarize_error(self, stderr: str, exc_type: Optional[str] = None) -> str:
        """
        Extracts the most relevant parts of a long error message.
        """
        if not stderr:
            return "No error output."

        # Prioritize the exception type if available
        summary = f"Exception Type: {exc_type}\n\n" if exc_type else ""

        if len(stderr) > self.max_error_chars:
            # Keep the beginning and the end of the traceback
            head = stderr[:self.max_error_chars // 2]
            tail = stderr[-self.max_error_chars // 2:]
            summary += f"Traceback (truncated):\n{head}\n[...]\n{tail}"
            logger.warning("Error context truncated to fit budget.")
        else:
            summary += f"Traceback:\n{stderr}"

        return summary

    async def summarize_knowledge(self, knowledge_docs: List[str], task_goal: str) -> str:
        """
        Uses an LLM to summarize a list of retrieved documents into a concise
        knowledge block relevant to the task.
        """
        if not knowledge_docs:
            return "No relevant knowledge was retrieved for this task."
        if not self.llm_service:
            logger.warning("LLMService not provided to ContextManager; returning raw knowledge.")
            return "\n\n".join(knowledge_docs)[:self.max_knowledge_chars]

        full_knowledge = "\n\n---\n\n".join(knowledge_docs)

        if len(full_knowledge) < self.max_knowledge_chars:
            return full_knowledge

        logger.info("Retrieved knowledge is too long; summarizing with LLM...")
        prompt = (
            f"The user is trying to achieve the following goal: '{task_goal}'.\n\n"
            "The following are retrieved documents that might be helpful. Summarize the most critical "
            "patterns, code snippets, and strategies from these documents that are directly relevant "
            "to the user's goal. Be concise."
            f"\n\n# DOCUMENTS\n{full_knowledge}"
        )

        summary = await self.llm_service.call(prompt)
        return summary


def summarize_repetitive_logs(log_text: str, min_repeats: int = 3) -> str:
    """
    Summarizes consecutive, identical lines in a log string.

    Args:
        log_text: The raw log output.
        min_repeats: The minimum number of consecutive repeats to summarize.

    Returns:
        A cleaned log string with repeated lines summarized.
    """
    if not log_text:
        return ""

    lines = log_text.strip().split('\n')
    summarized_lines = []

    # Use groupby to find consecutive identical elements
    for line, group in groupby(lines):
        count = len(list(group))
        if count >= min_repeats:
            # Add a summary line for the repeated block
            summarized_lines.append(f"<{line.strip()} (repeated {count} times)>")
        else:
            # If not repeated enough, add the lines back as they were
            summarized_lines.extend([line] * count)

    return '\n'.join(summarized_lines)


def truncate_output(
    output: str,
    max_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
) -> str:
    """
    Truncates long output by keeping the beginning and end portions.
    This is useful when execution output exceeds max_seq_len limits.

    Args:
        output: The raw execution output.
        max_chars: Maximum allowed characters (default: DEFAULT_MAX_OUTPUT_CHARS).

    Returns:
        Truncated output with truncation notice if needed.
    """
    if not output:
        return ""

    if len(output) <= max_chars:
        return output

    # Keep the first and last portions
    head_size = max_chars // 2
    tail_size = max_chars - head_size

    head = output[:head_size]
    tail = output[-tail_size:]

    truncation_notice = (
        f"\n\n... [TRUNCATED: {len(output) - max_chars} characters omitted "
        f"to prevent context overflow] ...\n\n"
    )

    logger.warning(f"Output truncated from {len(output)} to {max_chars} characters.")
    return head + truncation_notice + tail


def hard_truncate_chars(
    output: str,
    max_chars: int,
    *,
    marker_template: str = "\n...[TRUNCATED {omitted} chars]...\n",
) -> str:
    """
    Strictly truncate text to at most ``max_chars`` characters.

    Unlike ``truncate_output()``, this helper is intended for prompt-budget
    enforcement. The returned string is guaranteed to satisfy
    ``len(result) <= max_chars``.
    """
    if not output or max_chars <= 0:
        return ""

    if len(output) <= max_chars:
        return output

    if max_chars <= 3:
        return "." * max_chars

    omitted = len(output) - max_chars
    marker = marker_template.format(omitted=max(0, omitted))
    if len(marker) >= max_chars:
        return output[: max_chars - 3] + "..."

    remaining = max_chars - len(marker)
    head_size = remaining // 2
    tail_size = remaining - head_size
    return output[:head_size] + marker + output[-tail_size:]


def hard_truncate_head_tail(
    output: str,
    max_chars: int,
    *,
    head_ratio: float = 0.5,
    marker_template: str = "\n...[TRUNCATED {omitted} chars]...\n",
) -> str:
    """
    Strictly truncate text while preserving configurable head/tail proportions.

    This is useful for long observations where both the beginning and end are
    informative. The return value is always ``<= max_chars`` characters.
    """
    if not output or max_chars <= 0:
        return ""

    if len(output) <= max_chars:
        return output

    if max_chars <= 3:
        return "." * max_chars

    ratio = min(max(head_ratio, 0.0), 1.0)
    omitted = len(output) - max_chars
    marker = marker_template.format(omitted=max(0, omitted))
    if len(marker) >= max_chars:
        return output[: max_chars - 3] + "..."

    remaining = max_chars - len(marker)
    head_size = int(remaining * ratio)
    tail_size = remaining - head_size
    return output[:head_size] + marker + output[-tail_size:]
