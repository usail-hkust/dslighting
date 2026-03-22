"""Application service for Agent facade execution orchestration."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path
from uuid import uuid4

from dslighting.core.application.agent_config_builder import AgentConfigBuilder
from dslighting.core.application.task_input_resolver import TaskInputResolver
from dslighting.core.execution import TaskExecutor
from dslighting.core.interfaces import AgentResult


class AgentAppService:
    """Orchestrate Agent facade requests into TaskExecutor runs."""

    def __init__(
        self,
        *,
        workflow_name: str,
        model: str,
        api_key: Optional[Union[str, List[str]]],
        api_keys: Optional[List[str]],
        api_base: Optional[str],
        provider: Optional[str],
        temperature: Optional[float],
        timeout: int,
        keep_workspace: bool,
        sandbox_backend: Optional[str],
        sandbox_backend_type: Optional[str],
        sandbox_timeout: Optional[int],
        sandbox_api_key: Optional[str],
        init_kwargs: Dict[str, Any],
    ) -> None:
        self._workflow_name = workflow_name
        self._config_builder = AgentConfigBuilder(
            workflow_name=workflow_name,
            model=model,
            api_key=api_key,
            api_keys=api_keys,
            api_base=api_base,
            provider=provider,
            temperature=temperature,
            timeout=timeout,
            keep_workspace=keep_workspace,
            sandbox_backend=sandbox_backend,
            sandbox_backend_type=sandbox_backend_type,
            sandbox_timeout=sandbox_timeout,
            sandbox_api_key=sandbox_api_key,
            init_kwargs=init_kwargs,
        )

    async def run(
        self,
        *,
        task_id: Optional[str],
        data: Any,
        task: Optional[str],
        output: Optional[Union[str, Path]],
        kwargs: Dict[str, Any],
        on_runner_created: Optional[Callable[[Any], None]] = None,
    ) -> AgentResult:
        runtime_kwargs = dict(kwargs)
        description = runtime_kwargs.pop("description", None)
        data_dir = runtime_kwargs.pop("data_dir", None)
        registry_dir = runtime_kwargs.pop("registry_dir", None)

        resolved = TaskInputResolver.resolve(
            task_id=task_id,
            data=data,
            task=task,
            output=output,
            description=description,
            data_dir=data_dir,
            registry_dir=registry_dir,
            run_kwargs=runtime_kwargs,
        )
        config = self._config_builder.build(
            task_id=resolved.task_id,
            run_kwargs=resolved.run_kwargs,
        )
        if getattr(config.scheduler, "run_id", None) is None:
            config.scheduler.run_id = f"{self._workflow_name}_{resolved.task_id}_{uuid4().hex[:8]}"

        executor = TaskExecutor(config=config, workflow_name=self._workflow_name)
        return await executor.run_with_task_id(
            task_id=resolved.task_id,
            data_dir=resolved.data_dir,
            registry_dir=resolved.registry_dir,
            task_description=resolved.task_description,
            output=resolved.output,
            on_runner_created=on_runner_created,
        )
