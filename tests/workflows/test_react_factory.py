from __future__ import annotations

import pytest

from dslighting.config import (
    AgentRuntimeConfig,
    AgentRuntimeContextConfig,
    AgentRuntimeObservationConfig,
    DSLightingConfig,
    OutputContractConfig,
    WorkflowConfig,
)
from dslighting.error import ConfigurationError
from dslighting.workflows.factory import builtin
from dslighting.workflows.factory.builtin import ReActWorkflowFactory


class _DummyWorkspaceService:
    def __init__(self, run_name: str, base_dir=None):
        self.run_name = run_name
        self.base_dir = base_dir


class _DummyLLMService:
    def __init__(self, config):
        self.config = config


class _DummySandboxService:
    def __init__(self, workspace):
        self.workspace = workspace


def test_react_factory_reads_shared_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(builtin, "WorkspaceService", _DummyWorkspaceService)
    monkeypatch.setattr(builtin, "LLMService", _DummyLLMService)
    monkeypatch.setattr(
        builtin,
        "_create_sandbox_service",
        lambda workspace, config: _DummySandboxService(workspace),
    )

    config = DSLightingConfig(
        workflow=WorkflowConfig(
            name="react",
            params={
                "workspace_base_dir": "/tmp/react-workspace",
            },
        ),
        agent_runtime=AgentRuntimeConfig(
            max_steps=12,
            observation=AgentRuntimeObservationConfig(
                max_tokens=1200,
                head_tokens=600,
                tail_tokens=600,
            ),
            context=AgentRuntimeContextConfig(
                strategy="hybrid",
                keep_recent_turns=6,
                summary_trigger_turns=8,
            ),
        ),
        output_contract=OutputContractConfig(
            require_output_before_completion=True,
            missing_output_feedback_retries=2,
        ),
    )
    config.run.parameters = {
        "react": {"max_steps": 999},
        "max_steps": 999,
        "obs_max_tokens": 999,
    }

    workflow = ReActWorkflowFactory().create_workflow(config)
    operator = workflow.operators["react"]
    execute_operator = workflow.operators["execute"]

    assert operator.max_steps == 12
    assert operator.obs_max_tokens == 1200
    assert operator.obs_head_tokens == 600
    assert operator.obs_tail_tokens == 600
    assert execute_operator.name == "ExecuteAndTest"
    assert workflow.services["react_context_config"].strategy == "hybrid"
    assert workflow.services["react_context_config"].keep_recent_turns == 6
    assert workflow.services["output_contract_config"].require_output_before_completion is True
    assert workflow.services["output_contract_config"].missing_output_feedback_retries == 2
    assert workflow.agent_config == config.agent.model_dump()


def test_resolve_agent_runtime_settings_uses_defaults() -> None:
    config = DSLightingConfig(workflow=WorkflowConfig(name="react", params={}))

    max_steps, obs_max_tokens, obs_head_tokens, obs_tail_tokens, context_config = (
        builtin._resolve_agent_runtime_settings(config)
    )

    assert (max_steps, obs_max_tokens, obs_head_tokens, obs_tail_tokens) == (10, 4000, 2000, 2000)
    assert context_config.strategy == "hybrid"
    assert context_config.max_history_chars == 48000
    assert context_config.keep_recent_turns == 14
    assert context_config.summary_trigger_turns == 18
    assert context_config.summary_max_chars == 4000
    assert context_config.recent_observation_window == 8


def test_resolve_agent_runtime_settings_rejects_invalid_observation_budget() -> None:
    config = DSLightingConfig(
        workflow=WorkflowConfig(name="react", params={}),
        agent_runtime=AgentRuntimeConfig(
            observation=AgentRuntimeObservationConfig(
                max_tokens=100,
                head_tokens=60,
                tail_tokens=60,
            )
        ),
    )

    with pytest.raises(ConfigurationError, match="obs_head_tokens"):
        builtin._resolve_agent_runtime_settings(config)
