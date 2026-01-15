"""
DSLighting Agent - Simplified API for data science automation.

This module provides the main Agent class that wraps the complexity of
DSAT framework while providing full control when needed.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from dsat.config import DSATConfig
from dsat.models.task import TaskDefinition, TaskType
from dsat.runner import DSATRunner

from dslighting.core.config_builder import ConfigBuilder
from dslighting.core.data_loader import DataLoader, LoadedData

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """
    Result of running an Agent on a data science task.

    Attributes:
        success: Whether the task completed successfully
        output: Task output (predictions, answer, file path, etc.)
        score: Evaluation score (if available)
        cost: Total LLM cost in USD
        duration: Execution time in seconds
        artifacts_path: Path to generated artifacts
        workspace_path: Path to workspace directory
        error: Error message if failed
        metadata: Additional metadata
    """
    success: bool
    output: Any
    cost: float = 0.0
    duration: float = 0.0
    score: Optional[float] = None
    artifacts_path: Optional[Path] = None
    workspace_path: Optional[Path] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        if self.success:
            return (
                f"AgentResult(success={self.success}, "
                f"output={self.output}, "
                f"score={self.score}, "
                f"cost=${self.cost:.4f}, "
                f"duration={self.duration:.1f}s)"
            )
        else:
            return (
                f"AgentResult(success={self.success}, "
                f"error={self.error}, "
                f"cost=${self.cost:.4f})"
            )


class Agent:
    """
    Simplified interface to DSLighting's data science automation capabilities.

    The Agent class provides a scikit-learn-like API that handles the complexity
    of workflow selection, configuration, and execution while allowing advanced
    users to access underlying components when needed.

    Examples:
        Simple usage:
            >>> import dslighting
            >>> agent = dslighting.Agent()
            >>> result = agent.run("data/my-competition")

        Advanced usage:
            >>> agent = dslighting.Agent(
            ...     workflow="autokaggle",
            ...     model="gpt-4o",
            ...     temperature=0.5,
            ...     max_iterations=10
            ... )
            >>> result = agent.run(data_path)

        Access underlying components:
            >>> config = agent.get_config()
            >>> runner = agent.get_runner()
    """

    def __init__(
        self,
        workflow: str = None,
        model: str = None,
        api_key: str = None,
        api_base: str = None,
        provider: str = None,
        temperature: float = None,
        max_iterations: int = None,
        num_drafts: int = None,
        workspace_dir: str = None,
        run_name: str = None,
        verbose: bool = True,
        **kwargs
    ):
        """
        Initialize DSLighting Agent.

        Args:
            workflow: Workflow name (aide, autokaggle, automind, etc.)
                      Defaults to "aide" or auto-detected from data
            model: LLM model name (e.g., "gpt-4o-mini", "deepseek-chat")
                   Defaults to LLM_MODEL env var or "gpt-4o-mini"
            api_key: API key for LLM service
                     Defaults to API_KEY env var
            api_base: API base URL
                      Defaults to API_BASE env var or OpenAI
            provider: LLM provider for LiteLLM (e.g., "siliconflow")
            temperature: LLM temperature (0.0-1.0)
            max_iterations: Maximum agent search iterations
            num_drafts: Number of drafts to generate
            workspace_dir: Custom workspace directory
            run_name: Name for this run
            verbose: Enable verbose logging
            **kwargs: Additional parameters passed to DSATConfig
        """
        self.verbose = verbose
        self.logger = logger

        # Build configuration
        self.config_builder = ConfigBuilder()
        self.config = self.config_builder.build_config(
            workflow=workflow,
            model=model,
            api_key=api_key,
            api_base=api_base,
            provider=provider,
            temperature=temperature,
            max_iterations=max_iterations,
            num_drafts=num_drafts,
            workspace_dir=workspace_dir,
            run_name=run_name,
            **kwargs
        )

        # Create runner (will be created on first use)
        self._runner: Optional[DSATRunner] = None

        # Track results
        self._results: List[AgentResult] = []

        self.logger.info(f"Agent initialized with workflow: '{self.config.workflow.name}'")

    def run(
        self,
        data: Union[str, Path, dict, pd.DataFrame, LoadedData],
        task_id: str = None,
        output_path: str = None,
        description: str = None,
        **kwargs
    ) -> AgentResult:
        """
        Run the agent on a data science task.

        This is the main entry point for executing data science tasks.
        It handles data loading, task creation, workflow execution, and
        result collection.

        Args:
            data: Data source (path, DataFrame, dict, or LoadedData)
            task_id: Optional task identifier
            output_path: Custom output path for results
            description: Optional task description (overrides detected)
            **kwargs: Additional task parameters

        Returns:
            AgentResult with output, metrics, and metadata

        Examples:
            >>> result = agent.run("data/titanic")
            >>> print(f"Score: {result.score}, Cost: ${result.cost}")

            >>> result = agent.run(df, description="Predict price")
            >>> predictions = result.output
        """
        # Start timing
        start_time = time.time()

        try:
            # Load data if not already loaded
            if not isinstance(data, LoadedData):
                loader = DataLoader()
                loaded_data = loader.load(data)
            else:
                loaded_data = data

            # Get task information
            task_detection = loaded_data.task_detection

            # Determine workflow
            workflow = self._determine_workflow(task_detection)
            self.logger.info(f"Using workflow: {workflow}")

            # Create task definition
            task = self._create_task_definition(
                loaded_data=loaded_data,
                task_id=task_id,
                description=description,
                output_path=output_path,
                **kwargs
            )

            # Execute task (async wrapper)
            result = asyncio.run(self._execute_task(task, loaded_data))

            # Calculate duration
            duration = time.time() - start_time
            result.duration = duration

            # Store result
            self._results.append(result)

            if self.verbose:
                self._log_result(result)

            return result

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}", exc_info=True)

            duration = time.time() - start_time

            return AgentResult(
                success=False,
                output=None,
                duration=duration,
                error=str(e),
                metadata={"exception_type": type(e).__name__}
            )

    def run_batch(
        self,
        data_list: List[Union[str, Path, dict, pd.DataFrame]],
        **kwargs
    ) -> List[AgentResult]:
        """
        Run the agent on multiple data sources sequentially.

        Args:
            data_list: List of data sources
            **kwargs: Additional parameters passed to run()

        Returns:
            List of AgentResult objects

        Examples:
            >>> results = agent.run_batch([
            ...     "data/titanic",
            ...     "data/house-prices",
            ...     "data/fraud-detection"
            ... ])
            >>> for r in results:
            ...     print(f"{r.task_id}: {r.score}")
        """
        results = []

        for i, data in enumerate(data_list):
            self.logger.info(f"Running batch task {i+1}/{len(data_list)}")

            result = self.run(data, **kwargs)
            results.append(result)

        return results

    def get_config(self) -> DSATConfig:
        """
        Get the underlying DSAT configuration.

        This allows advanced users to modify configuration directly.

        Returns:
            DSATConfig object

        Examples:
            >>> config = agent.get_config()
            >>> config.llm.temperature = 0.5
        """
        return self.config

    def get_runner(self) -> DSATRunner:
        """
        Get the underlying DSATRunner instance.

        This allows advanced users to interact with the runner directly.

        Returns:
            DSATRunner instance

        Examples:
            >>> runner = agent.get_runner()
            >>> eval_fn = runner.get_eval_function()
        """
        if self._runner is None:
            self._runner = DSATRunner(self.config)

        return self._runner

    def get_results(self) -> List[AgentResult]:
        """Get all results from this agent session."""
        return self._results.copy()

    def _determine_workflow(self, task_detection) -> str:
        """Determine which workflow to use."""
        # If user specified workflow, use it
        if self.config.workflow and self.config.workflow.name:
            return self.config.workflow.name

        # Otherwise, use recommended workflow from detection
        if task_detection and task_detection.recommended_workflow:
            return task_detection.recommended_workflow

        # Fallback to default
        return "aide"

    def _create_task_definition(
        self,
        loaded_data: LoadedData,
        task_id: str = None,
        description: str = None,
        output_path: str = None,
        **kwargs
    ) -> TaskDefinition:
        """Create TaskDefinition from LoadedData."""
        # Generate task ID if not provided
        if task_id is None:
            safe_name = str(uuid.uuid4())[:8]
            task_id = f"task_{safe_name}"

        # Get task type
        task_type = loaded_data.get_task_type()

        # Get description
        if description is None:
            description = loaded_data.get_description()

        # Get I/O instructions
        io_instructions = loaded_data.get_io_instructions()

        # Build payload
        payload = kwargs.copy()
        payload["description"] = description
        payload["io_instructions"] = io_instructions

        # Add data directory if available
        if loaded_data.data_dir:
            payload["data_dir"] = str(loaded_data.data_dir)

        # Add output path if specified
        if output_path:
            payload["output_submission_path"] = str(output_path)

        # Create TaskDefinition
        task = TaskDefinition(
            task_id=task_id,
            task_type=TaskType(task_type),
            payload=payload
        )

        return task

    async def _execute_task(
        self,
        task: TaskDefinition,
        loaded_data: LoadedData
    ) -> AgentResult:
        """Execute a single task using DSATRunner."""
        runner = self.get_runner()

        # Link data directory to workspace if available
        if loaded_data.data_dir and hasattr(runner, 'benchmark') and runner.benchmark:
            workspace_service = None
            # Try to get workspace service from workflow
            if hasattr(runner, 'factory'):
                try:
                    workflow = runner.factory.create_workflow(self.config, benchmark=runner.benchmark)
                    workspace_service = workflow.services.get("workspace")
                    if workspace_service:
                        workspace_service.link_data_to_workspace(loaded_data.data_dir)
                except Exception:
                    pass

        # Get evaluation function
        eval_fn = runner.get_eval_function()

        # Execute task
        output, cost, usage_summary = await eval_fn(task)

        # Check for errors
        if isinstance(output, str) and output.startswith("[ERROR]"):
            return AgentResult(
                success=False,
                output=output,
                cost=cost,
                error=output
            )

        # Extract score if available
        score = None
        if isinstance(output, (int, float)):
            score = float(output)
        elif isinstance(output, dict) and "score" in output:
            score = output["score"]

        # Get workspace path
        workspace_path = None
        if hasattr(runner, 'run_records') and runner.run_records:
            last_record = runner.run_records[-1]
            workspace_path = last_record.get("workspace_dir")

        return AgentResult(
            success=True,
            output=output,
            cost=cost,
            score=score,
            workspace_path=Path(workspace_path) if workspace_path else None,
            metadata={"usage": usage_summary}
        )

    def _log_result(self, result: AgentResult):
        """Log result summary."""
        if result.success:
            self.logger.info(
                f"✓ Task completed successfully | "
                f"Score: {result.score or 'N/A'} | "
                f"Cost: ${result.cost:.4f} | "
                f"Duration: {result.duration:.1f}s"
            )
        else:
            self.logger.error(
                f"✗ Task failed | "
                f"Error: {result.error} | "
                f"Cost: ${result.cost:.4f}"
            )

    def __repr__(self) -> str:
        return (
            f"Agent(workflow='{self.config.workflow.name}', "
            f"model='{self.config.llm.model}', "
            f"results={len(self._results)})"
        )
