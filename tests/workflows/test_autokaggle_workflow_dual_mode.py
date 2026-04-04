from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from dslighting.core.types import FileArtifact, StepPlan, TaskContract
from dslighting.runtime.dag import NodeResult
from dslighting.workflows.manual.autokaggle_workflow import AutoKaggleWorkflow


def _build_contract() -> TaskContract:
    return TaskContract(
        task_goal="Predict labels",
        task_type="classification",
        input_files=[FileArtifact(filename="train.csv", description="training data")],
        output_files=[FileArtifact(filename="submission.csv", description="final predictions")],
        evaluation_metric="accuracy",
    )


def _build_workflow(tmp_path: Path) -> tuple[AutoKaggleWorkflow, Path]:
    sandbox_workdir = tmp_path / "sandbox"
    sandbox_workdir.mkdir(parents=True, exist_ok=True)

    sandbox_workspace = MagicMock()
    sandbox_workspace.get_path.return_value = sandbox_workdir

    sandbox_service = MagicMock()
    sandbox_service.workspace = sandbox_workspace

    services = {
        "workspace": MagicMock(),
        "llm": MagicMock(),
        "sandbox": sandbox_service,
    }
    workflow = AutoKaggleWorkflow(
        operators={},
        services=services,
        agent_config={"autokaggle": {"max_attempts_per_phase": 2, "success_threshold": 3.0}},
    )
    return workflow, sandbox_workdir


@pytest.mark.asyncio
async def test_autokaggle_solve_keeps_legacy_path(tmp_path: Path) -> None:
    workflow, sandbox_workdir = _build_workflow(tmp_path)

    task_contract = _build_contract()
    step_plan_phase_1 = StepPlan(
        plan="Create intermediate features.",
        input_artifacts=[],
        output_files=["features.csv"],
    )
    step_plan_phase_2 = StepPlan(
        plan="Train and export final submission.",
        input_artifacts=["features.csv"],
        output_files=["submission.csv"],
    )

    async def developer_side_effect(
        state,
        phase_goal: str,
        plan: str,
        attempt_history,
    ):
        _ = (state, plan, attempt_history)
        if phase_goal == "phase-1":
            (sandbox_workdir / "features.csv").write_text("f1,f2\n1,2\n", encoding="utf-8")
        if phase_goal == "phase-2":
            (sandbox_workdir / "submission.csv").write_text("id,pred\n1,0\n", encoding="utf-8")
        return {
            "status": True,
            "code": "print('ok')",
            "output": "ok",
            "error": "",
            "validation_result": {"status": "ok"},
            "format_validation_result": {"passed": True, "errors": []},
        }

    planner = MagicMock()
    planner.plan_phases = AsyncMock(return_value=["phase-1", "phase-2"])
    planner.plan_step_details = AsyncMock(side_effect=[step_plan_phase_1, step_plan_phase_2])

    workflow.operators = {
        "deconstructor": AsyncMock(return_value=task_contract),
        "planner": planner,
        "developer": AsyncMock(side_effect=developer_side_effect),
        "reviewer": AsyncMock(return_value={"score": 4.0, "suggestion": "looks good"}),
        "summarizer": AsyncMock(return_value="phase complete"),
    }

    output_path = tmp_path / "out" / "submission.csv"
    await workflow.solve(
        description="Solve the benchmark task",
        io_instructions="Input: train.csv; Output: submission.csv",
        data_dir=tmp_path / "data",
        output_path=output_path,
    )

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip() == "id,pred\n1,0"


def test_autokaggle_declarative_graph_runs_to_completion(tmp_path: Path) -> None:
    workflow, sandbox_workdir = _build_workflow(tmp_path)
    task_contract = _build_contract()
    step_plan = StepPlan(
        plan="Generate the final CSV.",
        input_artifacts=[],
        output_files=["submission.csv"],
    )

    graph = workflow.build_operator_graph(
        task_id="task-1",
        description="desc",
        io_instructions="io",
        data_dir=tmp_path / "data",
        output_path=tmp_path / "out" / "submission.csv",
    )
    dag_state = graph.initial_state

    deconstruct_node = graph.initial_nodes[0]
    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=deconstruct_node.node_id,
            task_id="task-1",
            status="success",
            outputs={"value": task_contract},
        ),
        dag_state=dag_state,
    )
    plan_phases_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=plan_phases_node.node_id,
            task_id="task-1",
            status="success",
            outputs={"value": ["phase-1"]},
        ),
        dag_state=dag_state,
    )
    step_plan_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=step_plan_node.node_id,
            task_id="task-1",
            status="success",
            outputs={"value": step_plan},
        ),
        dag_state=dag_state,
    )
    develop_node = delta.new_nodes[0]

    branch_workdir = Path(develop_node.payload["kwargs"]["branch_workdir"])
    (branch_workdir / "submission.csv").write_text("id,pred\n2,1\n", encoding="utf-8")
    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=develop_node.node_id,
            task_id="task-1",
            status="success",
            outputs={
                "status": True,
                "code": "print('ok')",
                "output": "ok",
                "error": "",
                "validation_result": {"status": "ok"},
                "format_validation_result": {"passed": True, "errors": []},
            },
        ),
        dag_state=dag_state,
    )
    review_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=review_node.node_id,
            task_id="task-1",
            status="success",
            outputs={"score": 4.2, "suggestion": "good"},
        ),
        dag_state=dag_state,
    )
    summarize_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=summarize_node.node_id,
            task_id="task-1",
            status="success",
            outputs={"value": "summary"},
        ),
        dag_state=dag_state,
    )
    finalize_node = delta.new_nodes[0]

    finalize_outputs = finalize_node.payload["callable"](**finalize_node.payload["kwargs"])
    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=finalize_node.node_id,
            task_id="task-1",
            status="success",
            outputs=finalize_outputs,
        ),
        dag_state=dag_state,
    )

    assert delta.done is True
    assert delta.final_result["status"] == "success"
    assert (tmp_path / "out" / "submission.csv").exists()


