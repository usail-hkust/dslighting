from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

pytest.importorskip("nbformat")

from dslighting.error import LLMServiceError
from dslighting.state.search.journal import JournalState
from dslighting.workflows.search.aide_workflow import AIDEWorkflow


def test_aide_workflow_build_task_context_includes_metric_semantics() -> None:
    workflow = AIDEWorkflow(
        operators={"execute": object(), "generate": object(), "review": object()},
        services={"state": JournalState(), "sandbox": object(), "llm": object(), "workspace": None},
        agent_config={"search": {"max_iterations": 1}, "task_context": {"metric_name": "score", "lower_is_better": True}},
        benchmark=None,
    )

    task_context = workflow._build_task_context(
        description="Solve task",
        io_instructions="write submission.csv",
    )

    assert task_context["goal_and_data"] == "Solve task"
    assert task_context["io_instructions"] == "write submission.csv"
    assert task_context["metric_name"] == "score"
    assert task_context["lower_is_better"] is True


@pytest.mark.asyncio
async def test_aide_grounded_review_failure_preserves_grounded_score(tmp_path: Path) -> None:
    sandbox_workdir = tmp_path / "sandbox_workdir"
    sandbox_workdir.mkdir()
    (sandbox_workdir / "submission.csv").write_text("id,pred\n1,1\n", encoding="utf-8")

    execute_result = SimpleNamespace(
        success=True,
        stdout="done",
        stderr="",
        exc_type=None,
        metadata={},
    )
    sandbox_service = Mock()
    sandbox_service.workspace.get_path.return_value = sandbox_workdir

    workflow = AIDEWorkflow(
        operators={
            "execute": AsyncMock(return_value=execute_result),
            "generate": AsyncMock(return_value=("plan", "print('ok')")),
            "review": AsyncMock(side_effect=LLMServiceError("review auth failed")),
        },
        services={
            "state": JournalState(),
            "sandbox": sandbox_service,
            "llm": Mock(call_history=[], get_call_history=Mock(return_value=[])),
            "workspace": None,
        },
        agent_config={"search": {"max_iterations": 1}, "task_context": {"lower_is_better": False}},
        benchmark=Mock(),
    )
    workflow._grade_submission_with_context = AsyncMock(return_value=1.0)  # type: ignore[method-assign]

    await workflow._execute_search_step(
        task_context={"goal_and_data": "Solve task", "io_instructions": "write submission.csv", "lower_is_better": False},
        output_path=Path("submission.csv"),
    )

    best_node = workflow.state.get_best_node()
    assert best_node is not None
    assert best_node.is_buggy is False
    assert best_node.metric.value == 1.0
    assert best_node.metric.maximize is True
    assert "Grounded Score: 1.0000." in best_node.analysis
    assert "Review unavailable due to LLM failure" in best_node.analysis
