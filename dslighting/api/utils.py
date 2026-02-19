"""
Utility functions for DSLighting API.
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from dslighting.benchmark.core.scheduler_core import RuntimeSchedulerOptions

logger = logging.getLogger(__name__)


def print_benchmark_banner() -> None:
    """Print DSLighting benchmark banner."""
    print("\n" + "=" * 70)
    print(" " * 15 + "🚀 DSLighting Benchmark Runner")
    print("=" * 70 + "\n")


def print_benchmark_info(
    benchmark_name: str,
    config,
    runtime_options: "RuntimeSchedulerOptions",
    num_tasks: int,
) -> None:
    """
    Print benchmark information summary.

    Args:
        benchmark_name: Name of the benchmark
        config: DSLightingConfig object
        runtime_options: RuntimeSchedulerOptions object
        num_tasks: Number of tasks to run
    """
    print("📊 Benchmark Configuration:")
    print("-" * 70)
    print(f"  Benchmark:        {benchmark_name}")
    print(f"  Tasks:            {num_tasks}")
    print(f"  Workflow:         {config.workflow.name}")
    print(f"  Model:            {config.llm.model}")
    print(f"  Max Iterations:   {config.agent.search.max_iterations}")

    print("\n⚙️  Runtime Configuration:")
    print("-" * 70)
    print(f"  Max Concurrency:  {runtime_options.max_concurrency}")
    print(f"  Scheduler Policy: {runtime_options.scheduler_policy}")
    print(f"  Queue Policy:     {runtime_options.queue_policy}")
    print(f"  GPU Policy:       {runtime_options.gpu_policy}")
    print(f"  Monitoring:       {'Enabled' if runtime_options.enable_monitoring else 'Disabled'}")

    if runtime_options.gpu_ids:
        print(f"  GPU IDs:          {runtime_options.gpu_ids}")

    print("\n" + "=" * 70 + "\n")


def validate_paths(
    data_dir: str,
    vendor_comp_dir: str,
) -> tuple[bool, Optional[str]]:
    """
    Validate that data and vendor directories exist.

    Args:
        data_dir: Data directory path
        vendor_comp_dir: Vendor competition directory path

    Returns:
        Tuple of (is_valid, error_message)
    """
    from pathlib import Path

    data_path = Path(data_dir)
    vendor_path = Path(vendor_comp_dir)

    if not data_path.exists():
        return False, f"Data directory not found: {data_dir}"

    if not vendor_path.exists():
        return False, f"Vendor directory not found: {vendor_comp_dir}"

    return True, None