def test_autokaggle_declarative_parallel_drafts_promotes_best_submission(tmp_path: Path) -> None:
    workflow, sandbox_workdir = _build_workflow(tmp_path)
    task_contract = _build_contract()
    first_step_plan = StepPlan(
        plan="First attempt.",
        input_artifacts=[],
        output_files=["submission.csv"],
    )
    second_step_plan = StepPlan(
        plan="Second attempt with parallel drafts.",
        input_artifacts=[],
        output_files=["submission.csv"],
    )

    graph = workflow.build_operator_graph(
        task_id="task-2",
        description="desc",
        io_instructions="io",
        data_dir=tmp_path / "data",
        output_path=tmp_path / "out" / "submission.csv",
        dag_options=SimpleNamespace(parallel_drafts=3, branch_budget=6),
    )
    dag_state = graph.initial_state

    deconstruct_node = graph.initial_nodes[0]
    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=deconstruct_node.node_id,
            task_id="task-2",
            status="success",
            outputs={"value": task_contract},
        ),
        dag_state=dag_state,
    )
    plan_phases_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=plan_phases_node.node_id,
            task_id="task-2",
            status="success",
            outputs={"value": ["phase-1"]},
        ),
        dag_state=dag_state,
    )
    first_step_plan_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=first_step_plan_node.node_id,
            task_id="task-2",
            status="success",
            outputs={"value": first_step_plan},
        ),
        dag_state=dag_state,
    )
    assert len(delta.new_nodes) == 1
    first_develop_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=first_develop_node.node_id,
            task_id="task-2",
            status="success",
            outputs={
                "status": False,
                "code": "print('fail')",
                "output": "",
                "error": "failed",
                "validation_result": {},
                "format_validation_result": {"passed": False, "errors": ["failed"]},
            },
        ),
        dag_state=dag_state,
    )
    first_review_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=first_review_node.node_id,
            task_id="task-2",
            status="success",
            outputs={"score": 1.0, "suggestion": "retry"},
        ),
        dag_state=dag_state,
    )
    second_step_plan_node = delta.new_nodes[0]

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=second_step_plan_node.node_id,
            task_id="task-2",
            status="success",
            outputs={"value": second_step_plan},
        ),
        dag_state=dag_state,
    )
    parallel_develop_nodes = delta.new_nodes
    assert len(parallel_develop_nodes) == 3

    review_nodes = []
    for index, develop_node in enumerate(parallel_develop_nodes):
        branch_workdir = Path(develop_node.payload["kwargs"]["branch_workdir"])
        if index in {0, 1}:
            (branch_workdir / "submission.csv").parent.mkdir(parents=True, exist_ok=True)
            (branch_workdir / "submission.csv").write_text(
                f"id,pred\n1,{index}\n",
                encoding="utf-8",
            )

        dev_status = index in {0, 1}
        delta = workflow.on_operator_node_result(
            result=NodeResult(
                node_id=develop_node.node_id,
                task_id="task-2",
                status="success",
                outputs={
                    "status": dev_status,
                    "code": f"print('draft-{index}')",
                    "output": "ok" if dev_status else "",
                    "error": "" if dev_status else "failed",
                    "validation_result": {"status": "ok"} if dev_status else {},
                    "format_validation_result": {"passed": dev_status, "errors": [] if dev_status else ["failed"]},
                },
            ),
            dag_state=dag_state,
        )
        review_nodes.append(delta.new_nodes[0])

    terminal_delta = None
    review_scores = {0: 3.2, 1: 4.8, 2: 1.0}
    for index, review_node in enumerate(review_nodes):
        terminal_delta = workflow.on_operator_node_result(
            result=NodeResult(
                node_id=review_node.node_id,
                task_id="task-2",
                status="success",
                outputs={"score": review_scores[index], "suggestion": "ok"},
            ),
            dag_state=dag_state,
        )

    assert terminal_delta is not None
    assert len(terminal_delta.new_nodes) == 1
    summarize_node = terminal_delta.new_nodes[0]

    promoted_submission = sandbox_workdir / "submission.csv"
    assert promoted_submission.exists()
    assert promoted_submission.read_text(encoding="utf-8").strip() == "id,pred\n1,1"

    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=summarize_node.node_id,
            task_id="task-2",
            status="success",
            outputs={"value": "summary"},
        ),
        dag_state=dag_state,
    )
    finalize_node = delta.new_nodes[0]

    finalize_outputs = finalize_node.payload["callable"](**finalize_node.payload["kwargs"])
    delta = workflow.on_operator_node_result(
        result=NodeResult(
            node_id=finalize_node.node_id,
            task_id="task-2",
            status="success",
            outputs=finalize_outputs,
        ),
        dag_state=dag_state,
    )

    assert delta.done is True
    assert delta.final_result["status"] == "success"
    assert (tmp_path / "out" / "submission.csv").read_text(encoding="utf-8").strip() == "id,pred\n1,1"

