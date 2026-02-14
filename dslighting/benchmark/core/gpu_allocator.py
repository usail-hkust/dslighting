"""GPU allocator with slot + memory-token admission control."""

from __future__ import annotations

import asyncio
import logging
import math
import os
import shutil
import subprocess
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from dslighting.benchmark.core.task_profile import TaskResourceProfile

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_SIZE = 6.0

__all__ = ["GpuAllocator"]


class GpuAllocator:
    """GPU allocator with slot + memory-token admission control."""

    def __init__(
        self,
        policy: str,
        gpu_ids: Optional[List[int]],
        slots_per_gpu: Optional[int],
        auto_tune_slots: bool,
        mem_target: float,
        memory_mode: str,
        default_memory_gb: Optional[float],
        reserved_memory_gb: float,
        cooldown_seconds: float,
        enable_mem_headroom_check: bool,
        mem_probe_interval_seconds: float,
        allocation_poll_interval_seconds: float,
    ):
        self.policy = policy
        self.mem_target = mem_target
        self.memory_mode = memory_mode
        self.default_memory_gb = default_memory_gb
        self.reserved_memory_gb = reserved_memory_gb
        self.cooldown_seconds = max(0.0, float(cooldown_seconds))
        self.enable_mem_headroom_check = bool(enable_mem_headroom_check)
        self.mem_probe_interval_seconds = max(0.05, float(mem_probe_interval_seconds))
        self.allocation_poll_interval_seconds = max(0.01, float(allocation_poll_interval_seconds))
        self.auto_tune_slots = auto_tune_slots
        self.gpu_ids = self._resolve_gpu_ids(gpu_ids)
        self._gpu_totals_gb = self._query_gpu_total_memory_gb()
        self._token_size_gb = self._resolve_token_size_gb(slots_per_gpu)
        self._slots_per_gpu = self._resolve_slots_per_gpu(slots_per_gpu)
        self._token_capacity = self._resolve_token_capacities()
        self._semaphores: Dict[int, asyncio.Semaphore] = {
            gpu_id: asyncio.Semaphore(self._slots_per_gpu[gpu_id]) for gpu_id in self.gpu_ids
        }
        self._inflight: Dict[int, int] = {gpu_id: 0 for gpu_id in self.gpu_ids}
        self._used_tokens: Dict[int, int] = {gpu_id: 0 for gpu_id in self.gpu_ids}
        self._cooldown_until: Dict[int, float] = {gpu_id: 0.0 for gpu_id in self.gpu_ids}
        self._memory_ratio_snapshot: Dict[int, float] = {}
        self._memory_snapshot_at: float = 0.0
        # Event-driven signaling for slot availability
        self._slot_available = asyncio.Condition()

    @staticmethod
    def _resolve_gpu_ids(gpu_ids: Optional[List[int]]) -> List[int]:
        if gpu_ids:
            return sorted({int(x) for x in gpu_ids})

        visible = (os.getenv("CUDA_VISIBLE_DEVICES") or "").strip()
        if visible and visible not in {"-1", "none", "None"}:
            resolved = []
            for token in visible.split(","):
                token = token.strip()
                if token and token.isdigit():
                    resolved.append(int(token))
            if resolved:
                return sorted(set(resolved))

        if shutil.which("nvidia-smi"):
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                ids = []
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.isdigit():
                        ids.append(int(line))
                if ids:
                    return sorted(set(ids))
            except Exception as exc:  # pragma: no cover - defensive path
                logger.debug("Failed to query GPU ids via nvidia-smi: %s", exc)
        return []

    def _query_gpu_total_memory_gb(self) -> Dict[int, float]:
        if not self.gpu_ids or not shutil.which("nvidia-smi"):
            return {}
        totals: Dict[int, float] = {}
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            for line in result.stdout.splitlines():
                parts = [x.strip() for x in line.split(",")]
                if len(parts) != 2:
                    continue
                if not parts[0].isdigit():
                    continue
                gpu_id = int(parts[0])
                if gpu_id not in self.gpu_ids:
                    continue
                try:
                    totals[gpu_id] = max(0.1, float(parts[1]) / 1024.0)
                except (TypeError, ValueError):
                    continue
        except Exception as exc:  # pragma: no cover - defensive path
            logger.debug("Failed GPU total-memory query via nvidia-smi: %s", exc)
        return totals

    def _resolve_token_size_gb(self, slots_per_gpu: Optional[int]) -> Optional[float]:
        if self.memory_mode == "off":
            return None
        if self.default_memory_gb and self.default_memory_gb > 0:
            return self.default_memory_gb

        if not self._gpu_totals_gb:
            return DEFAULT_TOKEN_SIZE

        if slots_per_gpu and slots_per_gpu > 0:
            candidates: List[float] = []
            for total_gb in self._gpu_totals_gb.values():
                usable = max(1.0, total_gb - self.reserved_memory_gb)
                candidates.append(max(1.0, usable / slots_per_gpu))
            if candidates:
                return max(1.0, min(candidates))
        return DEFAULT_TOKEN_SIZE

    def _resolve_slots_per_gpu(self, slots_per_gpu: Optional[int]) -> Dict[int, int]:
        resolved: Dict[int, int] = {}
        for gpu_id in self.gpu_ids:
            memory_slots = None
            if self.memory_mode in {"fixed", "token"} and self._token_size_gb:
                total_gb = self._gpu_totals_gb.get(gpu_id)
                if total_gb is not None:
                    usable = max(0.0, total_gb - self.reserved_memory_gb)
                    memory_slots = max(1, int(usable // self._token_size_gb))

            if slots_per_gpu is None:
                if self.auto_tune_slots and memory_slots is not None:
                    resolved[gpu_id] = memory_slots
                else:
                    resolved[gpu_id] = 1
                continue

            if self.auto_tune_slots and memory_slots is not None:
                resolved[gpu_id] = max(1, min(slots_per_gpu, memory_slots))
            else:
                resolved[gpu_id] = max(1, slots_per_gpu)
        return resolved

    def _resolve_token_capacities(self) -> Dict[int, int]:
        capacities: Dict[int, int] = {}
        for gpu_id in self.gpu_ids:
            if self.memory_mode == "off":
                capacities[gpu_id] = self._slots_per_gpu[gpu_id]
                continue

            total_gb = self._gpu_totals_gb.get(gpu_id)
            if total_gb is None or not self._token_size_gb:
                capacities[gpu_id] = self._slots_per_gpu[gpu_id]
                continue

            usable = max(0.0, total_gb - self.reserved_memory_gb)
            capacities[gpu_id] = max(1, int(usable // self._token_size_gb))
        return capacities

    @property
    def token_size_gb(self) -> Optional[float]:
        return self._token_size_gb

    def slot_snapshot(self) -> Dict[str, int]:
        return {str(gpu_id): slots for gpu_id, slots in self._slots_per_gpu.items()}

    def token_capacity_snapshot(self) -> Dict[str, int]:
        return {str(gpu_id): cap for gpu_id, cap in self._token_capacity.items()}

    def inflight_snapshot(self) -> Dict[str, int]:
        return {str(gpu_id): value for gpu_id, value in self._inflight.items()}

    def cooldown_snapshot(self) -> Dict[str, float]:
        now = time.time()
        remaining: Dict[str, float] = {}
        for gpu_id, deadline in self._cooldown_until.items():
            if deadline > now:
                remaining[str(gpu_id)] = round(deadline - now, 3)
        return remaining

    def memory_probe_snapshot(self) -> Dict[str, Any]:
        age = None
        if self._memory_snapshot_at > 0:
            age = round(max(0.0, time.monotonic() - self._memory_snapshot_at), 3)
        return {
            "enabled": self.enable_mem_headroom_check,
            "probe_interval_seconds": self.mem_probe_interval_seconds,
            "poll_interval_seconds": self.allocation_poll_interval_seconds,
            "cache_age_seconds": age,
            "cached_gpu_count": len(self._memory_ratio_snapshot),
        }

    @property
    def has_gpu(self) -> bool:
        return bool(self.gpu_ids)

    def mark_oom(self, gpu_id: Optional[int]) -> bool:
        """Put a GPU into cooldown after an OOM event."""
        if gpu_id is None or gpu_id not in self._cooldown_until:
            return False
        if self.cooldown_seconds <= 0:
            return False
        self._cooldown_until[gpu_id] = time.time() + self.cooldown_seconds
        return True

    def _is_cooling(self, gpu_id: int) -> bool:
        return time.time() < self._cooldown_until.get(gpu_id, 0.0)

    def _refresh_gpu_memory_snapshot(self, force: bool = False) -> None:
        if not self.enable_mem_headroom_check:
            return
        if not self.gpu_ids or not shutil.which("nvidia-smi"):
            return

        now = time.monotonic()
        if (
            not force
            and self._memory_snapshot_at > 0
            and (now - self._memory_snapshot_at) < self.mem_probe_interval_seconds
        ):
            return

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            snapshot: Dict[int, float] = {}
            for line in result.stdout.splitlines():
                parts = [x.strip() for x in line.split(",")]
                if len(parts) != 3 or not parts[0].isdigit():
                    continue
                gpu_id = int(parts[0])
                if gpu_id not in self.gpu_ids:
                    continue
                try:
                    used = float(parts[1])
                    total = float(parts[2])
                except (TypeError, ValueError):
                    continue
                if total <= 0:
                    continue
                snapshot[gpu_id] = used / total
            if snapshot:
                self._memory_ratio_snapshot = snapshot
                self._memory_snapshot_at = now
        except Exception as exc:  # pragma: no cover - defensive path
            self._memory_snapshot_at = now
            logger.debug("Failed to refresh GPU memory snapshot: %s", exc)

    def _gpu_has_mem_headroom(self, gpu_id: int) -> bool:
        if not self.enable_mem_headroom_check:
            return True
        if not shutil.which("nvidia-smi"):
            return True
        self._refresh_gpu_memory_snapshot()
        ratio = self._memory_ratio_snapshot.get(gpu_id)
        if ratio is None:
            return True
        return ratio <= self.mem_target

    def _min_wait_seconds(self) -> float:
        return self.allocation_poll_interval_seconds

    def _candidate_order(
        self,
        preferred_gpu: Optional[int],
        excluded_gpu_ids: Optional[List[int]] = None,
    ) -> List[int]:
        ids = list(self.gpu_ids)
        excluded = {int(x) for x in (excluded_gpu_ids or [])}
        if excluded:
            ids = [gpu_id for gpu_id in ids if gpu_id not in excluded]
        ids = [gpu_id for gpu_id in ids if not self._is_cooling(gpu_id)]
        if preferred_gpu is not None and preferred_gpu in ids:
            ids.remove(preferred_gpu)
            ids.insert(0, preferred_gpu)
        ids.sort(
            key=lambda gpu_id: (
                self._inflight.get(gpu_id, 0),
                self._used_tokens.get(gpu_id, 0),
            )
        )
        return ids

    def _required_tokens(self, profile: TaskResourceProfile) -> int:
        if self.memory_mode == "off":
            return 1
        token_gb = self._token_size_gb or 1.0
        requested_gb = profile.gpu_memory_gb
        if requested_gb is None:
            requested_gb = self.default_memory_gb or token_gb
        requested_gb = max(0.1, float(requested_gb))
        return max(1, int(math.ceil(requested_gb / token_gb)))

    def _can_allocate_tokens(self, gpu_id: int, tokens: int) -> bool:
        capacity = self._token_capacity.get(gpu_id, 1)
        used = self._used_tokens.get(gpu_id, 0)
        return used + tokens <= capacity

    def _next_cooldown_wait(self, excluded_gpu_ids: Optional[List[int]] = None) -> float:
        now = time.time()
        excluded = {int(x) for x in (excluded_gpu_ids or [])}
        candidates = [
            deadline - now
            for gpu_id, deadline in self._cooldown_until.items()
            if gpu_id not in excluded and deadline > now
        ]
        if not candidates:
            return self._min_wait_seconds()
        return max(self._min_wait_seconds(), min(candidates))

    async def acquire(
        self,
        profile: TaskResourceProfile,
        fallback_to_cpu: bool,
        excluded_gpu_ids: Optional[List[int]] = None,
    ) -> tuple[str, Optional[int], Optional[asyncio.Semaphore], int]:
        if self.policy == "cpu_default":
            if profile.requested_device == "gpu" and self.has_gpu:
                return await self._acquire_gpu(profile, excluded_gpu_ids=excluded_gpu_ids)
            return "cpu", None, None, 0

        if profile.requested_device == "cpu":
            return "cpu", None, None, 0

        if not self.has_gpu:
            if fallback_to_cpu:
                return "cpu", None, None, 0
            raise RuntimeError("No GPUs available and cpu fallback is disabled.")

        if self.policy == "manual" and profile.gpu_id is None and self.gpu_ids:
            profile = TaskResourceProfile(
                task_id=profile.task_id,
                requested_device=profile.requested_device,
                priority=profile.priority,
                allow_cpu_fallback=profile.allow_cpu_fallback,
                gpu_id=self.gpu_ids[0],
                gpu_memory_gb=profile.gpu_memory_gb,
                estimated_runtime_seconds=profile.estimated_runtime_seconds,
                dataset_size_mb=profile.dataset_size_mb,
            )
        return await self._acquire_gpu(profile, excluded_gpu_ids=excluded_gpu_ids)

    async def _acquire_gpu(
        self,
        profile: TaskResourceProfile,
        excluded_gpu_ids: Optional[List[int]] = None,
    ) -> tuple[str, Optional[int], Optional[asyncio.Semaphore], int]:
        required_tokens = self._required_tokens(profile)
        while True:
            candidates = self._candidate_order(profile.gpu_id, excluded_gpu_ids=excluded_gpu_ids)
            for gpu_id in candidates:
                sem = self._semaphores[gpu_id]
                if sem.locked():
                    continue
                if not self._can_allocate_tokens(gpu_id, required_tokens):
                    continue
                if not self._gpu_has_mem_headroom(gpu_id):
                    continue
                await sem.acquire()
                if not self._can_allocate_tokens(gpu_id, required_tokens):
                    sem.release()
                    continue
                self._inflight[gpu_id] += 1
                self._used_tokens[gpu_id] += required_tokens
                return "gpu", gpu_id, sem, required_tokens
            if profile.allow_cpu_fallback and not candidates:
                return "cpu", None, None, 0

            # Event-driven wait instead of polling
            async with self._slot_available:
                # Wait for signal with timeout
                try:
                    await asyncio.wait_for(
                        self._slot_available.wait(),
                        timeout=self._next_cooldown_wait(excluded_gpu_ids=excluded_gpu_ids)
                    )
                except asyncio.TimeoutError:
                    # Timeout is expected - just continue the loop
                    pass

    def release(
        self,
        gpu_id: Optional[int],
        sem: Optional[asyncio.Semaphore],
        gpu_tokens: int,
    ) -> None:
        if gpu_id is None or sem is None:
            return
        self._inflight[gpu_id] = max(0, self._inflight[gpu_id] - 1)
        self._used_tokens[gpu_id] = max(0, self._used_tokens[gpu_id] - max(0, int(gpu_tokens)))
        sem.release()

        # Notify waiting tasks that a slot is available
        async def _notify():
            async with self._slot_available:
                self._slot_available.notify_all()

        # Schedule notification without blocking
        asyncio.create_task(_notify())
