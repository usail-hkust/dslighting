"""
Prompt Templates - Standard Prompt Templates

Provides pre-built prompt templates for common data science tasks.
"""

from .data_science import create_modeling_prompt, create_eda_prompt
from .debugging import create_debug_prompt

__all__ = [
    "create_modeling_prompt",
    "create_eda_prompt",
    "create_debug_prompt",
]
