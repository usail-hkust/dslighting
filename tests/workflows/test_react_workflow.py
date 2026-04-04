from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from dslighting.ops.presets.react import ReActOperator
from dslighting.utils.typing import ExecutionResult
from dslighting.workflows.search.react_workflow import ReActWorkflow


class _DummyWorkspaceService:
    def __init__(self, root: Path):
        self.root = root
        (self.root / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.root / "sandbox_workdir").mkdir(parents=True, exist_ok=True)
        self.linked_data_dir: Path | None = None

    def get_path(self, key: str) -> Path:
        return self.root / key

    def link_data_to_workspace(self, data_dir: Path) -> None:
        self.linked_data_dir = data_dir
        sandbox_workdir = self.get_path("sandbox_workdir")
        for path in data_dir.iterdir():
            if path.is_file():
                shutil.copy2(path, sandbox_workdir / path.name)


class _DummyResponse:
    def __init__(self, content: str):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]


class _DummyLLMService:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[list[dict]] = []
        self.config = SimpleNamespace(max_retries=2)

    async def call_messages(self, messages, max_retries=None):
        self.calls.append(messages)
        assert self._responses, "No more stubbed LLM responses available."
        return _DummyResponse(self._responses.pop(0))


class _FakeExecuteOperator:
    def __init__(
        self,
        workspace: _DummyWorkspaceService,
        *,
        stdout: str = "ok",
        create_output_name: str | None = None,
        create_directory_output_name: str | None = None,
    ) -> None:
        self.workspace = workspace
        self.stdout = stdout
        self.create_output_name = create_output_name
        self.create_directory_output_name = create_directory_output_name
        self.calls: list[dict[str, str]] = []

    async def __call__(self, code: str, mode: str = "script", executor_context=None):
        self.calls.append(
            {
                "code": code,
                "mode": mode,
            }
        )
        _ = executor_context

        if self.create_output_name:
            target = self.workspace.get_path("sandbox_workdir") / self.create_output_name
            target.write_text("prediction\n1\n", encoding="utf-8")

        if self.create_directory_output_name:
            submission_dir = (
                self.workspace.get_path("sandbox_workdir") / self.create_directory_output_name
            )
            submission_dir.mkdir(parents=True, exist_ok=True)
            (submission_dir / "before_covariance.csv").write_text(
                "a,b\n1,2\n",
                encoding="utf-8",
            )
            (submission_dir / "after_covariance.csv").write_text(
                "a,b\n3,4\n",
                encoding="utf-8",
            )

        return ExecutionResult(success=True, stdout=self.stdout, stderr="")


