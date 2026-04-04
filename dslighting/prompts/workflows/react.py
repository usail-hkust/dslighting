"""
ReAct Workflow Prompts

Provides prompt templates for the ReAct workflow.
"""

from typing import Dict, Optional

from dslighting.prompts.base import dict_to_str
from dslighting.prompts.common import (
    _normalize_goal_and_data,
    _normalize_io_instructions,
)


def create_react_prompt(
    task_context: Dict,
    *,
    output_filename: Optional[str] = None,
) -> str:
    """Create the system prompt for the ReAct workflow."""
    _ = output_filename
    action_semantics = [
        "Every assistant reply MUST contain exactly two blocks in this order: <Think>...</Think> followed by either <Action>...</Action> or <Answer>...</Answer>.",
        "Do not output any text before, after, or outside these two blocks.",
        "Do not output <Observation> yourself. Observations are injected by the system after code execution.",
        "If your reply violates the protocol, the system may return <Feedback>...</Feedback>. You must fix the format on the next turn.",
        "Use <Action> only for executable Python code. The content of <Action> MUST be exactly one fenced ```python ... ``` block and nothing else.",
        "Use <Answer> only when the task is complete. The content of <Answer> MUST be plain text only and MUST NOT contain a code block.",
        "Never output <Final Answer> or any other completion tag variant.",
        "Always close every tag explicitly. In particular, finish completion replies with </Answer>.",
    ]

    prompt_dict = {
        "Role": "You are an expert Data Scientist and AI Engineer operating in a strict ReAct workflow.",
        "Task Goal and Data Overview": _normalize_goal_and_data(
            task_context.get("goal_and_data", "N/A")
        ),
        "CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)": _normalize_io_instructions(
            task_context.get("io_instructions", "N/A")
        ),
        "Instructions": {
            "Goal": "Solve the task step by step, using Python execution when needed, while strictly following the CRITICAL I/O REQUIREMENTS.",
            "Response Format": "Your response MUST contain exactly <Think>...</Think> and then either <Action>...</Action> or <Answer>...</Answer>.",
            "Action Semantics": action_semantics,
            "Execution Guidelines": [
                "Execute one step at a time.",
                "Any Python code must be self-contained and fully executable.",
                "Follow the CRITICAL I/O REQUIREMENTS precisely.",
                "Do not use interactive elements like `input()` or `matplotlib.pyplot.show()`.",
                "Do not rely on plotting or visualization to inspect the dataset. Print textual or numerical observations instead.",
            ],
            "Termination Rule": "Stop writing code and return <Answer>...</Answer> only when no additional execution is needed.",
        },
    }
    return dict_to_str(prompt_dict)


__all__ = ["create_react_prompt"]
