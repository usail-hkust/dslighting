"""Async evaluation runner for benchmark execution.

This module provides the async evaluation logic for running benchmarks
with scheduler integration, retry handling, and monitoring.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


__all__ = [
    "AsyncEvaluationRunner",
]


class AsyncEvaluationRunner:
    """Async runner for benchmark evaluation.

    This class handles the async execution of benchmark evaluations,
    including:
    - Scheduler integration
    - Retry handling for OOM and timeout errors
    - Metrics collection
    - Results and metadata persistence
    """

    def __init__(self, benchmark: Any) -> None:
        """Initialize the async evaluation runner.

        Args:
            benchmark: Benchmark instance to run.
        """
        self.benchmark = benchmark

    @staticmethod
    def _split_runtime_kwargs(kwargs: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """Extract runtime scheduler kwargs while keeping legacy kwargs for eval_fn.

        Args:
            kwargs: Keyword arguments from run_evaluation.

        Returns:
            Tuple of (RuntimeSchedulerOptions, eval_kwargs).
        """
        from dslighting.benchmark.core.scheduler_core import RuntimeSchedulerOptions

        runtime_keys = {
            "scheduler_options",
            "max_concurrency",
            "scheduler_policy",
            "queue_policy",
            "workload_mode",
            "gpu_policy",
            "gpu_ids",
            "gpu_max_tasks_per_device",
            "auto_tune_gpu_slots",
            "gpu_memory_utilization_target",
            "sandbox_memory_mode",
            "sandbox_default_memory_gb",
            "gpu_reserved_memory_gb",
            "gpu_memory_headroom_check",
            "gpu_memory_probe_interval_seconds",
            "allocator_poll_interval_seconds",
            "llm_max_concurrency",
            "oom_max_retries",
            "oom_retry_backoff_seconds",
            "oom_retry_memory_growth",
            "oom_force_cpu_after",
            "gpu_cooldown_seconds",
            "cpu_worker_pool_size",
            "auto_fallback_to_cpu",
            "task_resource_overrides",
            "shadow_scheduler",
            "enable_adaptive_concurrency",
            "adaptive_target_p95_seconds",
            "adaptive_adjust_interval_seconds",
            "adaptive_increase_step",
            "adaptive_decrease_factor",
            "adaptive_min_concurrency",
            "adaptive_max_concurrency",
            "enable_task_rate_limiting",
            "llm_task_start_rate",
            "sandbox_task_start_rate",
            "task_rate_burst_factor",
            "enable_dual_token_bucket",
            "llm_token_rate",
            "sandbox_token_rate",
            "token_bucket_burst",
            "warmup_rounds",
            "enable_monitoring",
            "exp_name",
            "monitor_language",
            "enable_file_sharing",
            "checkpoint_resume_enabled",
            "run_id",
        }
        runtime_kwargs: Dict[str, Any] = {}
        eval_kwargs: Dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in runtime_keys:
                runtime_kwargs[key] = value
            else:
                eval_kwargs[key] = value

        options_source = runtime_kwargs.get("scheduler_options")
        if isinstance(options_source, RuntimeSchedulerOptions):
            options = options_source
        elif isinstance(options_source, dict):
            options = RuntimeSchedulerOptions(**options_source)
        elif options_source is None:
            options = RuntimeSchedulerOptions()
        else:
            raise TypeError(
                "scheduler_options must be RuntimeSchedulerOptions or dict when provided."
            )

        overrides = {k: v for k, v in runtime_kwargs.items() if k != "scheduler_options"}
        for key, value in overrides.items():
            setattr(options, key, value)
        return options, eval_kwargs

    @staticmethod
    def _extract_error_message(result: Any) -> str:
        """Extract error message from result tuple.

        Args:
            result: Result tuple from evaluate_problem.

        Returns:
            Error message string.
        """
        if not isinstance(result, tuple):
            return ""
        if len(result) < 3:
            return ""
        candidate = result[2]
        if isinstance(candidate, str):
            return candidate
        return str(candidate or "")

    @staticmethod
    def _is_oom_error(message: Any) -> bool:
        """Check if error message indicates OOM.

        Args:
            message: Error message to check.

        Returns:
            True if OOM error.
        """
        text = str(message or "").lower()
        if not text:
            return False
        markers = (
            "out of memory",
            "cuda out of memory",
            "cuda error: out of memory",
            "cublas_status_alloc_failed",
            "resourceexhaustederror",
            "cannot allocate memory",
            "failed to allocate",
            "hip out of memory",
            "mps backend out of memory",
            "memoryerror",
            "oom",
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _is_timeout_error(message: Any) -> bool:
        """Check if error message indicates timeout.

        Args:
            message: Error message to check.

        Returns:
            True if timeout error.
        """
        text = str(message or "").lower()
        if not text:
            return False
        markers = ("timed out", "timeout", "wrk-003")
        return any(marker in text for marker in markers)

    @staticmethod
    def _inject_runtime_hint(task: Any, assignment: Any) -> Any:
        """Attach scheduler runtime hints to TaskDefinition payload.

        Args:
            task: Task object.
            assignment: RuntimeAssignment with hints.

        Returns:
            Modified task or original if modification fails.
        """
        payload = getattr(task, "payload", None)
        if not isinstance(payload, dict):
            return task

        updated_payload = dict(payload)
        runtime_payload = dict(assignment.to_runtime_payload())
        current_runtime = updated_payload.get("runtime")
        if isinstance(current_runtime, dict):
            merged_runtime = dict(current_runtime)
            merged_runtime.update(runtime_payload)
            runtime_payload = merged_runtime
        updated_payload["runtime"] = runtime_payload

        model_copy = getattr(task, "model_copy", None)
        if callable(model_copy):
            try:
                return model_copy(update={"payload": updated_payload})
            except Exception:
                return task
        return task

    @staticmethod
    def _normalize_run_id(value: Any) -> Optional[str]:
        """Normalize run_id value into a non-empty string."""
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _safe_checkpoint_component(value: Any, fallback: str) -> str:
        """Convert arbitrary identifier to a filesystem-safe component."""
        raw = str(value or "").strip()
        if not raw:
            return fallback
        safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw)
        safe = safe.strip("_")
        return safe or fallback

    @classmethod
    def _build_checkpoint_workflow_id(cls, benchmark_name: str, run_id: str) -> str:
        """Build workflow id used for persisted benchmark checkpoints."""
        safe_benchmark = cls._safe_checkpoint_component(benchmark_name, "benchmark")
        safe_run_id = cls._safe_checkpoint_component(run_id, "run")
        return f"{safe_benchmark}_{safe_run_id}"

    @staticmethod
    def _build_problem_resume_key(task_id: str, idx: int) -> str:
        """Build stable resume key for a benchmark problem."""
        return f"{idx}:{task_id}"

    async def _call_evaluate_problem(
        self,
        problem: Dict[str, Any],
        eval_fn: Callable,
        eval_kwargs: Dict[str, Any],
    ) -> Tuple:
        """Call evaluate_problem with signature compatibility.

        Args:
            problem: Problem dictionary.
            eval_fn: Evaluation function.
            eval_kwargs: Evaluation keyword arguments.

        Returns:
            Result tuple from evaluate_problem.
        """
        fn = self.benchmark.evaluate_problem
        sig = inspect.signature(fn)
        accepts_var_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in sig.parameters.values()
        )
        if accepts_var_kwargs:
            return await fn(problem, eval_fn=eval_fn, **eval_kwargs)

        accepted_kwargs = {
            key: value
            for key, value in eval_kwargs.items()
            if key in sig.parameters
        }
        return await fn(problem, eval_fn=eval_fn, **accepted_kwargs)

    def _warmup_perception_cache(self, rounds: int) -> Dict[str, Any]:
        """Warmup DataAnalyzer cache.

        Args:
            rounds: Number of warmup rounds.

        Returns:
            Dictionary with warmup statistics.
        """
        rounds = max(0, int(rounds or 0))
        if rounds <= 0:
            return {
                "enabled": False,
                "rounds": 0,
                "warmed_entries": 0,
                "elapsed_seconds": 0.0,
            }

        try:
            from dslighting.config import DSLightingConfig
            from dslighting.services.data_analysis_provider import create_data_perception_runtime
        except Exception as exc:
            logger.debug("Perception cache warmup unavailable: %s", exc)
            return {
                "enabled": False,
                "rounds": rounds,
                "warmed_entries": 0,
                "elapsed_seconds": 0.0,
                "note": "data perception import failed",
            }

        data_root = getattr(self.benchmark, "data_dir", None)
        if not data_root:
            return {
                "enabled": False,
                "rounds": rounds,
                "warmed_entries": 0,
                "elapsed_seconds": 0.0,
                "note": "benchmark has no data_dir",
            }

        try:
            data_root_path = Path(data_root)
        except Exception:
            return {
                "enabled": False,
                "rounds": rounds,
                "warmed_entries": 0,
                "elapsed_seconds": 0.0,
                "note": "invalid data_dir",
            }

        runtime = create_data_perception_runtime(DSLightingConfig())
        if runtime is None:
            return {
                "enabled": False,
                "rounds": rounds,
                "warmed_entries": 0,
                "elapsed_seconds": 0.0,
                "note": "data analyzer disabled by config",
            }
        warmed_entries = 0
        started = time.perf_counter()

        for _ in range(rounds):
            for idx, problem in enumerate(self.benchmark.problems, start=1):
                task_id = None
                if isinstance(problem, dict):
                    task_id = (
                        problem.get("competition_id")
                        or problem.get("task_id")
                        or f"task_{idx}"
                    )
                if not task_id:
                    continue

                prepared_public = data_root_path / str(task_id) / "prepared" / "public"
                if not prepared_public.exists():
                    continue
                try:
                    runtime.analyze_data(
                        prepared_public, task_type="kaggle", task_id=str(task_id)
                    )
                    warmed_entries += 1
                except Exception as exc:
                    logger.debug("Perception cache warmup skipped for %s: %s", task_id, exc)

        elapsed = max(0.0, time.perf_counter() - started)
        return {
            "enabled": True,
            "rounds": rounds,
            "warmed_entries": warmed_entries,
            "elapsed_seconds": elapsed,
        }


    @staticmethod
    def _extract_dag_summary_from_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract per-task DAG summary from one runner record."""
        if not isinstance(record, dict):
            return None

        direct = record.get("dag_runtime")
        if isinstance(direct, dict):
            return direct

        summary = record.get("summary")
        if not isinstance(summary, dict):
            return None

        usage = summary.get("usage")
        if isinstance(usage, dict) and isinstance(usage.get("dag_runtime"), dict):
            return usage.get("dag_runtime")

        return None

    def _collect_runner_dag_aggregate(self) -> Dict[str, Any]:
        """Aggregate DAG runtime metrics from runner task records."""
        runner = getattr(self.benchmark, "runner", None)
        get_records = getattr(runner, "get_run_records", None)
        if not callable(get_records):
            return {}

        try:
            run_records = get_records()
        except Exception as exc:
            logger.debug("Failed to read runner records for DAG aggregation: %s", exc)
            return {}

        if not isinstance(run_records, list) or not run_records:
            return {}

        dag_summaries: List[Dict[str, Any]] = []
        for record in run_records:
            dag_summary = self._extract_dag_summary_from_record(record)
            if isinstance(dag_summary, dict):
                dag_summaries.append(dag_summary)

        if not dag_summaries:
            return {}

        def _as_int(value: Any) -> int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        def _as_float(value: Any) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        total_nodes = sum(_as_int(item.get("total_nodes")) for item in dag_summaries)
        successful_nodes = sum(_as_int(item.get("successful_nodes")) for item in dag_summaries)
        failed_nodes = sum(_as_int(item.get("failed_nodes")) for item in dag_summaries)
        cancelled_nodes = sum(_as_int(item.get("cancelled_nodes")) for item in dag_summaries)
        retries = sum(_as_int(item.get("retries")) for item in dag_summaries)
        duration_seconds = sum(_as_float(item.get("duration_seconds")) for item in dag_summaries)
        actor_completed = sum(1 for item in dag_summaries if bool(item.get("actor_completed")))
        successful_tasks = sum(1 for item in dag_summaries if bool(item.get("success")))
        tasks_with_failures = sum(1 for item in dag_summaries if _as_int(item.get("failed_nodes")) > 0)

        task_count = len(dag_summaries)
        return {
            "task_count": task_count,
            "successful_task_count": successful_tasks,
            "actor_completed_task_count": actor_completed,
            "tasks_with_failed_nodes": tasks_with_failures,
            "total_nodes": total_nodes,
            "successful_nodes": successful_nodes,
            "failed_nodes": failed_nodes,
            "cancelled_nodes": cancelled_nodes,
            "retries": retries,
            "total_duration_seconds": duration_seconds,
            "avg_duration_seconds": (duration_seconds / task_count) if task_count else 0.0,
            "avg_nodes_per_task": (total_nodes / task_count) if task_count else 0.0,
        }

    async def run_async(self, eval_fn: Callable, **kwargs) -> List[Any]:
        """Run benchmark evaluation asynchronously.

        Args:
            eval_fn: Evaluation function.
            **kwargs: Keyword arguments for runtime and evaluation.

        Returns:
            List of results from all problems.
        """
        from dslighting.benchmark.core.scheduler_core import (
            BenchmarkRuntimeScheduler,
        )

        if not self.benchmark.problems:
            logger.error(
                "Evaluation for '%s' aborted: No problems were loaded.",
                self.benchmark.name,
            )
            return []

        logger.info(
            "Starting evaluation for benchmark '%s' with %s problems.",
            self.benchmark.name,
            len(self.benchmark.problems),
        )

        runtime_options, eval_kwargs = self._split_runtime_kwargs(kwargs)
        runtime_options.run_id = self._normalize_run_id(runtime_options.run_id)
        if runtime_options.checkpoint_resume_enabled and not runtime_options.run_id:
            runtime_options.run_id = str(uuid.uuid4())[:8]
        warmup_stats = self._warmup_perception_cache(runtime_options.warmup_rounds)
        if warmup_stats.get("enabled"):
            logger.info(
                "Perception cache warmup complete: rounds=%s warmed_entries=%s elapsed=%.3fs",
                warmup_stats.get("rounds"),
                warmup_stats.get("warmed_entries"),
                warmup_stats.get("elapsed_seconds", 0.0),
            )

        results: List[Any] = []
        queue_waits: List[float] = []
        assigned_gpu_tasks = 0
        cpu_fallback_tasks = 0
        total_gpu_tokens = 0
        oom_retry_attempts = 0
        tasks_with_oom = 0
        task_ids_with_oom: set = set()
        checkpoint_manager = None
        checkpoint_workflow_id: Optional[str] = None
        completed_problem_keys: Set[str] = set()
        resumed_task_count = 0

        if runtime_options.checkpoint_resume_enabled and runtime_options.run_id:
            try:
                from dslighting.checkpoint import create_checkpoint_manager

                checkpoint_dir = Path(self.benchmark.log_path) / "checkpoints"
                checkpoint_manager = create_checkpoint_manager(
                    checkpoint_dir=checkpoint_dir,
                    serializer="pickle",
                    max_checkpoints=20,
                )
                checkpoint_workflow_id = self._build_checkpoint_workflow_id(
                    self.benchmark.name,
                    runtime_options.run_id,
                )
                latest_checkpoint = checkpoint_manager.load_latest(checkpoint_workflow_id)
                if latest_checkpoint and isinstance(latest_checkpoint.state, dict):
                    checkpoint_state = latest_checkpoint.state
                    saved_keys = checkpoint_state.get("completed_problem_keys")
                    if isinstance(saved_keys, list):
                        completed_problem_keys = {str(key) for key in saved_keys}
                        resumed_task_count = len(completed_problem_keys)

                        saved_results = checkpoint_state.get("results")
                        if isinstance(saved_results, list):
                            results.extend(saved_results)

                    logger.info(
                        "Loaded checkpoint workflow=%s run_id=%s completed=%s",
                        checkpoint_workflow_id,
                        runtime_options.run_id,
                        resumed_task_count,
                    )
            except Exception as exc:
                logger.warning("Checkpoint resume initialization failed: %s", exc)
                checkpoint_manager = None
                checkpoint_workflow_id = None
                completed_problem_keys = set()
                resumed_task_count = 0

        def save_progress_checkpoint(description: str) -> None:
            """Persist benchmark runtime progress when checkpointing is enabled."""
            if not checkpoint_manager or not checkpoint_workflow_id:
                return
            try:
                step = len(completed_problem_keys)
                checkpoint_state: Dict[str, Any] = {
                    "run_id": runtime_options.run_id,
                    "benchmark_name": self.benchmark.name,
                    "total_problems": len(self.benchmark.problems),
                    "completed_problem_keys": sorted(completed_problem_keys),
                    "results": list(results),
                    "updated_at_utc": datetime.utcnow().isoformat() + "Z",
                }
                checkpoint_manager.save(
                    workflow_id=checkpoint_workflow_id,
                    state=checkpoint_state,
                    step=step,
                    description=description,
                )
                checkpoint_manager.cleanup(checkpoint_workflow_id, keep=20)
            except Exception as exc:
                logger.warning("Failed to persist checkpoint state: %s", exc)

        async def run_one(
            problem: Dict[str, Any], idx: int, scheduler: BenchmarkRuntimeScheduler
        ):
            nonlocal assigned_gpu_tasks, cpu_fallback_tasks, total_gpu_tokens
            nonlocal oom_retry_attempts, tasks_with_oom

            task_id = scheduler.resolve_task_id(problem, idx)
            problem_resume_key = self._build_problem_resume_key(task_id, idx)
            max_retries = max(0, int(runtime_options.oom_max_retries))
            retry_backoff = max(0.0, float(runtime_options.oom_retry_backoff_seconds))
            force_cpu_after = max(0, int(runtime_options.oom_force_cpu_after))
            force_cpu = False
            excluded_gpu_ids: List[int] = []

            for attempt in range(max_retries + 1):
                retry_state = {
                    "attempt": attempt,
                    "force_cpu": force_cpu,
                    "excluded_gpu_ids": excluded_gpu_ids,
                }
                assignment, lease = await scheduler.assign_runtime(
                    problem,
                    idx,
                    retry_state=retry_state,
                )
                if assignment.assigned_device == "gpu":
                    assigned_gpu_tasks += 1
                    total_gpu_tokens += assignment.gpu_tokens
                elif assignment.profile.get("requested_device") == "gpu":
                    cpu_fallback_tasks += 1
                queue_waits.append(assignment.queue_wait_seconds)

                async def eval_with_runtime(task: Any, *args, **inner_kwargs):
                    bound_task = self._inject_runtime_hint(task, assignment)
                    return await eval_fn(bound_task, *args, **inner_kwargs)

                result_payload: Any = None
                raised_exc: Optional[Exception] = None
                should_retry = False
                error_message = ""
                execution_started_at = time.perf_counter()
                try:
                    result_payload = await self._call_evaluate_problem(
                        problem,
                        eval_with_runtime,
                        eval_kwargs,
                    )
                    error_message = self._extract_error_message(result_payload)
                    if self._is_oom_error(error_message) and attempt < max_retries:
                        should_retry = True
                    elif self._is_timeout_error(error_message) and attempt < 1:
                        should_retry = True
                except Exception as exc:
                    raised_exc = exc
                    if self._is_oom_error(exc) and attempt < max_retries:
                        should_retry = True
                    elif self._is_timeout_error(exc) and attempt < 1:
                        should_retry = True
                    else:
                        raise
                finally:
                    execution_elapsed = max(0.0, time.perf_counter() - execution_started_at)
                    scheduler.release_runtime(assignment, lease)
                    scheduler.record_task_completion(
                        runtime_seconds=execution_elapsed,
                        queue_wait_seconds=assignment.queue_wait_seconds,
                        had_error=bool(raised_exc) or bool(error_message),
                        # Retry attempts should contribute to runtime/error signals,
                        # but not to user-facing completed-task progress.
                        count_as_completed=not should_retry,
                    )

                if should_retry:
                    task_id = str(assignment.task_id)
                    if task_id not in task_ids_with_oom:
                        task_ids_with_oom.add(task_id)
                        tasks_with_oom += 1
                    oom_retry_attempts += 1
                    scheduler.record_oom(assignment)
                    if assignment.assigned_gpu is not None:
                        excluded_gpu_ids.append(int(assignment.assigned_gpu))
                    if (
                        force_cpu_after > 0
                        and attempt + 1 >= force_cpu_after
                        and assignment.profile.get(
                            "allow_cpu_fallback", runtime_options.auto_fallback_to_cpu
                        )
                    ):
                        force_cpu = True
                    if retry_backoff > 0:
                        await asyncio.sleep(retry_backoff * (attempt + 1))
                    continue

                if raised_exc is not None:
                    raise raised_exc
                return problem_resume_key, result_payload

            raise RuntimeError(
                f"Task {task_id} exhausted retries without completion."
            )

        async def execute_all_tasks(scheduler: BenchmarkRuntimeScheduler):
            nonlocal results, queue_waits, assigned_gpu_tasks, cpu_fallback_tasks
            nonlocal total_gpu_tokens, oom_retry_attempts, tasks_with_oom, task_ids_with_oom

            ordered_problems = scheduler.order_problems()
            pending_problems: List[Tuple[int, Dict[str, Any]]] = []
            for idx, problem in ordered_problems:
                task_id = scheduler.resolve_task_id(problem, idx)
                problem_resume_key = self._build_problem_resume_key(task_id, idx)
                if problem_resume_key in completed_problem_keys:
                    continue
                pending_problems.append((idx, problem))

            if completed_problem_keys:
                logger.info(
                    "Resuming benchmark run_id=%s: completed=%s pending=%s total=%s",
                    runtime_options.run_id,
                    len(completed_problem_keys),
                    len(pending_problems),
                    len(ordered_problems),
                )

            tasks = [
                run_one(problem, idx, scheduler)
                for idx, problem in pending_problems
            ]

            for future in asyncio.as_completed(tasks):
                try:
                    problem_resume_key, task_result = await future
                    result_tuple, report, error_message = task_result
                    results.append(result_tuple)
                    completed_problem_keys.add(problem_resume_key)
                    save_progress_checkpoint(
                        description=(
                            f"progress {len(completed_problem_keys)}/{len(self.benchmark.problems)}"
                        )
                    )
                except Exception as e:
                    logger.error(
                        "An unexpected error occurred in evaluate_problem: %s",
                        e,
                        exc_info=True,
                    )

        benchmark_started_at_utc = datetime.utcnow().isoformat() + "Z"
        benchmark_started_at_perf = time.perf_counter()

        # Use MonitoringIntegration for running with monitoring
        from dslighting.benchmark.core.monitoring_integration import MonitoringIntegration
        scheduler = await MonitoringIntegration.run_with_monitoring(
            self.benchmark.problems,
            scheduler_options=runtime_options,
        )
        await execute_all_tasks(scheduler)
        save_progress_checkpoint(description="benchmark_complete")

        benchmark_ended_at_perf = time.perf_counter()
        benchmark_ended_at_utc = datetime.utcnow().isoformat() + "Z"
        benchmark_wall_clock_elapsed_seconds = max(
            0.0,
            benchmark_ended_at_perf - benchmark_started_at_perf,
        )

        df = pd.DataFrame(results, columns=self.benchmark.get_result_columns())
        df.to_csv(self.benchmark.results_path, index=False)

        scheduler_capacity = scheduler.capacity_snapshot()
        scheduler_stats = {
            "scheduler_policy": runtime_options.scheduler_policy,
            "queue_policy": runtime_options.queue_policy,
            "workload_mode": runtime_options.workload_mode,
            "gpu_policy": runtime_options.gpu_policy,
            "max_concurrency": runtime_options.max_concurrency,
            "avg_queue_wait_seconds": (
                sum(queue_waits) / len(queue_waits) if queue_waits else 0.0
            ),
            "max_queue_wait_seconds": max(queue_waits) if queue_waits else 0.0,
            "assigned_gpu_tasks": assigned_gpu_tasks,
            "cpu_fallback_tasks": cpu_fallback_tasks,
            "total_gpu_tokens": total_gpu_tokens,
            "sandbox_memory_mode": runtime_options.sandbox_memory_mode,
            "sandbox_default_memory_gb": runtime_options.sandbox_default_memory_gb,
            "gpu_reserved_memory_gb": runtime_options.gpu_reserved_memory_gb,
            "gpu_memory_headroom_check": runtime_options.gpu_memory_headroom_check,
            "gpu_memory_probe_interval_seconds": runtime_options.gpu_memory_probe_interval_seconds,
            "allocator_poll_interval_seconds": runtime_options.allocator_poll_interval_seconds,
            "llm_max_concurrency": runtime_options.llm_max_concurrency,
            "oom_max_retries": runtime_options.oom_max_retries,
            "oom_retry_attempts": oom_retry_attempts,
            "tasks_with_oom": tasks_with_oom,
            "gpu_cooldown_seconds": runtime_options.gpu_cooldown_seconds,
            "cpu_worker_pool_size": scheduler_capacity.get(
                "cpu_worker_pool_size", runtime_options.cpu_worker_pool_size
            ),
            "enable_adaptive_concurrency": runtime_options.enable_adaptive_concurrency,
            "adaptive_target_p95_seconds": runtime_options.adaptive_target_p95_seconds,
            "adaptive_adjust_interval_seconds": runtime_options.adaptive_adjust_interval_seconds,
            "adaptive_increase_step": runtime_options.adaptive_increase_step,
            "adaptive_decrease_factor": runtime_options.adaptive_decrease_factor,
            "adaptive_min_concurrency": runtime_options.adaptive_min_concurrency,
            "adaptive_max_concurrency": runtime_options.adaptive_max_concurrency,
            "enable_task_rate_limiting": runtime_options.enable_task_rate_limiting,
            "llm_task_start_rate": runtime_options.llm_task_start_rate,
            "sandbox_task_start_rate": runtime_options.sandbox_task_start_rate,
            "task_rate_burst_factor": runtime_options.task_rate_burst_factor,
            "enable_dual_token_bucket": runtime_options.enable_dual_token_bucket,
            "llm_token_rate": runtime_options.llm_token_rate,
            "sandbox_token_rate": runtime_options.sandbox_token_rate,
            "token_bucket_burst": runtime_options.token_bucket_burst,
            "warmup_rounds": runtime_options.warmup_rounds,
            "checkpoint_resume_enabled": runtime_options.checkpoint_resume_enabled,
            "run_id": runtime_options.run_id,
            "resumed_task_count": resumed_task_count,
            "checkpoint_workflow_id": checkpoint_workflow_id,
            "runtime_counters": scheduler.runtime_counters(),
            "adaptive_trace": scheduler.adaptive_trace(),
            "warmup": warmup_stats,
            "capacity": scheduler_capacity,
        }

        dag_runtime_stats = self._collect_runner_dag_aggregate()
        if dag_runtime_stats:
            scheduler_stats["dag_runtime"] = dag_runtime_stats

        self.benchmark._write_metadata_json(
            df,
            scheduler_stats=scheduler_stats,
            benchmark_wall_clock_elapsed_seconds=benchmark_wall_clock_elapsed_seconds,
            benchmark_started_at_utc=benchmark_started_at_utc,
            benchmark_ended_at_utc=benchmark_ended_at_utc,
            **kwargs,
        )

        logger.info("Evaluation complete. Results saved to %s", self.benchmark.results_path)
        return results
