"""
DSLighting 2.0 - Data Interpreter Workflow Prompts

Re-exports all Data Interpreter workflow prompts from DSAT.

Data Interpreter is a fast code execution loop in Jupyter.
"""

# Re-export all Data Interpreter prompt templates from DSAT
from dsat.prompts.data_interpreter_prompt import (
    PLAN_SYSTEM_MESSAGE,
    PLAN_PROMPT,
    GENERATE_CODE_PROMPT,
    REFLECT_AND_DEBUG_PROMPT,
    FINALIZE_OUTPUT_PROMPT,
)

__all__ = [
    "PLAN_SYSTEM_MESSAGE",
    "PLAN_PROMPT",
    "GENERATE_CODE_PROMPT",
    "REFLECT_AND_DEBUG_PROMPT",
    "FINALIZE_OUTPUT_PROMPT",
]
