"""
DSBenchmark - Unified DSLighting Benchmark Interface.

This module provides a simple, unified API for running DSLighting benchmarks
with minimal configuration while maintaining full control for advanced users.
"""

import logging
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from dslighting.api.task_loader import TaskLoader
from dslighting.api.utils import print_benchmark_banner, print_benchmark_info
from dslighting.benchmark import DABenchmark, MLEBenchmark
from dslighting.config import DSLightingConfig, WorkflowConfig
from dslighting.core.config.shared import get_workflow_for_benchmark
if TYPE_CHECKING:
    from dslighting.runner import DSLightingRunner

if TYPE_CHECKING:
    from dslighting.benchmark import RuntimeSchedulerOptions

logger = logging.getLogger(__name__)


class DSBenchmark:
    """
    Unified DSLighting Benchmark interface.

    Simplifies running DSLighting benchmarks with a single configuration
    object as the only source of runtime truth.

    **Predefined modes:**
        - "dabench": All DABench tasks
        - "mlebench": All MLE-Bench tasks
        - "mle-lite": 22 curated MLE-Bench tasks

    **Custom mode:**
        Provide explicit competitions list with data_dir and vendor_comp_dir.

    Examples:
        >>> # Predefined mode (simplest)
        >>> DSBenchmark("dabench").run()
        >>>
        >>> config = DSLightingConfig()
        >>> DSBenchmark("dabench").run(config=config)
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
                f"  - mle-lite: MLE-Lite curated subset (22 tasks)\n"
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
        config: DSLightingConfig,
        # Other options
        log_path: Optional[str] = None,
        verbose: bool = True,
    ):
        """
        Run the benchmark.

        Args:
            config: Unified DSLightingConfig object.

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
                >>> config = DSLightingConfig()
                >>> benchmark = DSBenchmark("dabench").run(config=config)
        """
        dslighting_config = self._prepare_config(config)
        runtime_options = self._build_runtime_options(dslighting_config)

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

    def _prepare_config(self, config: DSLightingConfig) -> DSLightingConfig:
        """Prepare and normalize benchmark config."""
        if not isinstance(config, DSLightingConfig):
            raise TypeError(
                f"`config` must be DSLightingConfig, got {type(config).__name__}."
            )

        prepared = config.model_copy(deep=True)
        if prepared.workflow is None:
            prepared.workflow = WorkflowConfig(
                name=get_workflow_for_benchmark(self._benchmark_type, default="aide"),
                params={},
            )

        if prepared.scheduler.exp_name is None:
            prepared.scheduler.exp_name = self.name

        # Backward-compatible env fallback for direct DSLightingConfig usage.
        # In previous API layers, API_KEY could be injected indirectly by ConfigBuilder.
        if not prepared.llm.api_key and not prepared.llm.api_keys:
            env_api_key = os.getenv("API_KEY")
            if env_api_key:
                prepared.llm.api_key = env_api_key

        # Backward-compatible model-specific env overrides (LLM_MODEL_CONFIGS).
        # Format:
        # {
        #   "model-name": {
        #       "api_key": "sk-..." or ["sk-1", "sk-2"],
        #       "api_base": "https://.../v1",
        #       "provider": "siliconflow",
        #       "temperature": 1.0
        #   }
        # }
        raw_model_configs = os.getenv("LLM_MODEL_CONFIGS")
        if raw_model_configs:
            try:
                parsed = json.loads(raw_model_configs)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                model_cfg = parsed.get(prepared.llm.model)
                if isinstance(model_cfg, dict):
                    if "api_key" in model_cfg:
                        key_val = model_cfg.get("api_key")
                        if isinstance(key_val, list) and key_val:
                            prepared.llm.api_keys = [str(k) for k in key_val if str(k).strip()]
                            prepared.llm.api_key = None
                        elif isinstance(key_val, str) and key_val.strip():
                            prepared.llm.api_key = key_val.strip()
                            prepared.llm.api_keys = None
                    if isinstance(model_cfg.get("api_base"), str) and model_cfg["api_base"].strip():
                        prepared.llm.api_base = model_cfg["api_base"].strip()
                    if isinstance(model_cfg.get("provider"), str) and model_cfg["provider"].strip():
                        prepared.llm.provider = model_cfg["provider"].strip()
                    if model_cfg.get("temperature") is not None:
                        try:
                            prepared.llm.temperature = float(model_cfg["temperature"])
                        except (TypeError, ValueError):
                            pass

        return prepared

    def _build_runtime_options(self, config: DSLightingConfig) -> "RuntimeSchedulerOptions":
        """Build RuntimeSchedulerOptions from DSLightingConfig.scheduler."""
        return config.scheduler.to_runtime_options()

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
        from dslighting.runner import DSLightingRunner

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
