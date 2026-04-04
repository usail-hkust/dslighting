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


def test_agent_config_builder_maps_react_namespace_to_workflow_params() -> None:
    config = _builder().build(
        task_id="demo",
        run_kwargs={
            "react": {
                "max_steps": "12",
                "obs_max_tokens": "1200",
                "obs_head_tokens": "600",
                "obs_tail_tokens": "600",
                "context": {
                    "strategy": "hybrid",
                    "keep_recent_turns": "6",
                    "keep_latest_feedback_only": "true",
                },
            }
        },
    )

    assert config.workflow is not None
    assert config.workflow.params == {
        "max_steps": 12,
        "obs_max_tokens": 1200,
        "obs_head_tokens": 600,
        "obs_tail_tokens": 600,
        "context": {
            "strategy": "hybrid",
            "keep_recent_turns": 6,
            "keep_latest_feedback_only": True,
        },
    }


def test_agent_config_builder_rejects_flat_react_keys() -> None:
    with pytest.raises(ConfigurationError, match="ReAct parameters must be passed via workflow namespace"):
        _builder().build(
            task_id="demo",
            run_kwargs={"max_steps": 9},
        )


def test_config_builder_maps_react_namespace_to_workflow_params() -> None:
    config = ConfigBuilder().build_config(
        workflow="react",
        react={
            "max_steps": "7",
            "obs_max_tokens": "900",
            "obs_head_tokens": "450",
            "obs_tail_tokens": "450",
            "context": {
                "strategy": "recent_turns",
                "keep_recent_turns": "4",
                "max_feedback_retries": "1",
            },
        },
    )

    assert config.workflow is not None
    assert config.workflow.params == {
        "max_steps": 7,
        "obs_max_tokens": 900,
        "obs_head_tokens": 450,
        "obs_tail_tokens": 450,
        "context": {
            "strategy": "recent_turns",
            "keep_recent_turns": 4,
            "max_feedback_retries": 1,
        },
    }


def test_config_builder_maps_full_react_context_namespace() -> None:
    config = ConfigBuilder().build_config(
        workflow="react",
        react={
            "max_steps": 9,
            "obs_max_tokens": 4096,
            "obs_head_tokens": 2048,
            "obs_tail_tokens": 2048,
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
    assert config.workflow.params == {
        "max_steps": 9,
        "obs_max_tokens": 4096,
        "obs_head_tokens": 2048,
        "obs_tail_tokens": 2048,
        "context": {
            "strategy": "hybrid",
            "max_history_chars": 52000,
            "keep_recent_turns": 16,
            "max_observation_chars": 18000,
            "summary_trigger_turns": 20,
            "summary_max_chars": 5000,
            "keep_latest_feedback_only": True,
            "max_feedback_retries": 3,
            "recent_observation_window": 10,
            "max_feedback_chars": 1600,
        },
    }


def test_config_builder_rejects_flat_react_keys() -> None:
    with pytest.raises(ConfigurationError, match="ReAct parameters must be passed via workflow namespace"):
        ConfigBuilder().build_config(
            workflow="react",
            max_steps=10,
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


def test_agent_config_builder_rejects_invalid_react_context_strategy() -> None:
    with pytest.raises(ConfigurationError, match="Invalid `react.context`"):
        _builder().build(
            task_id="demo",
            run_kwargs={"react": {"context": {"strategy": "bad-mode"}}},
        )


def test_agent_config_builder_rejects_invalid_react_observation_budget() -> None:
    with pytest.raises(ConfigurationError, match="obs_head_tokens"):
        _builder().build(
            task_id="demo",
            run_kwargs={
                "react": {
                    "obs_max_tokens": 100,
                    "obs_head_tokens": 60,
                    "obs_tail_tokens": 60,
                }
            },
        )


def test_config_builder_rejects_invalid_react_observation_budget() -> None:
    with pytest.raises(ConfigurationError, match="obs_head_tokens"):
        ConfigBuilder().build_config(
            workflow="react",
            react={
                "obs_max_tokens": 90,
                "obs_head_tokens": 45,
                "obs_tail_tokens": 46,
            },
        )
