"""
Agent - High-Level Agent Interface

User-friendly agent class that wraps preset agents using factory pattern.

Note:
    Agent.run() returns AgentResult for single-task execution.
    For multi-task benchmarks, use DSBenchmark.run() which returns
    a Benchmark object with comprehensive results for all tasks.

Example:
    >>> from dslighting import Agent, DSBenchmark
    >>>
    >>> # Single task - returns AgentResult
    >>> agent = Agent(workflow="aide", model="gpt-4o")
    >>> result = agent.run(task_id="bike-sharing-demand")
    >>> print(result.score)  # Access task score
    >>>
    >>> # Multiple tasks - returns Benchmark object
    >>> benchmark = DSBenchmark("dabench").run(model="gpt-4o")
    >>> print(benchmark.summary["score"])  # Average score across tasks
"""

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

# Import core interfaces
from dslighting.config import DSLightingConfig, LLMConfig, RunConfig, SandboxConfig, WorkflowConfig
from dslighting.core.execution import TaskExecutor
from dslighting.core.interfaces import AgentInterface, AgentResult
if TYPE_CHECKING:
    from dslighting.runner import DSLightingRunner
from dslighting.error import ConfigurationError, TaskError

if TYPE_CHECKING:
    from dslighting.core.data import TaskContext

logger = logging.getLogger(__name__)


WORKFLOW_ALIASES = {
    "aide": "aide",
    "autokaggle": "autokaggle",
    "kaggle": "autokaggle",
    "data_interpreter": "data_interpreter",
    "interpreter": "data_interpreter",
    "deepanalyze": "deepanalyze",
    "dsagent": "dsagent",
    "automind": "automind",
    "aflow": "aflow",
}


