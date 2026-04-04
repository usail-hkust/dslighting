"""
Tests for prompts module core functionality.

These tests verify:
- create_prompt_template function
- PromptBuilder class (fluent API)
- StructuredPromptBuilder class
- Helper functions
"""

import sys
import os
import importlib.util

# Load the prompts module directly without triggering package init
_prompts_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "dslighting", "prompts"
)

# Load builder module
_builder_path = os.path.join(_prompts_path, "builder.py")
_builder_spec = importlib.util.spec_from_file_location("builder", _builder_path)
builder_module = importlib.util.module_from_spec(_builder_spec)
_builder_spec.loader.exec_module(builder_module)

# Load base module
_base_path = os.path.join(_prompts_path, "base.py")
_base_spec = importlib.util.spec_from_file_location("base", _base_path)
base_module = importlib.util.module_from_spec(_base_spec)
_base_spec.loader.exec_module(base_module)

# Extract classes and functions for use in tests
PromptBuilder = builder_module.PromptBuilder
StructuredPromptBuilder = builder_module.StructuredPromptBuilder
PromptTemplate = builder_module.PromptTemplate
create_structured_prompt = builder_module.create_structured_prompt
truncate_output = builder_module.truncate_output
format_code_block = builder_module.format_code_block
create_prompt_template = base_module.create_prompt_template
get_common_guidelines = base_module.get_common_guidelines

import pytest
from typing import Dict, Any, List, Optional


class TestCreatePromptTemplate:
    """Tests for create_prompt_template function."""

    def test_simple_key_value(self):
        """Test prompt with simple key-value pairs."""
        prompt_dict = {
            "Role": "You are an expert data scientist",
            "Task": "Solve this classification problem",
        }
        result = create_prompt_template(prompt_dict)

        assert "## Role" in result
        assert "You are an expert data scientist" in result
        assert "## Task" in result
        assert "Solve this classification problem" in result

    def test_nested_dictionary(self):
        """Test prompt with nested dictionary."""
        prompt_dict = {
            "Role": "You are an expert",
            "Instructions": {
                "Goal": "Achieve high accuracy",
                "Requirements": ["Use cross-validation", "Save predictions"]
            }
        }
        result = create_prompt_template(prompt_dict)

        assert "## Instructions" in result
        assert "**Goal:**" in result
        assert "Achieve high accuracy" in result
        assert "**Requirements:**" in result
        assert "Use cross-validation" in result
        assert "Save predictions" in result

    def test_mixed_structure(self):
        """Test prompt with mixed simple and nested structures."""
        prompt_dict = {
            "Role": "Expert Data Scientist",
            "Task": "Predict outcomes",
            "Data": {
                "Source": "/path/to/data.csv",
                "Rows": 1000,
                "Columns": ["feature1", "feature2", "target"]
            }
        }
        result = create_prompt_template(prompt_dict)

        assert "## Role" in result
        assert "## Task" in result
        assert "## Data" in result
        assert "**Source:**" in result
        assert "/path/to/data.csv" in result

    def test_empty_dict(self):
        """Test prompt with empty dictionary."""
        result = create_prompt_template({})
        assert result == ""

    def test_result_stripped(self):
        """Test that result is stripped of leading/trailing whitespace."""
        prompt_dict = {
            "Role": "Test role",
            "Task": "Test task",
        }
        result = create_prompt_template(prompt_dict)
        # Should not have leading newlines
        assert not result.startswith("\n")
        # Should not have trailing newlines after last content
        lines = result.split("\n")
        assert lines[-1] != ""

    def test_complex_nested_structure(self):
        """Test complex nested structure with multiple levels."""
        prompt_dict = {
            "Role": "ML Engineer",
            "Task": "Build model",
            "Instructions": {
                "Goal": "Maximize accuracy",
                "Steps": ["Load data", "Preprocess", "Train"],
                "Validation": {
                    "Method": "cross-validation",
                    "Folds": 5
                }
            }
        }
        result = create_prompt_template(prompt_dict)

        assert "## Instructions" in result
        assert "**Goal:**" in result
        assert "Maximize accuracy" in result
        assert "**Steps:**" in result
        assert "Load data" in result
        assert "**Validation:**" in result
        assert "Method" in result
        assert "cross-validation" in result


class TestGetCommonGuidelines:
    """Tests for get_common_guidelines function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        result = get_common_guidelines()
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Test that result has expected keys."""
        result = get_common_guidelines()
        assert "Code Quality" in result
        assert "Best Practices" in result
        assert "Output Requirements" in result

    def test_values_are_lists(self):
        """Test that values are lists of strings."""
        result = get_common_guidelines()
        for key, value in result.items():
            assert isinstance(value, list)
            for item in value:
                assert isinstance(item, str)


