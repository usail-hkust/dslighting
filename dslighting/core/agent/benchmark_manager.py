"""
Benchmark management utilities for DSLighting Agent.

This module contains functions for benchmark registry management
and grading setup. Extracted from agent.py to improve code organization.
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def get_default_benchmark_dir(config: Any, logger_instance: logging.Logger = None) -> Path:
    """
    Get the default benchmark registry directory.

    This is where task registration files (grade.py, description.md, etc.) are stored.
    Priority:
        1. Built-in registry in dslighting package (dslighting/benchmark/vendor/mlebench/competitions/)
        2. Local benchmark/vendor/mlebench/competitions/
        3. Config-provided benchmark_dir

    Args:
        config: DSLighting configuration object
        logger_instance: Logger instance for output (uses module logger if None)

    Returns:
        Path to benchmark registry directory
    """
    log = logger_instance or logger

    # Try to get from config
    benchmark_dir = None

    if config and hasattr(config, 'run'):
        run_config = config.run
        if hasattr(run_config, 'parameters') and run_config.parameters:
            benchmark_dir = run_config.parameters.get('benchmark_dir')

    # Fallback 1: Try built-in benchmark registry in dslighting package
    if benchmark_dir is None:
        try:
            import dslighting
            dslighting_path = Path(dslighting.__file__).parent
            built_in_registry = dslighting_path / "benchmark" / "vendor" / "mlebench" / "competitions"

            if built_in_registry.exists():
                log.info(f"Using built-in registry: {built_in_registry}")
                return built_in_registry.resolve()
        except Exception as e:
            log.debug(f"Could not access built-in registry: {e}")

    # Fallback 2: Use relative path from current working directory
    if benchmark_dir is None:
        # Default: dslighting/benchmark/vendor/mlebench/competitions/
        benchmark_dir = "dslighting/benchmark/vendor/mlebench/competitions"

    benchmark_path = Path(benchmark_dir).resolve()

    log.debug(f"Benchmark registry directory: {benchmark_path}")

    return benchmark_path


def initialize_benchmark(
    task_id: str,
    data_dir: Optional[Path],
    registry_dir: Path,
    logger_instance: logging.Logger = None
):
    """
    Initialize benchmark for grading.

    Args:
        task_id: Task identifier
        data_dir: Data directory path
        registry_dir: Benchmark registry directory
        logger_instance: Logger instance for output (uses module logger if None)

    Returns:
        MLEBenchmark/DABenchmark instance or None
    """
    log = logger_instance or logger

    try:
        from dslighting.benchmark.benchmarks.da_benchmark import DABenchmark
        from dslighting.benchmark.benchmarks.mle_benchmark import MLEBenchmark

        # Only initialize benchmark if we have the required components
        if not task_id or not registry_dir or not data_dir:
            log.debug("Skipping benchmark initialization (missing required parameters)")
            return None

        data_dir = Path(data_dir).resolve()
        if data_dir.name == task_id:
            data_root = data_dir.parent
        elif data_dir.name in ("public", "public_val") and data_dir.parent.name in ("prepared", "prepared_val"):
            data_root = data_dir.parent.parent.parent
        else:
            data_root = data_dir

        if task_id.startswith("dabench-"):
            benchmark = DABenchmark(
                name=f"direct_{task_id}",
                log_path="runs/benchmarks/direct",
                data_dir=str(data_root),
                competitions=[task_id],
                data_source="prepared",
            )
        else:
            benchmark = MLEBenchmark(
                name=f"direct_{task_id}",
                file_path=None,
                log_path="runs/benchmarks/direct",
                data_dir=str(data_root),
                competitions=[task_id],
                data_source="prepared",
            )

        log.info(f"Benchmark initialized for task: {task_id}")
        return benchmark

    except Exception as e:
        log.warning(f"Failed to initialize benchmark: {e}")
        return None
