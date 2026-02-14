"""
Base Workflow Factory - Base class for all Workflow Factory

Provides standard MLE task loading functionality, users don't need to reimplement
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from dslighting.core.data import TaskContext

logger = logging.getLogger(__name__)


class BaseWorkflowFactory(ABC):
    """
    Base class for Workflow Factory

    Provides:
    1. Standard LLM/Sandbox/Workspace service creation
    2. Standard MLE task loading (from registry)
    3. run_with_task_id() convenience method

    Users only need to:
    1. Inherit from BaseWorkflowFactory
    2. Implement create_agent() method
    3. Define their own workflow class
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str = None,
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
            **agent_init_kwargs: Additional parameters, will be passed to create_agent()

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
            api_base=api_base,
            provider=provider,
            temperature=temperature,
        )

        # Extract LLM config from configuration
        llm_config = config.llm

        # Create services (infrastructure ready, users don't need to care)
        from dslighting.services import LLMService, SandboxService, WorkspaceService

        self.llm_service = LLMService(config=llm_config)
        self.workspace_service = WorkspaceService(
            run_name=f"{self._get_workflow_name()}_{model.replace('/', '_')}"
        )
        self.sandbox_service = SandboxService(
            workspace=self.workspace_service,
            timeout=timeout
        )

        logger.debug(f"{self.__class__.__name__} initialized")
        logger.debug(f"  - Model: {model}")
        logger.debug(f"  - Timeout: {timeout}s")
        logger.debug(f"  - Keep workspace: {keep_workspace}")

    def _get_workflow_name(self) -> str:
        """
        Get workflow name (used for logging and workspace naming).

        Subclasses can override this method to provide custom names.
        """
        return self.__class__.__name__.replace("Factory", "").lower()

    @abstractmethod
    def create_agent(self, **kwargs: Any) -> Any:
        """
        Create Agent instance (must be implemented by subclasses).

        Args:
            **kwargs: Agent configuration parameters

        Returns:
            Agent instance
        """
        raise NotImplementedError("Subclasses must implement create_agent()")

    def cleanup(self):
        """Cleanup workspace"""
        if not self.keep_workspace:
            self.workspace_service.cleanup()
            logger.debug(f"✓ Workspace cleaned")

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

        This is the recommended usage - automatically load standard MLE format config from registry.

        Args:
            task_id: Task ID (e.g. "bike-sharing-demand")
            data_dir: Optional data directory path. If not provided, will be looked up from registry
            task_loader: Optional TaskLoader. If not provided, uses MLETaskLoader
            output_path: Optional output file path. If not provided, uses default from task_loader
            **agent_kwargs: Parameters passed to create_agent() (e.g. max_iterations)

        Example:
            >>> factory = MyWorkflowFactory(model="gpt-4o")
            >>> await factory.run_with_task_id("bike-sharing-demand", max_iterations=3)
            >>> # Specify output filename
            >>> await factory.run_with_task_id("bike-sharing-demand", output_path="my_submission.csv")
        """
        logger.info(f"=" * 80)
        logger.info(f"Running {self.__class__.__name__} with task_id")
        logger.info(f"=" * 80)
        logger.info(f"  Task ID: {task_id}")
        logger.info(f"  Agent Config: {agent_kwargs}")
        logger.info(f"=" * 80)

        # Use TaskLoader to load task
        if task_loader is None:
            from dslighting.core.tasks import MLETaskLoader
            task_loader = MLETaskLoader()

        # For MLE format, only analyze public data (avoid leaking private/test_answer.csv)
        public_dir = data_dir / "prepared" / "public"

        if not public_dir.exists():
            logger.error(f"Public data directory not found: {public_dir}")
            logger.error(f"Expected structure: {data_dir}/prepared/public/train.csv")
            raise FileNotFoundError(
                f"Public data directory not found: {public_dir}\n"
                f"Expected structure: {data_dir}/prepared/public/train.csv"
            )

        logger.info(f"Using public data directory (avoid leaking answer): {public_dir}")

        # Load standard MLE format task config (pass public_dir, not data_dir)
        description, io_instructions, _, default_output_path = task_loader.load_task(
            task_id=task_id,
            data_dir=public_dir  # Only analyze public directory
        )

        # If user provided output_path, use theirs; otherwise use default
        output_path = output_path or default_output_path

        # Verify load result
        logger.info(f"Task load completed:")
        logger.info(f"  - Description length: {len(description)} characters")
        logger.info(f"  - I/O Instructions length: {len(io_instructions)} characters")
        logger.info(f"  - Public directory: {public_dir}")
        logger.info(f"  - Output path: {output_path}")

        # Automatically process data links (base infrastructure layer)
        # Link contents of public_dir to sandbox root
        logger.info(f"Automatically linking public data to sandbox...")
        logger.info(f"  Source directory: {public_dir}")
        self.workspace_service.link_data_to_workspace(public_dir)
        logger.info(f"  Sandbox is ready")

        # Check if io_instructions is complete (should contain "CRITICAL I/O REQUIREMENTS")
        if len(io_instructions) < 100 or "CRITICAL I/O" not in io_instructions:
            logger.warning(f"I/O Instructions may be incomplete! Length: {len(io_instructions)}")
            logger.warning(f"  First 200 characters: {io_instructions[:200]}")
            logger.warning(f"  This may cause the model to not correctly understand file path requirements!")
            logger.warning(f"  Attempting to regenerate complete I/O instructions...")

            # Attempt to regenerate complete I/O instructions
            try:
                from dslighting.services.data_analyzer import DataAnalyzer
                analyzer = DataAnalyzer()
                io_instructions = analyzer.generate_io_instructions(
                    output_path.name,
                    optimization_context=False
                )
                logger.info(f"Successfully regenerated I/O instructions! Length: {len(io_instructions)}")
            except Exception as e:
                logger.error(f"Regeneration failed: {e}")
                # Final fallback: use hardcoded format
                io_instructions = f"""
