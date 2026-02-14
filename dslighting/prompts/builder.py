"""
Prompt Builders

Unified prompt builder utilities (fluent + structured).

Provides:
- PromptBuilder: Fluent API for building prompts with method chaining
- StructuredPromptBuilder: Builds prompts from structured dictionaries
- PromptTemplate: Base class for defining prompt templates
- Helper functions for prompt manipulation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from dslighting.prompts.base import dict_to_str


class PromptBuilder:
    """
    Fluent API for building prompts.

    Example:
        prompt = (PromptBuilder()
                  .add_role("Expert Data Scientist")
                  .add_task("Predict bike sharing demand")
                  .add_guideline("Use XGBoost")
                  .add_context("Data", "/path/to/data")
                  .build())
    """

    def __init__(self):
        """Initialize an empty prompt builder."""
        self.parts: List[str] = []
        self.sections: Dict[str, List[str]] = {}

    def add_role(self, role: str) -> 'PromptBuilder':
        """
        Add a role definition.

        Args:
            role: The role to assign (e.g., "Expert Data Scientist")

        Returns:
            Self for method chaining
        """
        self.parts.append(f"## Role\n{role}\n")
        return self

    def add_task(self, task: str) -> 'PromptBuilder':
        """
        Add a task description.

        Args:
            task: The task to perform

        Returns:
            Self for method chaining
        """
        self.parts.append(f"## Task\n{task}\n")
        return self

    def add_guideline(self, guideline: str) -> 'PromptBuilder':
        """
        Add a single guideline.

        Args:
            guideline: A guideline to follow

        Returns:
            Self for method chaining
        """
        if "Guidelines" not in self.sections:
            self.sections["Guidelines"] = []
        self.sections["Guidelines"].append(guideline)
        return self

    def add_guidelines(self, guidelines: List[str]) -> 'PromptBuilder':
        """
        Add multiple guidelines.

        Args:
            guidelines: List of guidelines to follow

        Returns:
            Self for method chaining
        """
        if "Guidelines" not in self.sections:
            self.sections["Guidelines"] = []
        self.sections["Guidelines"].extend(guidelines)
        return self

    def add_context(self, key: str, value: str) -> 'PromptBuilder':
        """
        Add contextual information.

        Args:
            key: Context key
            value: Context value

        Returns:
            Self for method chaining
        """
        if "Context" not in self.sections:
            self.sections["Context"] = []
        self.sections["Context"].append(f"**{key}:** {value}")
        return self

    def add_requirement(self, requirement: str) -> 'PromptBuilder':
        """
        Add a requirement.

        Args:
            requirement: A specific requirement

        Returns:
            Self for method chaining
        """
        if "Requirements" not in self.sections:
            self.sections["Requirements"] = []
        self.sections["Requirements"].append(requirement)
        return self

    def add_requirements(self, requirements: List[str]) -> 'PromptBuilder':
        """
        Add multiple requirements.

        Args:
            requirements: List of requirements

        Returns:
            Self for method chaining
        """
        if "Requirements" not in self.sections:
            self.sections["Requirements"] = []
        self.sections["Requirements"].extend(requirements)
        return self

    def add_custom(self, title: str, content: str) -> 'PromptBuilder':
        """
        Add a custom section.

        Args:
            title: Section title
            content: Section content

        Returns:
            Self for method chaining
        """
        self.parts.append(f"## {title}\n{content}\n")
        return self

    def build(self) -> str:
        """
        Build the final prompt string.

        Returns:
            Complete prompt as a string
        """
        # Add all main parts
        result_parts = list(self.parts)

        # Add all sections
        for section_name, items in self.sections.items():
            result_parts.append(f"## {section_name}")
            for item in items:
                if item.startswith("**"):
                    # Already formatted
                    result_parts.append(item)
                else:
                    # Format as bullet point
                    result_parts.append(f"  - {item}")
            result_parts.append("")  # Blank line after section

        return "\n".join(result_parts).strip()

    def clear(self) -> 'PromptBuilder':
        """
        Clear all content and start fresh.

        Returns:
            Self for method chaining
        """
        self.parts.clear()
        self.sections.clear()
        return self

# Structured prompt utilities (merged from structured_builder.py)


class StructuredPromptBuilder:
    """
    Structured Prompt Builder

    Recommended format:
    ```python
    prompt_dict = {
        "Role": "You are an expert...",
        "Task Goal": "...",
        "Input Data": {...},
        "Instructions": {
            "Goal": "...",
            "Guideline": "...",
        }
    }
    ```

    Example:
        builder = StructuredPromptBuilder()
        prompt = builder.build(prompt_dict)
    """

    def __init__(self, max_length: Optional[int] = None):
        """
        Initialize the builder

        Args:
            max_length: Maximum prompt length (in characters)
        """
        self.max_length = max_length

    def build(self, prompt_dict: Dict[str, Any]) -> str:
        """
        Build the final prompt string

        Args:
            prompt_dict: Structured prompt dictionary

        Returns:
            Formatted prompt string
        """
        prompt = self._dict_to_str(prompt_dict, indent=0)

        # Truncate to max length
        if self.max_length and len(prompt) > self.max_length:
            prompt = prompt[:self.max_length] + "\n...[truncated]"

        return prompt

    def _dict_to_str(self, d: Dict, indent: int = 0) -> str:
        """
        Convert dictionary to formatted string.

        Note: This method delegates to the canonical dict_to_str function
        from base.py for consistency.
        """
        return dict_to_str(d, indent)


class PromptTemplate:
    """
    Prompt Template Base Class

    Recommended to inherit this class to define your prompt templates

    Example:
        class MyOperatorPrompt(PromptTemplate):
            def get_input_schema(self):
                return MyInputModel

            def get_output_schema(self):
                return MyOutputModel

            def build(self, **kwargs):
                return {
                    "Role": "You are...",
                    "Task": kwargs["task"],
                    ...
                }
    """

    def get_input_schema(self) -> Optional[BaseModel]:
        """
        Return the input Pydantic model

        Returns:
            Pydantic BaseModel class
        """
        return None

    def get_output_schema(self) -> Optional[BaseModel]:
        """
        Return the output Pydantic model

        Returns:
            Pydantic BaseModel class
        """
        return None

    def build(self, **kwargs) -> Dict[str, Any]:
        """
        Build prompt dictionary

        Args:
            **kwargs: Input parameters

        Returns:
            Prompt dictionary
        """
        raise NotImplementedError("Subclasses must implement build()")


# ============ Helper Functions ============

def truncate_output(text: str, max_length: int) -> str:
    """
    Truncate output to specified length

    Args:
        text: Original text
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n...[truncated]"


