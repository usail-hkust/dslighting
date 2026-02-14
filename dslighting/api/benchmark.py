"""
DSBenchmark - Unified DSLighting Benchmark Interface.

This module provides a simple, unified API for running DSLighting benchmarks
with minimal configuration while maintaining full control for advanced users.
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from dslighting.api.config import AgentSettingsConfig, RuntimeConfig
from dslighting.api.task_loader import TaskLoader
from dslighting.api.utils import print_benchmark_banner, print_benchmark_info
from dslighting.benchmark import DABenchmark, MLEBenchmark
from dslighting.core import ConfigBuilder
from dslighting.runner import DSLightingRunner

if TYPE_CHECKING:
    from dslighting.benchmark import RuntimeSchedulerOptions

logger = logging.getLogger(__name__)


class DSBenchmark:
    """
    Unified DSLighting Benchmark interface.

    Simplifies running DSLighting benchmarks with intelligent defaults and
    a clean API while maintaining backward compatibility.

    **Predefined modes:**
        - "dabench": All DABench tasks
        - "mlebench": All MLE-Bench tasks
        - "mle-lite": 22 low-complexity MLE-Bench tasks

    **Custom mode:**
        Provide explicit competitions list with data_dir and vendor_comp_dir.

    Examples:
        >>> # Predefined mode (simplest)
        >>> DSBenchmark("dabench").run()
        >>>
        >>> # With parameters
        >>> DSBenchmark("dabench").run(
        ...     model="gpt-4",
        ...     max_iterations=5,
        ...     enable_monitoring=True
        ... )
        >>>
        >>> # Custom mode
        >>> DSBenchmark(
        ...     name="custom",
        ...     data_dir="./my_data",
        ...     vendor_comp_dir="./my_vendor",
        ...     competitions=["task1", "task2"]
        ... ).run()
    """

    # Default path configurations (paths are resolved at runtime)
    DEFAULT_PATHS = {
        "dabench": {
            "data_dir": None,  # Must be provided by user or env var DSLIGHTING_DABENCH_DATA
            "vendor_dir": None,  # Will use package default path
        },
        "mlebench": {
            "data_dir": None,  # Must be provided by user or env var DSLIGHTING_MLEBENCH_DATA
            "vendor_dir": None,  # Will use package default path
        },
    }

    def __init__(
        self,
        benchmark_type: str,
        exp_name: Optional[str] = None,
        data_dir: Optional[str] = None,
        vendor_comp_dir: Optional[str] = None,
        competitions: Optional[List[str]] = None,
    ):
        """
        Initialize DSBenchmark.

        Args:
            benchmark_type: Predefined benchmark type ("dabench", "mlebench", "mle-lite")
                            or custom benchmark identifier
            exp_name: Optional experiment name for tracking/logging.
                      If not provided, uses benchmark_type.
                      Example: benchmark_type="dabench", exp_name="dabench_fine_opt"
            data_dir: Data directory path
            vendor_comp_dir: Vendor competition directory
            competitions: Optional explicit task list (enables custom mode)

        Raises:
            ValueError: If parameters are invalid or incompatible

        Examples:
            >>> # Use predefined dabench with default experiment name
            >>> DSBenchmark("dabench")

            >>> # Use predefined dabench with custom experiment name
            >>> DSBenchmark("dabench", exp_name="dabench_fine_opt")

            >>> # Custom mode with explicit tasks
            >>> DSBenchmark(
            ...     benchmark_type="custom",
            ...     exp_name="my_experiment",
            ...     data_dir="./data",
            ...     vendor_comp_dir="./vendor",
            ...     competitions=["task1", "task2"]
            ... )
        """
        # Store benchmark type and experiment name separately
        self._benchmark_type = benchmark_type
        self.name = exp_name or benchmark_type  # Used for logging/output paths

        # Mode detection and configuration
        if competitions is not None:
            # Custom mode with explicit competitions
            if data_dir is None:
                raise ValueError("Custom mode requires data_dir parameter")
            if vendor_comp_dir is None:
                raise ValueError("Custom mode requires vendor_comp_dir parameter")

            self._mode = "custom"
            self._competitions = competitions
            self._data_dir = data_dir
            self._vendor_comp_dir = vendor_comp_dir

        elif benchmark_type in TaskLoader.DABENCH_SUBSETS:
            # DABench subsets (da_summary_statistics, da_correlation_analysis, etc.)
            self._mode = "predefined"
            inferred_type = "dabench"

            # Resolve vendor_dir: use package default path if None
            if vendor_comp_dir is None:
                package_dir = Path(dslighting.__file__).parent
                self._vendor_comp_dir = str(package_dir / "benchmark" / "vendor" / inferred_type / "competitions")
            else:
                self._vendor_comp_dir = vendor_comp_dir

            # Resolve data_dir: Read from environment variable first, otherwise use user-provided value
            if data_dir is None:
                env_key = f"DSLIGHTING_{inferred_type.upper()}_DATA"
                self._data_dir = os.getenv(env_key)
            else:
                self._data_dir = data_dir

            if self._data_dir is None:
                raise ValueError(
                    f"Cannot determine data path for {inferred_type}. "
                    f"Please either:\n"
                    f"  1. Set {env_key} environment variable, or\n"
                    f"  2. Provide data_dir parameter when initializing DSBenchmark"
                )

            # Get predefined tasks from TaskLoader
            self._competitions = TaskLoader.get_dabench_subset_tasks(benchmark_type)
            if self._competitions is None:
                raise ValueError(f"DABench subset '{benchmark_type}' not found")

        elif benchmark_type in ["dabench", "mlebench"]:
            # Full benchmark modes
            self._mode = "predefined"
            inferred_type = self._infer_benchmark_type(benchmark_type)

            # Resolve vendor_dir: use package default path if None
            if vendor_comp_dir is None:
                import dslighting
                package_dir = Path(dslighting.__file__).parent
                self._vendor_comp_dir = str(package_dir / "benchmark" / "vendor" / inferred_type / "competitions")
            else:
                self._vendor_comp_dir = vendor_comp_dir

            # Resolve data_dir: Read from environment variable first, otherwise use user-provided value
            if data_dir is None:
                env_key = f"DSLIGHTING_{inferred_type.upper()}_DATA"
                self._data_dir = os.getenv(env_key)
            else:
                self._data_dir = data_dir

            if self._data_dir is None:
                raise ValueError(
                    f"Cannot determine data path for {inferred_type}. "
                    f"Please either:\n"
                    f"  1. Set {env_key} environment variable, or\n"
                    f"  2. Provide data_dir parameter when initializing DSBenchmark"
                )

            # Auto-discover all tasks
            prefix = "dabench-" if inferred_type == "dabench" else None
            self._competitions = TaskLoader.auto_discover_all_tasks(
                data_dir=self._data_dir,
                vendor_comp_dir=self._vendor_comp_dir,
                prefix=prefix,
            )

        elif benchmark_type == "mle-lite":
            # MLE-Lite predefined subset
            self._mode = "predefined"
            inferred_type = "mlebench"

            # Resolve vendor_dir: use package default path if None
            if vendor_comp_dir is None:
                import dslighting
                package_dir = Path(dslighting.__file__).parent
                self._vendor_comp_dir = str(package_dir / "benchmark" / "vendor" / inferred_type / "competitions")
            else:
                self._vendor_comp_dir = vendor_comp_dir

            # Resolve data_dir: Read from environment variable first, otherwise use user-provided value
            if data_dir is None:
                env_key = f"DSLIGHTING_{inferred_type.upper()}_DATA"
                self._data_dir = os.getenv(env_key)
            else:
                self._data_dir = data_dir

            if self._data_dir is None:
                raise ValueError(
                    f"Cannot determine data path for {inferred_type}. "
                    f"Please either:\n"
                    f"  1. Set {env_key} environment variable, or\n"
                    f"  2. Provide data_dir parameter when initializing DSBenchmark"
                )

            # Get predefined MLE-Lite tasks
            self._competitions = TaskLoader.get_predefined_tasks("mle-lite")
            if self._competitions is None:
                raise ValueError("MLE-Lite task list not found")

        else:
            raise ValueError(
                f"Unknown benchmark type: {benchmark_type}\n"
                f"Available predefined modes:\n"
                f"  - dabench, mlebench: Full benchmark\n"
                f"  - mle-lite: MLE-Lite subset (22 tasks)\n"
                f"  - da_summary_statistics: DABench summary statistics (90 tasks)\n"
                f"  - da_comprehensive_preprocessing: DABench comprehensive preprocessing (45 tasks)\n"
                f"  - da_correlation_analysis: DABench correlation analysis (72 tasks)\n"
                f"  - da_distribution_analysis: DABench distribution analysis (64 tasks)\n"
                f"  - da_feature_engineering: DABench feature engineering (50 tasks)\n"
                f"  - da_machine_learning: DABench machine learning (19 tasks)\n"
                f"  - da_outlier_detection: DABench outlier detection (35 tasks)\n"
                f"Or use custom mode (provide competitions parameter)"
            )

        logger.info(f"DSBenchmark initialized: {self.name} ({self._mode} mode)")
        logger.info(f"  Data dir: {self._data_dir}")
        logger.info(f"  Vendor dir: {self._vendor_comp_dir}")
        logger.info(f"  Competitions: {len(self._competitions)} tasks")

    def run(
        self,
        # Agent configuration (Second Layer)
        model: Optional[str] = None,
        workflow: Optional[str] = None,
        max_iterations: Optional[int] = None,
        temperature: Optional[float] = None,
        num_drafts: Optional[int] = None,
        api_key: Optional[str] = None,
        # Runtime configuration (Third Layer)
        max_concurrency: Optional[int] = None,
        scheduler_policy: Optional[str] = None,
        queue_policy: Optional[str] = None,
        workload_mode: Optional[str] = None,
        dag_enabled: Optional[bool] = None,
        dag_mode: Optional[str] = None,
        gpu_policy: Optional[str] = None,
        gpu_ids: Optional[List[int]] = None,
        enable_monitoring: bool = False,
        # Config objects (optional, override above params)
        agent_config: Optional[AgentSettingsConfig] = None,
        runtime_config: Optional[RuntimeConfig] = None,
        # Other options
        log_path: Optional[str] = None,
        verbose: bool = True,
    ):
        """
        Run the benchmark.

        Args:
            # Agent configuration
            model: LLM model name (REQUIRED)
            workflow: Workflow name ("aide", "autokaggle", etc.)
            max_iterations: Max agent iterations
            temperature: LLM temperature
            num_drafts: Number of drafts
            api_key: LLM API key

            # Runtime configuration
            max_concurrency: Max concurrent tasks
            scheduler_policy: Scheduling policy
            queue_policy: Queue policy
            workload_mode: Workload mode
            dag_enabled: Enable DAG runtime
            dag_mode: DAG mode ("coarse", "fine")
            gpu_policy: GPU policy
            gpu_ids: GPU ID list
            enable_monitoring: Enable monitoring

            # Config objects (override above)
            agent_config: AgentSettingsConfig object
            runtime_config: RuntimeConfig object (task + DAG settings)

            # Other options
            log_path: Log directory path
            verbose: Print detailed info

        Returns:
            Benchmark object containing:
            - results: List of all task results (one per competition/task)
            - metadata: Benchmark metadata including scores, costs, timing
            - results_path: Path to CSV results file
            - metadata_path: Path to JSON metadata file

            The returned Benchmark object provides comprehensive benchmark results:
            - benchmark.results: List of result tuples for each task
            - benchmark.results_path: CSV file with all task results
            - benchmark.metadata_path: JSON file with aggregated statistics

            Example:
                >>> benchmark = DSBenchmark("dabench").run(model="gpt-4o")
                >>> # Access results
                >>> benchmark.results  # List of all task results
                >>> # Access metadata
                >>> benchmark.metadata  # Aggregated statistics

        Raises:
            ValueError: If model is not specified via argument or LLM_MODEL env var
        """
        # Validate model is specified
        if model is None and agent_config is None:
            env_model = os.getenv("LLM_MODEL")
            if env_model is None:
                raise ValueError(
                    "model parameter is required!\n"
                    "Please specify the model via one of the following:\n"
                    "  1. Set LLM_MODEL in .env file\n"
                    "  2. Pass model parameter in code, e.g.:\n"
                    "     DSBenchmark('dabench').run(model='gpt-4o-mini')"
                )

        # Build final configurations
        final_agent_config = self._build_agent_config(
            agent_config,
            model=model,
            workflow=workflow,
            max_iterations=max_iterations,
            temperature=temperature,
            num_drafts=num_drafts,
            api_key=api_key,
        )

        final_runtime_config = self._build_runtime_config(
            runtime_config,
            max_concurrency=max_concurrency,
            scheduler_policy=scheduler_policy,
            queue_policy=queue_policy,
            workload_mode=workload_mode,
            dag_enabled=dag_enabled,
            dag_mode=dag_mode,
            gpu_policy=gpu_policy,
            gpu_ids=gpu_ids,
            enable_monitoring=enable_monitoring,
        )

        # Build DSLightingConfig
        dslighting_config = self._build_dslighting_config(final_agent_config, final_runtime_config)

        # Build RuntimeSchedulerOptions
        runtime_options = self._build_runtime_options(final_runtime_config)

        # Execute benchmark and return benchmark object
        return self._execute_benchmark(
            dslighting_config,
            runtime_options,
            log_path=log_path or f"runs/benchmarks/{self.name}",
            verbose=verbose,
        )

    def _infer_benchmark_type(self, name: str) -> str:
        """Infer benchmark type from name."""
        if name.startswith("mle"):
            return "mlebench"
        return "dabench"

    def _build_agent_config(self, base_config: Optional[AgentSettingsConfig], **kwargs) -> AgentSettingsConfig:
        """Build final AgentSettingsConfig."""
        if base_config:
            config = base_config
        else:
            config = AgentSettingsConfig()

        # Apply kwargs overrides
        for key, value in kwargs.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)

        return config

    def _build_runtime_config(self, base_config: Optional[RuntimeConfig], **kwargs) -> RuntimeConfig:
        """Build final RuntimeConfig.

        If base_config is provided, use it as-is (preserving all user-provided values).
        If base_config is None, create a new RuntimeConfig and apply kwargs overrides.
        """
        if base_config:
            # When user provides RuntimeConfig, use it directly (don't override)
            return base_config

        # Create new RuntimeConfig and apply kwargs overrides
        config = RuntimeConfig()
        for key, value in kwargs.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)

        return config

    def _build_dslighting_config(self, agent_config: AgentSettingsConfig, runtime_config: RuntimeConfig):
        """Build DSLightingConfig from AgentSettingsConfig."""
        builder = ConfigBuilder()

        config = builder.build_config(
            workflow=agent_config.get_workflow(self._benchmark_type),
            model=agent_config.get_model(),
            max_iterations=agent_config.get_max_iterations(),
            temperature=agent_config.get_temperature(),
            num_drafts=agent_config.get_num_drafts(),
            api_key=agent_config.api_key,
        )

        # Apply DAG configuration
        runtime_config.apply_dag_to_config(config)

        # Apply sandbox backend configuration
        runtime_config.apply_sandbox_to_config(config)

        return config

    def _build_runtime_options(self, runtime_config: RuntimeConfig) -> "RuntimeSchedulerOptions":
        """Build RuntimeSchedulerOptions from RuntimeConfig."""
        return runtime_config.to_runtime_options()

    def _execute_benchmark(
        self,
        config,
        runtime_options: "RuntimeSchedulerOptions",
        log_path: str,
        verbose: bool,
    ):
        """Execute the benchmark.

        Returns:
            Benchmark object (with .results attribute containing results list)
        """
        runner = DSLightingRunner(config)

        # Select benchmark class based on type
        benchmark_type = self._infer_benchmark_type(self._benchmark_type)

        if benchmark_type == "dabench":
            benchmark = DABenchmark(
                name=self.name,
                log_path=log_path,
                data_dir=self._data_dir,
                competitions=self._competitions,
                runner=runner,
            )
        else:  # mlebench
            benchmark = MLEBenchmark(
                name=self.name,
                file_path=None,
                log_path=log_path,
                data_dir=self._data_dir,
                competitions=self._competitions,
                runner=runner,
            )

        # Print banner and info
        if verbose:
            print_benchmark_banner()
            print_benchmark_info(
                benchmark_name=self.name,
                config=config,
                runtime_options=runtime_options,
                num_tasks=len(self._competitions),
            )

        # Run evaluation and save results to benchmark object
        benchmark.results = benchmark.run_evaluation(scheduler_options=runtime_options)

        return benchmark
