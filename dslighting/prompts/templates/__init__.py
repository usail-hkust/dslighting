"""
Prompt Templates - Standard Prompt Templates

Provides pre-built prompt templates for common data science tasks.

Modules:
- data_science.py: Prompts for ML modeling and EDA tasks
- debugging.py: Prompts for debugging and error fixing

Note:
    All exports are also re-exported from dslighting.prompts for convenience.
"""

from .data_science import create_modeling_prompt, create_eda_prompt
from .debugging import create_generic_debug_prompt

__all__ = [
    "create_modeling_prompt",
    "create_eda_prompt",
    "create_generic_debug_prompt",
]
