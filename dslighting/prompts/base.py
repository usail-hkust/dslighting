"""
Base Prompt Utilities

Provides fundamental prompt construction utilities including:
- Dictionary-to-string conversion for prompts
- Prompt template creation
- Common guidelines for data science tasks

Note:
    This module contains the canonical implementation of dict_to_str().
    Other modules may have similar functions but should use this one
    to ensure consistency across the codebase.
"""

from typing import Dict, Any


_TOP_LEVEL_KEYS_WITH_LEADING_BLANK_LINE = {
    "CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED)",
}


def dict_to_str(d: Dict, indent: int = 0) -> str:
    """
    Convert a dictionary to a formatted string for prompts.

    This is the canonical function for converting dictionaries to prompt strings.
    Uses 2-space indentation for nested structures.

    Args:
        d: Dictionary to convert
        indent: Current indentation level (for recursion)

    Returns:
        Formatted string representation
    """
    lines = []
    prefix = "  " * indent

    for key, value in d.items():
        if (
            indent == 0
            and isinstance(key, str)
            and key in _TOP_LEVEL_KEYS_WITH_LEADING_BLANK_LINE
            and lines
            and lines[-1] != ""
        ):
            lines.append("")

        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(dict_to_str(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}  -")
                    lines.append(dict_to_str(item, indent + 2))
                else:
                    lines.append(f"{prefix}  - {item}")
        else:
            lines.append(f"{prefix}{key}: {value}")

    return "\n".join(lines)


def create_prompt_template(prompt_dict: Dict[str, Any]) -> str:
    """
    Create a prompt from a dictionary structure.

    This is the standard format for DSLighting prompts.
    Follows the JSON-based pattern from DSLighting.

    Args:
        prompt_dict: Dictionary with prompt sections

    Returns:
        Formatted prompt string

    Example:
        prompt_dict = {
            "Role": "You are an expert data scientist",
            "Task": "Solve this classification problem",
            "Instructions": {
                "Goal": "Achieve high accuracy",
                "Requirements": ["Use cross-validation", "Save predictions"]
            }
        }
        prompt = create_prompt_template(prompt_dict)
    """
    sections = []

    for key, value in prompt_dict.items():
        if isinstance(value, dict):
            # Nested dictionary - format as subsections
            sections.append(f"## {key}")
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    # List items
                    sections.append(f"**{sub_key}:**")
                    for item in sub_value:
                        sections.append(f"  - {item}")
                else:
                    sections.append(f"**{sub_key}:** {sub_value}")
        else:
            # Simple key-value
            sections.append(f"## {key}\n{value}")

        sections.append("")  # Blank line between sections

    return "\n".join(sections).strip()


def get_common_guidelines() -> Dict[str, Any]:
    """
    Get common data science guidelines for prompts.

    This function provides standardized guidelines for data science tasks
    following DSLighting conventions. Use this function for template prompts.

    Returns:
        Dictionary with standard guidelines organized by category:
            - Code Quality: Best practices for code quality
            - Best Practices: ML/data science best practices
            - Output Requirements: Output format requirements
    """
    return {
        "Code Quality": [
            "Write clean, readable, and well-commented code",
            "Use meaningful variable names",
            "Include error handling where appropriate",
        ],
        "Best Practices": [
            "Use cross-validation for model evaluation",
            "Check for data quality issues (missing values, outliers)",
            "Scale/normalize features when necessary",
            "Save predictions in the required format",
        ],
        "Output Requirements": [
            "Print key metrics and results",
            "Save the final model and predictions",
            "Provide clear output messages",
        ],
    }


__all__ = [
    "create_prompt_template",
    "get_common_guidelines",
    "dict_to_str",
]