class Agent(AgentInterface):
    """
    High-level Agent interface.

    This is the user-facing agent class that provides a simple interface
    to run data science tasks.

    Example:
        from dslighting import Agent

        agent = Agent(workflow="aide", model="gpt-4o")
        result = agent.run(task_id="bike-sharing-demand")
    """

    def __init__(
        self,
        workflow: str = "aide",
        model: str = "gpt-4o",
        api_key: str = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        timeout: int = 300,
        keep_workspace: bool = False,
        **kwargs
    ):
        """
        Initialize Agent.

        Args:
            workflow: Name of the workflow to use ("aide", "autokaggle", "data_interpreter", "deepanalyze", "dsagent", "automind", "aflow")
            model: LLM model to use
            api_key: API key (optional, will be read from env if not provided)
            api_base: API base URL (optional, will be read from env if not provided)
            provider: LLM provider (optional)
            temperature: Temperature parameter (optional, will be read from env if not provided)
            timeout: Sandbox timeout in seconds
            keep_workspace: Whether to keep workspace after execution
            **kwargs: Additional arguments passed to create_agent()
        """
        workflow_key = workflow.lower()
        if workflow_key not in WORKFLOW_ALIASES:
            raise ConfigurationError(
                f"Unknown workflow: {workflow}. "
                f"Choose from: aide, autokaggle, data_interpreter, deepanalyze, dsagent, automind, aflow",
                error_code="CFG-002",
            )

        self.workflow_name = WORKFLOW_ALIASES[workflow_key]
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.provider = provider
        self.temperature = temperature
        self.timeout = timeout
        self.keep_workspace = keep_workspace
        self._agent_kwargs = kwargs
        self._last_runner: Optional[DSLightingRunner] = None

    def run(
        self,
        task_id: Optional[str] = None,
        data: Optional[Union[str, Path, 'TaskContext']] = None,
        task: Optional[str] = None,
        output: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> AgentResult:
        """
        Run the agent on a task synchronously.

        This method wraps the async execution for convenience. For async contexts,
        use async_run() instead.

        Args:
            task_id: Task ID to load from registry (recommended)
            data: Data to process (can be a path or TaskContext object)
            task: Task description
            output: Output path
            **kwargs: Additional arguments

        Returns:
            AgentResult object containing execution results

        Example:
            # Method 1: Use task_id (recommended)
            result = agent.run(task_id="bike-sharing-demand")

            # Method 2: Use data path
            result = agent.run(data="path/to/data", task="Predict demand")
        """
        return asyncio.run(
            self._run_with_task_id(
                task_id=task_id,
                data_dir=self._resolve_data_dir_sync(data, kwargs.pop("data_dir", None), task_id),
                task_description=kwargs.pop("description", None) or task,
                output=output,
                **kwargs,
            )
        )

    async def async_run(
        self,
        task_id: Optional[str] = None,
        data: Optional[Union[str, Path, 'TaskContext']] = None,
        task: Optional[str] = None,
        output: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> AgentResult:
        """
        Run the agent on a task asynchronously.

        Use this method when you need to run multiple agents concurrently
        or when integrating with async frameworks.

        Args:
            task_id: Task ID to load from registry (recommended)
            data: Data to process (can be a path or TaskContext object)
            task: Task description
            output: Output path
            **kwargs: Additional arguments

        Returns:
            AgentResult object containing execution results
        """
        description = kwargs.pop("description", None) or task
        data_dir_arg = kwargs.pop("data_dir", None)

        resolved_task_id = task_id or self._extract_task_id(data)
        if not resolved_task_id:
            raise TaskError(
                "Cannot determine task_id. Pass `task_id=` explicitly, or provide "
                "a TaskContext/path that includes the competition directory.",
                error_code="TSK-005",
            )

        resolved_data_dir = self._extract_data_dir(data, data_dir_arg, resolved_task_id)

        return await self._run_with_task_id(
            task_id=resolved_task_id,
            data_dir=resolved_data_dir,
            task_description=description,
            output=output,
            **kwargs,
        )

    def _resolve_data_dir_sync(
        self,
        data: Any,
        data_dir_arg: Optional[Union[str, Path]],
        task_id: str,
    ) -> Optional[Path]:
        """Synchronous wrapper for data directory resolution."""
        resolved_task_id = task_id or self._extract_task_id(data)
        if not resolved_task_id:
            return None
        return self._extract_data_dir(data, data_dir_arg, resolved_task_id)

    def _extract_task_id(self, data: Any) -> Optional[str]:
        if data is None:
            return None

        task_id = getattr(data, "task_id", None)
        if task_id:
            return str(task_id)

        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.is_file():
                return path.parent.name
            return path.name

        return None

    def _extract_data_dir(
        self,
        data: Any,
        data_dir_arg: Optional[Union[str, Path]],
        task_id: str,
    ) -> Optional[Path]:
        if data_dir_arg is not None:
            return Path(data_dir_arg)

        context_data_dir = getattr(data, "data_dir", None)
        if context_data_dir is not None:
            return Path(context_data_dir)

        if isinstance(data, (str, Path)):
            candidate = Path(data)
            if candidate.is_file():
                return candidate.parent
            if candidate.exists():
                return candidate

        return None

    def _build_config(self, task_id: str, run_kwargs: Dict[str, Any]) -> DSLightingConfig:
        # Build LLM config with provided values (api_key takes precedence over env vars)
        llm_kwargs = {"model": self.model}
        if self.api_key is not None:
            llm_kwargs["api_key"] = self.api_key
        if self.api_base is not None:
            llm_kwargs["api_base"] = self.api_base
        if self.provider is not None:
            llm_kwargs["provider"] = self.provider
        if self.temperature is not None:
            llm_kwargs["temperature"] = self.temperature

        llm = LLMConfig(**llm_kwargs)

        config = DSLightingConfig(
            run=RunConfig(
                name=f"agent_{self.workflow_name}_{task_id}",
                keep_all_workspaces=self.keep_workspace,
                keep_workspace_on_failure=self.keep_workspace,
            ),
            workflow=WorkflowConfig(name=self.workflow_name, params={}),
            llm=llm,
            sandbox=SandboxConfig(timeout=self.timeout),
        )

        # Merge initialization-time kwargs first, then run-time kwargs.
        merged = {**self._agent_kwargs, **run_kwargs}

        search_keys = {"num_drafts", "debug_prob", "max_iterations", "max_debug_depth"}
        if self.workflow_name != "autokaggle":
            search_keys.add("enforce_no_plotting")
        for key in search_keys:
            if key in merged:
                setattr(config.agent.search, key, merged.pop(key))

        autokaggle_keys = {"max_attempts_per_phase", "success_threshold"}
        if self.workflow_name == "autokaggle":
            autokaggle_keys.add("enforce_no_plotting")
        for key in autokaggle_keys:
            if key in merged:
                setattr(config.agent.autokaggle, key, merged.pop(key))

        if merged:
            config.run.parameters.update(merged)

        return config

    async def _run_with_task_id(
        self,
        task_id: str,
        data_dir: Optional[Path] = None,
        registry_dir: Optional[Union[str, Path]] = None,
        task_description: Optional[str] = None,
        output: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> AgentResult:
        config = self._build_config(task_id=task_id, run_kwargs=kwargs)
        executor = TaskExecutor(config=config, workflow_name=self.workflow_name)
        return await executor.run_with_task_id(
            task_id=task_id,
            data_dir=data_dir,
            registry_dir=registry_dir,
            task_description=task_description,
            output=output,
            on_runner_created=lambda runner: setattr(self, "_last_runner", runner),
        )

    def cleanup(self):
        """Clean up workspace"""
        # DSLightingRunner/workflow cleanup is handled inside the evaluation pipeline.
        # Keep this method for API compatibility.
        self._last_runner = None
