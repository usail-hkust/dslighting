from types import SimpleNamespace

from dslighting.benchmark.core.gpu_allocator import GpuAllocator
from dslighting.benchmark.core.scheduler_core import RuntimeSchedulerOptions


def test_runtime_scheduler_options_normalize_new_timing_fields():
    options = RuntimeSchedulerOptions(
        gpu_memory_probe_interval_seconds=-3.0,
        allocator_poll_interval_seconds=0.0,
    ).normalize(problem_count=5)

    assert options.gpu_memory_probe_interval_seconds == 0.05
    assert options.allocator_poll_interval_seconds == 0.01


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
