"""Scheduler core module - contains BenchmarkRuntimeScheduler and RuntimeSchedulerOptions."""

from __future__ import annotations

import asyncio
import logging
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from dslighting.benchmark.core.admission_control import AdmissionController
from dslighting.benchmark.core.gpu_allocator import GpuAllocator
from dslighting.benchmark.core.queue_policies import create_queue_policy
from dslighting.benchmark.core.task_profile import (
    TaskResourceProfile,
    RuntimeAssignment,
    RuntimeLease,
)
from dslighting.benchmark.core.token_bucket import AsyncTokenBucket
from dslighting.utils.math import p95

logger = logging.getLogger(__name__)


__all__ = [
    "BenchmarkRuntimeScheduler",
    "RuntimeSchedulerOptions",
]


@dataclass
class RuntimeSchedulerOptions:
    """Runtime options for benchmark scheduling.

    Attributes:
        max_concurrency: Maximum number of concurrent tasks.
        scheduler_policy: Scheduling policy - "full_parallel", "balanced", or "conservative".
        queue_policy: Queue ordering policy - "fifo", "lpt_backfill", etc.
        workload_mode: Workload type - "auto", "dabench_fast", or "conservative".
        gpu_policy: GPU allocation policy - "auto", "manual", or "cpu_default".
        gpu_ids: List of GPU IDs to use.
        gpu_max_tasks_per_device: Maximum tasks per GPU.
        auto_tune_gpu_slots: Whether to auto-tune GPU slots.
        gpu_memory_utilization_target: Target GPU memory utilization (0.1-0.99).
        sandbox_memory_mode: Sandbox memory mode - "off", "fixed", or "token".
        sandbox_default_memory_gb: Default sandbox memory in GB.
        gpu_reserved_memory_gb: Reserved GPU memory in GB.
        gpu_memory_headroom_check: Whether to check GPU memory headroom.
        gpu_memory_probe_interval_seconds: Interval for GPU memory probing.
        allocator_poll_interval_seconds: Polling interval for allocator.
        llm_max_concurrency: Maximum LLM concurrency.
        oom_max_retries: Maximum OOM retry attempts.
        oom_retry_backoff_seconds: Backoff time between OOM retries.
        oom_retry_memory_growth: Memory growth factor between retries.
        oom_force_cpu_after: Force CPU fallback after N OOM errors.
        gpu_cooldown_seconds: GPU cooldown period after OOM.
        cpu_worker_pool_size: Size of CPU worker pool.
        auto_fallback_to_cpu: Whether to auto-fallback to CPU.
        task_resource_overrides: Per-task resource overrides.
        shadow_scheduler: Whether to run in shadow mode.
        enable_adaptive_concurrency: Whether to enable adaptive concurrency.
        adaptive_target_p95_seconds: Target P95 runtime for adaptive concurrency.
        adaptive_adjust_interval_seconds: Interval between adaptive adjustments.
        adaptive_increase_step: Concurrency increase step for adaptive scaling.
        adaptive_decrease_factor: Concurrency decrease factor for adaptive scaling.
        adaptive_min_concurrency: Minimum concurrency for adaptive scaling.
        adaptive_max_concurrency: Maximum concurrency for adaptive scaling.
        enable_task_rate_limiting: Whether to enable task start rate limiting.
        llm_task_start_rate: Task start rate limiter derived from expected LLM pressure.
        sandbox_task_start_rate: Task start rate limiter derived from expected sandbox pressure.
        task_rate_burst_factor: Burst factor for task start rate limiting.
        warmup_rounds: Number of warmup rounds.
        enable_monitoring: Whether to enable monitoring.
        exp_name: Experiment name for monitoring.
        checkpoint_resume_enabled: Whether to enable checkpoint resume.
        run_id: Unique run identifier.
    """

    max_concurrency: Optional[int] = None
    scheduler_policy: str = "full_parallel"
    queue_policy: str = "fifo"
    workload_mode: str = "auto"
    gpu_policy: str = "auto"
    gpu_ids: Optional[List[int]] = None
    gpu_max_tasks_per_device: Optional[int] = None
    auto_tune_gpu_slots: bool = True
    gpu_memory_utilization_target: float = 0.85
    sandbox_memory_mode: str = "off"
    sandbox_default_memory_gb: Optional[float] = None
    gpu_reserved_memory_gb: float = 2.0
    gpu_memory_headroom_check: bool = True
    gpu_memory_probe_interval_seconds: float = 2.0
    allocator_poll_interval_seconds: float = 0.1
    llm_max_concurrency: Optional[int] = None
    oom_max_retries: int = 1
    oom_retry_backoff_seconds: float = 2.0
    oom_retry_memory_growth: float = 1.35
    oom_force_cpu_after: int = 1
    gpu_cooldown_seconds: float = 30.0
    cpu_worker_pool_size: Optional[int] = None
    auto_fallback_to_cpu: bool = True
    task_resource_overrides: Optional[Dict[str, Dict[str, Any]]] = None
    shadow_scheduler: bool = False
    enable_adaptive_concurrency: bool = False
    adaptive_target_p95_seconds: float = 60.0
    adaptive_adjust_interval_seconds: float = 5.0
    adaptive_increase_step: int = 1
    adaptive_decrease_factor: float = 0.85
    adaptive_min_concurrency: Optional[int] = None
    adaptive_max_concurrency: Optional[int] = None
    enable_task_rate_limiting: Optional[bool] = None
    llm_task_start_rate: Optional[float] = None
    sandbox_task_start_rate: Optional[float] = None
    task_rate_burst_factor: Optional[float] = None
    enable_dual_token_bucket: bool = False
    llm_token_rate: Optional[float] = None
    sandbox_token_rate: Optional[float] = None
    token_bucket_burst: float = 2.0
    warmup_rounds: int = 0
    enable_monitoring: bool = False
    exp_name: Optional[str] = None
    monitor_language: str = "zh"  # Language for monitoring UI (zh=中文, en=英文)
    enable_file_sharing: bool = True  # Enable file-based metric sharing
    checkpoint_resume_enabled: bool = False
    run_id: Optional[str] = None

    def normalize(self, problem_count: int) -> "RuntimeSchedulerOptions":
        """Normalize and validate scheduler options.

        Args:
            problem_count: Number of problems to schedule.

        Returns:
            Normalized RuntimeSchedulerOptions instance.
        """
        policy = (self.scheduler_policy or "full_parallel").strip().lower()
        if policy not in {"full_parallel", "balanced", "conservative"}:
            policy = "full_parallel"
        self.scheduler_policy = policy

        queue_policy = (self.queue_policy or "fifo").strip().lower()
        if queue_policy not in {"fifo", "lpt_backfill", "srpt_aging_backfill", "multilevel_feedback"}:
            queue_policy = "fifo"
        self.queue_policy = queue_policy

        # Auto-promote: a non-fifo queue_policy only has effect when there is an admission
        # queue (max_concurrency < problem_count). If the user requested ordered scheduling
        # but left scheduler_policy at the default "full_parallel" (which sets
        # max_concurrency = problem_count, bypassing the queue), silently promote to
        # "balanced" so the requested ordering actually takes effect.
        if queue_policy != "fifo" and policy == "full_parallel" and self.max_concurrency is None:
            policy = "balanced"
            self.scheduler_policy = policy
            logger.info(
                "queue_policy=%r requires an admission queue to take effect; "
                "scheduler_policy automatically promoted from 'full_parallel' to 'balanced'. "
                "Set scheduler_policy explicitly to suppress this promotion.",
                queue_policy,
            )

        workload_mode = (self.workload_mode or "auto").strip().lower()
        if workload_mode not in {"auto", "dabench_fast", "conservative"}:
            workload_mode = "auto"
        self.workload_mode = workload_mode

        gpu_policy = (self.gpu_policy or "auto").strip().lower()
        if gpu_policy not in {"auto", "manual", "cpu_default"}:
            gpu_policy = "auto"
        self.gpu_policy = gpu_policy

        if self.max_concurrency is None:
            if policy == "full_parallel":
                self.max_concurrency = max(1, problem_count)
            elif policy == "balanced":
                self.max_concurrency = max(1, min(problem_count, 4))
            else:
                self.max_concurrency = 1
        self.max_concurrency = max(1, int(self.max_concurrency))

        if self.gpu_max_tasks_per_device is not None:
            try:
                slots = int(self.gpu_max_tasks_per_device)
            except (TypeError, ValueError):
                slots = 1
            self.gpu_max_tasks_per_device = max(1, slots)

        try:
            target = float(self.gpu_memory_utilization_target)
        except (TypeError, ValueError):
            target = 0.85
        self.gpu_memory_utilization_target = min(max(target, 0.1), 0.99)

        memory_mode = (self.sandbox_memory_mode or "off").strip().lower()
        if memory_mode not in {"off", "fixed", "token"}:
            memory_mode = "off"
        self.sandbox_memory_mode = memory_mode

        if self.sandbox_default_memory_gb is not None:
            try:
                default_memory = float(self.sandbox_default_memory_gb)
            except (TypeError, ValueError):
                default_memory = None
            self.sandbox_default_memory_gb = default_memory if default_memory and default_memory > 0 else None

        try:
            reserved_memory = float(self.gpu_reserved_memory_gb)
        except (TypeError, ValueError):
            reserved_memory = 2.0
        self.gpu_reserved_memory_gb = max(0.0, reserved_memory)

        self.gpu_memory_headroom_check = bool(self.gpu_memory_headroom_check)
        try:
            probe_interval = float(self.gpu_memory_probe_interval_seconds)
        except (TypeError, ValueError):
            probe_interval = 0.75
        self.gpu_memory_probe_interval_seconds = max(0.05, probe_interval)

        try:
            poll_interval = float(self.allocator_poll_interval_seconds)
        except (TypeError, ValueError):
            poll_interval = 0.1
        self.allocator_poll_interval_seconds = max(0.01, poll_interval)

        if self.llm_max_concurrency is not None:
            try:
                llm_cap = int(self.llm_max_concurrency)
            except (TypeError, ValueError):
                llm_cap = 1
            self.llm_max_concurrency = max(1, llm_cap)

        self.oom_max_retries = max(0, int(self.oom_max_retries or 0))
        try:
            backoff = float(self.oom_retry_backoff_seconds)
        except (TypeError, ValueError):
            backoff = 2.0
        self.oom_retry_backoff_seconds = max(0.0, backoff)

        try:
            growth = float(self.oom_retry_memory_growth)
        except (TypeError, ValueError):
            growth = 1.35
        self.oom_retry_memory_growth = max(1.0, growth)

        self.oom_force_cpu_after = max(0, int(self.oom_force_cpu_after or 0))
        try:
            cooldown = float(self.gpu_cooldown_seconds)
        except (TypeError, ValueError):
            cooldown = 30.0
        self.gpu_cooldown_seconds = max(0.0, cooldown)

        if self.cpu_worker_pool_size is not None:
            try:
                cpu_pool = int(self.cpu_worker_pool_size)
            except (TypeError, ValueError):
                cpu_pool = self.max_concurrency
            self.cpu_worker_pool_size = max(1, cpu_pool)

        if self.task_resource_overrides is None:
            self.task_resource_overrides = {}

        self.enable_adaptive_concurrency = bool(self.enable_adaptive_concurrency)
        try:
            adaptive_target = float(self.adaptive_target_p95_seconds)
        except (TypeError, ValueError):
            adaptive_target = 45.0
        self.adaptive_target_p95_seconds = max(1.0, adaptive_target)

        try:
            adjust_interval = float(self.adaptive_adjust_interval_seconds)
        except (TypeError, ValueError):
            adjust_interval = 5.0
        self.adaptive_adjust_interval_seconds = max(0.5, adjust_interval)

        try:
            increase_step = int(self.adaptive_increase_step)
        except (TypeError, ValueError):
            increase_step = 1
        self.adaptive_increase_step = max(1, increase_step)

        try:
            decrease_factor = float(self.adaptive_decrease_factor)
        except (TypeError, ValueError):
            decrease_factor = 0.85
        self.adaptive_decrease_factor = min(max(decrease_factor, 0.1), 0.95)

        if self.adaptive_min_concurrency is None:
            self.adaptive_min_concurrency = max(4, int(self.max_concurrency * 0.3))
        else:
            try:
                self.adaptive_min_concurrency = max(1, int(self.adaptive_min_concurrency))
            except (TypeError, ValueError):
                self.adaptive_min_concurrency = max(4, int(self.max_concurrency * 0.3))

        if self.adaptive_max_concurrency is None:
            self.adaptive_max_concurrency = self.max_concurrency
        else:
            try:
                self.adaptive_max_concurrency = max(1, int(self.adaptive_max_concurrency))
            except (TypeError, ValueError):
                self.adaptive_max_concurrency = self.max_concurrency

        if self.adaptive_max_concurrency < self.adaptive_min_concurrency:
            self.adaptive_max_concurrency = self.adaptive_min_concurrency

        legacy_task_rate_enabled = bool(self.enable_dual_token_bucket)
        if self.enable_task_rate_limiting is None:
            self.enable_task_rate_limiting = legacy_task_rate_enabled
        else:
            self.enable_task_rate_limiting = bool(self.enable_task_rate_limiting)
            if legacy_task_rate_enabled and not self.enable_task_rate_limiting:
                raise ValueError(
                    "Conflicting task rate limiting options: "
                    "enable_task_rate_limiting=False but enable_dual_token_bucket=True."
                )
        if legacy_task_rate_enabled:
            logger.warning(
                "enable_dual_token_bucket is deprecated; use enable_task_rate_limiting instead."
            )
        self.enable_dual_token_bucket = self.enable_task_rate_limiting

        legacy_llm_task_rate = self.llm_token_rate
        if self.llm_task_start_rate is not None and legacy_llm_task_rate is not None:
            try:
                if float(self.llm_task_start_rate) != float(legacy_llm_task_rate):
                    raise ValueError(
                        "Conflicting task rate options: "
                        "llm_task_start_rate and llm_token_rate must match when both are set."
                    )
            except (TypeError, ValueError) as exc:
                if isinstance(exc, ValueError) and "Conflicting task rate options" in str(exc):
                    raise
        effective_llm_task_rate = (
            self.llm_task_start_rate
            if self.llm_task_start_rate is not None
            else legacy_llm_task_rate
        )
        if legacy_llm_task_rate is not None:
            logger.warning(
                "llm_token_rate is deprecated; use llm_task_start_rate instead."
            )
        if effective_llm_task_rate is not None:
            try:
                llm_rate = float(effective_llm_task_rate)
            except (TypeError, ValueError):
                llm_rate = 0.0
            self.llm_task_start_rate = llm_rate if llm_rate > 0 else None
        else:
            self.llm_task_start_rate = None
        self.llm_token_rate = self.llm_task_start_rate

        legacy_sandbox_task_rate = self.sandbox_token_rate
        if self.sandbox_task_start_rate is not None and legacy_sandbox_task_rate is not None:
            try:
                if float(self.sandbox_task_start_rate) != float(legacy_sandbox_task_rate):
                    raise ValueError(
                        "Conflicting task rate options: "
                        "sandbox_task_start_rate and sandbox_token_rate must match when both are set."
                    )
            except (TypeError, ValueError) as exc:
                if isinstance(exc, ValueError) and "Conflicting task rate options" in str(exc):
                    raise
        effective_sandbox_task_rate = (
            self.sandbox_task_start_rate
            if self.sandbox_task_start_rate is not None
            else legacy_sandbox_task_rate
        )
        if legacy_sandbox_task_rate is not None:
            logger.warning(
                "sandbox_token_rate is deprecated; use sandbox_task_start_rate instead."
            )
        if effective_sandbox_task_rate is not None:
            try:
                sandbox_rate = float(effective_sandbox_task_rate)
            except (TypeError, ValueError):
                sandbox_rate = 0.0
            self.sandbox_task_start_rate = sandbox_rate if sandbox_rate > 0 else None
        else:
            self.sandbox_task_start_rate = None
        self.sandbox_token_rate = self.sandbox_task_start_rate

        legacy_burst = self.token_bucket_burst
        if self.task_rate_burst_factor is not None and legacy_burst != 2.0:
            try:
                if float(self.task_rate_burst_factor) != float(legacy_burst):
                    raise ValueError(
                        "Conflicting task rate options: "
                        "task_rate_burst_factor and token_bucket_burst must match when both are set."
                    )
            except (TypeError, ValueError) as exc:
                if isinstance(exc, ValueError) and "Conflicting task rate options" in str(exc):
                    raise
        effective_burst = (
            self.task_rate_burst_factor
            if self.task_rate_burst_factor is not None
            else legacy_burst
        )
        if legacy_burst != 2.0:
            logger.warning(
                "token_bucket_burst is deprecated; use task_rate_burst_factor instead."
            )
        try:
            burst = float(2.0 if effective_burst is None else effective_burst)
        except (TypeError, ValueError):
            burst = 2.0
        self.task_rate_burst_factor = max(1.0, burst)
        self.token_bucket_burst = self.task_rate_burst_factor
        self.warmup_rounds = max(0, int(self.warmup_rounds or 0))

        if (
            problem_count > 1
            and self.scheduler_policy == "full_parallel"
            and self.queue_policy != "fifo"
            and self.max_concurrency >= problem_count
        ):
            logger.warning(
                "queue_policy=%r does not affect admission queue ordering when "
                "scheduler_policy='full_parallel' and max_concurrency=%d >= problem_count=%d; "
                "all tasks are submitted immediately and only the initial coroutine submission order remains. "
                "Use scheduler_policy='balanced' or set max_concurrency below problem_count "
                "to make queue ordering materially affect scheduling.",
                self.queue_policy,
                self.max_concurrency,
                problem_count,
            )
        return self