class TestPromptBuilder:
    """Tests for PromptBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create a fresh PromptBuilder for each test."""
        return PromptBuilder()

    def test_initial_state(self, builder):
        """Test that builder initializes with empty state."""
        assert len(builder.parts) == 0
        assert len(builder.sections) == 0

    def test_add_role(self, builder):
        """Test adding a role."""
        result = builder.add_role("Expert Data Scientist").build()

        assert "## Role" in result
        assert "Expert Data Scientist" in result

    def test_add_task(self, builder):
        """Test adding a task."""
        result = builder.add_task("Predict bike sharing demand").build()

        assert "## Task" in result
        assert "Predict bike sharing demand" in result

    def test_add_single_guideline(self, builder):
        """Test adding a single guideline."""
        result = builder.add_guideline("Use XGBoost").build()

        assert "## Guidelines" in result
        assert "Use XGBoost" in result

    def test_add_multiple_guidelines(self, builder):
        """Test adding multiple guidelines."""
        result = builder.add_guidelines(["Use XGBoost", "Use cross-validation"]).build()

        assert "## Guidelines" in result
        assert "Use XGBoost" in result
        assert "Use cross-validation" in result

    def test_add_context(self, builder):
        """Test adding context."""
        result = builder.add_context("Data", "/path/to/data.csv").build()

        assert "## Context" in result
        assert "**Data:**" in result
        assert "/path/to/data.csv" in result

    def test_add_requirement(self, builder):
        """Test adding a single requirement."""
        result = builder.add_requirement("Save predictions").build()

        assert "## Requirements" in result
        assert "Save predictions" in result

    def test_add_requirements(self, builder):
        """Test adding multiple requirements."""
        result = builder.add_requirements(["Save predictions", "Print metrics"]).build()

        assert "## Requirements" in result
        assert "Save predictions" in result
        assert "Print metrics" in result

    def test_add_custom_section(self, builder):
        """Test adding a custom section."""
        result = builder.add_custom("Notes", "Some notes here").build()

        assert "## Notes" in result
        assert "Some notes here" in result

    def test_method_chaining(self, builder):
        """Test that methods return self for chaining."""
        result = (
            builder
            .add_role("Expert")
            .add_task("Task")
            .add_guideline("Guideline")
            .add_context("Key", "Value")
        )

        assert result is builder

    def test_full_builder(self, builder):
        """Test complete builder workflow."""
        prompt = (
            builder
            .add_role("Expert Data Scientist")
            .add_task("Predict bike sharing demand")
            .add_guidelines(["Use XGBoost", "Use cross-validation"])
            .add_context("Data", "/path/to/data")
            .add_requirements(["Save predictions", "Print metrics"])
            .build()
        )

        assert "## Role" in prompt
        assert "## Task" in prompt
        assert "## Guidelines" in prompt
        assert "## Context" in prompt
        assert "## Requirements" in prompt
        assert "Expert Data Scientist" in prompt
        assert "Predict bike sharing demand" in prompt

    def test_clear(self, builder):
        """Test clearing the builder."""
        builder.add_role("Expert")
        builder.add_task("Task")

        builder.clear()

        assert len(builder.parts) == 0
        assert len(builder.sections) == 0

    def test_clear_reuse(self, builder):
        """Test clearing and reusing the builder."""
        prompt1 = builder.add_role("Role1").build()
        builder.clear()
        prompt2 = builder.add_role("Role2").build()

        assert "Role1" in prompt1
        assert "Role2" in prompt2
        assert prompt1 != prompt2


