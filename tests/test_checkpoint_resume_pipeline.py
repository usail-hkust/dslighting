import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from dslighting.benchmark.core.async_runner import AsyncEvaluationRunner
from dslighting.benchmark.core.scheduler_core import BenchmarkRuntimeScheduler


class DummyBenchmark:
    RESULT_COLUMNS = [
        "task_id",
        "score",
        "cost",
        "duration",
        "output",
        "error",
        "metadata",
    ]

    def __init__(self, log_dir: Path, problems: List[Dict[str, Any]], name: str = "demo"):
        self.name = name
        self.problems = problems
        self.log_path = str(log_dir)
        self.results_path = log_dir / f"{name}_results.csv"
        self.metadata_path = log_dir / f"{name}_metadata.json"
        self._metadata_payload: Dict[str, Any] = {}
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

    def get_result_columns(self) -> List[str]:
        return list(self.RESULT_COLUMNS)

    async def evaluate_problem(self, problem: Dict[str, Any], eval_fn, **kwargs):  # noqa: ANN001
        task = SimpleNamespace(payload={"task_id": problem["task_id"]})
        result = await eval_fn(task, **kwargs)
        return (
            (
                problem["task_id"],
                float(result.get("score", 1.0)),
                0.0,
                0.0,
                "",
                "",
                "{}",
            ),
            None,
            "",
        )

    def _write_metadata_json(self, df, **kwargs):  # noqa: ANN001
        self._metadata_payload = kwargs
        self.metadata_path.write_text(json.dumps(kwargs, default=str), encoding="utf-8")


@pytest.fixture
def patch_monitoring(monkeypatch):
    async def fake_run_with_monitoring(
        problems: List[Dict[str, Any]],
        scheduler_options,
        monitor_options=None,  # noqa: ANN001
    ):
        return BenchmarkRuntimeScheduler(problems, scheduler_options)

    from dslighting.benchmark.core.monitoring_integration import MonitoringIntegration

    monkeypatch.setattr(
        MonitoringIntegration,
        "run_with_monitoring",
        staticmethod(fake_run_with_monitoring),
    )


@pytest.mark.asyncio
async def test_checkpoint_resume_uses_run_id_to_skip_completed_tasks(tmp_path: Path, patch_monitoring):
    problems = [
        {"task_id": "task-1"},
        {"task_id": "task-2"},
        {"task_id": "task-3"},
    ]
    run_id = "resume-001"
    first_benchmark = DummyBenchmark(tmp_path, problems, name="resume_demo")
    first_runner = AsyncEvaluationRunner(first_benchmark)
    first_calls: List[str] = []

    async def eval_fail_once(task: Any, *args, **kwargs):  # noqa: ANN002, ANN003
        task_id = task.payload["task_id"]
        first_calls.append(task_id)
        if task_id == "task-2":
            raise RuntimeError("simulated failure")
        return {"score": 1.0}

    first_results = await first_runner.run_async(
        eval_fail_once,
        checkpoint_resume_enabled=True,
        run_id=run_id,
        max_concurrency=1,
    )

    assert len(first_results) == 2
    assert set(first_calls) == {"task-1", "task-2", "task-3"}

    second_benchmark = DummyBenchmark(tmp_path, problems, name="resume_demo")
    second_runner = AsyncEvaluationRunner(second_benchmark)
    second_calls: List[str] = []

    async def eval_success(task: Any, *args, **kwargs):  # noqa: ANN002, ANN003
        task_id = task.payload["task_id"]
        second_calls.append(task_id)
        return {"score": 1.0}

    second_results = await second_runner.run_async(
        eval_success,
        checkpoint_resume_enabled=True,
        run_id=run_id,
        max_concurrency=1,
    )

    assert len(second_results) == 3
    assert second_calls == ["task-2"]

    scheduler_stats = second_benchmark._metadata_payload["scheduler_stats"]
    assert scheduler_stats["checkpoint_resume_enabled"] is True
    assert scheduler_stats["run_id"] == run_id
    assert scheduler_stats["resumed_task_count"] == 2


@pytest.mark.asyncio
async def test_checkpoint_resume_different_run_id_does_not_resume(tmp_path: Path, patch_monitoring):
    problems = [
        {"task_id": "task-a"},
        {"task_id": "task-b"},
    ]
    first_benchmark = DummyBenchmark(tmp_path, problems, name="run_id_isolation")
    first_runner = AsyncEvaluationRunner(first_benchmark)

    async def eval_first(task: Any, *args, **kwargs):  # noqa: ANN002, ANN003
        if task.payload["task_id"] == "task-b":
            raise RuntimeError("fail to leave partial checkpoint")
        return {"score": 1.0}

    await first_runner.run_async(
        eval_first,
        checkpoint_resume_enabled=True,
        run_id="run-alpha",
        max_concurrency=1,
    )

    second_benchmark = DummyBenchmark(tmp_path, problems, name="run_id_isolation")
    second_runner = AsyncEvaluationRunner(second_benchmark)
    second_calls: List[str] = []

    async def eval_second(task: Any, *args, **kwargs):  # noqa: ANN002, ANN003
        second_calls.append(task.payload["task_id"])
        return {"score": 1.0}

    second_results = await second_runner.run_async(
        eval_second,
        checkpoint_resume_enabled=True,
        run_id="run-beta",
        max_concurrency=1,
    )

    assert len(second_results) == 2
    assert set(second_calls) == {"task-a", "task-b"}
