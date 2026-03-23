"""Shared task execution entrypoint for task_id-based runs."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, Union
from uuid import uuid4
from dataclasses import replace

from dslighting.config import DSLightingConfig
from dslighting.debug import debug_scope, get_debug_session
from dslighting.debug.models import RunDebugContext
from dslighting.core.execution.result_mapper import map_execution_result
from dslighting.core.interfaces import AgentResult
from dslighting.core.tasks import FileSubmissionTaskAdapter, TaskResolver
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

        session = get_debug_session()
        run_id = getattr(self._config.scheduler, "run_id", None) or f"run_{uuid4().hex[:8]}"
        if getattr(self._config.scheduler, "run_id", None) != run_id:
            self._config.scheduler.run_id = run_id
        run_context = None
        if session is not None and session.enabled:
            run_context = RunDebugContext(
                session_id=session.session_id,
                run_id=run_id,
                task_id=task_id,
                workflow_name=self._workflow_name,
            )

        with debug_scope(run=run_context):
            runner = DSLightingRunner(self._config)
            if on_runner_created is not None:
                on_runner_created(runner)

            resolver = TaskResolver()
            layout = resolver.resolve(
                task_id=task_id,
                data=data_dir,
                registry_dir=registry_dir,
            )
            adapter = FileSubmissionTaskAdapter(self._config)
            spec = adapter.build_file_submission_spec(layout, adapter.data_perception)
            adapter.cleanup()

            if task_description:
                spec = replace(spec, description_text=task_description)
            if output is not None:
                overridden_output = Path(output)
                submission_contract = spec.submission_artifact_contract
                if submission_contract is not None:
                    submission_contract = submission_contract.with_output_path(overridden_output)
                spec = replace(
                    spec,
                    output_path=overridden_output,
                    submission_artifact_contract=submission_contract,
                )

            task = TaskDefinition(
                task_id=task_id,
                task_type=layout.task_type,
                payload={
                    **spec.to_payload(),
                    "registry_dir": str(layout.registry_root),
                    "task_root": str(layout.task_root),
                    "data_root": str(layout.data_root),
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
