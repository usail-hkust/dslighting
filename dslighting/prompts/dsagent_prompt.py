"""
DSLighting 2.0 - DSAgent Workflow Prompts

Re-exports all DSAgent workflow prompts from DSAT.

DSAgent is a structured operator-based workflow with logging.
"""

# Re-export all DSAgent prompt templates from DSAT
from dsat.prompts.dsagent_prompt import (
    PLAN_PROMPT_TEMPLATE,
    PROGRAMMER_PROMPT_TEMPLATE,
    DEBUGGER_PROMPT_TEMPLATE,
    LOGGER_PROMPT_TEMPLATE,
)

__all__ = [
    "PLAN_PROMPT_TEMPLATE",
    "PROGRAMMER_PROMPT_TEMPLATE",
    "DEBUGGER_PROMPT_TEMPLATE",
    "LOGGER_PROMPT_TEMPLATE",
]
