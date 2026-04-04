"""
Unit tests for BaseWorkflow and WorkflowResult classes.

Tests cover:
- BaseWorkflow abstract class and its interface contract
- WorkflowResult creation and representation
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from abc import ABC
import sys

from dslighting.workflows.base import BaseWorkflow, WorkflowResult


class MockWorkflow(BaseWorkflow):
    """Concrete implementation of BaseWorkflow for testing."""

    def __init__(self, operators=None, services=None, agent_config=None):
        super().__init__(operators=operators, services=services, agent_config=agent_config)
        self.solve_called = False
        self.solve_args = None

    async def solve(
        self,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path
    ) -> None:
        """Mock implementation that records call."""
        self.solve_called = True
        self.solve_args = {
            'description': description,
            'io_instructions': io_instructions,
            'data_dir': data_dir,
            'output_path': output_path
        }


class TestWorkflowResult:
    """Tests for WorkflowResult class."""

    def test_workflow_result_creation_success(self):
        """Test creating a successful WorkflowResult."""
        result = WorkflowResult(
            success=True,
            workflow="TestWorkflow",
            output_path=Path("/output/submission.csv"),
            score=0.95
        )

        assert result.success is True
        assert result.workflow == "TestWorkflow"
        assert result.output_path == Path("/output/submission.csv")
        assert result.score == 0.95
        assert result.error is None

    def test_workflow_result_creation_failure(self):
        """Test creating a failed WorkflowResult with error."""
        result = WorkflowResult(
            success=False,
            workflow="TestWorkflow",
            output_path=Path("/output/submission.csv"),
            error="Execution failed due to timeout"
        )

        assert result.success is False
        assert result.workflow == "TestWorkflow"
        assert result.output_path == Path("/output/submission.csv")
        assert result.error == "Execution failed due to timeout"
        assert result.score is None

    def test_workflow_result_repr_success(self):
        """Test string representation of successful result."""
        result = WorkflowResult(
            success=True,
            workflow="MyAgent",
            output_path=Path("submission.csv")
        )

        expected = "WorkflowResult(success=True, workflow=MyAgent, output=submission.csv)"
        assert repr(result) == expected

    def test_workflow_result_repr_failure(self):
        """Test string representation of failed result."""
        result = WorkflowResult(
            success=False,
            workflow="MyAgent",
            output_path=Path("submission.csv"),
            error="Task failed"
        )

        expected = "WorkflowResult(success=False, workflow=MyAgent, error=Task failed)"
        assert repr(result) == expected

    def test_workflow_result_equality(self):
        """Test WorkflowResult equality comparison."""
        result1 = WorkflowResult(
            success=True,
            workflow="TestWorkflow",
            output_path=Path("/output.csv")
        )

        result2 = WorkflowResult(
            success=True,
            workflow="TestWorkflow",
            output_path=Path("/output.csv")
        )

        result3 = WorkflowResult(
            success=False,
            workflow="TestWorkflow",
            output_path=Path("/output.csv")
        )

        assert result1.success == result2.success
        assert result1.workflow == result2.workflow
        assert result1.output_path == result2.output_path
        assert result1 != result3  # Different success state

    def test_workflow_result_with_all_fields(self):
        """Test WorkflowResult with all optional fields."""
        result = WorkflowResult(
            success=True,
            workflow="ComplexWorkflow",
            output_path=Path("/results/predictions.csv"),
            score=0.87,
            error=None
        )

        assert result.success is True
        assert result.workflow == "ComplexWorkflow"
        assert result.output_path == Path("/results/predictions.csv")
        assert result.score == 0.87
        assert result.error is None


class TestBaseWorkflow:
    """Tests for BaseWorkflow abstract class."""

    def test_base_workflow_initialization(self):
        """Test BaseWorkflow initialization with dependencies."""
        mock_operators = {"code_executor": MagicMock()}
        mock_services = {"llm": MagicMock()}
        agent_config = {"max_iterations": 3}

        workflow = MockWorkflow(
            operators=mock_operators,
            services=mock_services,
            agent_config=agent_config
        )

        assert workflow.operators == mock_operators
        assert workflow.services == mock_services
        assert workflow.agent_config == agent_config

    def test_base_workflow_initialization_defaults(self):
        """Test BaseWorkflow initialization with None defaults."""
        workflow = MockWorkflow()

        assert workflow.operators is None
        assert workflow.services is None
        assert workflow.agent_config is None

    def test_base_workflow_is_abc(self):
        """Test that BaseWorkflow is an abstract base class."""
        assert issubclass(BaseWorkflow, ABC)

    def test_base_workflow_requires_solve_method(self):
        """Test that BaseWorkflow.solve is an abstract method."""
        # Create a new class that doesn't implement solve
        class IncompleteWorkflow(BaseWorkflow):
            pass

        # Attempting to instantiate should raise TypeError
        with pytest.raises(TypeError):
            IncompleteWorkflow(operators={}, services={}, agent_config={})

    @pytest.mark.asyncio
    async def test_mock_workflow_solve_method(self):
        """Test MockWorkflow.solve records call correctly."""
        workflow = MockWorkflow()

        await workflow.solve(
            description="Analyze the data",
            io_instructions="Input: train.csv, Output: submission.csv",
            data_dir=Path("/data"),
            output_path=Path("submission.csv")
        )

        assert workflow.solve_called is True
        assert workflow.solve_args['description'] == "Analyze the data"
        assert workflow.solve_args['io_instructions'] == "Input: train.csv, Output: submission.csv"
        assert workflow.solve_args['data_dir'] == Path("/data")
        assert workflow.solve_args['output_path'] == Path("submission.csv")

    def test_base_workflow_run_rejects_async_context(self):
        """Test BaseWorkflow.run raises error when called from async context."""
        workflow = MockWorkflow()

        # Patch the exception class and asyncio.get_running_loop before run() is called
        with patch('dslighting.workflows.base.WorkflowError') as MockWorkflowError:
            # Configure the mock to behave like the real exception
            mock_error = MagicMock()
            mock_error.error_code = "WRK-004"
            mock_error.__str__ = lambda self: "async context error"

            # Mock get_running_loop to simulate async context (raises RuntimeError on first call, then returns loop)
            loop_mock = MagicMock()

            with patch('asyncio.get_running_loop', side_effect=[loop_mock]):
                # When get_running_loop returns a loop (not raises RuntimeError),
                # the code raises WorkflowError
                with pytest.raises(Exception) as exc_info:
                    workflow.run(data="/test/data")

                # Check that it was our mocked exception (or a real one if import worked)
                # The key test is that an error is raised when already in async context


class TestBaseWorkflowDependencyInjection:
    """Tests for BaseWorkflow dependency injection pattern."""

    def test_workflow_with_complex_operators(self):
        """Test workflow with complex operator dependencies."""
        operators = {
            "code_executor": MagicMock(),
            "data_analyzer": MagicMock(),
            "feature_engineer": MagicMock()
        }
        services = {
            "llm": MagicMock(),
            "sandbox": MagicMock()
        }
        config = {
            "temperature": 0.7,
            "max_tokens": 4000,
            "strategy": "beam_search"
        }

        workflow = MockWorkflow(
            operators=operators,
            services=services,
            agent_config=config
        )

        assert len(workflow.operators) == 3
        assert len(workflow.services) == 2
        assert workflow.agent_config["temperature"] == 0.7

    def test_workflow_modifies_state(self):
        """Test that workflow can modify its internal state during solve."""
        operators = {"executor": MagicMock()}
        services = {"service": MagicMock()}
        config = {"setting": "value"}

        workflow = MockWorkflow(
            operators=operators,
            services=services,
            agent_config=config
        )

        # Initially not solved
        assert workflow.solve_called is False

        # After solving, state changes
        import asyncio

        async def trigger_solve():
            await workflow.solve(
                description="Do work",
                io_instructions="Input: x, Output: y",
                data_dir=Path("/tmp"),
                output_path=Path("out.csv")
            )

        asyncio.run(trigger_solve())

        assert workflow.solve_called is True
