"""Monitoring integration module for the benchmark scheduler."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from dslighting.benchmark.core.scheduler_core import (
    BenchmarkRuntimeScheduler,
    RuntimeSchedulerOptions,
)
from dslighting.benchmark.core.task_profile import RuntimeAssignment, RuntimeLease

if TYPE_CHECKING:
    from dslighting.monitoring.monitoring import SystemMonitor

logger = logging.getLogger(__name__)


__all__ = [
    "monitoring_context",
]


async def monitoring_context(
    problems: List[Dict[str, Any]],
    scheduler_options: RuntimeSchedulerOptions,
    monitor_options: Optional[Dict[str, Any]] = None,
) -> BenchmarkRuntimeScheduler:
    """Create a scheduler with monitoring context.

    Args:
        problems: List of problem dictionaries.
        scheduler_options: RuntimeSchedulerOptions instance.
        monitor_options: Options for the global monitor.

    Returns:
        BenchmarkRuntimeScheduler instance.
    """
    from dslighting.monitoring.monitoring import get_global_monitor, start_global_monitor, stop_global_monitor
    import uuid

    monitor_options = monitor_options or {}
    monitor: Optional[SystemMonitor] = None
    scheduler_instance: Optional[BenchmarkRuntimeScheduler] = None

    should_monitor = scheduler_options.enable_monitoring
    run_id = scheduler_options.run_id or str(uuid.uuid4())[:8]
    scheduler_options.run_id = run_id

    try:
        if should_monitor:
            monitor = await start_global_monitor(
                exp_name=scheduler_options.exp_name,
                run_id=run_id,
                **monitor_options
            )

        scheduler_instance = BenchmarkRuntimeScheduler(problems, scheduler_options)

        if should_monitor and monitor and scheduler_options.exp_name:
            if scheduler_options.checkpoint_resume_enabled:
                last_exp_name = getattr(monitor, '_last_exp_name', None)
                if scheduler_options.exp_name != last_exp_name:
                    monitor.reset_for_new_experiment(scheduler_options.exp_name, run_id)
                    monitor._last_exp_name = scheduler_options.exp_name
            else:
                monitor.reset_for_new_experiment(scheduler_options.exp_name, run_id)
                monitor._last_exp_name = scheduler_options.exp_name

        if should_monitor and monitor:
            monitor.update_dslighting_metrics(
                total_tasks=len(problems),
                run_mode=scheduler_options.exp_name
            )

        yield scheduler_instance
    finally:
        if should_monitor and monitor:
            await stop_global_monitor()
            monitor.print_summary()


class MonitoringIntegration:
    """Integration helper for monitoring with the scheduler.

    This class provides methods for integrating system monitoring
    with benchmark scheduling.
    """

    @staticmethod
    async def run_with_monitoring(
        problems: List[Dict[str, Any]],
        scheduler_options: RuntimeSchedulerOptions,
        monitor_options: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkRuntimeScheduler:
        """Run benchmark with global system monitoring.

        Args:
            problems: List of problem dictionaries.
            scheduler_options: RuntimeSchedulerOptions for the scheduler.
            monitor_options: Dictionary of options for start_global_monitor.

        Returns:
            BenchmarkRuntimeScheduler instance.
        """
        from dslighting.monitoring.monitoring import get_global_monitor, start_global_monitor, stop_global_monitor
        import uuid

        monitor_options = monitor_options or {}
        monitor: Optional[SystemMonitor] = None

        should_monitor = scheduler_options.enable_monitoring
        run_id = scheduler_options.run_id or str(uuid.uuid4())[:8]
        scheduler_options.run_id = run_id

        if should_monitor:
            monitor = await start_global_monitor(
                exp_name=scheduler_options.exp_name,
                run_id=run_id,
                enable_file_sharing=scheduler_options.enable_file_sharing,
                **monitor_options
            )

        scheduler_instance = BenchmarkRuntimeScheduler(problems, scheduler_options)

        if should_monitor and monitor and scheduler_options.exp_name:
            if scheduler_options.checkpoint_resume_enabled:
                last_exp_name = getattr(monitor, '_last_exp_name', None)
                if scheduler_options.exp_name != last_exp_name:
                    monitor.reset_for_new_experiment(scheduler_options.exp_name, run_id)
                    monitor._last_exp_name = scheduler_options.exp_name
            else:
                monitor.reset_for_new_experiment(scheduler_options.exp_name, run_id)
                monitor._last_exp_name = scheduler_options.exp_name

        if should_monitor and monitor:
            monitor.update_dslighting_metrics(
                language=scheduler_options.monitor_language,
                total_tasks=len(problems),
                run_mode=scheduler_options.exp_name
            )

        return scheduler_instance


async def execute_all_tasks(
    scheduler: BenchmarkRuntimeScheduler,
    task_executor: Callable[[Dict[str, Any], int, RuntimeAssignment, RuntimeLease], Any],
) -> List[Any]:
    """Execute all tasks managed by the scheduler.

    Args:
        scheduler: BenchmarkRuntimeScheduler instance.
        task_executor: Async callable that executes a single task.

    Returns:
        List of results from each task.
    """
    import time

    async def _run_single_task_wrapper(problem_data, problem_idx):
        assignment: Optional[RuntimeAssignment] = None
        lease: Optional[RuntimeLease] = None
        task_succeeded = False
        task_start_time = time.perf_counter()

        queue_wait_start_for_assignment = time.perf_counter()

        try:
            assignment, lease = await scheduler.assign_runtime(problem_data, problem_idx)

            assignment.queue_wait_seconds = time.perf_counter() - queue_wait_start_for_assignment

            task_result = await task_executor(problem_data, problem_idx, assignment, lease)
            task_succeeded = True
            return task_result
        except asyncio.CancelledError:
            logger.info(
                "Task %s cancelled: %s",
                problem_idx,
                problem_data.get('competition_id') or problem_data.get('task_id')
            )
            raise
        except Exception as exc:
            logger.error(
                "Task %s failed: %s",
                problem_idx,
                problem_data.get('competition_id') or problem_data.get('task_id'),
                exc,
                exc_info=True
            )
            task_succeeded = False
            return exc
        finally:
            runtime_seconds = time.perf_counter() - task_start_time
            if assignment and lease:
                scheduler.release_runtime(assignment, lease)

            scheduler.record_task_completion(
                runtime_seconds=runtime_seconds,
                queue_wait_seconds=assignment.queue_wait_seconds if assignment else 0.0,
                had_error=not task_succeeded,
            )

    tasks = []
    problem_tasks = scheduler.order_problems()

    for problem_idx, problem_data in problem_tasks:
        tasks.append(
            asyncio.create_task(_run_single_task_wrapper(problem_data, problem_idx))
        )

    return await asyncio.gather(*tasks, return_exceptions=True)
