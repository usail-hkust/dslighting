from pathlib import Path

import pytest

from dslighting.core.application.agent_app_service import AgentAppService
from dslighting.core.interfaces import AgentResult


@pytest.mark.asyncio
async def test_app_service_calls_task_executor_with_resolved_input(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    class _FakeExecutor:
        def __init__(self, config, workflow_name):
            captured["workflow_name"] = workflow_name
            captured["config"] = config

        async def run_with_task_id(self, **kwargs):
            captured["executor_kwargs"] = kwargs
            return AgentResult(success=True, output="ok")

    monkeypatch.setattr("dslighting.core.application.agent_app_service.TaskExecutor", _FakeExecutor)

    service = AgentAppService(
        workflow_name="aide",
        model="gpt-4o",
        api_key=None,
        api_base=None,
        provider=None,
        temperature=None,
        timeout=300,
        keep_workspace=False,
        sandbox_backend=None,
        sandbox_backend_type=None,
        sandbox_timeout=None,
        sandbox_api_key=None,
        init_kwargs={"max_iterations": 2},
    )

    comp_dir = tmp_path / "comp"
    comp_dir.mkdir()
    data_file = comp_dir / "train.csv"
    data_file.write_text("x,y\n1,2\n")

    result = await service.run(
        task_id=None,
        data=data_file,
        task="task fallback",
        output="submission.csv",
        kwargs={"description": "explicit", "custom": 7},
    )

    assert result.success is True
    assert captured["workflow_name"] == "aide"
    assert captured["executor_kwargs"]["task_id"] == "comp"
    assert captured["executor_kwargs"]["data_dir"] == comp_dir
    assert captured["executor_kwargs"]["task_description"] == "explicit"
    assert captured["executor_kwargs"]["output"] == "submission.csv"
    assert captured["config"].run.parameters["custom"] == 7
