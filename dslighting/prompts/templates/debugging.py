"""
Debugging Prompt Templates

Standard prompts for debugging and error fixing.
"""

from typing import Optional
from ..base import create_prompt_template


def create_debug_prompt(
    code: str,
    error: str,
    context: Optional[str] = None,
) -> str:
    """
    Create a debugging prompt.

    Args:
        code: The code that has an error
        error: The error message or traceback
        context: Additional context about the task

    Returns:
        Formatted debugging prompt
    """
    prompt_dict = {
        "Role": "You are an expert Python programmer and debugger.",
        "Task": "Fix the error in the provided code.",
        "Context": context or "Data science/ML task",
        "Code": code,
        "Error": error,
        "Instructions": {
            "Goal": "Understand the error and provide corrected code",
            "Requirements": [
                "Analyze the error carefully",
                "Identify the root cause",
                "Provide a corrected version of the code",
                "Explain what was wrong and how it was fixed",
                "Ensure the fix doesn't break other functionality",
            ],
        }
    }

    return create_prompt_template(prompt_dict)