class TestStructuredPromptBuilder:
    """Tests for StructuredPromptBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create a fresh StructuredPromptBuilder for each test."""
        return StructuredPromptBuilder()

    def test_build_simple_dict(self, builder):
        """Test building prompt from simple dictionary."""
        prompt_dict = {
            "Role": "You are an expert",
            "Task": "Solve this task",
        }
        result = builder.build(prompt_dict)

        assert "Role:" in result
        assert "You are an expert" in result
        assert "Task:" in result
        assert "Solve this task" in result

    def test_build_nested_dict(self, builder):
        """Test building prompt with nested dictionaries."""
        prompt_dict = {
            "Role": "Expert",
            "Instructions": {
                "Goal": "High accuracy",
                "Steps": ["Step1", "Step2"]
            }
        }
        result = builder.build(prompt_dict)

        assert "Role:" in result
        assert "Instructions:" in result
        assert "Goal:" in result
        assert "High accuracy" in result
        assert "Steps:" in result

    def test_build_with_max_length(self):
        """Test that max_length truncates output."""
        builder = StructuredPromptBuilder(max_length=50)
        prompt_dict = {
            "Role": "This is a very long role description that exceeds the limit",
            "Task": "Task description",
        }
        result = builder.build(prompt_dict)

        assert "...[truncated]" in result
        # Result should be around 50 chars + "[truncated]" suffix
        # The actual length depends on where the truncation occurs
        assert len(result) <= 80  # Allow some margin for truncation

    def test_build_with_list_items(self, builder):
        """Test building prompt with list items."""
        prompt_dict = {
            "Role": "Expert",
            "Requirements": ["Req1", "Req2", "Req3"]
        }
        result = builder.build(prompt_dict)

        assert "Requirements:" in result
        assert "- Req1" in result
        assert "- Req2" in result
        assert "- Req3" in result

    def test_build_empty_dict(self, builder):
        """Test building prompt from empty dictionary."""
        result = builder.build({})
        assert result == ""


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_truncate_output_short(self):
        """Test truncate_output with text shorter than max_length."""
        result = truncate_output("Hello", 100)
        assert result == "Hello"

    def test_truncate_output_long(self):
        """Test truncate_output with text longer than max_length."""
        text = "This is a very long text that should be truncated"
        result = truncate_output(text, 20)
        # Should contain the truncation indicator
        assert "...[truncated]" in result
        assert result.startswith("This is a very ")
        assert len(result) > 20  # Should be longer than original max_length

    def test_truncate_output_exact_length(self):
        """Test truncate_output with text exactly at max_length."""
        result = truncate_output("Hello", 5)
        assert result == "Hello"

    def test_format_code_block(self):
        """Test format_code_block."""
        code = "print('Hello World')"
        result = format_code_block(code)

        assert "```python" in result
        assert "print('Hello World')" in result
        assert "```" in result

    def test_format_code_block_custom_language(self):
        """Test format_code_block with custom language."""
        code = "function test() { return 1; }"
        result = format_code_block(code, "javascript")

        assert "```javascript" in result
        assert "function test() { return 1; }" in result
        assert "```" in result


class TestCreateStructuredPrompt:
    """Tests for create_structured_prompt function."""

    def test_basic_creation(self):
        """Test basic prompt creation."""
        result = create_structured_prompt(
            role="Expert",
            task_goal="Predict values",
            instructions={"Goal": "Maximize accuracy"}
        )

        assert result["Role"] == "Expert"
        assert result["Task Goal"] == "Predict values"
        assert "Instructions" in result
        assert result["Instructions"]["Goal"] == "Maximize accuracy"

    def test_with_guidelines(self):
        """Test prompt creation with guidelines."""
        result = create_structured_prompt(
            role="Expert",
            task_goal="Task",
            instructions={"Goal": "Goal"},
            guidelines=["Use cross-validation", "Save models"]
        )

        assert "Guidelines" in result["Instructions"]
        assert "Use cross-validation" in result["Instructions"]["Guidelines"]

    def test_with_requirements(self):
        """Test prompt creation with requirements."""
        result = create_structured_prompt(
            role="Expert",
            task_goal="Task",
            instructions={"Goal": "Goal"},
            requirements=["Save predictions", "Print metrics"]
        )

        assert "Requirements" in result["Instructions"]
        assert "Save predictions" in result["Instructions"]["Requirements"]

    def test_with_context(self):
        """Test prompt creation with context."""
        result = create_structured_prompt(
            role="Expert",
            task_goal="Task",
            instructions={"Goal": "Goal"},
            context={"Data": "/path/to/data.csv"}
        )

        assert "Data" in result
        assert result["Data"] == "/path/to/data.csv"

    def test_without_optional_args(self):
        """Test prompt creation without optional arguments."""
        result = create_structured_prompt(
            role="Expert",
            task_goal="Task",
            instructions={"Goal": "Goal"}
        )

        assert result["Role"] == "Expert"
        assert result["Task Goal"] == "Task"
        assert "Guidelines" not in result["Instructions"]
        assert "Requirements" not in result["Instructions"]


class TestPromptTemplate:
    """Tests for PromptTemplate base class."""

    def test_get_input_schema_returns_none(self):
        """Test that get_input_schema returns None by default."""
        template = PromptTemplate()
        assert template.get_input_schema() is None

    def test_get_output_schema_returns_none(self):
        """Test that get_output_schema returns None by default."""
        template = PromptTemplate()
        assert template.get_output_schema() is None

    def test_build_raises_not_implemented(self):
        """Test that build raises NotImplementedError."""
        template = PromptTemplate()
        with pytest.raises(NotImplementedError):
            template.build()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
