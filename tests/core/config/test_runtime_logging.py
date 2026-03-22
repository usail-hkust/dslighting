from __future__ import annotations

import logging

import pytest

from dslighting.core.application.agent_config_builder import AgentConfigBuilder
from dslighting.core.types import TaskDefinition
from dslighting.runner import DSLightingRunner
from dslighting.workflows.factory.builtin import AIDEWorkflowFactory


TARGET_MODEL = "openai/deepseek-ai/DeepSeek-V3.1-Terminus"


def _build_agent_config():
    builder = AgentConfigBuilder(
        workflow_name="aide",
        model=TARGET_MODEL,
        api_key=None,
        api_keys=["k1", "k2"],
        api_base="https://api.siliconflow.cn/v1",
        provider=None,
        temperature=1.0,
        timeout=300,
        keep_workspace=False,
        sandbox_backend=None,
        sandbox_backend_type=None,
        sandbox_timeout=None,
        sandbox_api_key=None,
        init_kwargs={},
    )
    return builder.build(task_id="dacode-di-text-001", run_kwargs={})


def test_factory_init_no_longer_logs_default_model(caplog) -> None:
    with caplog.at_level(logging.DEBUG):
        AIDEWorkflowFactory()

    assert "  - Model: gpt-4o" not in caplog.text
    assert "AIDEWorkflowFactory initialized" in caplog.text


def test_direct_factory_logs_resolved_model_from_config(caplog) -> None:
    factory = AIDEWorkflowFactory(
        model=TARGET_MODEL,
        api_keys=["k1", "k2"],
        api_base="https://api.siliconflow.cn/v1",
        temperature=1.0,
    )

    with caplog.at_level(logging.DEBUG):
        config = factory._build_config(task_id="dacode-di-text-001", run_kwargs={})

    assert config.llm.model == TARGET_MODEL
    assert f"  - Model: {TARGET_MODEL}" in caplog.text
    assert "runtime resolved from config" in caplog.text


@pytest.mark.asyncio
async def test_runner_logs_resolved_model_from_config(caplog) -> None:
    config = _build_agent_config()
    task = TaskDefinition(
        task_id="dacode-di-text-001",
        task_type="kaggle",
        mode="standard_ml",
        payload={},
    )

    with caplog.at_level(logging.DEBUG):
        runner = DSLightingRunner(config)
        prepared = await runner._prepare_task_execution(task)

    assert prepared.llm.model == TARGET_MODEL
    assert f"  - Model: {TARGET_MODEL}" in caplog.text
    assert "  - Model: gpt-4o" not in caplog.text
