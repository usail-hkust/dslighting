from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from dslighting.ops.presets.react import ReActOperator
from dslighting.runtime.dag import DagRuntime, DagRuntimeOptions, SolveWorkflowActor
from dslighting.utils.typing import ExecutionResult
from dslighting.workflows.search.react.workflow import ReActWorkflow


class _DummyWorkspaceService:
    def __init__(self, root: Path):
        self.root = root
        (self.root / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.root / "sandbox_workdir").mkdir(parents=True, exist_ok=True)

    def get_path(self, key: str) -> Path:
        return self.root / key

    def link_data_to_workspace(self, data_dir: Path) -> None:
        _ = data_dir


class _DummyResponse:
    def __init__(self, content: str):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]


class _DummyLLMService:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.config = SimpleNamespace(max_retries=2)

    async def call_messages(self, messages, max_retries=None):
        _ = messages, max_retries
        assert self._responses, "No more stubbed LLM responses available."
        return _DummyResponse(self._responses.pop(0))


class _FakeExecuteOperator:
    def __init__(self, workspace: _DummyWorkspaceService):
        self.workspace = workspace
        self.calls: list[dict[str, str]] = []

    async def __call__(self, code: str, mode: str = "script", executor_context=None):
        self.calls.append({"code": code, "mode": mode})
        _ = executor_context
        target = self.workspace.get_path("sandbox_workdir") / "answer.txt"
        target.write_text("ok", encoding="utf-8")
        return ExecutionResult(success=True, stdout="ok", stderr="")


@pytest.mark.asyncio
async def test_react_workflow_build_actor_returns_solve_workflow_actor(tmp_path) -> None:
    workspace = _DummyWorkspaceService(tmp_path / "workspace")
    workflow = ReActWorkflow(
        operators={
            "react": ReActOperator(max_steps=2),
            "execute": _FakeExecuteOperator(workspace),
        },
        services={
            "llm": _DummyLLMService(["<Think>x</Think><Answer>ok</Answer>"]),
            "sandbox": SimpleNamespace(),
            "workspace": workspace,
        },
        agent_config={},
    )

    actor = workflow.build_actor(
        task_id="react-dag",
        description="Return the answer.",
        io_instructions="Write to answer.txt.",
        data_dir=tmp_path / "data",
        output_path=tmp_path / "out" / "answer.txt",
        dag_options=None,
    )

    assert isinstance(actor, SolveWorkflowActor)


@pytest.mark.asyncio
async def test_react_workflow_runs_via_dag_runtime(tmp_path) -> None:
    workspace = _DummyWorkspaceService(tmp_path / "workspace")
    execute_operator = _FakeExecuteOperator(workspace)
    workflow = ReActWorkflow(
        operators={
            "react": ReActOperator(max_steps=2),
            "execute": execute_operator,
        },
        services={
            "llm": _DummyLLMService(
                [
                    "<Think>x</Think><Action>```python\nprint('ok')\n```</Action>",
                    "<Think>done</Think><Answer>ok</Answer>",
                ]
            ),
            "sandbox": SimpleNamespace(),
            "workspace": workspace,
        },
        agent_config={},
    )

    output_path = tmp_path / "out" / "answer.txt"
    actor = workflow.build_actor(
        task_id="react-dag-runtime",
        description="Return the answer.",
        io_instructions="Write to answer.txt.",
        data_dir=tmp_path / "data",
        output_path=output_path,
        dag_options=None,
    )

    runtime = DagRuntime(options=DagRuntimeOptions(max_inflight_nodes=1))
    summary = await runtime.run_actor(actor)

    assert summary.actor_completed is True
    assert summary.failed_nodes == 0
    assert execute_operator.calls == [{"code": "print('ok')", "mode": "script"}]
    assert (workspace.get_path("sandbox_workdir") / "answer.txt").read_text(
        encoding="utf-8"
    ) == "ok"
    assert not output_path.exists()
