from __future__ import annotations

from pathlib import Path

import pytest

from dslighting.config import DSLightingConfig, WorkflowConfig
from dslighting.error import WorkflowError
from dslighting.runner import DSLightingRunner
from dslighting.runtime.dag.types import DagRunSummary, DagRuntimeOptions


@pytest.mark.asyncio
async def test_execute_workflow_entrypoint_raises_when_final_result_failed(monkeypatch) -> None:
    runner = DSLightingRunner(DSLightingConfig(workflow=WorkflowConfig(name="aide", params={})))

    monkeypatch.setattr(runner, "_build_dag_actor", lambda **kwargs: object())

    class _FakeRuntime:
        async def run_actor(self, actor):
            return DagRunSummary(
                task_id="task-x",
                actor_completed=True,
                final_result={"status": "failed", "error": "phase failed"},
            )

    monkeypatch.setattr("dslighting.runner.DagRuntime", lambda options, dispatcher: _FakeRuntime())

    class _Workflow:
        async def solve(self, **kwargs):
            return None

    with pytest.raises(WorkflowError, match="phase failed"):
        await runner._execute_workflow_entrypoint(
            task_id="task-x",
            workflow=_Workflow(),
            description="desc",
            io_instructions="io",
            data_dir=Path("."),
            output_path=Path("out.csv"),
            dag_options=DagRuntimeOptions(enabled=True),
        )
