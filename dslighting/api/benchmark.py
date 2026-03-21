"""
DSBenchmark - Unified DSLighting Benchmark Interface.

This module provides a simple, unified API for running DSLighting benchmarks
with minimal configuration while maintaining full control for advanced users.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from dslighting.api.utils import print_benchmark_banner, print_benchmark_info
from dslighting.benchmark.core.source_catalog import (
    BenchmarkSourceDescriptor,
    get_benchmark_source_catalog,
)
from dslighting.config import DSLightingConfig, WorkflowConfig
from dslighting.core.config.shared import get_workflow_for_benchmark
from dslighting.error import ConfigurationError
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
        >>> from dslighting.core import ConfigBuilder
        >>> config = ConfigBuilder().build_config(model="gpt-4o")
        >>> DSBenchmark("dabench").run(config=config)
        >>>
        >>> config = ConfigBuilder().build_config(model="gpt-4o-mini")
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
        self._catalog = get_benchmark_source_catalog()
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
            self._source = self._catalog.resolve_source_by_registry_root(
                Path(vendor_comp_dir),
                search_hints=[Path(data_dir), Path.cwd()],
            )
            self._source_id = self._source.source_id
            self._vendor_comp_dir = str(self._source.registry_root)

        else:
            preset = self._catalog.resolve_preset(benchmark_type)
            if preset is not None:
                self._mode = "predefined"
                self._source = self._catalog.get_source(preset.source_id)
                self._source_id = self._source.source_id
                self._vendor_comp_dir = str(self._resolve_vendor_dir(self._source, vendor_comp_dir))
                self._data_dir = self._catalog.resolve_data_dir(self._source, data_dir)
                self._competitions = preset.get_task_ids()
                if not self._competitions:
                    raise ValueError(f"Preset '{benchmark_type}' did not resolve to any tasks")

            else:
                try:
                    self._source = self._catalog.get_source(benchmark_type)
                except Exception as exc:
                    available_modes = ", ".join(self._catalog.list_available_benchmark_types())
                    raise ValueError(
                        f"Unknown benchmark type: {benchmark_type}\n"
                        f"Available predefined modes:\n  - {available_modes}\n"
                        "Or use custom mode (provide competitions parameter)"
                    ) from exc

                self._source_id = self._source.source_id
                self._mode = "predefined"
                self._vendor_comp_dir = str(self._resolve_vendor_dir(self._source, vendor_comp_dir))
                self._data_dir = self._catalog.resolve_data_dir(self._source, data_dir)
                self._competitions = self._catalog.discover_tasks(
                    self._source,
                    data_dir=self._data_dir,
                )

        logger.info(f"DSBenchmark initialized: {self.name} ({self._mode} mode)")
        logger.info(f"  Source: {self._source_id}")
        logger.info(f"  Data dir: {self._data_dir}")
        logger.info(f"  Vendor dir: {self._vendor_comp_dir}")
        logger.info(f"  Competitions: {len(self._competitions)} tasks")

    def _resolve_vendor_dir(
        self,
        source: BenchmarkSourceDescriptor,
        vendor_comp_dir: Optional[str],
    ) -> Path:
        if vendor_comp_dir is None:
            return source.registry_root

        resolved = self._catalog.resolve_source_by_registry_root(
            Path(vendor_comp_dir),
            search_hints=[Path.cwd()],
        )
        if resolved.source_id != source.source_id and resolved.manifest_path is not None:
            raise ValueError(
                f"Registry '{vendor_comp_dir}' belongs to source '{resolved.source_id}', "
                f"not '{source.source_id}'."
            )
        return resolved.registry_root

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
                >>> from dslighting.core import ConfigBuilder
                >>> config = ConfigBuilder().build_config(model="gpt-4o")
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
        preset = self._catalog.resolve_preset(name)
        if preset is not None:
            return preset.source_id
        if name in self._catalog.list_available_benchmark_types():
            return name
        if name.startswith("mle"):
            return "mlebench"
        return "dabench"

    def _prepare_config(self, config: DSLightingConfig) -> DSLightingConfig:
        """Prepare benchmark-specific defaults for a fully resolved DSLightingConfig."""
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

        if not prepared.llm.get_api_keys():
            raise ConfigurationError(
                "DSBenchmark.run(config=...) requires a fully resolved LLM config. "
                "Build the config with ConfigBuilder.build_config(...) or provide llm.api_key/api_keys explicitly.",
                error_code="CFG-002",
            )

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
        benchmark = self._catalog.build_benchmark(
            self._source,
            name=self.name,
            data_dir=self._data_dir,
            competitions=self._competitions,
            runner=runner,
            log_path=log_path,
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
