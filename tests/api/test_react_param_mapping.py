from __future__ import annotations

import pytest

from dslighting.core.application.agent_config_builder import AgentConfigBuilder
from dslighting.core.config import ConfigBuilder
from dslighting.error import ConfigurationError


def _builder() -> AgentConfigBuilder:
    return AgentConfigBuilder(
        workflow_name="react",
        model="gpt-4o",
        api_key=None,
        api_keys=None,
        api_base=None,
        provider=None,
        temperature=None,
        timeout=300,
        keep_workspace=False,
        sandbox_backend=None,
        sandbox_backend_type=None,
        sandbox_timeout=None,
        sandbox_api_key=None,
        init_kwargs={},
    )


def test_agent_config_builder_maps_agent_runtime_to_shared_config() -> None:
    config = _builder().build(
        task_id="demo",
        run_kwargs={
            "agent_runtime": {
                "max_steps": "12",
                "observation": {
                    "max_tokens": "1200",
                    "head_tokens": "600",
                    "tail_tokens": "600",
                },
                "context": {
                    "strategy": "hybrid",
                    "keep_recent_turns": "6",
                    "keep_latest_feedback_only": "true",
                },
            },
            "output_contract": {
                "require_output_before_completion": "true",
                "missing_output_feedback_retries": "2",
            },
        },
    )

    assert config.workflow is not None
    assert config.workflow.params == {}
    assert config.agent_runtime.max_steps == 12
    assert config.agent_runtime.observation.max_tokens == 1200
    assert config.agent_runtime.observation.head_tokens == 600
    assert config.agent_runtime.observation.tail_tokens == 600
    assert config.agent_runtime.context.strategy == "hybrid"
    assert config.agent_runtime.context.keep_recent_turns == 6
    assert config.agent_runtime.context.keep_latest_feedback_only is True
    assert config.output_contract.require_output_before_completion is True
    assert config.output_contract.missing_output_feedback_retries == 2


def test_agent_config_builder_rejects_legacy_react_namespace() -> None:
    with pytest.raises(ConfigurationError, match="react.*no longer supported"):
        _builder().build(
            task_id="demo",
            run_kwargs={"react": {"max_steps": 9}},
        )


def test_agent_config_builder_rejects_flat_react_keys() -> None:
    with pytest.raises(ConfigurationError, match="Legacy ReAct runtime parameters"):
        _builder().build(
            task_id="demo",
            run_kwargs={"max_steps": 9},
        )


def test_config_builder_maps_agent_runtime_to_shared_config() -> None:
    config = ConfigBuilder().build_config(
        workflow="react",
        agent_runtime={
            "max_steps": "7",
            "observation": {
                "max_tokens": "900",
                "head_tokens": "450",
                "tail_tokens": "450",
            },
            "context": {
                "strategy": "recent_turns",
                "keep_recent_turns": "4",
                "max_feedback_retries": "1",
            },
        },
    )

    assert config.workflow is not None
    assert config.workflow.params == {}
    assert config.agent_runtime.max_steps == 7
    assert config.agent_runtime.observation.max_tokens == 900
    assert config.agent_runtime.observation.head_tokens == 450
    assert config.agent_runtime.observation.tail_tokens == 450
    assert config.agent_runtime.context.strategy == "recent_turns"
    assert config.agent_runtime.context.keep_recent_turns == 4
    assert config.agent_runtime.context.max_feedback_retries == 1


def test_config_builder_maps_full_agent_runtime_context_namespace() -> None:
    config = ConfigBuilder().build_config(
        workflow="react",
        agent_runtime={
            "max_steps": 9,
            "observation": {
                "max_tokens": 4096,
                "head_tokens": 2048,
                "tail_tokens": 2048,
            },
            "context": {
                "strategy": "hybrid",
                "max_history_chars": "52000",
                "keep_recent_turns": "16",
                "max_observation_chars": "18000",
                "summary_trigger_turns": "20",
                "summary_max_chars": "5000",
                "keep_latest_feedback_only": "true",
                "max_feedback_retries": "3",
                "recent_observation_window": "10",
                "max_feedback_chars": "1600",
            },
        },
    )

    assert config.workflow is not None
    assert config.workflow.params == {}
    assert config.agent_runtime.max_steps == 9
    assert config.agent_runtime.observation.max_tokens == 4096
    assert config.agent_runtime.context.max_history_chars == 52000
    assert config.agent_runtime.context.keep_recent_turns == 16
    assert config.agent_runtime.context.max_observation_chars == 18000
    assert config.agent_runtime.context.summary_trigger_turns == 20
    assert config.agent_runtime.context.summary_max_chars == 5000
    assert config.agent_runtime.context.keep_latest_feedback_only is True
    assert config.agent_runtime.context.max_feedback_retries == 3
    assert config.agent_runtime.context.recent_observation_window == 10
    assert config.agent_runtime.context.max_feedback_chars == 1600


def test_config_builder_rejects_flat_react_keys() -> None:
    with pytest.raises(ConfigurationError, match="Legacy ReAct runtime parameters"):
        ConfigBuilder().build_config(
            workflow="react",
            max_steps=10,
        )


def test_config_builder_rejects_legacy_react_namespace() -> None:
    with pytest.raises(ConfigurationError, match="react.*no longer supported"):
        ConfigBuilder().build_config(
            workflow="react",
            react={"max_steps": 10},
        )


def test_load_config_from_dict_rejects_legacy_react_run_parameter_paths() -> None:
    with pytest.raises(ConfigurationError, match="Legacy ReAct runtime parameter paths"):
        ConfigBuilder().load_config_from_dict(
            {
                "workflow": {"name": "react", "params": {}},
                "run": {"parameters": {"react": {"max_steps": 10}}},
            },
            skip_migration=True,
        )


def test_load_config_from_dict_rejects_legacy_react_workflow_params() -> None:
    with pytest.raises(ConfigurationError, match="agent_runtime"):
        ConfigBuilder().load_config_from_dict(
            {
                "workflow": {"name": "react", "params": {"max_steps": 10}},
            },
            skip_migration=True,
        )


def test_agent_config_builder_rejects_invalid_agent_runtime_context_strategy() -> None:
    with pytest.raises(ConfigurationError, match="agent_runtime.context"):
        _builder().build(
            task_id="demo",
            run_kwargs={"agent_runtime": {"context": {"strategy": "bad-mode"}}},
        )


def test_agent_config_builder_rejects_invalid_agent_runtime_observation_budget() -> None:
    with pytest.raises(ConfigurationError, match="head_tokens"):
        _builder().build(
            task_id="demo",
            run_kwargs={
                "agent_runtime": {
                    "observation": {
                        "max_tokens": 100,
                        "head_tokens": 60,
                        "tail_tokens": 60,
                    },
                }
            },
        )


def test_config_builder_rejects_invalid_agent_runtime_observation_budget() -> None:
    with pytest.raises(ConfigurationError, match="head_tokens"):
        ConfigBuilder().build_config(
            workflow="react",
            agent_runtime={
                "observation": {
                    "max_tokens": 90,
                    "head_tokens": 45,
                    "tail_tokens": 46,
                },
            },
        )
