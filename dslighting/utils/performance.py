"""
Performance profiling utilities for DSLighting.

This module provides tools for tracking and analyzing performance metrics
during task execution, helping identify bottlenecks and optimization opportunities.
"""

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """A single performance metric entry."""
    operation: str
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class PerformanceProfiler:
    """
    Tracks performance metrics for operations with nested context support.

    This profiler can be used to measure the execution time of operations
    and generate summary statistics for performance analysis.

    Example:
        profiler = PerformanceProfiler()

        async with profiler.profile("load_data", dataset_name="train"):
            data = load_dataset("train.csv")

        async with profiler.profile("preprocess"):
            preprocess(data)

        summary = profiler.get_summary()
        print(summary)
    """

    def __init__(self):
        self._metrics: List[PerformanceMetrics] = []
        self._stack: List[str] = []
        self._enabled = True

    def enable(self) -> None:
        """Enable profiling."""
        self._enabled = True

    def disable(self) -> None:
        """Disable profiling (metrics are silently discarded)."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if profiling is enabled."""
        return self._enabled

    @contextlib.asynccontextmanager
    async def profile(self, operation: str, **metadata):
        """
        Context manager for profiling an async operation.

        Args:
            operation: Name of the operation being profiled
            **metadata: Additional metadata to attach to the metric

        Example:
            async with profiler.profile("database_query", table="users"):
                result = await db.query("SELECT * FROM users")
        """
        if not self._enabled:
            yield
            return

        start = time.perf_counter()
        self._stack.append(operation)
        operation_id = f"{operation}/{len(self._metrics)}"

        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self._metrics.append(PerformanceMetrics(
                operation=operation,
                duration_seconds=duration,
                metadata={
                    "operation_id": operation_id,
                    "stack": "/".join(self._stack),
                    **metadata
                }
            ))
            self._stack.pop()

    @contextlib.contextmanager
    def profile_sync(self, operation: str, **metadata):
        """
        Context manager for profiling a synchronous operation.

        Args:
            operation: Name of the operation being profiled
            **metadata: Additional metadata to attach to the metric

        Example:
            with profiler.profile_sync("file_read", path="data.csv"):
                data = read_file("data.csv")
        """
        if not self._enabled:
            yield
            return

        start = time.perf_counter()
        self._stack.append(operation)
        operation_id = f"{operation}/{len(self._metrics)}"

        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self._metrics.append(PerformanceMetrics(
                operation=operation,
                duration_seconds=duration,
                metadata={
                    "operation_id": operation_id,
                    "stack": "/".join(self._stack),
                    **metadata
                }
            ))
            self._stack.pop()

    def record_metric(self, operation: str, duration_seconds: float, **metadata) -> None:
        """
        Manually record a performance metric.

        Args:
            operation: Name of the operation
            duration_seconds: Duration in seconds
            **metadata: Additional metadata to attach
        """
        if not self._enabled:
            return

        self._metrics.append(PerformanceMetrics(
            operation=operation,
            duration_seconds=duration_seconds,
            metadata=metadata
        ))

    def get_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics from collected metrics.

        Returns:
            Dictionary containing:
                - by_operation: Stats grouped by operation name
                - total_metrics: Total number of metrics collected
                - total_duration_seconds: Sum of all durations
                - p50/p95/p99 latency percentiles
        """
        if not self._metrics:
            return {
                "by_operation": {},
                "total_metrics": 0,
                "total_duration_seconds": 0.0,
            }

        by_operation: Dict[str, Dict[str, Any]] = {}
        total_duration = 0.0

        for metric in self._metrics:
            if metric.operation not in by_operation:
                by_operation[metric.operation] = {
                    "count": 0,
                    "total_seconds": 0.0,
                    "min_seconds": float('inf'),
                    "max_seconds": 0.0,
                    "_timings": [],  # Track individual timings for percentiles
                }
            stats = by_operation[metric.operation]
            stats["count"] += 1
            stats["total_seconds"] += metric.duration_seconds
            stats["min_seconds"] = min(stats["min_seconds"], metric.duration_seconds)
            stats["max_seconds"] = max(stats["max_seconds"], metric.duration_seconds)
            stats["_timings"].append(metric.duration_seconds)
            total_duration += metric.duration_seconds

        # Calculate averages and percentiles
        for stats in by_operation.values():
            stats["avg_seconds"] = stats["total_seconds"] / stats["count"]
            # Calculate percentiles
            timings = sorted(stats["_timings"])
            count = len(timings)
            stats["p50_seconds"] = timings[int(count * 0.50)] if count >= 2 else timings[0] if timings else 0.0
            stats["p95_seconds"] = timings[int(count * 0.95)] if count >= 20 else stats["max_seconds"]
            stats["p99_seconds"] = timings[int(count * 0.99)] if count >= 100 else stats["max_seconds"]
            # Convert inf to 0 for min if no measurements
            if stats["min_seconds"] == float('inf'):
                stats["min_seconds"] = 0.0
            # Remove internal timings list
            del stats["_timings"]

        return {
            "by_operation": by_operation,
            "total_metrics": len(self._metrics),
            "total_duration_seconds": total_duration,
        }

    def get_metrics(self) -> List[PerformanceMetrics]:
        """
        Get all collected metrics.

        Returns:
            List of all PerformanceMetric objects
        """
        return list(self._metrics)

    def clear(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
        self._stack.clear()

    def get_slowest_operations(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the N slowest operations.

        Args:
            n: Number of slowest operations to return

        Returns:
            List of dictionaries containing operation details
        """
        sorted_metrics = sorted(self._metrics, key=lambda m: m.duration_seconds, reverse=True)
        return [
            {
                "operation": m.operation,
                "duration_seconds": m.duration_seconds,
                "metadata": m.metadata,
            }
            for m in sorted_metrics[:n]
        ]

    def print_summary(self) -> None:
        """Print a formatted summary of collected metrics to the logger."""
        summary = self.get_summary()

        if summary["total_metrics"] == 0:
            logger.info("No performance metrics collected")
            return

        logger.info("=" * 80)
        logger.info("Performance Summary")
        logger.info("=" * 80)
        logger.info(f"Total metrics: {summary['total_metrics']}")
        logger.info(f"Total duration: {summary['total_duration_seconds']:.2f}s")
        logger.info("")

        logger.info("Operations by name:")
        logger.info("-" * 80)
        for op_name, stats in sorted(
            summary["by_operation"].items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        ):
            logger.info(
                f"  {op_name:50s} | "
                f"count={stats['count']:4d} | "
                f"total={stats['total_seconds']:7.2f}s | "
                f"avg={stats['avg_seconds']:7.2f}s | "
                f"min={stats['min_seconds']:7.2f}s | "
                f"max={stats['max_seconds']:7.2f}s"
            )

        logger.info("")
        logger.info("Slowest operations:")
        logger.info("-" * 80)
        for i, op in enumerate(self.get_slowest_operations(10), 1):
            logger.info(
                f"  {i:2d}. {op['operation']:40s} | "
                f"{op['duration_seconds']:.2f}s"
            )
        logger.info("=" * 80)


# Global profiler instance
_global_profiler = PerformanceProfiler()


def get_global_profiler() -> PerformanceProfiler:
    """Get the global performance profiler instance."""
    return _global_profiler


@contextlib.asynccontextmanager
async def profile_operation(operation: str, **metadata):
    """
    Convenience function to profile an operation using the global profiler.

    Args:
        operation: Name of the operation
        **metadata: Additional metadata

    Example:
        async with profile_operation("load_data"):
            data = load_dataset("train.csv")
    """
    async with _global_profiler.profile(operation, **metadata):
        yield


@contextlib.contextmanager
def profile_operation_sync(operation: str, **metadata):
    """
    Convenience function to profile a synchronous operation using the global profiler.

    Args:
        operation: Name of the operation
        **metadata: Additional metadata

    Example:
        with profile_operation_sync("load_data"):
            data = load_dataset("train.csv")
    """
    with _global_profiler.profile_sync(operation, **metadata):
        yield
