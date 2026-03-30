import logging
from types import SimpleNamespace

import pytest

from dslighting.benchmark.core.async_runner import AsyncEvaluationRunner
from dslighting.benchmark.core.gpu_allocator import GpuAllocator
from dslighting.benchmark.core.scheduler_core import (
    BenchmarkRuntimeScheduler,
    RuntimeSchedulerOptions,
)


def test_runtime_scheduler_options_normalize_new_timing_fields():
    options = RuntimeSchedulerOptions(
        gpu_memory_probe_interval_seconds=-3.0,
        allocator_poll_interval_seconds=0.0,
        enable_task_rate_limiting=True,
        llm_task_start_rate="4",
        sandbox_task_start_rate="2.5",
        task_rate_burst_factor=0.4,
    ).normalize(problem_count=5)

    assert options.gpu_memory_probe_interval_seconds == 0.05
    assert options.allocator_poll_interval_seconds == 0.01
    assert options.enable_task_rate_limiting is True
    assert options.enable_dual_token_bucket is True
    assert options.llm_task_start_rate == 4.0
    assert options.llm_token_rate == 4.0
    assert options.sandbox_task_start_rate == 2.5
    assert options.sandbox_token_rate == 2.5
    assert options.task_rate_burst_factor == 1.0
    assert options.token_bucket_burst == 1.0


def test_runtime_scheduler_options_legacy_task_rate_aliases_warn(caplog):
    with caplog.at_level(logging.WARNING):
        options = RuntimeSchedulerOptions(
            enable_dual_token_bucket=True,
            llm_token_rate=3.0,
            sandbox_token_rate=2.0,
            token_bucket_burst=4.0,
        ).normalize(problem_count=5)

    assert options.enable_task_rate_limiting is True
    assert options.llm_task_start_rate == 3.0
    assert options.sandbox_task_start_rate == 2.0
    assert options.task_rate_burst_factor == 4.0
    assert "enable_dual_token_bucket is deprecated" in caplog.text
    assert "llm_token_rate is deprecated" in caplog.text
    assert "sandbox_token_rate is deprecated" in caplog.text
    assert "token_bucket_burst is deprecated" in caplog.text


def test_runtime_scheduler_options_rejects_conflicting_task_rate_aliases():
    with pytest.raises(ValueError, match="Conflicting task rate options"):
        RuntimeSchedulerOptions(
            llm_task_start_rate=2.0,
            llm_token_rate=3.0,
        ).normalize(problem_count=5)


def test_async_runner_accepts_new_task_rate_kwargs():
    options, eval_kwargs = AsyncEvaluationRunner._split_runtime_kwargs(
        {
            "enable_task_rate_limiting": True,
            "llm_task_start_rate": 7.0,
            "sandbox_task_start_rate": 5.0,
            "task_rate_burst_factor": 3.0,
            "custom_eval_kwarg": "kept",
        }
    )

    assert options.enable_task_rate_limiting is True
    assert options.llm_task_start_rate == 7.0
    assert options.sandbox_task_start_rate == 5.0
    assert options.task_rate_burst_factor == 3.0
    assert eval_kwargs == {"custom_eval_kwarg": "kept"}


def test_runtime_scheduler_options_warns_when_queue_policy_loses_admission_queue_effect(caplog):
    with caplog.at_level(logging.WARNING):
        RuntimeSchedulerOptions(queue_policy="lpt_backfill").normalize(problem_count=5)

    assert "does not affect admission queue ordering" in caplog.text


def test_runtime_scheduler_options_skips_queue_warning_when_explicit_cap_enables_queueing(caplog):
    with caplog.at_level(logging.WARNING):
        RuntimeSchedulerOptions(
            queue_policy="lpt_backfill",
            max_concurrency=2,
        ).normalize(problem_count=5)

    assert "does not affect admission queue ordering" not in caplog.text


def test_scheduler_logs_cpu_only_mode_when_no_gpu(monkeypatch, caplog):
    class _FakeAllocator:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            self.has_gpu = False
            self.token_size_gb = None

        def slot_snapshot(self):
            return {}

        def token_capacity_snapshot(self):
            return {}

        def inflight_snapshot(self):
            return {}

        def cooldown_snapshot(self):
            return {}

        def memory_probe_snapshot(self):
            return {}

    monkeypatch.setattr(
        "dslighting.benchmark.core.scheduler_core.GpuAllocator",
        _FakeAllocator,
    )

    with caplog.at_level(logging.INFO):
        scheduler = BenchmarkRuntimeScheduler(
            problems=[{"task_id": "task-1"}],
            options=RuntimeSchedulerOptions(gpu_ids=[0]),
        )

    assert scheduler.capacity_snapshot()["cpu_only_mode"] is True
    assert "Running in CPU-only mode" in caplog.text


def test_gpu_allocator_memory_probe_is_cached(monkeypatch):
    calls = {"total_query": 0, "headroom_query": 0}

    def fake_which(_name: str):
        return "/usr/bin/nvidia-smi"

    def fake_run(cmd, check, capture_output, text):  # noqa: ANN001
        query = " ".join(cmd)
        if "memory.total" in query and "memory.used" not in query:
            calls["total_query"] += 1
            return SimpleNamespace(stdout="0, 24576\n")
        if "memory.used,memory.total" in query:
            calls["headroom_query"] += 1
            return SimpleNamespace(stdout="0, 100, 1000\n")
        raise AssertionError(f"Unexpected nvidia-smi query: {cmd}")

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)

    allocator = GpuAllocator(
        policy="auto",
        gpu_ids=[0],
        slots_per_gpu=1,
        auto_tune_slots=False,
        mem_target=0.85,
        memory_mode="off",
        default_memory_gb=None,
        reserved_memory_gb=2.0,
        cooldown_seconds=30.0,
        enable_mem_headroom_check=True,
        mem_probe_interval_seconds=10.0,
        allocation_poll_interval_seconds=0.1,
    )

    assert allocator._gpu_has_mem_headroom(0) is True
    assert allocator._gpu_has_mem_headroom(0) is True

    assert calls["total_query"] == 1
    assert calls["headroom_query"] == 1
