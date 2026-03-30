"""Admission control for task scheduling with concurrency management."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Deque, Dict, List, Optional

if TYPE_CHECKING:
    from dslighting.benchmark.core.scheduler_core import RuntimeSchedulerOptions

from dslighting.utils.math import p95

logger = logging.getLogger(__name__)


class AdmissionController:
    """Controls task admission and concurrency management."""

    def __init__(
        self,
        options: RuntimeSchedulerOptions,
        cpu_worker_pool_size: int,
    ):
        self.options = options
        self._admission = asyncio.Semaphore(options.max_concurrency)
        cpu_pool_size = cpu_worker_pool_size or options.max_concurrency
        self._cpu_worker_pool_size = max(1, int(cpu_pool_size))
        self._cpu_pool = asyncio.Semaphore(self._cpu_worker_pool_size)
        self._state_lock = asyncio.Lock()
        self._active_tasks = 0
        self._cpu_inflight = 0
        self._admission_limit = options.max_concurrency
        self._cpu_dynamic_limit = self._cpu_worker_pool_size

        # Adaptive concurrency tracking
        self._adaptive_adjustments = 0
        self._task_runtime_history: Deque[float] = deque(maxlen=512)
        self._queue_wait_history: Deque[float] = deque(maxlen=512)
        self._error_history: Deque[int] = deque(maxlen=512)
        self._adaptive_trace: List[Dict[str, Any]] = []
        self._last_adaptive_adjust_at = time.monotonic()
        self._stability_counter = 0

        # Token bucket for sandbox/LLM rate limiting
        self._token_wait_events = {"sandbox": 0, "llm": 0}
        self._token_wait_seconds = {"sandbox": 0.0, "llm": 0.0}

    @property
    def active_tasks(self) -> int:
        return self._active_tasks

    @property
    def cpu_inflight(self) -> int:
        return self._cpu_inflight

    @property
    def admission_limit(self) -> int:
        return self._admission_limit

    @property
    def cpu_dynamic_limit(self) -> int:
        return self._cpu_dynamic_limit

    @property
    def cpu_worker_pool_size(self) -> int:
        return self._cpu_worker_pool_size

    async def reserve_admission_slot(self, poll_interval: float = 0.1) -> None:
        """Reserve an admission slot, waiting if necessary."""
        await self._admission.acquire()
        poll_interval = max(0.01, poll_interval)
        while True:
            async with self._state_lock:
                if self._active_tasks < self._admission_limit:
                    self._active_tasks += 1
                    return
            await asyncio.sleep(poll_interval)

    async def reserve_cpu_slot(self, poll_interval: float = 0.1) -> None:
        """Reserve a CPU slot, waiting if necessary."""
        await self._cpu_pool.acquire()
        poll_interval = max(0.01, poll_interval)
        while True:
            async with self._state_lock:
                if self._cpu_inflight < self._cpu_dynamic_limit:
                    self._cpu_inflight += 1
                    return
            await asyncio.sleep(poll_interval)

    def release_admission_slot(self) -> None:
        """Release an admission slot."""
        self._active_tasks = max(0, self._active_tasks - 1)
        self._admission.release()

    def release_cpu_slot(self) -> None:
        """Release a CPU slot."""
        self._cpu_inflight = max(0, self._cpu_inflight - 1)
        self._cpu_pool.release()

    def record_task_completion(
        self,
        runtime_seconds: float,
        queue_wait_seconds: float,
        had_error: bool,
    ) -> None:
        """Record task completion for adaptive concurrency adjustment."""
        self._task_runtime_history.append(max(0.0, float(runtime_seconds)))
        self._queue_wait_history.append(max(0.0, float(queue_wait_seconds)))
        self._error_history.append(1 if had_error else 0)
        self._maybe_adjust_concurrency()

    def snapshot(self) -> Dict[str, Any]:
        """Return admission controller state snapshot."""
        return {
            "admission_limit": self._admission_limit,
            "active_tasks": self._active_tasks,
            "cpu_worker_pool_size": self._cpu_worker_pool_size,
            "cpu_dynamic_limit": self._cpu_dynamic_limit,
            "cpu_inflight": self._cpu_inflight,
        }

    def runtime_counters(self) -> Dict[str, int]:
        """Return runtime counters."""
        return {
            "adaptive_adjustments": self._adaptive_adjustments,
            "token_wait_events_sandbox": self._token_wait_events["sandbox"],
            "token_wait_events_llm": self._token_wait_events["llm"],
        }

    def adaptive_trace(self) -> List[Dict[str, Any]]:
        """Return adaptive adjustment trace."""
        return list(self._adaptive_trace)

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
