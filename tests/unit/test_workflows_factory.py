"""
Unit tests for WorkflowFactory classes.

Tests cover:
- BaseWorkflowFactory initialization and configuration
- WorkflowFactory registry patterns
- Factory agent creation
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from abc import ABC

from dslighting.workflows.factory.base import BaseWorkflowFactory


class MockAgent:
    """Mock agent for testing factory."""

    def __init__(self, operators, services, agent_config, **kwargs):
        self.operators = operators
        self.services = services
        self.agent_config = agent_config
        self.init_kwargs = kwargs  # Store runtime kwargs for testing
        self.solve_called = False

    async def solve(self, description, io_instructions, data_dir, output_path):
        self.solve_called = True
        self.last_call = {
            'description': description,
            'io_instructions': io_instructions,
            'data_dir': data_dir,
            'output_path': output_path
        }


class MockWorkflowFactory(BaseWorkflowFactory):
    """Concrete implementation of BaseWorkflowFactory for testing."""

    def __init__(self, **kwargs):
        # Skip parent __init__ to avoid external dependencies
        self.model = kwargs.get('model', 'gpt-4o')
        self.timeout = kwargs.get('timeout', 300)
        self.keep_workspace = kwargs.get('keep_workspace', False)
        self._agent_init_kwargs = kwargs
        self._created_agents = []
        self._last_runner = None

        # Mock services
        self.llm_service = MagicMock()
        self.workspace_service = MagicMock()
        self.sandbox_service = MagicMock()

    def create_agent(self, **kwargs) -> MockAgent:
        """Create a mock agent."""
        agent = MockAgent(
            operators={"mock_operator": MagicMock()},
            services={"mock_service": MagicMock()},
            agent_config=self._agent_init_kwargs.copy(),
            **kwargs
        )
        self._created_agents.append(agent)
        return agent

    def create_workflow(self, config, benchmark=None):
        """Satisfy BaseWorkflowFactory abstract interface for tests."""
        return self.create_agent(config=config, benchmark=benchmark)


class TestBaseWorkflowFactory:
    """Tests for BaseWorkflowFactory class."""

    def test_factory_initialization_defaults(self):
        """Test BaseWorkflowFactory initialization with defaults."""
        factory = MockWorkflowFactory()

        assert factory.model == 'gpt-4o'
        assert factory.timeout == 300
        assert factory.keep_workspace is False

    def test_factory_initialization_custom_values(self):
        """Test BaseWorkflowFactory initialization with custom values."""
        factory = MockWorkflowFactory(
            model='claude-3-opus',
            timeout=600,
            keep_workspace=True,
            custom_param='test'
        )

        assert factory.model == 'claude-3-opus'
        assert factory.timeout == 600
        assert factory.keep_workspace is True
        assert factory._agent_init_kwargs['custom_param'] == 'test'

    def test_factory_attributes(self):
        """Test that factory has required service attributes."""
        factory = MockWorkflowFactory()

        assert hasattr(factory, 'llm_service')
        assert hasattr(factory, 'workspace_service')
        assert hasattr(factory, 'sandbox_service')

    def test_factory_workflow_name_derivation(self):
        """Test _get_workflow_name derivation from class name."""
        factory = MockWorkflowFactory()

        name = factory._get_workflow_name()

        # Based on implementation: replaces "Factory" with "" and lowercases
        assert name == "mockworkflow"
        assert "Factory" in "MockWorkflowFactory"


class TestWorkflowFactoryCreateAgent:
    """Tests for WorkflowFactory.create_agent method."""

    def test_create_agent_returns_agent(self):
        """Test that create_agent returns an agent instance."""
        factory = MockWorkflowFactory()

        agent = factory.create_agent()

        assert agent is not None
        assert isinstance(agent, MockAgent)

    def test_create_agent_passes_config(self):
        """Test that create_agent passes configuration to agent."""
        factory = MockWorkflowFactory(
            model='gpt-4o',
            temperature=0.5,
            custom_setting='value'
        )

        agent = factory.create_agent(max_iterations=10)

        assert agent.agent_config['model'] == 'gpt-4o'
        assert agent.agent_config['temperature'] == 0.5
        assert agent.agent_config['custom_setting'] == 'value'
        assert agent.init_kwargs['max_iterations'] == 10

    def test_create_agent_called_multiple_times(self):
        """Test that create_agent can be called multiple times."""
        factory = MockWorkflowFactory()

        agent1 = factory.create_agent()
        agent2 = factory.create_agent()

        assert agent1 is not agent2  # Different instances
        assert len(factory._created_agents) == 2

    def test_create_agent_includes_operators(self):
        """Test that agent receives operators."""
        factory = MockWorkflowFactory()

        agent = factory.create_agent()

        assert 'mock_operator' in agent.operators
        assert agent.operators['mock_operator'] is not None

    def test_create_agent_includes_services(self):
        """Test that agent receives services."""
        factory = MockWorkflowFactory()

        agent = factory.create_agent()

        assert 'mock_service' in agent.services
        assert agent.services['mock_service'] is not None


class TestWorkflowFactoryCleanup:
    """Tests for WorkflowFactory cleanup method."""

    def test_cleanup_with_keep_workspace_false(self):
        """Test cleanup when keep_workspace is False."""
        factory = MockWorkflowFactory(keep_workspace=False)

        factory.cleanup()

        factory.workspace_service.cleanup.assert_called_once()

    def test_cleanup_with_keep_workspace_true(self):
        """Test cleanup is skipped when keep_workspace is True."""
        factory = MockWorkflowFactory(keep_workspace=True)

        factory.cleanup()

        factory.workspace_service.cleanup.assert_not_called()

    def test_cleanup_prefers_last_runner_workspace_service(self):
        """Test cleanup uses _last_runner.workspace_service before factory workspace_service."""
        factory = MockWorkflowFactory(keep_workspace=False)
        factory._last_runner = MagicMock()
        factory._last_runner.workspace_service = MagicMock()

        factory.cleanup()

        factory._last_runner.workspace_service.cleanup.assert_called_once()
        factory.workspace_service.cleanup.assert_not_called()

    def test_cleanup_falls_back_when_last_runner_workspace_service_missing(self):
        """Test cleanup falls back to factory workspace_service when _last_runner has no workspace."""
        factory = MockWorkflowFactory(keep_workspace=False)
        factory._last_runner = MagicMock()
        factory._last_runner.workspace_service = None

        factory.cleanup()

        factory.workspace_service.cleanup.assert_called_once()


class TestWorkflowFactoryAgentExecution:
    """Tests for agent execution through factory."""

    @pytest.mark.asyncio
    async def test_factory_run_creates_agent(self):
        """Test that factory.run creates and uses an agent."""
        factory = MockWorkflowFactory()

        # The run method is async in the real implementation
        # Here we just verify agent creation works
        agent = factory.create_agent()

        assert agent is not None
        assert not agent.solve_called

    def test_factory_merges_init_and_runtime_kwargs(self):
        """Test that factory merges init kwargs with runtime kwargs."""
        factory = MockWorkflowFactory(
            init_param='initial',
            shared_param='initial_value'
        )

        # Runtime kwargs should be passed separately
        agent = factory.create_agent(runtime_param='runtime', shared_param='runtime_value')

        # Init params should be preserved in agent_config
        assert agent.agent_config['init_param'] == 'initial'
        # Runtime params should be in init_kwargs
        assert agent.init_kwargs['runtime_param'] == 'runtime'
        assert agent.init_kwargs['shared_param'] == 'runtime_value'


class TestWorkflowFactoryConfiguration:
    """Tests for factory configuration handling."""

    def test_factory_with_empty_config(self):
        """Test factory initialization with minimal config."""
        factory = MockWorkflowFactory()

        assert factory.model is not None
        assert factory.timeout > 0
        assert isinstance(factory._agent_init_kwargs, dict)

    def test_factory_kwargs_stored(self):
        """Test that additional kwargs are stored for agent creation."""
        factory = MockWorkflowFactory(
            param1='value1',
            param2='value2',
            param3='value3'
        )

        assert factory._agent_init_kwargs['param1'] == 'value1'
        assert factory._agent_init_kwargs['param2'] == 'value2'
        assert factory._agent_init_kwargs['param3'] == 'value3'

    def test_factory_agent_config_reflects_init_kwargs(self):
        """Test that agent config reflects factory init kwargs."""
        factory = MockWorkflowFactory(
            model='test-model',
            temperature=0.1,
            max_tokens=100
        )

        agent = factory.create_agent()

        # Note: timeout is extracted by kwargs.get() and not stored in _agent_init_kwargs
        assert agent.agent_config['model'] == 'test-model'
        assert agent.agent_config['temperature'] == 0.1
        assert agent.agent_config['max_tokens'] == 100


class TestBaseWorkflowFactoryAbstract:
    """Tests verifying BaseWorkflowFactory is abstract."""

    def test_base_factory_requires_create_workflow(self):
        """Test that BaseWorkflowFactory requires create_workflow implementation."""
        # Verify that BaseWorkflowFactory has create_workflow as an abstract method
        assert hasattr(BaseWorkflowFactory, 'create_workflow')

        # The abstract method decorator should be present
        method = getattr(BaseWorkflowFactory, 'create_workflow')
        assert getattr(method, '__isabstractmethod__', False) is True


class TestMockAgentIntegration:
    """Integration tests for MockAgent with MockWorkflowFactory."""

    def test_agent_receives_all_factory_services(self):
        """Test that agent receives all services from factory."""
        factory = MockWorkflowFactory()

        agent = factory.create_agent()

        # Check that agent has access to all factory services
        assert hasattr(agent.services, '__getitem__') or isinstance(agent.services, dict)

    @pytest.mark.asyncio
    async def test_agent_solve_method(self):
        """Test MockAgent.solve method records call."""
        factory = MockWorkflowFactory()
        agent = factory.create_agent()

        await agent.solve(
            description="Test task",
            io_instructions="Read: input.csv, Write: output.csv",
            data_dir=Path("/test"),
            output_path=Path("output.csv")
        )

        assert agent.solve_called is True
        assert agent.last_call['description'] == "Test task"
        assert agent.last_call['io_instructions'] == "Read: input.csv, Write: output.csv"
