from __future__ import annotations

import pytest

from dslighting.core.application.agent_config_builder import AgentConfigBuilder
from dslighting.error import ConfigurationError


def _builder(**kwargs) -> AgentConfigBuilder:
    return AgentConfigBuilder(
        workflow_name="aide",
        model="gpt-4o",
        api_key=None,
        api_base=None,
        provider=None,
        temperature=None,
        timeout=300,
        keep_workspace=False,
        sandbox_backend=kwargs.get("sandbox_backend"),
        sandbox_backend_type=kwargs.get("sandbox_backend_type"),
        sandbox_timeout=kwargs.get("sandbox_timeout"),
        sandbox_api_key=kwargs.get("sandbox_api_key"),
        init_kwargs=kwargs.get("init_kwargs", {}),
    )


def test_sandbox_params_map_to_config() -> None:
    config = _builder(
        sandbox_backend="ds_sandbox",
        sandbox_backend_type="local",
        sandbox_timeout=1200,
    ).build(task_id="demo", run_kwargs={})

    assert config.sandbox.backend == "ds_sandbox"
    assert config.sandbox.backend_type == "local"
    assert config.sandbox.timeout == 1200


def test_sandbox_runtime_kwargs_override_init() -> None:
    config = _builder(
        sandbox_backend="local",
        sandbox_timeout=300,
    ).build(
        task_id="demo",
        run_kwargs={
            "sandbox_backend": "ds_sandbox",
            "sandbox_backend_type": "docker",
            "sandbox_timeout": 900,
        },
    )

    assert config.sandbox.backend == "ds_sandbox"
    assert config.sandbox.backend_type == "docker"
    assert config.sandbox.timeout == 900


def test_invalid_sandbox_backend_raises_cfg_002() -> None:
    with pytest.raises(ConfigurationError, match="sandbox_backend"):
        _builder(sandbox_backend="dssandbox").build(task_id="demo", run_kwargs={})


def test_e2b_requires_api_key() -> None:
    with pytest.raises(ConfigurationError, match="E2B API key"):
        _builder(sandbox_backend="e2b").build(task_id="demo", run_kwargs={})
