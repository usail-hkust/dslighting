"""
DSLighting 2.0 - AutoKaggle Workflow Prompts

Re-exports all AutoKaggle workflow prompts from DSAT.

AutoKaggle is a multi-phase competition solver with dynamic planning.
"""

# Re-export all AutoKaggle prompt functions from DSAT
from dsat.prompts.autokaggle_prompt import (
    get_deconstructor_prompt,
    get_phase_planner_prompt,
    get_step_planner_prompt,
    get_developer_prompt,
    get_validator_prompt,
    get_reviewer_prompt,
    get_summarizer_prompt,
)

__all__ = [
    "get_deconstructor_prompt",
    "get_phase_planner_prompt",
    "get_step_planner_prompt",
    "get_developer_prompt",
    "get_validator_prompt",
    "get_reviewer_prompt",
    "get_summarizer_prompt",
]
