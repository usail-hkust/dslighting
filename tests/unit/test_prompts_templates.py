"""
Tests for prompt templates.

These tests verify:
- Data science prompt templates (modeling, EDA)
- Debugging prompt templates
- Common prompt utilities
"""

import sys
import os

# Add the project root to path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _project_root)

import pytest
from typing import Dict, Any, List, Optional

# Import functions from templates modules
from dslighting.prompts.templates.data_science import (
    create_modeling_prompt,
    create_eda_prompt,
)
from dslighting.prompts.templates.debugging import (
    create_generic_debug_prompt,
)
from dslighting.prompts.common import (
    create_draft_prompt,
    _get_common_guidelines,
)
from dslighting.prompts.base import dict_to_str


class TestCreateModelingPrompt:
    """Tests for create_modeling_prompt function."""

    def test_basic_prompt(self):
        """Test basic modeling prompt creation."""
        result = create_modeling_prompt(
            task_type="regression",
            data_description="House prices dataset with 1000 rows",
            target_variable="price"
        )

        assert "## Role" in result
        assert "Machine Learning Engineer" in result or "Data Scientist" in result
        assert "## Task" in result
        assert "regression" in result
        assert "price" in result

    def test_classification_task(self):
        """Test classification task type."""
        result = create_modeling_prompt(
            task_type="classification",
            data_description="Iris dataset",
            target_variable="species"
        )

        assert "classification" in result
        assert "species" in result

    def test_with_requirements(self):
        """Test prompt with additional requirements."""
        result = create_modeling_prompt(
            task_type="regression",
            data_description="Dataset",
            target_variable="target",
            requirements=["Use ensemble methods", "Handle missing values"]
        )

        # Check that requirements are included
        assert "ensemble" in result.lower() or "Handle" in result

    def test_includes_guidelines(self):
        """Test that common guidelines are included."""
        result = create_modeling_prompt(
            task_type="regression",
            data_description="Dataset",
            target_variable="target"
        )

        # Should include common guidelines
        assert "Code Quality" in result or "cross-validation" in result

    def test_includes_submission_instruction(self):
        """Test that submission.csv instruction is present."""
        result = create_modeling_prompt(
            task_type="regression",
            data_description="Dataset",
            target_variable="target"
        )

        assert "submission.csv" in result

    def test_includes_eda_instruction(self):
        """Test that EDA instruction is present."""
        result = create_modeling_prompt(
            task_type="regression",
            data_description="Dataset",
            target_variable="target"
        )

        assert "exploratory data analysis" in result.lower() or "EDA" in result


class TestCreateEdaPrompt:
    """Tests for create_eda_prompt function."""

    def test_basic_eda_prompt(self):
        """Test basic EDA prompt creation."""
        result = create_eda_prompt(
            data_description="Sales data from 2020-2023"
        )

        assert "## Role" in result
        assert "Data Analyst" in result or "expert" in result.lower()
        assert "## Task" in result
        assert "EDA" in result or "Exploratory Data Analysis" in result

    def test_default_focus_areas(self):
        """Test that default focus areas are included."""
        result = create_eda_prompt(
            data_description="Dataset"
        )

        # Default focus areas
        assert "Data quality" in result or "missing values" in result
        assert "Distribution" in result
        assert "Correlations" in result
        assert "Outliers" in result

    def test_custom_focus_areas(self):
        """Test EDA prompt with custom focus areas."""
        result = create_eda_prompt(
            data_description="Dataset",
            focus_areas=["Time series patterns", "Seasonality", "Trends"]
        )

        assert "Time series patterns" in result
        assert "Seasonality" in result
        assert "Trends" in result

    def test_includes_requirements(self):
        """Test that EDA requirements are included."""
        result = create_eda_prompt(
            data_description="Dataset"
        )

        assert "summary statistics" in result
        assert "visualizations" in result or "visualisations" in result

    def test_includes_reporting(self):
        """Test that reporting requirement is included."""
        result = create_eda_prompt(
            data_description="Dataset"
        )

        assert "Report" in result or "findings" in result


