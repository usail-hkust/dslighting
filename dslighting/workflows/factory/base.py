"""
Base Workflow Factory - Base class for all Workflow Factory

Provides standard MLE task loading functionality, users don't need to reimplement
"""

import logging
from pathlib import Path
from typing import Any, List, Optional, TYPE_CHECKING, Union
from abc import ABC, abstractmethod

from dslighting.config import DSLightingConfig, DataAnalysisConfig, RunConfig, SandboxConfig, WorkflowConfig
from dslighting.core.visualization_policy import consume_visualization_policy
from dslighting.core.config.runtime_logging import log_resolved_runtime_config
from dslighting.core.data import TaskContext
from dslighting.core.execution import TaskExecutor
from dslighting.core.interfaces import WorkflowFactoryInterface

if TYPE_CHECKING:
    from dslighting.runner import DSLightingRunner

logger = logging.getLogger(__name__)


class BaseWorkflowFactory(WorkflowFactoryInterface, ABC):
    """
    Base class for Workflow Factory

    Provides:
    1. Standard LLM/Sandbox/Workspace service creation
    2. Standard MLE task loading (from registry)
    3. run_with_task_id() convenience method

    Users only need to:
    1. Inherit from BaseWorkflowFactory
    2. Implement create_workflow() method
    3. Define their own workflow class
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Union[str, List[str], None] = None,
        api_keys: Optional[List[str]] = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        timeout: int = 300,
        keep_workspace: bool = False,
        **agent_init_kwargs
    ):
        """
        Initialize factory

        Args:
            model: LLM model name
            api_key: API key (optional, read from env var if not provided)
            api_base: API base URL (optional, read from env var if not provided)
            provider: LLM provider (optional)
            temperature: Temperature parameter (optional, read from env var if not provided)
            timeout: Sandbox timeout
            keep_workspace: Whether to keep workspace
            **agent_init_kwargs: Additional parameters, used for run/config initialization

        Note:
            Use DSLighting's ConfigBuilder to automatically read config from environment variables:
            - API_KEY, API_BASE, LLM_MODEL
            - LLM_MODEL_CONFIGS (multi-model config)

        Example:
            >>> factory = MyWorkflowFactory(
            ...     model="gpt-4o",
            ...     max_iterations=3,  # Passed to create_agent()
            ...     use_data_insights=True
            ... )
        """
        self.model = model
        self.timeout = timeout
        self.keep_workspace = keep_workspace
        self._agent_init_kwargs = agent_init_kwargs

        # Use DSLighting's ConfigBuilder to automatically read config from environment variables
        from dslighting.core import ConfigBuilder
        config_builder = ConfigBuilder()
        config = config_builder.build_config(
            model=model,
            api_key=api_key,
            api_keys=api_keys,
            api_base=api_base,
            provider=provider,
            temperature=temperature,
            data_analysis=agent_init_kwargs.get("data_analysis"),
        )
        self._base_config = config

        logger.debug("%s initialized", self.__class__.__name__)
        self._last_runner: Optional[DSLightingRunner] = None

    def _get_workflow_name(self) -> str:
        """
        Get workflow name (used for logging and workspace naming).

        Subclasses can override this method to provide custom names.
        """
        return self.__class__.__name__.replace("Factory", "").lower()

    def create_agent(self, **kwargs: Any) -> Any:
        """
        Create workflow/agent instance for advanced usage.

        Default behavior routes through create_workflow() using an ad-hoc config.
        Subclasses may override this if they require custom create semantics.

        Args:
            **kwargs: Agent configuration parameters

        Returns:
            Agent instance
        """
        config = self._build_config(task_id="adhoc", run_kwargs=kwargs)
        return self.create_workflow(config=config, benchmark=None)

    @abstractmethod
    def create_workflow(self, config: DSLightingConfig, benchmark: Any = None) -> Any:
        """
        Create configured workflow instance for runner execution.

        Args:
            config: Full DSLighting configuration.
            benchmark: Optional benchmark object.
        """
        raise NotImplementedError("Subclasses must implement create_workflow()")

    def cleanup(self):
        """Cleanup workspace"""
        if self.keep_workspace:
            return

        workspace_service = None
        last_runner = getattr(self, "_last_runner", None)
        if last_runner is not None:
            workspace_service = getattr(last_runner, "workspace_service", None)

        if workspace_service is None:
            workspace_service = getattr(self, "workspace_service", None)

        if workspace_service is not None:
            workspace_service.cleanup()
            logger.debug("✓ Workspace cleaned")

    def run(
        self,
        data: Any = None,
        task_id: Optional[str] = None,
        data_dir: Optional[Path] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Run workflow - Unified entry point (recommended).

        This is a synchronous method, users don't need to handle async/await.

        Supports multiple calling modes:

        1. **Using TaskContext object** (simplest):
           >>> data = dslighting.load_data("/path/to/data")
           >>> result = factory.run(data)

        2. **Using task_id**:
           >>> result = factory.run(task_id="bike-sharing-demand")

        3. **Using task_id + data_dir**:
           >>> result = factory.run(
           ...     task_id="bike-sharing-demand",
           ...     data_dir="/path/to/data"
           ... )

        4. **Using dataset dict/dictionary** (from datasets.load_xxx()):
           >>> dataset = dslighting.datasets.load_bike_sharing_demand()
           >>> result = factory.run(dataset)

        Args:
            data: Optional, can be:
                - TaskContext object (from dslighting.load_data())
                - dataset dict/dictionary (from dslighting.datasets.load_xxx())
                - If provided, task_id and data_dir will be extracted from it
            task_id: Task ID (e.g. "bike-sharing-demand")
                - If not provided and data is also not provided, data_dir must be specified
            data_dir: Data directory path
            **kwargs: Parameters passed to create_agent()

        Returns:
            Execution result

        Example:
            >>> factory = MyWorkflowFactory(model="gpt-4o")
            >>> # Mode 1: Using TaskContext
            >>> data = dslighting.load_data("/path/to/data")
            >>> result = factory.run(data)
            >>> # Mode 2: Using task_id
            >>> result = factory.run(task_id="bike-sharing-demand")
            >>> # Mode 3: Using dataset dict
            >>> dataset = dslighting.datasets.load_bike_sharing_demand()
            >>> result = factory.run(dataset)
        """
        import asyncio
        return asyncio.run(self._run_async(data=data, task_id=task_id, data_dir=data_dir, **kwargs))

    async def _run_async(
        self,
        data: Any = None,
        task_id: Optional[str] = None,
        data_dir: Optional[Path] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Run workflow - Unified entry point (recommended).

        Supports multiple calling modes:

        1. **Using TaskContext object** (simplest):
           >>> data = dslighting.load_data("/path/to/data")
           >>> await factory.run(data)

        2. **Using task_id**:
           >>> await factory.run(task_id="bike-sharing-demand")

        3. **Using task_id + data_dir**:
           >>> await factory.run(
           ...     task_id="bike-sharing-demand",
           ...     data_dir="/path/to/data"
           ... )

        4. **Using dataset dict/dictionary** (from datasets.load_xxx()):
           >>> dataset = dslighting.datasets.load_bike_sharing_demand()
           >>> await factory.run(dataset)

        Args:
            data: Optional, can be:
                - TaskContext object (from dslighting.load_data())
                - dataset dict/dictionary (from dslighting.datasets.load_xxx())
                - If provided, task_id and data_dir will be extracted from it
            task_id: Task ID (e.g. "bike-sharing-demand")
                - If not provided and data is also not provided, data_dir must be specified
            data_dir: Data directory path
            **kwargs: Parameters passed to create_agent()

        Example:
            >>> factory = MyWorkflowFactory(model="gpt-4o")
            >>> # Mode 1: Using TaskContext
            >>> data = dslighting.load_data("/path/to/data")
            >>> await factory.run(data)
            >>> # Mode 2: Using task_id
            >>> await factory.run(task_id="bike-sharing-demand")
            >>> # Mode 3: Using dataset dict
            >>> dataset = dslighting.datasets.load_bike_sharing_demand()
            >>> await factory.run(dataset)
        """
        # Case 1: data parameter was provided
        if data is not None:
            # Check data type
            if isinstance(data, TaskContext):
                # TaskContext object
                logger.info(f"Detected TaskContext object")
                task_id = data.task_id
                data_dir = data.data_dir
            elif isinstance(data, dict) and 'data_dir' in data:
                # dataset dict/dictionary (from dslighting.datasets.load_xxx())
                logger.info(f"Detected dataset dict/dictionary")
                data_dir = Path(data['data_dir'])
                task_id = task_id or data.get('task_id')
            else:
                raise ValueError(
                    f"Unsupported data type: {type(data)}\n"
                    f"Expected: TaskContext object or dataset dict/dictionary"
                )

        # Case 2: only task_id was provided
        elif task_id is not None and data_dir is None:
            # Automatically find data_dir from registry
            logger.info(f"Only task_id provided, will look up data_dir from registry")
            # Call run_with_task_id, let its internal logic handle data_dir lookup
            return await self.run_with_task_id(task_id=task_id, **kwargs)

        # Case 3: must provide task_id and data_dir
        if task_id is None:
            raise ValueError("task_id parameter must be provided (or provide data object containing task_id)")
        if data_dir is None:
            raise ValueError("data_dir parameter must be provided (or provide data object containing data_dir)")

        # Call run_with_task_id
        return await self.run_with_task_id(
            task_id=task_id,
            data_dir=Path(data_dir) if not isinstance(data_dir, Path) else data_dir,
            **kwargs
        )

    async def run_with_task_id(
        self,
        task_id: str,
        data_dir: Optional[Path] = None,
        task_loader: Optional[Any] = None,
        output_path: Optional[Path] = None,
        **agent_kwargs: Any,
    ) -> Any:
        """
        Run workflow using task_id (similar to DSLighting's run_agent).

        This is the recommended usage - automatically resolve the task layout from registry/data.

        Args:
            task_id: Task ID (e.g. "bike-sharing-demand")
            data_dir: Optional data directory path. If not provided, will be looked up from registry
            task_loader: Deprecated legacy parameter. Shared runner path ignores it.
            output_path: Optional output file path. If not provided, uses the task resolver default
            **agent_kwargs: Parameters passed to create_agent() (e.g. max_iterations)

        Example:
            >>> factory = MyWorkflowFactory(model="gpt-4o")
            >>> await factory.run_with_task_id("bike-sharing-demand", max_iterations=3)
            >>> # Specify output filename
            >>> await factory.run_with_task_id("bike-sharing-demand", output_path="my_submission.csv")
        """
        if task_loader is not None:
            logger.warning("`task_loader` is ignored; shared runner path always uses TaskResolver.")

        config = self._build_config(task_id=task_id, run_kwargs=agent_kwargs)
        executor = TaskExecutor(config=config, workflow_name=self._get_workflow_name())
        return await executor.run_with_task_id(
            task_id=task_id,
            data_dir=data_dir,
            output=output_path,
            on_runner_created=lambda runner: setattr(self, "_last_runner", runner),
        )

    def _build_config(self, task_id: str, run_kwargs: dict[str, Any]) -> DSLightingConfig:
        config = self._base_config.model_copy(deep=True)
        config.run = RunConfig(
            name=f"{self._get_workflow_name()}_{task_id}",
            keep_all_workspaces=self.keep_workspace,
            keep_workspace_on_failure=self.keep_workspace,
        )
        config.workflow = WorkflowConfig(name=self._get_workflow_name(), params={})
        config.sandbox = SandboxConfig(timeout=self.timeout)

        merged = {**self._agent_init_kwargs, **run_kwargs}
        raw_data_analysis = merged.pop("data_analysis", None)
        if raw_data_analysis is not None:
            if not isinstance(raw_data_analysis, dict):
                raise ValueError("`data_analysis` must be a dict matching DataAnalysisConfig.")
            config.data_analysis = DataAnalysisConfig(**raw_data_analysis)

        visualization_policy = consume_visualization_policy(merged)
        if visualization_policy is not None:
            config.agent.visualization.policy = visualization_policy

        search_keys = {"num_drafts", "debug_prob", "max_iterations", "max_debug_depth"}
        for key in search_keys:
            if key in merged:
                setattr(config.agent.search, key, merged.pop(key))

        autokaggle_keys = {"max_attempts_per_phase", "success_threshold"}
        for key in autokaggle_keys:
            if key in merged:
                setattr(config.agent.autokaggle, key, merged.pop(key))

        if merged:
            config.run.parameters.update(merged)

        log_resolved_runtime_config(
            logger,
            config=config,
            source=self.__class__.__name__,
            task_id=task_id,
        )
        return config