def format_code_block(code: str, language: str = "python") -> str:
    """
    Format code block

    Args:
        code: Code
        language: Language

    Returns:
        Formatted code block
    """
    return f"```{language}\n{code}\n```"


def create_structured_prompt(
    role: str,
    task_goal: str,
    instructions: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    guidelines: Optional[List[str]] = None,
    requirements: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Helper function to quickly create structured prompt

    Args:
        role: Role
        task_goal: Task goal
        instructions: Instructions dictionary
        context: Context information (optional)
        guidelines: Guidelines list (optional)
        requirements: Requirements list (optional)

    Returns:
        Prompt dictionary
    """
    prompt_dict = {
        "Role": role,
        "Task Goal": task_goal,
    }

    # Add context
    if context:
        prompt_dict.update(context)

    # Build instructions
    instructions_dict = dict(instructions)

    # Add guidelines
    if guidelines:
        instructions_dict["Guidelines"] = guidelines

    # Add requirements
    if requirements:
        instructions_dict["Requirements"] = requirements

    prompt_dict["Instructions"] = instructions_dict

    return prompt_dict


__all__ = [
    "PromptBuilder",
    "StructuredPromptBuilder",
    "PromptTemplate",
    "create_structured_prompt",
    "truncate_output",
    "format_code_block",
]
