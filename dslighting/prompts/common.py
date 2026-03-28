"""
Common Prompt Utilities

Shared utilities for prompt construction across workflow modules.
This module provides helper functions used by workflow-specific prompt builders.

Note:
    This module uses dict_to_str from base.py for dictionary-to-string conversion.
    Use base.get_common_guidelines() for standardized guidelines in templates.
    Use _get_common_guidelines() for workflow-specific guidelines (different format).
"""

from typing import Dict, List, Optional

from dslighting.core.visualization_policy import (
    VisualizationPolicy,
    build_visualization_instruction_text,
)
from dslighting.prompts.base import dict_to_str


def _normalize_goal_and_data(goal_and_data: Optional[str]) -> str:
    """Normalize goal/data section to remove leading and trailing blank lines."""
    text = str(goal_and_data or "N/A").strip()
    return text or "N/A"


def _normalize_io_instructions(io_instructions: Optional[str]) -> str:
    """Normalize I/O instructions to avoid duplicate section headers and blank lines."""
    text = str(io_instructions or "N/A").strip()
    if not text:
        return "N/A"

    marker = "--- CRITICAL I/O REQUIREMENTS ---"
    if text.startswith(marker):
        text = text[len(marker):].lstrip("\n").strip()

    return text or "N/A"


def _get_common_guidelines(
    visualization_policy: VisualizationPolicy = VisualizationPolicy.NO_DISPLAY,
) -> Dict:
    """
    Returns workflow-specific common instructions for all prompts.

    This function provides guidelines optimized for workflow execution
    (AIDE, AutoKaggle, etc.) with emphasis on:
    - Response format requirements
    - Implementation constraints for self-contained scripts

    Use base.get_common_guidelines() for standardized data science guidelines.

    Returns:
        Dictionary with Response Format and Implementation Guidelines
    """
    return {
        "Response Format": (
            "Your response MUST start with a brief natural language plan (3-5 sentences), "
            "followed by a single, complete Python code block wrapped in ```python ... ```. "
            "Do not include any other text or headings."
        ),
        "Implementation Guidelines": [
            "The code must be a self-contained, single-file Python script.",
            "If the task involves modeling or optimization, print key metrics (e.g., validation scores) to standard output. Otherwise, ensure the output clearly presents the findings or results.",
            "Follow the CRITICAL I/O REQUIREMENTS provided in the task description precisely for all file operations.",
            "Do not use interactive elements like `input()` or `matplotlib.pyplot.show()`.",
            build_visualization_instruction_text(visualization_policy),
        ]
    }


__all__ = [
    "create_draft_prompt",
]

def create_draft_prompt(
    task_context: Dict,
    memory_summary: str,
    retrieved_knowledge: Optional[str] = None,
    extra_context: Optional[str] = None,
    visualization_policy: VisualizationPolicy = VisualizationPolicy.NO_DISPLAY,
) -> str:
    """
    Creates the system prompt for generating an initial solution draft.

    Args:
        task_context: MLE standard format dict with keys:
            - goal_and_data: Task description and data overview (DO NOT modify)
            - io_instructions: I/O requirements (DO NOT modify)
        memory_summary: Summary of previous attempts
        retrieved_knowledge: Optional knowledge from RAG/system
        extra_context: Optional additional context (e.g., data insights, analysis results)

    Returns:
        Formatted prompt string

    Note:
        IMPORTANT: Always keep task_context in MLE standard format.
        Use extra_context parameter to add additional information.
        This ensures compatibility with MLE data parsing and grading systems.
    """
    prompt_dict = {
        "Role": "You are an expert Data Scientist and AI Engineer.",
        "Task Goal and Data Overview": _normalize_goal_and_data(
            task_context.get("goal_and_data", "N/A")
        ),
        "Memory of Past Attempts": memory_summary,
        "Retrieved Knowledge": retrieved_knowledge or "No relevant knowledge was retrieved for this task.",
    }

    # Add extra context if provided (before I/O requirements)
    if extra_context:
        prompt_dict["Additional Context"] = extra_context

    # CRITICAL I/O REQUIREMENTS should come AFTER Additional Context but BEFORE Instructions
    # This ensures model sees data insights first, then I/O constraints, then implementation guidelines
    prompt_dict["CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)"] = _normalize_io_instructions(task_context.get("io_instructions", "N/A"))

    prompt_dict["Instructions"] = {
        "Goal": "Propose a simple but effective plan and implement it in Python" + (
            ", incorporating insights from the retrieved knowledge and additional context if applicable." if (retrieved_knowledge or extra_context) else "."
        ),
        "Design Guideline": "Your first solution should be straightforward and robust. Focus on correctly addressing the core requirements based on the data report AND the CRITICAL I/O REQUIREMENTS." + (
            " Consider the additional context provided above if applicable." if extra_context else ""
        ),
        **_get_common_guidelines(visualization_policy)
    }

    return dict_to_str(prompt_dict)
