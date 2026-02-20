from __future__ import annotations

import pytest

from dslighting.core.application.agent_config_builder import AgentConfigBuilder
from dslighting.error import ConfigurationError


def _builder(workflow_name: str) -> AgentConfigBuilder:
    return AgentConfigBuilder(
        workflow_name=workflow_name,
        model="gpt-4o",
        api_key=None,
        api_base=None,
        provider=None,
        temperature=None,
        timeout=300,
        keep_workspace=False,
        init_kwargs={},
    )


def test_dsagent_rag_params_mapped_from_namespace() -> None:
    config = _builder("dsagent").build(
        task_id="demo",
        run_kwargs={"dsagent": {"enable_rag": False, "case_dir": "./cases"}},
    )
    assert config.workflow is not None
    assert config.workflow.params["enable_rag"] is False
    assert config.workflow.params["case_dir"] == "./cases"


def test_automind_rag_params_mapped_from_namespace() -> None:
    config = _builder("automind").build(
        task_id="demo",
        run_kwargs={"automind": {"enable_rag": True, "case_dir": "./experience_replay"}},
    )
    assert config.workflow is not None
    assert config.workflow.params["enable_rag"] is True
    assert config.workflow.params["case_dir"] == "./experience_replay"


def test_flat_rag_keys_are_rejected_for_dsagent() -> None:
    with pytest.raises(ConfigurationError, match="must be passed via workflow namespace"):
        _builder("dsagent").build(
            task_id="demo",
            run_kwargs={"enable_rag": True, "case_dir": "./cases"},
        )
