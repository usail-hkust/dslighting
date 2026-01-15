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
        keep_workspace: bool = False,
        keep_workspace_on_failure: bool = True,
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
            keep_workspace: Keep workspace after completion (default: False)
            keep_workspace_on_failure: Keep workspace on failure (default: True)
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
            keep_workspace=keep_workspace,
            keep_workspace_on_failure=keep_workspace_on_failure,
            **kwargs
        )

        # Create runner (will be created on first use)
        self._runner: Optional[DSATRunner] = None

        # Track results
        self._results: List[AgentResult] = []

        self.logger.info(f"Agent initialized with workflow: '{self.config.workflow.name}'")

    def run(
        self,
        data: Union[str, Path, dict, pd.DataFrame, LoadedData] = None,
        task_id: str = None,
        data_dir: str = None,
        output_path: str = None,
        description: str = None,
        registry_dir: str = None,
        **kwargs
    ) -> AgentResult:
        """
        Run the agent on a data science task.

        This is the main entry point for executing data science tasks.
        It handles data loading, task creation, workflow execution, and
        result collection.

        Args:
            data: Optional data source (path, DataFrame, dict, or LoadedData).
                  If not provided, use task_id + data_dir pattern.
            task_id: Task/Competition identifier (e.g., "bike-sharing-demand").
                     Required when using MLE benchmark format.
            data_dir: Base data directory containing competition data.
                     Default: "data/competitions"
            output_path: Custom output path for results
            description: Optional task description (overrides detected)
            registry_dir: Path to competition registry directory for grading.
                          Example: "/path/to/mlebench/competitions"
            **kwargs: Additional task parameters

        Returns:
            AgentResult with output, metrics, and metadata

        Examples:
            >>> # Method 1: Recommended - using task_id + data_dir
            >>> result = agent.run(
            ...     task_id="bike-sharing-demand",
            ...     data_dir="data/competitions"
            ... )

            >>> # Method 2: With custom registry for grading
            >>> result = agent.run(
            ...     data="data/competitions/bike-sharing-demand",
            ...     registry_dir="/path/to/mlebench/competitions"
            ... )

            >>> # Method 3: Using DataFrame
            >>> result = agent.run(df, description="Predict price")
        """
        # Start timing
        start_time = time.time()

        try:
            # ========== New simplified API: task_id + data_dir ==========
            if task_id:
                # Set default data_dir if not provided
                if data_dir is None:
                    data_dir = "data/competitions"

                self.logger.info(f"Using MLE benchmark format")
                self.logger.info(f"  task_id: {task_id}")
                self.logger.info(f"  data_dir: {data_dir}")

                # Resolve paths
                data_dir_path = Path(data_dir).resolve()
                competition_dir = data_dir_path / task_id

                # Check if task exists in benchmarks registry
                benchmark_dir = self._get_default_benchmark_dir()
                task_registry = benchmark_dir / task_id

                if not task_registry.exists():
                    self.logger.warning(
                        f"Task '{task_id}' not found in benchmark registry: {benchmark_dir}"
                    )
                    self.logger.warning(
                        f"This means the task cannot be auto-graded. "
                        f"To enable grading, register the task at: {task_registry}"
                    )
                else:
                    self.logger.info(f"  ✓ Task registered: {task_registry}")

                # Check if data exists
                if not competition_dir.exists():
                    raise FileNotFoundError(
                        f"Data directory not found: {competition_dir}\n"
                        f"Please ensure data is prepared at: {competition_dir}/prepared/"
                    )

                self.logger.info(f"  Data directory: {competition_dir}")

                # Load data
                loader = DataLoader()
                loaded_data = loader.load(competition_dir)

            # ========== Recommended API: LoadedData with task_id ==========
            elif data is not None:
                # Load data if not already loaded
                if not isinstance(data, LoadedData):
                    loader = DataLoader()
                    loaded_data = loader.load(data)
                else:
                    loaded_data = data

                # Extract task_id from loaded_data if available
                if loaded_data.task_id:
                    # Use task_id from loaded_data for benchmark initialization
                    extracted_task_id = loaded_data.task_id
                    self.logger.info(f"Detected task_id from data: {extracted_task_id}")

                    # Override task_id parameter for benchmark initialization
                    task_id = extracted_task_id
            else:
                raise ValueError(
                    "Either 'task_id' or 'data' must be provided. "
                    "Example: agent.run(task_id='bike-sharing-demand', data_dir='data/competitions')"
                )

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

            # Initialize benchmark for MLE tasks (for grading)
            if task_id and loaded_data.get_task_type() == "kaggle":
                try:
                    from mlebench.grade import grade_csv
                    from mlebench.registry import Registry

                    # Resolve data_dir - use the same path as the competition data
                    if data_dir is None:
                        data_dir = "data/competitions"
                    data_dir_path = Path(data_dir).expanduser().resolve()

                    self.logger.info(f"Initializing MLE-Bench grading for: {task_id}")
                    self.logger.info(f"  Data directory: {data_dir_path}")

                    # Create custom registry with correct data_dir
                    custom_registry = Registry(data_dir=data_dir_path)

                    # Create simple wrapper class
                    class SimpleMLEBenchmark:
                        def __init__(self, registry_instance):
                            self.registry = registry_instance

                        async def grade(self, submission_path):
                            """Grade submission using custom registry."""
                            competition = self.registry.get_competition(task_id)
                            report = grade_csv(
                                submission_path,
                                competition,
                            )
                            # Return the score (float), not the entire report
                            return report.score if report.score is not None else 0.0

                    benchmark = SimpleMLEBenchmark(custom_registry)
                    runner = self.get_runner()
                    runner.benchmark = benchmark
                    self.logger.info(f"✓ Benchmark initialized for grading: {task_id}")

                except ImportError as e:
                    self.logger.warning(f"MLE-Bench import failed: {e}")
                    self.logger.warning("Grading will be skipped.")
                except Exception as e:
                    self.logger.warning(f"Benchmark initialization failed: {e}")
                    self.logger.warning("Grading will be skipped")

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

        # Add data directory based on task type
        if loaded_data.data_dir:
            data_dir = loaded_data.data_dir

            if task_type == "kaggle":
                # MLE/Kaggle format: needs public_data_dir and output_submission_path
                # Follow MLEBenchmark pattern: {data_dir}/prepared/public
                prepared_dir = data_dir / "prepared"
                public_dir = prepared_dir / "public"

                # Check if prepared/public exists (MLE format)
                if public_dir.exists():
                    payload["public_data_dir"] = str(public_dir.resolve())
                    self.logger.info(f"Using MLE prepared data: {public_dir.resolve()}")
                else:
                    # Fallback: use data_dir directly
                    payload["public_data_dir"] = str(data_dir.resolve())
                    self.logger.warning(
                        f"Prepared data not found at {public_dir}, using data_dir instead"
                    )

                # Set output path - use simple filename, will be saved in workspace/sandbox
                if output_path is None:
                    # Extract competition_id from data_dir path if possible
                    competition_id = data_dir.name
                    unique_id = str(uuid.uuid4())[:8]
                    output_filename = f"submission_{competition_id}_{unique_id}.csv"

                    # Use just the filename - DSAT will save it in workspace/sandbox
                    output_path = Path(output_filename)

                payload["output_submission_path"] = str(output_path)
                self.logger.info(f"Output submission file: {output_path}")
            else:
                # Other task types: use data_dir
                payload["data_dir"] = str(data_dir)

        # Add output path if specified (for non-kaggle tasks)
        if output_path and task_type != "kaggle":
            payload["output_submission_path"] = str(output_path)

        # Create TaskDefinition
        task = TaskDefinition(
            task_id=task_id,
            task_type=task_type,  # Pass string directly, Pydantic will validate
            payload=payload
        )

        return task

    def _get_workspace_dir(self) -> Path:
        """Get the workspace directory for this agent run."""
        # Try to get from config
        workspace_dir = None

        if hasattr(self, 'config') and hasattr(self.config, 'run'):
            run_config = self.config.run
            if hasattr(run_config, 'parameters') and run_config.parameters:
                workspace_dir = run_config.parameters.get('workspace_dir')

        # Fallback to default workspace directory
        if workspace_dir is None:
            from dslighting.utils.defaults import DEFAULT_WORKSPACE_DIR
            workspace_dir = DEFAULT_WORKSPACE_DIR

        # Ensure workspace exists
        workspace_path = Path(workspace_dir)
        workspace_path.mkdir(parents=True, exist_ok=True)

        return workspace_path

    def _get_default_benchmark_dir(self) -> Path:
        """
        Get the default benchmark registry directory.

        This is where task registration files (grade.py, description.md, etc.) are stored.
        Default: benchmarks/mlebench/competitions/

        Returns:
            Path to benchmark registry directory
        """
        # Try to get from config
        benchmark_dir = None

        if hasattr(self, 'config') and hasattr(self.config, 'run'):
            run_config = self.config.run
            if hasattr(run_config, 'parameters') and run_config.parameters:
                benchmark_dir = run_config.parameters.get('benchmark_dir')

        # Fallback to default benchmark directory
        if benchmark_dir is None:
            # Use relative path from current working directory
            # Default: benchmarks/mlebench/competitions/
            benchmark_dir = "benchmarks/mlebench/competitions"

        benchmark_path = Path(benchmark_dir).resolve()

        self.logger.debug(f"Benchmark registry directory: {benchmark_path}")

        return benchmark_path

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