class TestCreateDebugPrompt:
    """Tests for create_generic_debug_prompt function."""

    def test_basic_debug_prompt(self):
        """Test basic debug prompt creation."""
        code = "def add(a, b):\n    return a + b"
        error = "TypeError: unsupported operand type(s) for +: 'str' and 'str'"

        result = create_generic_debug_prompt(code=code, error=error)

        assert "## Role" in result
        assert "debugger" in result.lower() or "programmer" in result.lower()
        assert "## Task" in result
        assert "Fix the error" in result

    def test_includes_code(self):
        """Test that code is included in prompt."""
        code = "print(undefined_variable)"
        error = "NameError: name 'undefined_variable' is not defined"

        result = create_generic_debug_prompt(code=code, error=error)

        assert "undefined_variable" in result

    def test_includes_error(self):
        """Test that error message is included."""
        code = "x = 1 / 0"
        error = "ZeroDivisionError: division by zero"

        result = create_generic_debug_prompt(code=code, error=error)

        assert "ZeroDivisionError" in result

    def test_with_context(self):
        """Test debug prompt with context."""
        code = "import pandas as pd\ndf = pd.read_csv('file.csv')"
        error = "FileNotFoundError: file.csv not found"

        result = create_generic_debug_prompt(
            code=code,
            error=error,
            context="Loading training data"
        )

        assert "Loading training data" in result

    def test_default_context(self):
        """Test that default context is used when not provided."""
        code = "x = 1"
        error = "Error"

        result = create_generic_debug_prompt(code=code, error=error)

        # Default context should be present
        assert "Data science/ML task" in result

    def test_includes_fix_requirements(self):
        """Test that fix requirements are included."""
        code = "x = 1"
        error = "Error"

        result = create_generic_debug_prompt(code=code, error=error)

        # Should include requirements about providing corrected code and explanation
        assert "corrected" in result.lower() or "Explain" in result

    def test_includes_analysis_requirements(self):
        """Test that error analysis requirements are included."""
        code = "x = 1"
        error = "Error"

        result = create_generic_debug_prompt(code=code, error=error)

        assert "Analyze" in result or "root cause" in result.lower()


class TestCommonPromptUtilities:
    """Tests for common prompt utilities."""

    def testdict_to_str_simple(self):
        """Test dict_to_str with simple dictionary."""
        d = {"key": "value"}
        result = dict_to_str(d)

        assert "key:" in result
        assert "value" in result

    def testdict_to_str_nested(self):
        """Test dict_to_str with nested dictionary."""
        d = {
            "outer": {
                "inner": "value"
            }
        }
        result = dict_to_str(d)

        assert "outer:" in result
        assert "inner:" in result

    def testdict_to_str_with_list(self):
        """Test dict_to_str with list values."""
        d = {"items": ["a", "b", "c"]}
        result = dict_to_str(d)

        assert "items:" in result
        assert "- a" in result
        assert "- b" in result

    def testdict_to_str_indentation(self):
        """Test that indentation is applied correctly."""
        d = {"level1": {"level2": {"level3": "deep"}}}
        result = dict_to_str(d, indent=0)

        # Should have increasing indentation for nested levels
        lines = result.split("\n")
        # Check that nested levels have more indentation
        assert any(line.startswith("  ") for line in lines)

    def test_get_common_guidelines(self):
        """Test _get_common_guidelines function."""
        result = _get_common_guidelines()

        assert isinstance(result, dict)
        assert "Response Format" in result or "Implementation Guidelines" in result


