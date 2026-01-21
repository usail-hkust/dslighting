"""
DSLighting 2.0 - AIDE Workflow Prompts

Re-exports all AIDE workflow prompts from DSAT.

AIDE is an iterative code generation workflow with review cycles.
"""

# Re-export all AIDE prompt functions from DSAT
from dsat.prompts.aide_prompt import (
    create_improve_prompt,
    create_debug_prompt,
)

__all__ = [
    "create_improve_prompt",
    "create_debug_prompt",
]
