"""
DSLighting 2.0 - Common Prompt Utilities

Re-exports common prompt utilities from DSAT.
"""

# Re-export common prompt functions from DSAT
from dsat.prompts.common import (
    _dict_to_str,
    _get_common_guidelines,
    create_draft_prompt,
)

__all__ = [
    "_dict_to_str",
    "_get_common_guidelines",
    "create_draft_prompt",
]
