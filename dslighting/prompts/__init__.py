"""
DSLighting Prompts - Unified entrypoint.

This module provides unified prompt construction utilities for DSLighting:

Builder Classes:
- PromptBuilder: Fluent API for building prompts with method chaining
- StructuredPromptBuilder: Builds prompts from structured dictionaries
- PromptTemplate: Base class for defining prompt templates

Template Functions:
- create_modeling_prompt: Create prompts for ML modeling tasks
- create_eda_prompt: Create prompts for exploratory data analysis
- create_generic_debug_prompt: Generic debugging prompt for any task type

Utility Functions:
- create_prompt_template: Convert dictionary to formatted prompt string
- get_common_guidelines: Get standardized data science guidelines
- dict_to_str: Convert dictionary to formatted string
- create_structured_prompt: Helper to create structured prompts
"""

from dslighting.prompts.builder import (
    PromptBuilder,
    StructuredPromptBuilder,
    PromptTemplate,
    create_structured_prompt,
)
from dslighting.prompts.base import (
    create_prompt_template,
    get_common_guidelines,
    dict_to_str,
)
from dslighting.prompts.templates.data_science import (
    create_modeling_prompt,
    create_eda_prompt,
)
from dslighting.prompts.templates.debugging import (
    create_generic_debug_prompt,
)

__all__ = [
    # Builder classes
    "PromptBuilder",
    "StructuredPromptBuilder",
    "PromptTemplate",
    # Builder functions
    "create_structured_prompt",
    # Base utilities
    "create_prompt_template",
    "get_common_guidelines",
    "dict_to_str",
    # Template functions
    "create_modeling_prompt",
    "create_eda_prompt",
    "create_generic_debug_prompt",
]