class TestCreateDraftPrompt:
    """Tests for create_draft_prompt function."""

    def test_basic_draft_prompt(self):
        """Test basic draft prompt creation."""
        task_context = {
            "goal_and_data": "Build a model for prediction",
            "io_instructions": "Save predictions to submission.csv"
        }
        memory_summary = "Previous attempt failed due to overfitting"

        result = create_draft_prompt(
            task_context=task_context,
            memory_summary=memory_summary
        )

        # common.py uses "Role:" format instead of "## Role"
        assert "Role:" in result or "## Role" in result
        assert "goal" in result.lower() or "Goal" in result
        assert "Memory" in result or "memory" in result or "Past" in result

    def test_with_retrieved_knowledge(self):
        """Test draft prompt with retrieved knowledge."""
        task_context = {
            "goal_and_data": "Task description",
            "io_instructions": "I/O instructions"
        }
        memory_summary = "Memory"
        retrieved_knowledge = "Use XGBoost for this task"

        result = create_draft_prompt(
            task_context=task_context,
            memory_summary=memory_summary,
            retrieved_knowledge=retrieved_knowledge
        )

        assert "XGBoost" in result

    def test_with_extra_context(self):
        """Test draft prompt with extra context."""
        task_context = {
            "goal_and_data": "Task description",
            "io_instructions": "I/O instructions"
        }
        memory_summary = "Memory"
        extra_context = "Data has many missing values"

        result = create_draft_prompt(
            task_context=task_context,
            memory_summary=memory_summary,
            extra_context=extra_context
        )

        assert "missing values" in result

    def test_empty_retrieved_knowledge(self):
        """Test that empty retrieved knowledge uses default."""
        task_context = {
            "goal_and_data": "Task",
            "io_instructions": "I/O"
        }
        memory_summary = "Memory"

        result = create_draft_prompt(
            task_context=task_context,
            memory_summary=memory_summary,
            retrieved_knowledge=None
        )

        # Should contain default message
        assert "No relevant knowledge" in result

    def test_contains_io_requirements(self):
        """Test that I/O requirements are included."""
        task_context = {
            "goal_and_data": "Task",
            "io_instructions": "Save to submission.csv"
        }
        memory_summary = "Memory"

        result = create_draft_prompt(
            task_context=task_context,
            memory_summary=memory_summary
        )

        assert "submission.csv" in result or "REQUIREMENTS" in result

    def test_contains_instructions(self):
        """Test that instructions are included."""
        task_context = {
            "goal_and_data": "Task",
            "io_instructions": "I/O"
        }
        memory_summary = "Memory"

        result = create_draft_prompt(
            task_context=task_context,
            memory_summary=memory_summary
        )

        assert "Instructions" in result or "Goal" in result


class TestTemplateIntegration:
    """Integration tests for template modules."""

    def test_templates_importable(self):
        """Test that templates can be imported."""
        # This is a basic sanity check
        assert callable(create_modeling_prompt)
        assert callable(create_eda_prompt)
        assert callable(create_generic_debug_prompt)

    def test_templates_return_strings(self):
        """Test that template functions return strings."""
        modeling_result = create_modeling_prompt(
            task_type="regression",
            data_description="Data",
            target_variable="target"
        )
        eda_result = create_eda_prompt(data_description="Data")
        debug_result = create_generic_debug_prompt(code="x = 1", error="Error")

        assert isinstance(modeling_result, str)
        assert isinstance(eda_result, str)
        assert isinstance(debug_result, str)

    def test_templates_not_empty(self):
        """Test that template functions return non-empty strings."""
        modeling_result = create_modeling_prompt(
            task_type="regression",
            data_description="Data",
            target_variable="target"
        )
        eda_result = create_eda_prompt(data_description="Data")
        debug_result = create_generic_debug_prompt(code="x = 1", error="Error")

        assert len(modeling_result) > 0
        assert len(eda_result) > 0
        assert len(debug_result) > 0

    def test_templates_contain_role(self):
        """Test that all templates contain role sections."""
        modeling_result = create_modeling_prompt(
            task_type="regression",
            data_description="Data",
            target_variable="target"
        )
        eda_result = create_eda_prompt(data_description="Data")
        debug_result = create_generic_debug_prompt(code="x = 1", error="Error")

        assert "Role" in modeling_result
        assert "Role" in eda_result
        assert "Role" in debug_result

    def test_templates_contain_task(self):
        """Test that all templates contain task sections."""
        modeling_result = create_modeling_prompt(
            task_type="regression",
            data_description="Data",
            target_variable="target"
        )
        eda_result = create_eda_prompt(data_description="Data")
        debug_result = create_generic_debug_prompt(code="x = 1", error="Error")

        # Check for task-related content
        content = modeling_result + eda_result + debug_result
        assert "Task" in content or "Fix" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
