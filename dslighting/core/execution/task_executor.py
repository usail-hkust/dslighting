"""Shared task execution entrypoint for task_id-based runs."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, Union

from dslighting.config import DSLightingConfig
from dslighting.core.execution.result_mapper import map_execution_result
from dslighting.core.interfaces import AgentResult
from dslighting.core.types import TaskDefinition

if TYPE_CHECKING:
    from dslighting.runner import DSLightingRunner


class TaskExecutor:
    """Run a single task_id through DSLightingRunner and normalize the result."""

    def __init__(self, config: DSLightingConfig, workflow_name: str) -> None:
        self._config = config
        self._workflow_name = workflow_name

    async def run_with_task_id(
        self,
        *,
        task_id: str,
        data_dir: Optional[Path] = None,
        registry_dir: Optional[Union[str, Path]] = None,
        task_description: Optional[str] = None,
        output: Optional[Union[str, Path]] = None,
        on_runner_created: Optional[Callable[["DSLightingRunner"], None]] = None,
    ) -> AgentResult:
        from dslighting.runner import DSLightingRunner

        runner = DSLightingRunner(self._config)
        if on_runner_created is not None:
            on_runner_created(runner)

        from dslighting.core.tasks import MLETaskLoader

        loader = MLETaskLoader()
        description, _, public_data_dir, output_path = loader.load_task(
            task_id=task_id,
            data_dir=data_dir,
            registry_dir=registry_dir,
        )
        task_type = getattr(loader, "last_task_type", "kaggle")
        resolved_registry_dir = getattr(loader, "last_registry_root", None)

        if task_description:
            description = task_description
        if output is not None:
            output_path = Path(output)

        task = TaskDefinition(
            task_id=task_id,
            task_type=task_type,
            payload={
                "description": description,
                "public_data_dir": str(public_data_dir),
                "output_submission_path": str(output_path),
                "registry_dir": str(resolved_registry_dir) if resolved_registry_dir else None,
            },
        )

        eval_fn = runner.get_eval_function()
        started_at = time.perf_counter()
        raw_output, total_cost, usage = await eval_fn(task)
        duration = time.perf_counter() - started_at

        return map_execution_result(
            raw_output=raw_output,
            total_cost=total_cost,
            usage=usage,
            workflow_name=self._workflow_name,
            task_id=task_id,
            duration=duration,
        )
