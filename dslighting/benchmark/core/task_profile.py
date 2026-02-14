"""Task resource profile definitions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional


__all__ = ["TaskResourceProfile", "RuntimeAssignment", "RuntimeLease"]


@dataclass
class TaskResourceProfile:
    """Resource preferences for a benchmark task."""

    task_id: str
    requested_device: str = "auto"  # auto | gpu | cpu
    priority: int = 0
    allow_cpu_fallback: bool = True
    gpu_id: Optional[int] = None
    gpu_memory_gb: Optional[float] = None
    estimated_runtime_seconds: float = 1.0
    dataset_size_mb: Optional[float] = None
    workload_class: str = "general"  # general | cpu_light_llm_heavy | gpu_bound | sandbox_heavy


@dataclass
class RuntimeAssignment:
    """Final runtime assignment made by the scheduler."""

    task_id: str
    assigned_device: str  # cpu | gpu
    assigned_gpu: Optional[int]
    queue_wait_seconds: float
    scheduler_policy: str
    queue_policy: str
    gpu_tokens: int
    llm_max_concurrency: Optional[int]
    attempt: int
    worker_pool: Dict[str, Any]
    profile: Dict[str, Any]

    def to_runtime_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "assigned_device": self.assigned_device,
            "assigned_gpu": self.assigned_gpu,
            "scheduler_policy": self.scheduler_policy,
            "queue_policy": self.queue_policy,
            "queue_wait_seconds": round(self.queue_wait_seconds, 4),
            "gpu_tokens": self.gpu_tokens,
            "attempt": self.attempt,
            "worker_pool": self.worker_pool,
            "resource_profile": self.profile,
        }
        if self.llm_max_concurrency is not None:
            payload["llm_max_concurrency"] = self.llm_max_concurrency
        if self.assigned_device == "gpu" and self.assigned_gpu is not None:
            payload["cuda_visible_devices"] = str(self.assigned_gpu)
        elif self.assigned_device == "cpu":
            payload["cuda_visible_devices"] = ""
        return payload


@dataclass
class RuntimeLease:
    """Opaque lease for resources acquired by the scheduler."""

    gpu_sem: Optional[asyncio.Semaphore]
    cpu_acquired: bool = False
