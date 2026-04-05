"""Unified Benchmark Base

Problem-based benchmark runner used by DSLighting and DSLighting-style benchmarks.
Each benchmark provides a list of problems and implements:
- get_result_columns()
- evaluate_problem(problem, eval_fn, **kwargs)

Optional Dependencies:
- DABenchmark, MLEBenchmark, ScienceBenchBenchmark are optional integrations.
  They are loaded lazily when needed. If not available, benchmarks will
  gracefully degrade to using only core functionality.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from dslighting.benchmark.core.abstract_base import AbstractBenchmark, AbstractTaskEvaluator
from dslighting.benchmark.core.async_runner import AsyncEvaluationRunner
from dslighting.benchmark.core.preflight import run_preflight_checks
from dslighting.benchmark.core.scheduler_core import (
    BenchmarkRuntimeScheduler,
    RuntimeAssignment,
    RuntimeSchedulerOptions,
)

logger = logging.getLogger(__name__)


__all__ = [
    "BaseBenchmark",
    "BenchmarkTaskEvaluator",
]


class BenchmarkTaskEvaluator(AbstractTaskEvaluator):
    """Base class for task evaluation logic.

    This class provides common functionality for evaluating tasks
    and processing results. Subclasses can override the evaluate
    method to provide specific evaluation logic.

    Attributes:
        RESULT_COLUMNS: Default result column names.
    """

    RESULT_COLUMNS = [
        "task_id",
        "score",
        "cost",
        "duration",
        "output",
        "error",
        "metadata",
    ]

    def __init__(self) -> None:
        """Initialize the task evaluator."""
        super().__init__()

    async def evaluate(
        self,
        task: Any,
        eval_fn: Callable,
        **kwargs: Any,
    ) -> Tuple[Any, Optional[Any], Optional[str]]:
        """Evaluate a single task.

        Args:
            task: Task to evaluate.
            eval_fn: Evaluation function to call.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple of (result_row, report, error_message).
        """
        error_message = None

        try:
            result = await eval_fn(task, **kwargs)
        except Exception as exc:
            result = {}
            error_message = str(exc)

        return self._process_result(task, result, error_message)


class BaseBenchmark(AbstractBenchmark):
    """Abstract base class for all benchmark tests.

    This base class expects subclasses to provide a list of problems (dicts)
    and implement evaluation logic that returns a tuple matching
    get_result_columns().

    Attributes:
        name: Benchmark name.
        file_path: Path to JSONL file with problems.
        log_path: Directory for output logs.
        problems: List of problem dictionaries.
        results_path: Path to results CSV.
        metadata_path: Path to metadata JSON.
        mismatches_path: Path to mismatches log.
    """

    def __init__(self, name: str, file_path: Optional[str], log_path: str, **kwargs: Any):
        """Initialize the benchmark.

        Args:
            name: Benchmark name.
            file_path: Path to JSONL file with problems.
            log_path: Directory for output logs.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(name, file_path, log_path, **kwargs)
        run_preflight_checks()
        self._runner = AsyncEvaluationRunner(self)

    def _load_problems(self) -> List[Dict[str, Any]]:
        """Load problems from jsonl file if provided."""
        if not self.file_path:
            logger.debug("No file_path provided. Subclass is expected to override _load_problems.")
            return []

        with open(self.file_path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def get_result_columns(self) -> List[str]:
        raise NotImplementedError

    async def evaluate_problem(self, problem: Dict[str, Any], eval_fn: Callable, **kwargs: Any) -> Tuple:
        raise NotImplementedError

    def set_eval_function(self, eval_fn: Callable) -> None:
        """Bind a default task-evaluation function for no-arg run_evaluation()."""
        self._default_eval_fn = eval_fn

    def log_mismatch(self, **kwargs: Any) -> None:
        """Log a mismatch to the mismatches log file."""
        with open(self.mismatches_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(kwargs) + "\n")

    @staticmethod
    def _inject_runtime_hint(task: Any, assignment: RuntimeAssignment) -> Any:
        """Attach scheduler runtime hints to a TaskDefinition payload when possible."""
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
    def _split_runtime_kwargs(kwargs: Dict[str, Any]) -> Tuple[RuntimeSchedulerOptions, Dict[str, Any]]:
        """Extract runtime scheduler kwargs while keeping legacy kwargs for eval_fn."""
        return AsyncEvaluationRunner._split_runtime_kwargs(kwargs)

    async def _call_evaluate_problem(
        self, problem: Dict[str, Any], eval_fn: Callable, eval_kwargs: Dict[str, Any]
    ) -> Tuple:
        """Call evaluate_problem while preserving compatibility with varying signatures."""
        fn = self.evaluate_problem
        sig = inspect.signature(fn)
        accepts_var_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in sig.parameters.values()
        )
        if accepts_var_kwargs:
            return await fn(problem, eval_fn=eval_fn, **eval_kwargs)

        accepted_kwargs = {
            key: value for key, value in eval_kwargs.items() if key in sig.parameters
        }
        return await fn(problem, eval_fn=eval_fn, **accepted_kwargs)

    @staticmethod
    def _extract_error_message(result: Any) -> str:
        """Try to read error_message from evaluate_problem return tuple."""
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
        """Check if error message indicates OOM."""
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
        """Check if error message indicates timeout."""
        text = str(message or "").lower()
        if not text:
            return False
        markers = (
            "timed out",
            "timeout",
            "wrk-003",
        )
        return any(marker in text for marker in markers)

    def _warmup_perception_cache(self, rounds: int) -> Dict[str, Any]:
        """Warmup DataAnalyzer cache based on known benchmark problem layout."""
        return self._runner._warmup_perception_cache(rounds)

    async def _run_evaluation_async(self, eval_fn: Callable, **kwargs: Any):
        """Run the entire benchmark evaluation asynchronously."""
        return await self._runner.run_async(eval_fn, **kwargs)

    def run_evaluation(
        self,
        eval_fn: Optional[Callable] = None,
        *,
        scheduler_options: Optional[Any] = None,
        max_concurrency: Optional[int] = None,
        scheduler_policy: str = "full_parallel",
        queue_policy: str = "fifo",
        workload_mode: str = "auto",
        gpu_policy: str = "auto",
        gpu_ids: Optional[List[int]] = None,
        gpu_max_tasks_per_device: Optional[int] = None,
        auto_tune_gpu_slots: bool = True,
        gpu_memory_utilization_target: float = 0.85,
        sandbox_memory_mode: str = "off",
        sandbox_default_memory_gb: Optional[float] = None,
        gpu_reserved_memory_gb: float = 2.0,
        gpu_memory_headroom_check: bool = True,
        gpu_memory_probe_interval_seconds: float = 0.75,
        allocator_poll_interval_seconds: float = 0.1,
        llm_max_concurrency: Optional[int] = None,
        oom_max_retries: int = 1,
        oom_retry_backoff_seconds: float = 2.0,
        oom_retry_memory_growth: float = 1.35,
        oom_force_cpu_after: int = 1,
        gpu_cooldown_seconds: float = 30.0,
        cpu_worker_pool_size: Optional[int] = None,
        auto_fallback_to_cpu: bool = True,
        task_resource_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        shadow_scheduler: bool = False,
        enable_adaptive_concurrency: bool = False,
        adaptive_target_p95_seconds: float = 45.0,
        adaptive_adjust_interval_seconds: float = 5.0,
        adaptive_increase_step: int = 1,
        adaptive_decrease_factor: float = 0.7,
        adaptive_min_concurrency: Optional[int] = None,
        adaptive_max_concurrency: Optional[int] = None,
        enable_task_rate_limiting: Optional[bool] = None,
        llm_task_start_rate: Optional[float] = None,
        sandbox_task_start_rate: Optional[float] = None,
        task_rate_burst_factor: Optional[float] = None,
        enable_dual_token_bucket: bool = False,
        llm_token_rate: Optional[float] = None,
        sandbox_token_rate: Optional[float] = None,
        token_bucket_burst: float = 2.0,
        warmup_rounds: int = 0,
        **kwargs,
    ):
        """Run benchmark evaluation.

        Usage:
            - benchmark.run_evaluation(eval_fn) (explicit callback)
            - benchmark.run_evaluation() after binding default callback via
              constructor (eval_fn=) or set_eval_function(...).

        Args:
            eval_fn: Evaluation function to use.
            scheduler_options: RuntimeSchedulerOptions instance.
            max_concurrency: Maximum concurrent tasks.
            scheduler_policy: Scheduling policy.
            queue_policy: Queue ordering policy.
            workload_mode: Workload type.
            gpu_policy: GPU allocation policy.
            gpu_ids: List of GPU IDs.
            gpu_max_tasks_per_device: Max tasks per GPU.
            auto_tune_gpu_slots: Whether to auto-tune GPU slots.
            gpu_memory_utilization_target: Target GPU memory utilization.
            sandbox_memory_mode: Sandbox memory mode.
            sandbox_default_memory_gb: Default sandbox memory.
            gpu_reserved_memory_gb: Reserved GPU memory.
            gpu_memory_headroom_check: Whether to check GPU memory headroom.
            gpu_memory_probe_interval_seconds: GPU memory probe interval.
            allocator_poll_interval_seconds: Allocator poll interval.
            llm_max_concurrency: Max LLM concurrency.
            oom_max_retries: Max OOM retry attempts.
            oom_retry_backoff_seconds: OOM retry backoff.
            oom_retry_memory_growth: OOM retry memory growth.
            oom_force_cpu_after: Force CPU after N OOMs.
            gpu_cooldown_seconds: GPU cooldown period.
            cpu_worker_pool_size: CPU worker pool size.
            auto_fallback_to_cpu: Whether to auto-fallback to CPU.
            task_resource_overrides: Per-task resource overrides.
            shadow_scheduler: Whether to run shadow scheduler.
            enable_adaptive_concurrency: Whether to enable adaptive concurrency.
            adaptive_target_p95_seconds: Adaptive target P95.
            adaptive_adjust_interval_seconds: Adaptive adjustment interval.
            adaptive_increase_step: Adaptive increase step.
            adaptive_decrease_factor: Adaptive decrease factor.
            adaptive_min_concurrency: Adaptive minimum concurrency.
            adaptive_max_concurrency: Adaptive maximum concurrency.
            enable_task_rate_limiting: Whether to enable task start rate limiting.
            llm_task_start_rate: Task start rate limiter for expected LLM pressure.
            sandbox_task_start_rate: Task start rate limiter for expected sandbox pressure.
            task_rate_burst_factor: Burst factor for task start rate limiting.
            enable_dual_token_bucket: Deprecated alias for enable_task_rate_limiting.
            llm_token_rate: Deprecated alias for llm_task_start_rate.
            sandbox_token_rate: Deprecated alias for sandbox_task_start_rate.
            token_bucket_burst: Deprecated alias for task_rate_burst_factor.
            warmup_rounds: Number of warmup rounds.
            **kwargs: Additional keyword arguments.
        """
        resolved_eval_fn = eval_fn or self._default_eval_fn
        if resolved_eval_fn is None:
            raise ValueError(
                "run_evaluation() requires an eval function. "
                "Pass one explicitly or bind it via `set_eval_function(...)`."
            )

        runtime_kwargs: Dict[str, Any] = {}
        if scheduler_options is not None:
            runtime_kwargs["scheduler_options"] = scheduler_options
        if max_concurrency is not None:
            runtime_kwargs["max_concurrency"] = max_concurrency
        if scheduler_policy != "full_parallel":
            runtime_kwargs["scheduler_policy"] = scheduler_policy
        if queue_policy != "fifo":
            runtime_kwargs["queue_policy"] = queue_policy
        if workload_mode != "auto":
            runtime_kwargs["workload_mode"] = workload_mode
        if gpu_policy != "auto":
            runtime_kwargs["gpu_policy"] = gpu_policy
        if gpu_ids is not None:
            runtime_kwargs["gpu_ids"] = gpu_ids
        if gpu_max_tasks_per_device is not None:
            runtime_kwargs["gpu_max_tasks_per_device"] = gpu_max_tasks_per_device
        if auto_tune_gpu_slots is not True:
            runtime_kwargs["auto_tune_gpu_slots"] = auto_tune_gpu_slots
        if gpu_memory_utilization_target != 0.85:
            runtime_kwargs["gpu_memory_utilization_target"] = gpu_memory_utilization_target
        if sandbox_memory_mode != "off":
            runtime_kwargs["sandbox_memory_mode"] = sandbox_memory_mode
        if sandbox_default_memory_gb is not None:
            runtime_kwargs["sandbox_default_memory_gb"] = sandbox_default_memory_gb
        if gpu_reserved_memory_gb != 2.0:
            runtime_kwargs["gpu_reserved_memory_gb"] = gpu_reserved_memory_gb
        if gpu_memory_headroom_check is not True:
            runtime_kwargs["gpu_memory_headroom_check"] = gpu_memory_headroom_check
        if gpu_memory_probe_interval_seconds != 0.75:
            runtime_kwargs["gpu_memory_probe_interval_seconds"] = gpu_memory_probe_interval_seconds
        if allocator_poll_interval_seconds != 0.1:
            runtime_kwargs["allocator_poll_interval_seconds"] = allocator_poll_interval_seconds
        if llm_max_concurrency is not None:
            runtime_kwargs["llm_max_concurrency"] = llm_max_concurrency
        if oom_max_retries != 1:
            runtime_kwargs["oom_max_retries"] = oom_max_retries
        if oom_retry_backoff_seconds != 2.0:
            runtime_kwargs["oom_retry_backoff_seconds"] = oom_retry_backoff_seconds
        if oom_retry_memory_growth != 1.35:
            runtime_kwargs["oom_retry_memory_growth"] = oom_retry_memory_growth
        if oom_force_cpu_after != 1:
            runtime_kwargs["oom_force_cpu_after"] = oom_force_cpu_after
        if gpu_cooldown_seconds != 30.0:
            runtime_kwargs["gpu_cooldown_seconds"] = gpu_cooldown_seconds
        if cpu_worker_pool_size is not None:
            runtime_kwargs["cpu_worker_pool_size"] = cpu_worker_pool_size
        if auto_fallback_to_cpu is not True:
            runtime_kwargs["auto_fallback_to_cpu"] = auto_fallback_to_cpu
        if task_resource_overrides is not None:
            runtime_kwargs["task_resource_overrides"] = task_resource_overrides
        if shadow_scheduler:
            runtime_kwargs["shadow_scheduler"] = shadow_scheduler
        if enable_adaptive_concurrency:
            runtime_kwargs["enable_adaptive_concurrency"] = enable_adaptive_concurrency
        if adaptive_target_p95_seconds != 45.0:
            runtime_kwargs["adaptive_target_p95_seconds"] = adaptive_target_p95_seconds
        if adaptive_adjust_interval_seconds != 5.0:
            runtime_kwargs["adaptive_adjust_interval_seconds"] = adaptive_adjust_interval_seconds
        if adaptive_increase_step != 1:
            runtime_kwargs["adaptive_increase_step"] = adaptive_increase_step
        if adaptive_decrease_factor != 0.7:
            runtime_kwargs["adaptive_decrease_factor"] = adaptive_decrease_factor
        if adaptive_min_concurrency is not None:
            runtime_kwargs["adaptive_min_concurrency"] = adaptive_min_concurrency
        if adaptive_max_concurrency is not None:
            runtime_kwargs["adaptive_max_concurrency"] = adaptive_max_concurrency
        if enable_task_rate_limiting is not None:
            runtime_kwargs["enable_task_rate_limiting"] = enable_task_rate_limiting
        if llm_task_start_rate is not None:
            runtime_kwargs["llm_task_start_rate"] = llm_task_start_rate
        if sandbox_task_start_rate is not None:
            runtime_kwargs["sandbox_task_start_rate"] = sandbox_task_start_rate
        if task_rate_burst_factor is not None:
            runtime_kwargs["task_rate_burst_factor"] = task_rate_burst_factor
        if enable_dual_token_bucket:
            runtime_kwargs["enable_dual_token_bucket"] = enable_dual_token_bucket
        if llm_token_rate is not None:
            runtime_kwargs["llm_token_rate"] = llm_token_rate
        if sandbox_token_rate is not None:
            runtime_kwargs["sandbox_token_rate"] = sandbox_token_rate
        if token_bucket_burst != 2.0:
            runtime_kwargs["token_bucket_burst"] = token_bucket_burst
        if warmup_rounds > 0:
            runtime_kwargs["warmup_rounds"] = warmup_rounds

        coro = self._run_evaluation_async(
            resolved_eval_fn,
            **runtime_kwargs,
            **kwargs,
        )

        async def _run_with_litellm_cleanup():
            try:
                return await coro
            finally:
                await self._close_litellm_async_clients()

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run_with_litellm_cleanup())
        return _run_with_litellm_cleanup()

    def run_evaluation_sync(self, eval_fn: Callable, **kwargs: Any):
        """Synchronous wrapper for benchmark evaluation.

        This keeps asyncio details inside the framework so end-user scripts can
        call a plain blocking API.

        Args:
            eval_fn: Evaluation function.
            **kwargs: Additional keyword arguments.
        """
        return self.run_evaluation(eval_fn, **kwargs)

    async def _close_litellm_async_clients(self) -> None:
        """Close LiteLLM async clients to avoid unclosed aiohttp session warnings."""
        try:
            import litellm

            close_fn = getattr(litellm, "close_litellm_async_clients", None)
            if not callable(close_fn):
                return

            result = close_fn()
            if inspect.isawaitable(result):
                await result
        except Exception as exc:
            logger.debug("Failed to close LiteLLM async clients cleanly: %s", exc)

    def _resolve_model_name_for_metadata(self, explicit_model_name: Optional[str] = None) -> str:
        """Resolve model name for CSV metadata."""
        return super()._resolve_model_name_for_metadata(explicit_model_name)

    def _write_metadata_json(self, df: pd.DataFrame, **kwargs: Any) -> None:
        """Write benchmark metadata summary to a standalone JSON file."""
        try:
            score_col = 'score' if 'score' in df.columns else None
            cost_col = 'cost' if 'cost' in df.columns else None
            running_time_col = 'running_time' if 'running_time' in df.columns else None
            input_tokens_col = 'input_tokens' if 'input_tokens' in df.columns else None
            output_tokens_col = 'output_tokens' if 'output_tokens' in df.columns else None
            total_tokens_col = 'total_tokens' if 'total_tokens' in df.columns else None

            stats: Dict[str, Any] = {}
            total_tasks = int(len(df))
            if score_col:
                score_series = pd.to_numeric(df[score_col], errors="coerce")
                valid_scores = score_series.dropna()
                if len(valid_scores) > 0:
                    stats['average_score'] = float(valid_scores.mean())
                    stats['actual_average_score'] = float(score_series.fillna(0.0).mean())
                    stats['scored_task_count'] = int(len(valid_scores))
                    stats['unscored_task_count'] = int(total_tasks - len(valid_scores))
                    stats['median_score'] = float(valid_scores.median())
                    stats['std_score'] = float(valid_scores.std())

            if cost_col:
                valid_costs = df[cost_col].dropna()
                if len(valid_costs) > 0:
                    stats['avg_cost'] = float(valid_costs.mean())
                    stats['total_cost'] = float(valid_costs.sum())

            if running_time_col:
                valid_times = df[running_time_col].dropna()
                if len(valid_times) > 0:
                    stats['avg_running_time'] = float(valid_times.mean())
                    stats['total_running_time'] = float(valid_times.sum())

            if input_tokens_col:
                valid_input_tokens = df[input_tokens_col].dropna()
                if len(valid_input_tokens) > 0:
                    stats['avg_input_tokens'] = float(valid_input_tokens.mean())
                    stats['total_input_tokens'] = float(valid_input_tokens.sum())

            if output_tokens_col:
                valid_output_tokens = df[output_tokens_col].dropna()
                if len(valid_output_tokens) > 0:
                    stats['avg_output_tokens'] = float(valid_output_tokens.mean())
                    stats['total_output_tokens'] = float(valid_output_tokens.sum())

            if total_tokens_col:
                valid_total_tokens = df[total_tokens_col].dropna()
                if len(valid_total_tokens) > 0:
                    stats['avg_total_tokens'] = float(valid_total_tokens.mean())
                    stats['total_total_tokens'] = float(valid_total_tokens.sum())

            exists_col = 'submission_exists' if 'submission_exists' in df.columns else None
            valid_submission_col = 'valid_submission' if 'valid_submission' in df.columns else None
            exists_series = None
            valid_series = None
            if exists_col:
                exists_series = df[exists_col].map(
                    lambda value: str(value).strip().lower() in {"1", "true", "yes", "on"}
                )
                exists_count = int(exists_series.sum())
                stats['submission_exists_count'] = exists_count
                stats['submission_exists_rate'] = float(exists_count / total_tasks) if total_tasks else 0.0
                missing_count = int(total_tasks - exists_count)
                stats['missing_submission_count'] = missing_count
                stats['missing_submission_rate'] = float(missing_count / total_tasks) if total_tasks else 0.0

            if valid_submission_col:
                valid_series = df[valid_submission_col].map(
                    lambda value: str(value).strip().lower() in {"1", "true", "yes", "on"}
                )
                valid_count = int(valid_series.sum())
                failed_count = int(total_tasks - valid_count)
                stats['valid_submission_count'] = valid_count
                stats['valid_submission_rate'] = float(valid_count / total_tasks) if total_tasks else 0.0
                stats['failed_submission_count'] = failed_count
                stats['failed_submission_rate'] = float(failed_count / total_tasks) if total_tasks else 0.0
                if exists_series is not None:
                    invalid_count = int((exists_series & ~valid_series).sum())
                    stats['invalid_submission_count'] = invalid_count
                    stats['invalid_submission_rate'] = float(invalid_count / total_tasks) if total_tasks else 0.0

            model_info = self._resolve_model_name_for_metadata(kwargs.get("model_name"))
            scheduler_stats = kwargs.get("scheduler_stats") or {}

            task_sum_running_time = stats.get("total_running_time")
            wall_clock_elapsed = kwargs.get("benchmark_wall_clock_elapsed_seconds")
            try:
                wall_clock_elapsed = (
                    float(wall_clock_elapsed) if wall_clock_elapsed is not None else None
                )
            except (TypeError, ValueError):
                wall_clock_elapsed = None

            metadata: Dict[str, Any] = {
                "model": model_info,
                "total_tasks": total_tasks,
                "score": {
                    "average": stats.get("average_score"),
                    "actual_average": stats.get("actual_average_score"),
                    "scored_task_count": stats.get("scored_task_count"),
                    "unscored_task_count": stats.get("unscored_task_count"),
                    "median": stats.get("median_score"),
                    "std": stats.get("std_score"),
                },
                "submissions": {
                    "exists_count": stats.get("submission_exists_count"),
                    "exists_rate": stats.get("submission_exists_rate"),
                    "valid_count": stats.get("valid_submission_count"),
                    "valid_rate": stats.get("valid_submission_rate"),
                    "failed_submission_count": stats.get("failed_submission_count"),
                    "failed_submission_rate": stats.get("failed_submission_rate"),
                    "missing_submission_count": stats.get("missing_submission_count"),
                    "missing_submission_rate": stats.get("missing_submission_rate"),
                    "invalid_submission_count": stats.get("invalid_submission_count"),
                    "invalid_submission_rate": stats.get("invalid_submission_rate"),
                },
                "cost": {
                    "average": stats.get("avg_cost"),
                    "total": stats.get("total_cost"),
                },
                "running_time_seconds": {
                    "average": stats.get("avg_running_time"),
                    "total": task_sum_running_time,
                    "task_sum_total": task_sum_running_time,
                    "wall_clock_elapsed": wall_clock_elapsed,
                },
                "tokens": {
                    "input": {
                        "average": stats.get("avg_input_tokens"),
                        "total": stats.get("total_input_tokens"),
                    },
                    "output": {
                        "average": stats.get("avg_output_tokens"),
                        "total": stats.get("total_output_tokens"),
                    },
                    "total": {
                        "average": stats.get("avg_total_tokens"),
                        "total": stats.get("total_total_tokens"),
                    },
                },
                "scheduler": scheduler_stats if isinstance(scheduler_stats, dict) else {},
                "evaluation_window": {
                    "started_at_utc": kwargs.get("benchmark_started_at_utc"),
                    "ended_at_utc": kwargs.get("benchmark_ended_at_utc"),
                    "wall_clock_elapsed_seconds": wall_clock_elapsed,
                },
                "results_csv": str(self.results_path),
                "mismatches_log": str(self.mismatches_path),
            }

            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                f.write("\n")

            logger.info("Metadata written to %s", self.metadata_path)
        except Exception as e:
            logger.warning("Failed to write metadata json: %s", e)