class BenchmarkRuntimeScheduler:
    """Task admission + runtime assignment helper for benchmark execution.

    This class manages task scheduling, GPU allocation, and admission control
    for benchmark execution.

    Attributes:
        problems: List of problems to schedule.
        options: RuntimeSchedulerOptions instance.
        allocator: GpuAllocator instance for GPU resource management.
    """

    def __init__(self, problems: List[Dict[str, Any]], options: RuntimeSchedulerOptions):
        """Initialize the benchmark runtime scheduler.

        Args:
            problems: List of problem dictionaries.
            options: RuntimeSchedulerOptions instance.
        """
        self.problems = problems
        self.options = options.normalize(problem_count=len(problems))
        self.allocator = GpuAllocator(
            policy=self.options.gpu_policy,
            gpu_ids=self.options.gpu_ids,
            slots_per_gpu=self.options.gpu_max_tasks_per_device,
            auto_tune_slots=self.options.auto_tune_gpu_slots,
            mem_target=self.options.gpu_memory_utilization_target,
            memory_mode=self.options.sandbox_memory_mode,
            default_memory_gb=self.options.sandbox_default_memory_gb,
            reserved_memory_gb=self.options.gpu_reserved_memory_gb,
            cooldown_seconds=self.options.gpu_cooldown_seconds,
            enable_mem_headroom_check=self.options.gpu_memory_headroom_check,
            mem_probe_interval_seconds=self.options.gpu_memory_probe_interval_seconds,
            allocation_poll_interval_seconds=self.options.allocator_poll_interval_seconds,
        )
        if not self.allocator.has_gpu:
            logger.info(
                "No GPU detected (gpu_ids=%r, CUDA_VISIBLE_DEVICES=%r). "
                "All gpu_* parameters are ignored. Running in CPU-only mode.",
                self.options.gpu_ids,
                os.environ.get("CUDA_VISIBLE_DEVICES"),
            )
        # Use AdmissionController for admission control logic
        self._admission_controller = AdmissionController(
            options=self.options,
            cpu_worker_pool_size=self.options.cpu_worker_pool_size,
        )
        self._oom_events = 0
        self._gpu_cooldown_events = 0
        self._tasks_completed = 0

        self._sandbox_token_bucket: Optional[AsyncTokenBucket] = None
        self._llm_token_bucket: Optional[AsyncTokenBucket] = None
        if self.options.enable_task_rate_limiting:
            sandbox_rate = self.options.sandbox_task_start_rate or float(max(1, self._cpu_worker_pool_size))
            llm_fallback = self.options.llm_max_concurrency or self.options.max_concurrency
            llm_rate = self.options.llm_task_start_rate or float(max(1, llm_fallback))
            self._sandbox_token_bucket = AsyncTokenBucket(
                rate_per_second=sandbox_rate,
                burst_tokens=max(1.0, sandbox_rate * self.options.task_rate_burst_factor),
            )
            self._llm_token_bucket = AsyncTokenBucket(
                rate_per_second=llm_rate,
                burst_tokens=max(1.0, llm_rate * self.options.task_rate_burst_factor),
            )

    # Delegate admission control properties to AdmissionController
    @property
    def _admission(self):
        return self._admission_controller._admission

    @property
    def _cpu_pool(self):
        return self._admission_controller._cpu_pool

    @property
    def _state_lock(self):
        return self._admission_controller._state_lock

    @property
    def _active_tasks(self):
        return self._admission_controller._active_tasks

    @property
    def _cpu_inflight(self):
        return self._admission_controller._cpu_inflight

    @property
    def _admission_limit(self):
        return self._admission_controller._admission_limit

    @property
    def _cpu_dynamic_limit(self):
        return self._admission_controller._cpu_dynamic_limit

    @property
    def _cpu_worker_pool_size(self):
        return self._admission_controller._cpu_worker_pool_size

    @property
    def _task_runtime_history(self):
        return self._admission_controller._task_runtime_history

    @property
    def _queue_wait_history(self):
        return self._admission_controller._queue_wait_history

    @property
    def _error_history(self):
        return self._admission_controller._error_history

    @property
    def _adaptive_trace(self):
        return self._admission_controller._adaptive_trace

    @property
    def _stability_counter(self):
        return self._admission_controller._stability_counter

    @property
    def _last_adaptive_adjust_at(self):
        return self._admission_controller._last_adaptive_adjust_at

    @property
    def _token_wait_events(self):
        return self._admission_controller._token_wait_events

    @property
    def _token_wait_seconds(self):
        return self._admission_controller._token_wait_seconds

    @property
    def _adaptive_adjustments(self):
        return self._admission_controller._adaptive_adjustments

    @_active_tasks.setter
    def _active_tasks(self, value):
        self._admission_controller._active_tasks = value

    @_cpu_inflight.setter
    def _cpu_inflight(self, value):
        self._admission_controller._cpu_inflight = value

    @_admission_limit.setter
    def _admission_limit(self, value):
        self._admission_controller._admission_limit = value

    @_cpu_dynamic_limit.setter
    def _cpu_dynamic_limit(self, value):
        self._admission_controller._cpu_dynamic_limit = value

    @_stability_counter.setter
    def _stability_counter(self, value):
        self._admission_controller._stability_counter = value

    @_last_adaptive_adjust_at.setter
    def _last_adaptive_adjust_at(self, value):
        self._admission_controller._last_adaptive_adjust_at = value

    @_adaptive_trace.setter
    def _adaptive_trace(self, value):
        self._admission_controller._adaptive_trace = value

    @staticmethod
    def resolve_task_id(problem: Dict[str, Any], fallback_idx: int) -> str:
        """Resolve task ID from problem dictionary.

        Args:
            problem: Problem dictionary containing task information.
            fallback_idx: Fallback index if no task ID found.

        Returns:
            Resolved task ID string.
        """
        if isinstance(problem, dict):
            if "competition_id" in problem and problem["competition_id"]:
                return str(problem["competition_id"])
            if "task_id" in problem and problem["task_id"]:
                return str(problem["task_id"])
            task_obj = problem.get("task")
            task_id = getattr(task_obj, "task_id", None)
            if task_id:
                return str(task_id)
        return f"task_{fallback_idx}"

    def _collect_task_resources(self, problem: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Collect task resources from problem and overrides.

        Args:
            problem: Problem dictionary.
            task_id: Task identifier.

        Returns:
            Dictionary of task resources.
        """
        resources: Dict[str, Any] = {}
        if isinstance(problem, dict) and isinstance(problem.get("resources"), dict):
            resources.update(problem["resources"])
        override = self.options.task_resource_overrides.get(task_id, {})
        if isinstance(override, dict):
            resources.update(override)
        return resources

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        """Coerce value to float.

        Args:
            value: Value to coerce.

        Returns:
            Float value or None if coercion fails.
        """
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        """Coerce value to int.

        Args:
            value: Value to coerce.
            default: Default value if coercion fails.

        Returns:
            Int value or default.
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _estimate_runtime_seconds(self, problem: Dict[str, Any], resources: Dict[str, Any]) -> float:
        """Estimate runtime for a task based on resources.

        Args:
            problem: Problem dictionary.
            resources: Task resources.

        Returns:
            Estimated runtime in seconds.
        """
        explicit = (
            self._coerce_float(resources.get("estimated_runtime_seconds"))
            or self._coerce_float(resources.get("expected_runtime_seconds"))
            or self._coerce_float(resources.get("runtime_seconds"))
        )
        if explicit and explicit > 0:
            return explicit

        dataset_mb = (
            self._coerce_float(resources.get("dataset_size_mb"))
            or self._coerce_float(resources.get("data_size_mb"))
            or self._coerce_float(resources.get("dataset_mb"))
        )
        num_rows = (
            self._coerce_float(resources.get("num_rows"))
            or self._coerce_float(resources.get("row_count"))
            or self._coerce_float(resources.get("n_rows"))
        )
        difficulty = self._coerce_int(resources.get("difficulty"), default=1)
        base = 5.0
        if dataset_mb is not None and dataset_mb > 0:
            base += min(900.0, dataset_mb) * 0.12
        if num_rows is not None and num_rows > 0:
            base += min(5_000_000.0, num_rows) / 150_000.0
        base += max(0, difficulty - 1) * 4.0
        mode = str(problem.get("mode", "")).lower() if isinstance(problem, dict) else ""
        if mode == "open_ended":
            base += 10.0
        return max(1.0, base)

    def _infer_workload_class(
        self,
        task_id: str,
        problem: Dict[str, Any],
        resources: Dict[str, Any],
        requested_device: str,
    ) -> str:
        """Infer workload class for a task.

        Args:
            task_id: Task identifier.
            problem: Problem dictionary.
            resources: Task resources.
            requested_device: Requested device type.

        Returns:
            Workload class string.
        """
        if requested_device == "gpu":
            return "gpu_bound"

        has_gpu_signal = any(
            resources.get(key) is not None
            for key in ("gpu_memory_gb", "gpu_id", "gpu_memory", "device")
        )
        if has_gpu_signal and str(resources.get("device", "")).strip().lower() == "gpu":
            return "gpu_bound"

        mode = str(problem.get("mode", "")).lower() if isinstance(problem, dict) else ""
        if mode == "open_ended":
            return "sandbox_heavy"

        is_dabench = task_id.startswith("dabench-")
        if self.options.workload_mode == "dabench_fast" and is_dabench:
            return "cpu_light_llm_heavy"
        if self.options.workload_mode == "auto" and is_dabench:
            return "cpu_light_llm_heavy"
        return "general"

    async def _reserve_admission_slot(self) -> None:
        """Reserve an admission slot, waiting if necessary."""
        await self._admission.acquire()
        poll_interval = max(0.01, self.options.allocator_poll_interval_seconds)
        while True:
            async with self._state_lock:
                if self._active_tasks < self._admission_limit:
                    self._active_tasks += 1
                    self._update_system_monitor()
                    return
            await asyncio.sleep(poll_interval)

    async def _reserve_cpu_slot(self) -> None:
        """Reserve a CPU slot, waiting if necessary."""
        await self._cpu_pool.acquire()
        poll_interval = max(0.01, self.options.allocator_poll_interval_seconds)
        while True:
            async with self._state_lock:
                if self._cpu_inflight < self._cpu_dynamic_limit:
                    self._cpu_inflight += 1
                    return
            await asyncio.sleep(poll_interval)

    def _release_admission_slot(self) -> None:
        """Release an admission slot."""
        self._active_tasks = max(0, self._active_tasks - 1)
        self._admission.release()
        self._update_system_monitor()

    def _release_cpu_slot(self) -> None:
        """Release a CPU slot."""
        self._cpu_inflight = max(0, self._cpu_inflight - 1)
        self._cpu_pool.release()

    async def _consume_token(self, bucket: AsyncTokenBucket, bucket_name: str) -> None:
        """Consume a token from the bucket.

        Args:
            bucket: Token bucket to consume from.
            bucket_name: Name for tracking wait events.
        """
        waited = await bucket.consume(1.0)
        if waited > 0:
            self._token_wait_events[bucket_name] += 1
            self._token_wait_seconds[bucket_name] += waited

    def _maybe_adjust_concurrency(self) -> None:
        """Adjust concurrency based on runtime history."""
        if not self.options.enable_adaptive_concurrency:
            return

        now = time.monotonic()
        if (now - self._last_adaptive_adjust_at) < self.options.adaptive_adjust_interval_seconds:
            return
        self._last_adaptive_adjust_at = now

        durations = list(self._task_runtime_history)
        queue_waits = list(self._queue_wait_history)
        errors = list(self._error_history)
        if not durations:
            return

        p95_runtime = p95(durations)
        avg_queue_wait = (sum(queue_waits) / len(queue_waits)) if queue_waits else 0.0
        error_rate = (sum(errors) / len(errors)) if errors else 0.0

        target = self.options.adaptive_target_p95_seconds
        min_cap = max(4, int(self.options.adaptive_min_concurrency or int(self.options.max_concurrency * 0.3)))
        max_cap = max(min_cap, int(self.options.adaptive_max_concurrency or self.options.max_concurrency))
        old_admission = self._admission_limit
        old_cpu = self._cpu_dynamic_limit
        action = "hold"

        overload = (
            error_rate >= 0.08
            or p95_runtime > target * 1.30
            or avg_queue_wait > target
        )
        underutilized = (
            error_rate <= 0.01
            and p95_runtime < target * 0.80
            and avg_queue_wait < target * 0.50
        )

        if overload:
            self._stability_counter += 1
            if self._stability_counter >= 3:
                reduced = max(min_cap, int(self._admission_limit * 0.85))
                self._admission_limit = max(min_cap, min(max_cap, reduced))
                cpu_reduced = max(1, int(self._cpu_dynamic_limit * 0.85))
                self._cpu_dynamic_limit = max(1, min(self._cpu_worker_pool_size, cpu_reduced))
                action = "decrease"
                self._stability_counter = 0
        elif underutilized:
            self._stability_counter = 0
            self._admission_limit = min(
                max_cap,
                self._admission_limit + self.options.adaptive_increase_step,
            )
            self._cpu_dynamic_limit = min(
                self._cpu_worker_pool_size,
                self._cpu_dynamic_limit + self.options.adaptive_increase_step,
            )
            action = "increase"
        else:
            self._stability_counter = 0

        if self._admission_limit != old_admission or self._cpu_dynamic_limit != old_cpu:
            self._adaptive_adjustments += 1

        self._adaptive_trace.append(
            {
                "ts": round(now, 3),
                "action": action,
                "p95_runtime_seconds": round(p95_runtime, 4),
                "avg_queue_wait_seconds": round(avg_queue_wait, 4),
                "error_rate": round(error_rate, 4),
                "admission_limit": self._admission_limit,
                "cpu_dynamic_limit": self._cpu_dynamic_limit,
                "stability_counter": self._stability_counter,
            }
        )
        if len(self._adaptive_trace) > 200:
            self._adaptive_trace = self._adaptive_trace[-200:]

    def record_task_completion(
        self,
        *,
        runtime_seconds: float,
        queue_wait_seconds: float,
        had_error: bool,
        count_as_completed: bool = True,
    ) -> None:
        """Record task completion for monitoring and adaptive concurrency.

        Args:
            runtime_seconds: Task execution time in seconds.
            queue_wait_seconds: Time spent waiting in queue.
            had_error: Whether the task encountered an error.
            count_as_completed: Whether this attempt should count toward
                user-facing completed task progress.
        """
        self._task_runtime_history.append(max(0.0, float(runtime_seconds)))
        self._queue_wait_history.append(max(0.0, float(queue_wait_seconds)))
        self._error_history.append(1 if had_error else 0)
        self._maybe_adjust_concurrency()

        if count_as_completed:
            self._tasks_completed += 1
        self._update_system_monitor()

    def build_profile(
        self,
        problem: Dict[str, Any],
        fallback_idx: int,
        retry_state: Optional[Dict[str, Any]] = None,
    ) -> TaskResourceProfile:
        """Build a task resource profile from problem data.

        Args:
            problem: Problem dictionary.
            fallback_idx: Fallback index for task ID.
            retry_state: Optional retry state dictionary.

        Returns:
            TaskResourceProfile instance.
        """
        task_id = self.resolve_task_id(problem, fallback_idx)
        resources = self._collect_task_resources(problem, task_id)

        requested = str(resources.get("device", "auto")).strip().lower()
        if requested not in {"auto", "gpu", "cpu"}:
            requested = "auto"

        workload_class = self._infer_workload_class(
            task_id=task_id,
            problem=problem,
            resources=resources,
            requested_device=requested,
        )

        if workload_class == "cpu_light_llm_heavy" and requested == "auto":
            requested = "cpu"
        if self.options.workload_mode == "conservative" and requested == "auto":
            requested = "cpu"

        profile = TaskResourceProfile(
            task_id=task_id,
            requested_device=requested,
            priority=self._coerce_int(resources.get("priority"), default=0),
            allow_cpu_fallback=bool(
                resources.get("allow_cpu_fallback", self.options.auto_fallback_to_cpu)
            ),
            gpu_id=resources.get("gpu_id"),
            gpu_memory_gb=self._coerce_float(resources.get("gpu_memory_gb")),
            estimated_runtime_seconds=self._estimate_runtime_seconds(problem, resources),
            dataset_size_mb=(
                self._coerce_float(resources.get("dataset_size_mb"))
                or self._coerce_float(resources.get("data_size_mb"))
            ),
            workload_class=workload_class,
        )
        if profile.gpu_id is not None:
            try:
                profile.gpu_id = int(profile.gpu_id)
            except (TypeError, ValueError):
                profile.gpu_id = None

        retry_state = retry_state or {}
        retry_attempt = self._coerce_int(retry_state.get("attempt"), default=0)
        if retry_attempt > 0 and profile.gpu_memory_gb is not None:
            profile.gpu_memory_gb = profile.gpu_memory_gb * (
                self.options.oom_retry_memory_growth ** retry_attempt
            )

        if retry_state.get("force_cpu"):
            profile.requested_device = "cpu"

        forced_gpu_id = retry_state.get("force_gpu_id")
        if forced_gpu_id is not None:
            try:
                profile.gpu_id = int(forced_gpu_id)
            except (TypeError, ValueError):
                pass
        return profile

    def order_problems(self) -> List[Tuple[int, Dict[str, Any]]]:
        """Order problems according to the configured queue policy.

        Returns:
            List of (index, problem) tuples in scheduled order.
        """
        policy = create_queue_policy(self.options.queue_policy, self)
        return policy.order(self.problems)

    def capacity_snapshot(self) -> Dict[str, Any]:
        """Get capacity and state snapshot.

        Returns:
            Dictionary containing scheduler capacity information.
        """
        return {
            "queue_policy": self.options.queue_policy,
            "admission_queue_enabled": self.options.max_concurrency < len(self.problems),
            "workload_mode": self.options.workload_mode,
            "sandbox_memory_mode": self.options.sandbox_memory_mode,
            "sandbox_memory_token_gb": self.allocator.token_size_gb,
            "gpu_reserved_memory_gb": self.options.gpu_reserved_memory_gb,
            "gpu_available": self.allocator.has_gpu,
            "cpu_only_mode": not self.allocator.has_gpu,
            "gpu_slots": self.allocator.slot_snapshot(),
            "gpu_token_capacity": self.allocator.token_capacity_snapshot(),
            "gpu_inflight": self.allocator.inflight_snapshot(),
            "gpu_cooldown_seconds": self.options.gpu_cooldown_seconds,
            "gpu_cooling": self.allocator.cooldown_snapshot(),
            "gpu_memory_probe": self.allocator.memory_probe_snapshot(),
            "cpu_worker_pool_size": self._cpu_worker_pool_size,
            "cpu_dynamic_limit": self._cpu_dynamic_limit,
            "admission_limit": self._admission_limit,
            "active_tasks": self._active_tasks,
            "cpu_inflight": self._cpu_inflight,
            "task_rate_limiting": {
                "enabled": self.options.enable_task_rate_limiting,
                "sandbox_task_start_rate": self.options.sandbox_task_start_rate,
                "llm_task_start_rate": self.options.llm_task_start_rate,
                "task_rate_burst_factor": self.options.task_rate_burst_factor,
                "wait_events": dict(self._token_wait_events),
                "wait_seconds": dict(self._token_wait_seconds),
            },
            "token_bucket": {
                "enabled": self.options.enable_dual_token_bucket,
                "sandbox_rate": self.options.sandbox_token_rate,
                "llm_rate": self.options.llm_token_rate,
                "wait_events": dict(self._token_wait_events),
                "wait_seconds": dict(self._token_wait_seconds),
            },
            "adaptive": {
                "enabled": self.options.enable_adaptive_concurrency,
                "target_p95_seconds": self.options.adaptive_target_p95_seconds,
                "min_concurrency": self.options.adaptive_min_concurrency,
                "max_concurrency": self.options.adaptive_max_concurrency,
                "adjust_interval_seconds": self.options.adaptive_adjust_interval_seconds,
                "adjustments": self._adaptive_adjustments,
            },
        }

    def record_oom(self, assignment: RuntimeAssignment) -> None:
        """Record an OOM event.

        Args:
            assignment: RuntimeAssignment from failed task.
        """
        self._oom_events += 1
        if self.allocator.mark_oom(assignment.assigned_gpu):
            self._gpu_cooldown_events += 1

    def runtime_counters(self) -> Dict[str, int]:
        """Get runtime counters.

        Returns:
            Dictionary of runtime counters.
        """
        return {
            "oom_events": self._oom_events,
            "gpu_cooldown_events": self._gpu_cooldown_events,
            "adaptive_adjustments": self._adaptive_adjustments,
            "token_wait_events_sandbox": self._token_wait_events["sandbox"],
            "token_wait_events_llm": self._token_wait_events["llm"],
        }

    def adaptive_trace(self) -> List[Dict[str, Any]]:
        """Get adaptive adjustment trace.

        Returns:
            List of adaptive adjustment records.
        """
        return list(self._adaptive_trace)

    async def assign_runtime(
        self,
        problem: Dict[str, Any],
        fallback_idx: int,
        retry_state: Optional[Dict[str, Any]] = None,
    ) -> Tuple[RuntimeAssignment, RuntimeLease]:
        """Assign runtime resources to a task.

        Args:
            problem: Problem dictionary.
            fallback_idx: Fallback index for task ID.
            retry_state: Optional retry state.

        Returns:
            Tuple of (RuntimeAssignment, RuntimeLease).
        """
        retry_state = retry_state or {}
        excluded_gpu_ids = retry_state.get("excluded_gpu_ids")
        if excluded_gpu_ids is not None and not isinstance(excluded_gpu_ids, list):
            excluded_gpu_ids = None

        profile = self.build_profile(problem, fallback_idx, retry_state=retry_state)

        _queue_start = time.monotonic()
        await self._reserve_admission_slot()

        sem: Optional[asyncio.Semaphore] = None
        cpu_acquired = False
        gpu_id: Optional[int] = None
        assigned_device = "cpu"
        gpu_tokens = 0
        try:
            if self._sandbox_token_bucket is not None:
                await self._consume_token(self._sandbox_token_bucket, "sandbox")
            if self._llm_token_bucket is not None:
                await self._consume_token(self._llm_token_bucket, "llm")

            assigned_device, gpu_id, sem, gpu_tokens = await self.allocator.acquire(
                profile=profile,
                fallback_to_cpu=profile.allow_cpu_fallback,
                excluded_gpu_ids=excluded_gpu_ids,
            )
            if assigned_device == "cpu":
                await self._reserve_cpu_slot()
                cpu_acquired = True
        except Exception:
            self.allocator.release(gpu_id, sem, gpu_tokens)
            if cpu_acquired:
                self._release_cpu_slot()
            self._release_admission_slot()
            raise

        waited = time.monotonic() - _queue_start
        assignment = RuntimeAssignment(
            task_id=profile.task_id,
            assigned_device=assigned_device,
            assigned_gpu=gpu_id,
            queue_wait_seconds=waited,
            scheduler_policy=self.options.scheduler_policy,
            queue_policy=self.options.queue_policy,
            gpu_tokens=gpu_tokens,
            llm_max_concurrency=self.options.llm_max_concurrency,
            attempt=self._coerce_int(retry_state.get("attempt"), default=0),
            worker_pool={
                "cpu_pool_size": self._cpu_worker_pool_size,
                "cpu_dynamic_limit": self._cpu_dynamic_limit,
                "cpu_inflight": self._cpu_inflight,
                "admission_limit": self._admission_limit,
                "active_tasks": self._active_tasks,
                "gpu_slots": self.allocator.slot_snapshot(),
            },
            profile={
                "requested_device": profile.requested_device,
                "priority": profile.priority,
                "gpu_id": profile.gpu_id,
                "gpu_memory_gb": profile.gpu_memory_gb,
                "estimated_runtime_seconds": profile.estimated_runtime_seconds,
                "dataset_size_mb": profile.dataset_size_mb,
                "allow_cpu_fallback": profile.allow_cpu_fallback,
                "workload_class": profile.workload_class,
            },
        )
        if self.options.shadow_scheduler:
            logger.info(
                "[shadow-scheduler] %s -> %s gpu=%s tokens=%s wait=%.3fs",
                assignment.task_id,
                assignment.assigned_device,
                assignment.assigned_gpu,
                assignment.gpu_tokens,
                assignment.queue_wait_seconds,
            )
        return assignment, RuntimeLease(gpu_sem=sem, cpu_acquired=cpu_acquired)

    def release_runtime(self, assignment: RuntimeAssignment, lease: RuntimeLease) -> None:
        """Release runtime resources.

        Args:
            assignment: RuntimeAssignment to release.
            lease: RuntimeLease to release.
        """
        try:
            self.allocator.release(assignment.assigned_gpu, lease.gpu_sem, assignment.gpu_tokens)
            if lease.cpu_acquired:
                self._release_cpu_slot()
        finally:
            self._release_admission_slot()

    def _update_system_monitor(self) -> None:
        """Update DSLighting metrics for SystemMonitor."""
        try:
            from dslighting.monitoring.monitoring import get_global_monitor
            monitor = get_global_monitor()
            if not monitor:
                return

            max_conc = getattr(self.options, 'max_concurrency', None) if self.options else None
            if max_conc is None:
                logger.warning("[DEBUG] max_concurrency is None! self.options=%s", self.options)
                logger.warning("[DEBUG] type(self.options)=%s", type(self.options))
                if hasattr(self.options, '__dict__'):
                    logger.warning("[DEBUG] options attributes: %s", list(self.options.__dict__.keys()))
            else:
                logger.debug("[DEBUG] max_concurrency=%s", max_conc)

            # queue_length should represent real pending tasks, not idle slots.
            total_tasks = len(self.problems)
            completed_tasks = max(0, int(self._tasks_completed))
            active_tasks = max(0, int(self._active_tasks))
            queue_length = max(0, total_tasks - completed_tasks - active_tasks)

            p95_runtime = 0.0
            if self._task_runtime_history:
                p95_runtime = p95(list(self._task_runtime_history))

            avg_queue_wait = 0.0
            if self._queue_wait_history:
                avg_queue_wait = sum(self._queue_wait_history) / len(self._queue_wait_history)

            error_rate = 0.0
            if self._error_history:
                error_rate = sum(self._error_history) / len(self._error_history)

            cache_hit_rate = 0.0
            cache_entries = 0
            cache_size_mb = 0.0
            try:
                from dslighting.core.data.perception.cache import DataPerceptionCache
                cache_stats = DataPerceptionCache.get_cache_stats()
                if cache_stats:
                    cache_hit_rate = cache_stats.get('hit_rate', 0.0)
                    cache_entries = cache_stats.get('entries', 0)
                    cache_size_mb = cache_stats.get('size_mb', 0.0)
            except Exception:
                pass

            llm_total_cost = 0.0
            try:
                from dslighting.services.llm import LLMService
                llm_total_cost = LLMService.get_global_total_cost()
            except Exception:
                pass

            logger.debug(
                "[SCHEDULER DEBUG] About to call update_dslighting_metrics: active_tasks=%s, max_concurrency=%s, monitor_id=%s",
                self._active_tasks, self.options.max_concurrency, id(monitor)
            )
            monitor.update_dslighting_metrics(
                active_tasks=self._active_tasks,
                queue_length=queue_length,
                cache_hit_rate=cache_hit_rate,
                cache_entries=cache_entries,
                cache_size_mb=cache_size_mb,
                avg_queue_wait_seconds=avg_queue_wait,
                p95_runtime_seconds=p95_runtime,
                error_rate=error_rate,
                run_mode=self.options.exp_name,
                total_tasks=len(self.problems),
                max_concurrency=self.options.max_concurrency,
                llm_total_cost=llm_total_cost,
                tasks_completed=self._tasks_completed,
            )

        except Exception:
            pass