--- CRITICAL I/O REQUIREMENTS ---

You MUST follow these file system rules precisely. Failure to do so will cause a fatal error.

1. **INPUT DATA:**
   - All input files are located in the **current working directory** (./).
   - Example: Use `pd.read_csv('train.csv')`.

2. **OUTPUT FILE:**
   - You MUST save your final submission file to the **current working directory** (./).
   - The required output filename is: `{output_path.name}`
   - **Correct Example:** `submission_df.to_csv('{output_path.name}', index=False)`

**IMPORTANT:** These path requirements are non-negotiable and must be followed exactly.
"""

        # Create agent (merge parameters saved during __init__ with runtime parameters)
        all_agent_kwargs = {**self._agent_init_kwargs, **agent_kwargs}
        agent = self.create_agent(**all_agent_kwargs)

        # Record start time (used for calculating duration)
        import time
        start_time = time.time()

        # Run workflow (pass public_dir to workflow)
        await agent.solve(
            description=description,
            io_instructions=io_instructions,  # Contains output file name requirements
            data_dir=public_dir  # Only pass public directory to workflow
        )

        # Calculate execution time
        duration = time.time() - start_time

        # Auto-grading (base infrastructure, users don't need to care)
        logger.info(f"\n{'='*80}")
        logger.info(f"Auto-grading in progress...")
        logger.info(f"{'='*80}")

        score = None
        try:
            # Get submission file path
            submission_file = self.workspace_service.get_path("sandbox_workdir") / output_path.name

            if submission_file.exists():
                logger.info(f"Submission file: {submission_file}")

                # Universal grading logic: try multiple ways to load benchmark
                benchmark = None
                benchmark_loaded = False

                # Method 1: Check if task_loader has load_benchmark method
                if hasattr(task_loader, 'load_benchmark'):
                    try:
                        logger.info(f"Attempting to use task_loader.load_benchmark()...")
                        benchmark = task_loader.load_benchmark(
                            task_id=task_id,
                            data_dir=data_dir
                        )
                        if benchmark:
                            benchmark_loaded = True
                            logger.info(f"Benchmark loaded via task_loader")
                    except Exception as e:
                        logger.warning(f"task_loader.load_benchmark() failed: {e}")

                # Fallback 2: Try loading directly from bundled registry
                if not benchmark_loaded:
                    try:
                        logger.info("Attempting to load directly from bundled registry...")
                        from pathlib import Path as LibPath
                        if task_id.startswith("dabench-"):
                            from dslighting.benchmark.vendor.dabench.registry import Registry as DirectRegistry
                        else:
                            from dslighting.benchmark.vendor.mlebench.registry import Registry as DirectRegistry

                        data_root = LibPath(data_dir)
                        if data_root.name in ("public", "public_val") and data_root.parent.name in (
                            "prepared",
                            "prepared_val",
                        ):
                            data_root = data_root.parent.parent.parent
                        elif data_root.name == task_id and (data_root / "prepared").exists():
                            data_root = data_root.parent

                        registry = DirectRegistry().set_data_dir(data_root)
                        competition = registry.get_competition(task_id)

                        if competition:
                            # Create simple benchmark wrapper
                            class DirectBenchmark:
                                def __init__(self, comp):
                                    self.competition = comp

                                async def grade(self, submission_path: str):
                                    from dslighting.benchmark.vendor.mlebench.grade import grade_csv
                                    report = grade_csv(LibPath(submission_path), self.competition)
                                    return {
                                        'score': report.score,
                                        'valid_submission': report.valid_submission
                                    }

                            benchmark = DirectBenchmark(competition)
                            benchmark_loaded = True
                            logger.debug("Loaded benchmark directly from bundled registry")
                    except Exception as e:
                        logger.warning(f"Failed to load bundled registry directly: {e}")

                # Fallback 3: Use universal grading (check file format)
                if not benchmark_loaded:
                    logger.info(f"Using universal grading logic...")
                    try:
                        import pandas as pd
                        # Check if file can be read normally
                        df = pd.read_csv(submission_file)
                        logger.info(f"Valid submission file: {len(df)} rows")

                        # Universal grading: file exists and is readable = success
                        # (Cannot calculate real score without ground truth)
                        score = 0.0
                        logger.info(f"Universal grading: file valid but cannot calculate real score (requires ground truth)")
                        logger.info(f"Tip: Implement task_loader.load_benchmark() method to get real score")
                    except Exception as e:
                        logger.warning(f"Universal grading failed: {e}")

                # If benchmark was successfully loaded, use it for grading
                if benchmark_loaded and benchmark and hasattr(benchmark, 'grade'):
                    try:
                        # Call benchmark.grade() for grading
                        grade_result = await benchmark.grade(
                            submission_path=str(submission_file)
                        )

                        # Extract score (grade_result may be dict or object)
                        if isinstance(grade_result, dict):
                            score = grade_result.get('score', grade_result.get('metric', 0.0))
                        else:
                            score = float(grade_result) if grade_result is not None else 0.0

                        logger.info(f"Auto-grading completed | Score: {score}")
                    except Exception as e:
                        logger.warning(f"Benchmark grading failed: {e}")
                        logger.warning(f"   Will fall back to universal grading")
                        score = 0.0
            else:
                logger.warning(f"Submission file not found: {submission_file}")
                logger.warning(f"   Workflow execution failed, cannot grade")

        except Exception as e:
            logger.warning(f"Auto-grading failed: {e}")
            logger.warning(f"   Please check submission file format and benchmark configuration")

        logger.info(f"{'='*80}\n")

        # Build result object
        from types import SimpleNamespace
        result = SimpleNamespace()

        # Determine success: submission file exists and grading completed
        result.score = score if score is not None else 0.0
        result.success = score is not None
        result.error = None if score is not None else "Grading failed or submission not found"

        # Get cost (from LLM service)
        result.cost = self.llm_service.get_total_cost() if hasattr(self.llm_service, 'get_total_cost') else 0.0
        result.duration = duration

        logger.info(f"=" * 80)
        logger.info(f"Workflow completed")
        logger.info(f"  - Success: {result.success}")
        logger.info(f"  - Score: {result.score}")
        logger.info(f"  - Cost: ${result.cost:.4f}")
        logger.info(f"  - Duration: {result.duration:.2f}s")
        logger.info(f"=" * 80)

        # Return result object
        return result
