"""
PromptBuilder - Fluent API for Building Prompts

Provides a convenient way to construct prompts incrementally.
"""

from typing import List, Optional


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
