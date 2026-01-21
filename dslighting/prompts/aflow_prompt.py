"""
DSLighting 2.0 - AFlow Workflow Prompts

Re-exports all AFlow workflow prompts from DSAT.

AFlow is a meta-optimization workflow that selects the best approach.
"""

# Re-export all AFlow prompt functions and classes from DSAT
from dsat.prompts.aflow_prompt import (
    get_operator_description,
    get_graph_optimize_prompt,
    GraphOptimize,
)

__all__ = [
    "get_operator_description",
    "get_graph_optimize_prompt",
    "GraphOptimize",
]
