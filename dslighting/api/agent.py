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
    >>> from dslighting.core import ConfigBuilder
    >>> config = ConfigBuilder().build_config(model="gpt-4o")
    >>> benchmark = DSBenchmark("dabench").run(config=config)
    >>> print(benchmark.summary["score"])  # Average score across all tasks
"""

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Union

from dslighting.core.application import AgentAppService
from dslighting.core.interfaces import AgentInterface, AgentResult
if TYPE_CHECKING:
    from dslighting.runner import DSLightingRunner
from dslighting.error import ConfigurationError

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
    "react": "react",
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
        api_key: Union[str, List[str], None] = None,
        api_keys: Optional[List[str]] = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        timeout: int = 300,
        keep_workspace: bool = False,
        sandbox_backend: Optional[str] = None,
        sandbox_backend_type: Optional[str] = None,
        sandbox_timeout: Optional[int] = None,
        sandbox_api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Agent.

        Args:
            workflow: Name of the workflow to use ("aide", "autokaggle", "data_interpreter", "deepanalyze", "dsagent", "automind", "aflow")
            model: LLM model to use
            api_key: API key (optional, will be read from env if not provided)
            api_keys: API key pool for rotation (optional)
            api_base: API base URL (optional, will be read from env if not provided)
            provider: LLM provider (optional)
            temperature: Temperature parameter (optional, will be read from env if not provided)
            timeout: Sandbox timeout in seconds
            keep_workspace: Whether to keep workspace after execution
            sandbox_backend: Optional sandbox backend:
                "local" | "e2b" | "ds_sandbox"
            sandbox_backend_type: Optional DS-Sandbox backend type:
                "docker" | "local"
            sandbox_timeout: Optional sandbox timeout override in seconds
            sandbox_api_key: Optional API key for E2B backend.
                If omitted, E2B_API_KEY from environment is used.
            **kwargs: Additional arguments passed to configuration builder.
                For RAG workflows, use namespaced arguments:
                `dsagent={"enable_rag": True, "case_dir": "./experience_replay"}`
                or `automind={"enable_rag": True, "case_dir": "./experience_replay"}`.
        """
        workflow_key = workflow.lower()
        if workflow_key not in WORKFLOW_ALIASES:
            raise ConfigurationError(
                f"Unknown workflow: {workflow}. "
                f"Choose from: aide, autokaggle, data_interpreter, deepanalyze, dsagent, automind, aflow, react",
                error_code="CFG-002",
            )

        if api_key is not None and api_keys is not None:
            raise ConfigurationError(
                "Only one of `api_key` or `api_keys` may be provided.",
                error_code="CFG-002",
            )

        self.workflow_name = WORKFLOW_ALIASES[workflow_key]
        self.model = model
        self.api_key = api_key
        self.api_keys = api_keys
        self.api_base = api_base
        self.provider = provider
        self.temperature = temperature
        self.timeout = timeout
        self.keep_workspace = keep_workspace
        self.sandbox_backend = sandbox_backend
        self.sandbox_backend_type = sandbox_backend_type
        self.sandbox_timeout = sandbox_timeout
        self.sandbox_api_key = sandbox_api_key
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
        try:
            asyncio.get_running_loop()
            raise ConfigurationError(
                "Agent.run() cannot be called from an async context.",
                error_code="CFG-003",
                details={"method": "run", "alternative": "async_run"},
                suggestion="Use `await agent.async_run(...)` in async contexts.",
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e):
                raise

        return asyncio.run(self.async_run(task_id=task_id, data=data, task=task, output=output, **kwargs))

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
        app_service = self._create_app_service()
        return await app_service.run(
            task_id=task_id,
            data=data,
            task=task,
            output=output,
            kwargs=kwargs,
            on_runner_created=lambda runner: setattr(self, "_last_runner", runner),
        )

    def _create_app_service(self) -> AgentAppService:
        return AgentAppService(
            workflow_name=self.workflow_name,
            model=self.model,
            api_key=self.api_key,
            api_keys=self.api_keys,
            api_base=self.api_base,
            provider=self.provider,
            temperature=self.temperature,
            timeout=self.timeout,
            keep_workspace=self.keep_workspace,
            sandbox_backend=self.sandbox_backend,
            sandbox_backend_type=self.sandbox_backend_type,
            sandbox_timeout=self.sandbox_timeout,
            sandbox_api_key=self.sandbox_api_key,
            init_kwargs=self._agent_kwargs,
        )

    def cleanup(self):
        """Clean up workspace"""
        # DSLightingRunner/workflow cleanup is handled inside the evaluation pipeline.
        # Keep this method for API compatibility.
        self._last_runner = None
