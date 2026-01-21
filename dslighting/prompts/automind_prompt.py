"""
DSLighting 2.0 - AutoMind Workflow Prompts

Re-exports all AutoMind workflow prompts from DSAT.

AutoMind is a planning + reasoning workflow with knowledge base (RAG).
"""

# Re-export all AutoMind prompt functions from DSAT
from dsat.prompts.automind_prompt import (
    create_stepwise_code_prompt,
    create_stepwise_debug_prompt,
)

__all__ = [
    "create_stepwise_code_prompt",
    "create_stepwise_debug_prompt",
]
