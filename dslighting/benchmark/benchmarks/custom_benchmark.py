"""
Custom Benchmark

Fully lightweight custom benchmark (no dependency on open-source frameworks).

This benchmark is designed for:
- User-defined task lists
- Tasks loaded from config.yaml
- No dependency on open-source frameworks like MLE-Bench

Example:
    >>> tasks = [task1, task2, task3]
    >>> benchmark = CustomBenchmark("my-benchmark", tasks)
    >>> results = await benchmark.run_evaluation(eval_fn)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from dslighting.benchmark.core.base import BaseBenchmark, BenchmarkTaskEvaluator
from dslighting.core.types.task import TaskDefinition

logger = logging.getLogger(__name__)


__all__ = ["CustomBenchmark", "CustomTaskEvaluator"]


class CustomTaskEvaluator(BenchmarkTaskEvaluator):
    """Task evaluator for custom benchmarks.

    This evaluator processes tasks from custom benchmarks and transforms
    evaluation results into the standard format.

    Attributes:
        RESULT_COLUMNS: Result column names for CSV output.
    """

    RESULT_COLUMNS = [
        "task_id",
        "score",
        "cost",
        "duration",
        "output",
        "error",
        "metadata",
    ]

    async def evaluate(
        self,
        task: TaskDefinition,
        eval_fn: Callable,
        **kwargs: Any,
    ) -> Tuple[Tuple, Optional[Any], Optional[str]]:
        """Evaluate a single custom task.

        Args:
            task: TaskDefinition to evaluate.
            eval_fn: Evaluation function to call.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple of (result_row, report, error_message).
        """
        error_message = None

        try:
            result = await eval_fn(task, **kwargs)
        except Exception as exc:
            result = {}
            error_message = str(exc)

        if not isinstance(result, dict):
            error_message = error_message or f"Invalid result type: {type(result)}"
            result = {"output": result}

        score = result.get("score")
        cost = result.get("cost")
        duration = result.get("duration")
        output = result.get("output")
        if not error_message:
            error_message = result.get("error")

        extras = {
            key: value
            for key, value in result.items()
            if key not in {"task_id", "score", "cost", "duration", "output", "error"}
        }
        metadata = json.dumps(extras, ensure_ascii=True) if extras else ""

        row = (
            task.task_id,
            score,
            cost,
            duration,
            output,
            error_message,
            metadata,
        )
        return row, None, error_message


class CustomBenchmark(BaseBenchmark):
    """Fully lightweight custom benchmark.

    This benchmark class allows users to define their own task lists
    without depending on external frameworks like MLE-Bench.

    Attributes:
        RESULT_COLUMNS: Result column names for CSV output.

    Example:
        >>> tasks = [task1, task2, task3]
        >>> benchmark = CustomBenchmark("my-benchmark", tasks)
        >>> results = benchmark.run_evaluation(eval_fn)
    """

    RESULT_COLUMNS = [
        "task_id",
        "score",
        "cost",
        "duration",
        "output",
        "error",
        "metadata",
    ]

    def __init__(
        self,
        name: str,
        tasks: List[TaskDefinition],
        log_path: str = "runs/benchmarks/custom",
    ):
        """Initialize the custom benchmark.

        Args:
            name: Benchmark name.
            tasks: List of TaskDefinition objects.
            log_path: Directory for output logs.
        """
        self._tasks = tasks
        super().__init__(name, file_path=None, log_path=log_path)
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

        logger.debug(f"Custom Benchmark initialized: {name}")
        logger.info(f"  Tasks: {len(tasks)}")

    def _load_problems(self) -> List[Dict[str, Any]]:
        """Load problems from internal task list."""
        return [{"task": task} for task in self._tasks]

    def get_result_columns(self) -> List[str]:
        """Get result column names.

        Returns:
            List of column names for the results CSV.
        """
        return self.RESULT_COLUMNS

    async def evaluate_problem(
        self,
        problem: Dict[str, Any],
        eval_fn: Callable,
        **kwargs: Any,
    ) -> Tuple[Tuple, Optional[Any], Optional[str]]:
        """Evaluate a single problem.

        Args:
            problem: Problem dictionary containing task.
            eval_fn: Evaluation function to call.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple of (result_row, report, error_message).
        """
        evaluator = CustomTaskEvaluator()
        task: TaskDefinition = problem["task"]
        return await evaluator.evaluate(task, eval_fn, **kwargs)

    @classmethod
    def from_config(
        cls,
        name: str,
        config: Dict[str, Any],
        registry_dir: Path,
        data_dir: Path,
    ) -> "CustomBenchmark":
        """Create benchmark from configuration.

        Args:
            name: Benchmark name.
            config: Configuration dictionary with task definitions.
            registry_dir: Registry directory path.
            data_dir: Data directory path.

        Returns:
            CustomBenchmark instance.
        """
        from dslighting.api.convenience import load_data

        tasks: List[TaskDefinition] = []

        for task_config in config.get("tasks", []):
            task_id = task_config.get("task_id") or task_config.get("id")

            if not task_id:
                logger.warning(f"Skipping task without task_id: {task_config}")
                continue

            try:
                loaded_data = load_data(
                    task_id=task_id,
                    registry_parent_dir=str(registry_dir),
                    data_parent_dir=str(data_dir),
                )

                task = TaskDefinition(
                    task_id=task_id,
                    task_type=loaded_data.get_task_type(),
                    payload={
                        "description": loaded_data.description or "",
                        "data_dir": str(loaded_data.data_dir) if loaded_data.data_dir else None,
                    },
                )

                tasks.append(task)

            except Exception as exc:
                logger.warning(f"Failed to load task '{task_id}': {exc}")
                continue

        logger.info(f"Loaded {len(tasks)} tasks from config")

        return cls(name, tasks)
