"""
Base Prompt Utilities

Provides fundamental prompt construction utilities.
"""

from typing import Dict, Any


def create_prompt_template(prompt_dict: Dict[str, Any]) -> str:
    """
    Create a prompt from a dictionary structure.

    This is the standard format for DSLighting prompts.
    Follows the JSON-based pattern from DSAT.

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

    Returns:
        Dictionary with standard guidelines
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
