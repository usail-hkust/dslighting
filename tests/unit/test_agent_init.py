"""
Test Agent initialization and configuration

These tests verify that the Agent class can be properly initialized
with different configurations.
"""

import pytest
import dslighting
from dslighting import Agent


@pytest.mark.unit
def test_agent_init_default():
    """Test Agent initialization with default parameters"""
    agent = Agent(workflow="aide")

    assert agent is not None
    assert agent.config.workflow.name == "aide"
    assert agent.config.llm.model is not None


@pytest.mark.unit
def test_agent_init_with_model():
    """Test Agent initialization with custom model"""
    agent = Agent(
        workflow="aide",
        model="gpt-4o"
    )

    assert agent.config.llm.model == "gpt-4o"


@pytest.mark.unit
def test_agent_init_with_temperature():
    """Test Agent initialization with temperature"""
    agent = Agent(
        workflow="aide",
        temperature=0.5
    )

    assert agent.config.llm.temperature == 0.5


@pytest.mark.unit
@pytest.mark.parametrize("workflow", [
    "aide",
    "autokaggle",
    "data_interpreter",
    "automind",
    "dsagent",
    "deepanalyze",
])
def test_all_workflows_init(workflow: str):
    """
    Test that all workflows can be initialized

    Args:
        workflow: Workflow name to test
    """
    agent = Agent(workflow=workflow)

    assert agent is not None
    assert agent.config.workflow.name == workflow


@pytest.mark.unit
def test_dsagent_with_enable_rag_false():
    """Test DS-Agent initialization with RAG disabled"""
    agent = Agent(
        workflow="dsagent",
        dsagent={"enable_rag": False}
    )

    assert agent.config.workflow.name == "dsagent"
    # Configuration should be stored for later use


@pytest.mark.unit
def test_automind_with_enable_rag_false():
    """Test AutoMind initialization with RAG disabled"""
    agent = Agent(
        workflow="automind",
        automind={"enable_rag": False}
    )

    assert agent.config.workflow.name == "automind"
    # Configuration should be stored for later use


@pytest.mark.unit
def test_agent_repr():
    """Test Agent string representation"""
    agent = Agent(workflow="aide")

    repr_str = repr(agent)
    assert "Agent" in repr_str
    assert "aide" in repr_str


@pytest.mark.unit
def test_agent_with_multiple_params():
    """Test Agent with multiple parameters"""
    agent = Agent(
        workflow="aide",
        model="gpt-4o",
        temperature=0.7,
        max_iterations=10
    )

    assert agent is not None
    assert agent.config.workflow.name == "aide"


@pytest.mark.unit
def test_agent_with_workflow_params():
    """Test Agent with workflow-specific parameters"""
    agent = Agent(
        workflow="dsagent",
        dsagent={
            "enable_rag": False,
            "case_dir": "./test_replay"
        }
    )

    assert agent is not None
    assert agent.config.workflow.name == "dsagent"