@pytest.mark.asyncio
async def test_react_workflow_executes_via_shared_execute_operator_and_saves_messages(tmp_path) -> None:
    workspace = _DummyWorkspaceService(tmp_path / "workspace")
    llm = _DummyLLMService(
        [
            "<Think>Inspect the data.</Think>\n<Action>```python\nprint('run')\n```</Action>",
            "<Think>Done.</Think>\n<Answer>final answer</Answer>",
        ]
    )

    react_operator = ReActOperator(max_steps=3)
    execute_operator = _FakeExecuteOperator(
        workspace,
        stdout="run",
        create_output_name="submission.csv",
    )
    workflow = ReActWorkflow(
        operators={"react": react_operator, "execute": execute_operator},
        services={"llm": llm, "sandbox": SimpleNamespace(), "workspace": workspace},
        agent_config={},
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "train.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    output_path = tmp_path / "out" / "submission.csv"

    await workflow.solve(
        description='Save the results to "submission.csv".',
        io_instructions="Write a submission file.",
        data_dir=data_dir,
        output_path=output_path,
    )

    assert workspace.linked_data_dir == data_dir
    sandbox_output = workspace.get_path("sandbox_workdir") / "submission.csv"
    assert sandbox_output.read_text(encoding="utf-8") == "prediction\n1\n"
    assert not output_path.exists()
    messages_path = workspace.get_path("artifacts") / "messages.json"
    assert messages_path.exists()
    saved_messages = json.loads(messages_path.read_text(encoding="utf-8"))
    assert saved_messages[0]["role"] == "system"
    assert saved_messages[2]["role"] == "assistant"
    assert execute_operator.calls == [{"code": "print('run')", "mode": "script"}]
    assert len(llm.calls) == 2
    assert llm.calls[0][0]["role"] == "system"
    assert "Role:" in llm.calls[0][0]["content"]
    assert "Task Goal and Data Overview:" in llm.calls[0][0]["content"]
    assert 'exact filename `submission.csv`' not in llm.calls[0][0]["content"]


@pytest.mark.asyncio
async def test_react_workflow_allows_plain_answer_without_artifact_gate(tmp_path) -> None:
    workspace = _DummyWorkspaceService(tmp_path / "workspace")
    llm = _DummyLLMService(["<Think>x</Think><Answer>42</Answer>"])

    workflow = ReActWorkflow(
        operators={"react": ReActOperator(max_steps=1), "execute": _FakeExecuteOperator(workspace)},
        services={"llm": llm, "sandbox": SimpleNamespace(), "workspace": workspace},
        agent_config={},
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    output_path = tmp_path / "out" / "answer.txt"

    await workflow.solve(
        description="Return the final answer.",
        io_instructions="Write the answer to answer.txt.",
        data_dir=data_dir,
        output_path=output_path,
    )

    assert not output_path.exists()
    assert len(llm.calls) == 1


@pytest.mark.asyncio
async def test_react_workflow_repairs_unclosed_answer_and_stops(tmp_path) -> None:
    workspace = _DummyWorkspaceService(tmp_path / "workspace")
    llm = _DummyLLMService(["<Think>x</Think>\n<Answer>42"])

    workflow = ReActWorkflow(
        operators={"react": ReActOperator(max_steps=3), "execute": _FakeExecuteOperator(workspace)},
        services={"llm": llm, "sandbox": SimpleNamespace(), "workspace": workspace},
        agent_config={},
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    output_path = tmp_path / "out" / "answer.txt"

    await workflow.solve(
        description="Return the final answer.",
        io_instructions="Write the answer to answer.txt.",
        data_dir=data_dir,
        output_path=output_path,
    )

    assert len(llm.calls) == 1
    messages_path = workspace.get_path("artifacts") / "messages.json"
    saved_messages = json.loads(messages_path.read_text(encoding="utf-8"))
    assert saved_messages[-1]["content"] == "<Think>x</Think>\n<Answer>42\n</Answer>"


@pytest.mark.asyncio
async def test_react_workflow_leaves_directory_submission_artifact_in_sandbox(tmp_path) -> None:
    workspace = _DummyWorkspaceService(tmp_path / "workspace")
    llm = _DummyLLMService(["<Think>x</Think><Action>```python\nprint('dir')\n```</Action>"])

    workflow = ReActWorkflow(
        operators={
            "react": ReActOperator(max_steps=1),
            "execute": _FakeExecuteOperator(
                workspace,
                stdout="dir",
                create_directory_output_name="submission_bundle",
            ),
        },
        services={"llm": llm, "sandbox": SimpleNamespace(), "workspace": workspace},
        agent_config={},
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    output_path = tmp_path / "out" / "submission_bundle"

    await workflow.solve(
        description="Create a submission directory with the required covariance files.",
        io_instructions="Create submission_bundle in the working directory.",
        data_dir=data_dir,
        output_path=output_path,
    )

    sandbox_dir = workspace.get_path("sandbox_workdir") / "submission_bundle"
    assert sandbox_dir.is_dir()
    assert (sandbox_dir / "before_covariance.csv").exists()
    assert (sandbox_dir / "after_covariance.csv").exists()
    assert not output_path.exists()
