"""Real-time system monitoring for DSLighting.

This module provides tools for monitoring system resources and performance
metrics in real-time, enabling visibility into optimization effectiveness.

WARNING: This module uses global singletons (_global_monitor) which may cause
issues in concurrent or multi-process scenarios. The global monitor is designed
for single-process use cases. For concurrent scenarios, consider instantiating
SystemMonitor directly and using dependency injection instead of relying on
the global state managed by start_global_monitor() and get_global_monitor().
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SystemSnapshot:
    """A snapshot of system metrics at a point in time."""
    timestamp: float
    active_tasks: int
    queue_length: int
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_used_gb: float
    memory_available_gb: float
    gpu_usage: Dict[int, Dict[str, Any]]  # gpu_id -> {utilization, memory_used_mb, memory_total_mb}
    throughput_tasks_per_second: float
    p95_runtime_seconds: float
    total_tasks: Optional[int] = None  # Added total_tasks
    exp_name: Optional[str] = None  # Experiment name for independent monitoring
    run_mode: Optional[str] = None  # Run mode (legacy, now uses exp_name)
    max_concurrency: Optional[int] = None  # Maximum concurrency setting
    concurrency_utilization: Optional[float] = None  # Concurrency utilization percentage (0-100)
    llm_total_cost: Optional[float] = None  # Total LLM API cost accumulated
    language: Optional[str] = None  # Language setting: 'zh' or 'en'
    # P0 LLM Service Metrics
    llm_current_rpm: Optional[float] = None  # Current requests per minute for LLM API
    llm_rate_limit: Optional[float] = None  # Effective total RPM limit across active keys
    llm_rate_limit_usage_percent: Optional[float] = None  # Percentage of rate limit used (current_rpm/rate_limit * 100)
    llm_active_api_keys: Optional[str] = None  # Number of active API keys (e.g., "3/4")
    llm_rate_limited_keys: Optional[int] = None  # Number of API keys currently rate-limited
    llm_p95_latency_ms: Optional[float] = None  # P95 latency in milliseconds
    llm_p99_latency_ms: Optional[float] = None  # P99 latency in milliseconds
    llm_realtime_cost: Optional[float] = None  # Real-time accumulated cost (保留)
    # P0 LLM Token Metrics (新增)
    llm_input_tokens: Optional[float] = None  # Input/Prompt tokens (in thousands)
    llm_output_tokens: Optional[float] = None  # Output/Completion tokens (in thousands)
    # P1 Bottleneck Identification Metrics
    primary_bottleneck: Optional[str] = None  # "LLM", "GPU", "CPU", "Memory", "I/O", or "None"
    bottleneck_severity: Optional[float] = None  # 0-100 severity score
    efficiency_percent: Optional[float] = None  # Actual vs theoretical max speed percentage
    optimization_suggestion: Optional[str] = None  # Dynamic optimization suggestion
    # P1 Progress Estimation Metrics
    estimated_time_remaining_seconds: Optional[float] = None  # ETA in seconds
    theoretical_max_throughput: Optional[float] = None  # Maximum possible throughput
    actual_vs_theoretical_speed_percent: Optional[float] = None  # Efficiency percentage
    tasks_remaining: Optional[int] = None  # Tasks still pending
    progress_percent: Optional[float] = None  # Overall progress percentage (0-100)
    # P2 GPU Optimization Metrics
    gpu_oom_retry_count: Optional[int] = None  # Number of OOM retries
    gpu_idle_time_percent: Optional[float] = None  # GPU idle time percentage
    gpu_peak_memory_mb: Optional[float] = None  # Peak GPU memory usage
    gpu_memory_efficiency_percent: Optional[float] = None  # Memory efficiency percentage


class SystemMonitor:
    """
    Real-time system monitor with configurable update interval.

    Tracks CPU, memory, GPU usage, and DSLighting-specific metrics.
    Maintains a sliding window of historical data for analysis.

    Example:
        monitor = SystemMonitor(update_interval=1.0)
        await monitor.start()

        # Get current state
        snapshot = monitor.get_snapshot()

        # Stop monitoring
        await monitor.stop()
    """

    def __init__(
        self,
        update_interval: float = 1.0,
        history_size: int = 1000,
        enable_gpu_monitoring: bool = True,
    ):
        """
        Initialize the system monitor.

        Args:
            update_interval: Seconds between metric collection (default: 1.0s)
            history_size: Maximum number of snapshots to keep (default: 1000)
            enable_gpu_monitoring: Whether to monitor GPU usage (requires nvidia-smi)
        """
        self.update_interval = update_interval
        self.history_size = history_size
        self.enable_gpu_monitoring = enable_gpu_monitoring

        # Current metrics
        self._current_metrics: Dict[str, Any] = {
            "language": None,  # Language setting: 'zh' or 'en'
            "active_tasks": 0,
            "queue_length": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "memory_used_gb": 0.0,
            "memory_available_gb": 0.0,
            "gpu_usage": {},
            "throughput_tasks_per_second": 0.0,
            "p95_runtime_seconds": 0.0,
            "exp_name": None,  # Experiment name for independent monitoring files
            "total_tasks": None, # Added total_tasks
            "max_concurrency": None,
            "concurrency_utilization": None,
            "llm_total_cost": None,  # Total LLM cost accumulated
            # P0 LLM Service Metrics
            "llm_current_rpm": None,  # Current requests per minute for LLM API
            "llm_rate_limit": None,  # Effective total RPM limit across active keys
            "llm_rate_limit_usage_percent": None,  # Percentage of rate limit used
            "llm_active_api_keys": None,  # Number of active API keys (e.g., "3/4")
            "llm_rate_limited_keys": None,  # Number of API keys currently rate-limited
            "llm_p95_latency_ms": None,  # P95 latency in milliseconds
            "llm_p99_latency_ms": None,  # P99 latency in milliseconds
            "llm_realtime_cost": None,  # Real-time accumulated cost
            # P0 LLM Token Metrics
            "llm_input_tokens": None,  # Input tokens in thousands
            "llm_output_tokens": None,  # Output tokens in thousands
            # P1 Bottleneck Identification Metrics
            "primary_bottleneck": None,  # "LLM", "GPU", "CPU", "Memory", "I/O", or "None"
            "bottleneck_severity": None,  # 0-100 severity score
            "efficiency_percent": None,  # Actual vs theoretical max speed percentage
            "optimization_suggestion": None,  # Dynamic optimization suggestion
            # P1 Progress Estimation Metrics
            "estimated_time_remaining_seconds": None,  # ETA in seconds
            "theoretical_max_throughput": None,  # Maximum possible throughput
            "actual_vs_theoretical_speed_percent": None,  # Efficiency percentage
            "tasks_remaining": None,  # Tasks still pending
            "progress_percent": None,  # Overall progress percentage (0-100)
            # P2 GPU Optimization Metrics
            "gpu_oom_retry_count": None,  # Number of OOM retries
            "gpu_idle_time_percent": None,  # GPU idle time percentage
            "gpu_peak_memory_mb": None,  # Peak GPU memory usage
            "gpu_memory_efficiency_percent": None,  # Memory efficiency percentage
        }

        # Historical data
        self._history: Deque[SystemSnapshot] = deque(maxlen=history_size)

        # LLM latency tracking for percentiles (store latencies in milliseconds)
        self._llm_latencies: Deque[float] = deque(maxlen=1000)

        # LLM metrics tracking
        self._llm_request_times: Deque[float] = deque(maxlen=60)  # Track request timestamps for RPM calculation
        self._llm_rate_limit: float = 60.0  # Per-key rate limit (requests per minute)
        self._llm_active_keys: int = 1  # Number of active API keys
        self._llm_total_keys: int = 1  # Total number of API keys
        self._llm_rate_limited_count: int = 0  # Count of rate-limited keys
        self._llm_realtime_cost: float = 0.0  # Real-time accumulated cost
        self._llm_total_requests: int = 0  # Total requests made
        # P0 Token Metrics
        self._llm_input_tokens: int = 0  # Total input/prompt tokens
        self._llm_output_tokens: int = 0  # Total output/completion tokens

        # State
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time: Optional[float] = None
        self._tasks_completed = 0
        self._file_updater_thread: Optional[threading.Thread] = None  # Reference to file updater thread
        self._exp_name: Optional[str] = None  # Experiment name for file monitor
        self._run_id: Optional[str] = None  # Run ID for file monitor
        self._file_updater_first_update_done = threading.Event()  # Signal when FileUpdater completes first update
        self._metrics_updated = threading.Event()  # Signal when metrics are updated (for reset/update cycle)

        # Per-resource monitors
        self._gpu_ids: List[int] = []
        self._try_detect_gpus()

        # P2 GPU Optimization Metrics tracking
        self._gpu_oom_retry_count: int = 0  # Total OOM retry occurrences
        self._gpu_idle_samples: int = 0  # Number of samples where GPU was idle
        self._gpu_total_samples: int = 0  # Total number of GPU samples
        self._gpu_peak_memory_mb: float = 0.0  # Peak GPU memory usage across all GPUs
        self._gpu_idle_memory_samples: Deque[float] = deque(maxlen=history_size)  # Memory samples during idle periods
        self._gpu_active_memory_samples: Deque[float] = deque(maxlen=history_size)  # Memory samples during active periods
        self._gpu_total_memory_mb: float = 0.0  # Total GPU memory available (across all GPUs)

    def _try_detect_gpus(self) -> None:
        """Detect available GPUs by calling nvidia-smi."""
        if not self.enable_gpu_monitoring:
            return

        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._gpu_ids = [int(line.strip()) for line in result.stdout.strip().split("\n") if line.strip()]
                logger.info(f"Detected {len(self._gpu_ids)} GPUs: {self._gpu_ids}")
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as exc:
            logger.debug(f"Could not detect GPUs: {exc}")
            self.enable_gpu_monitoring = False

    async def start(self) -> None:
        """Start the monitoring loop."""
        if self._running:
            task_alive = self._task is not None and not self._task.done()
            if task_alive:
                logger.warning("SystemMonitor already running")
                return

            # The previous asyncio loop may have exited without calling stop().
            # Recover by clearing stale state and creating a fresh task.
            logger.warning(
                "SystemMonitor had stale running state (task not alive), restarting."
            )
            self._running = False
            self._task = None

        # Reset events for new start cycle
        self._file_updater_first_update_done.clear()
        self._metrics_updated.clear()

        self._running = True
        self._start_time = time.time()
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"SystemMonitor started (update_interval={self.update_interval}s)")

    async def stop(self) -> None:
        """Stop the monitoring loop."""
        if not self._running:
            return

        # Wait for file updater to complete first update (up to 2 seconds)
        if self._file_updater_thread is not None and self._file_updater_thread.is_alive():
            logger.debug("Waiting for file updater to complete first update...")
            self._file_updater_first_update_done.wait(timeout=2.0)
            logger.debug("File updater first update done or timeout")

        # Wait for metrics to be updated (reset/update cycle)
        # This ensures the file updater can read the latest metrics before we stop
        if self._running:  # Check again in case we're in a rapid start/stop cycle
            logger.info("Waiting for metrics to be updated...")
            self._metrics_updated.wait(timeout=1.0)
            logger.info("Metrics updated or timeout")

        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("SystemMonitor stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Update CPU and memory (psutil is optional)
                try:
                    import psutil
                    self._current_metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=None)
                    memory = psutil.virtual_memory()
                    self._current_metrics["memory_usage_percent"] = memory.percent
                    self._current_metrics["memory_used_gb"] = (memory.used / (1024**3))
                    self._current_metrics["memory_available_gb"] = (memory.available / (1024**3))
                except ImportError:
                    # psutil not available, skip CPU/memory metrics
                    pass

                # Update GPU metrics
                if self.enable_gpu_monitoring:
                    self._update_gpu_metrics()

                # Calculate throughput
                if self._start_time is not None:
                    elapsed = time.time() - self._start_time
                    if elapsed > 0:
                        self._current_metrics["throughput_tasks_per_second"] = self._tasks_completed / elapsed

                # Update LLM metrics
                self._update_llm_metrics()

                # Calculate P1 progress estimation metrics
                self.calculate_progress_metrics()

                # Analyze bottleneck and calculate efficiency (updates efficiency_percent, primary_bottleneck, etc.)
                self.analyze_bottleneck()

                # Create snapshot and add to history
                # Note: gpu_usage needs to be copied to avoid reference issues
                metrics_copy = self._current_metrics.copy()
                metrics_copy["gpu_usage"] = self._current_metrics["gpu_usage"].copy()

                snapshot = SystemSnapshot(
                    timestamp=time.time(),
                    **metrics_copy,
                )
                self._history.append(snapshot)

                # Wait for next update
                await asyncio.sleep(self.update_interval)

            except Exception as exc:
                logger.error(f"Error in monitoring loop: {exc}", exc_info=True)
                await asyncio.sleep(self.update_interval)

    def _update_gpu_metrics(self) -> None:
        """Update GPU metrics using nvidia-smi."""
        try:
            import subprocess

            # Query GPU utilization and memory
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode == 0:
                gpu_usage = {}
                total_memory = 0.0
                max_memory_used = 0.0
                total_utilization = 0.0
                gpu_count = 0

                for line in result.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split(",")
                    if len(parts) == 4:
                        gpu_id = int(parts[0].strip())
                        utilization = float(parts[1].strip())
                        memory_used = float(parts[2].strip())
                        memory_total = float(parts[3].strip())

                        gpu_usage[gpu_id] = {
                            "utilization_percent": utilization,
                            "memory_used_mb": memory_used,
                            "memory_total_mb": memory_total,
                            "memory_used_percent": (memory_used / memory_total * 100) if memory_total > 0 else 0.0,
                        }

                        total_memory += memory_total
                        max_memory_used = max(max_memory_used, memory_used)
                        total_utilization += utilization
                        gpu_count += 1

                        # Track peak memory across all GPUs
                        if memory_used > self._gpu_peak_memory_mb:
                            self._gpu_peak_memory_mb = memory_used

                self._current_metrics["gpu_usage"] = gpu_usage

                # Update total GPU memory
                self._gpu_total_memory_mb = total_memory

                # Track idle time (GPU utilization < 10%)
                if gpu_count > 0:
                    avg_utilization = total_utilization / gpu_count
                    self._gpu_total_samples += 1
                    if avg_utilization < 10.0:
                        self._gpu_idle_samples += 1
                        # Track memory during idle periods
                        self._gpu_idle_memory_samples.append(max_memory_used)
                    else:
                        # Track memory during active periods
                        self._gpu_active_memory_samples.append(max_memory_used)

        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as exc:
            logger.debug(f"Could not update GPU metrics: {exc}")

    def update_dslighting_metrics(
        self,
        language: str = None,
        active_tasks: int = None,
        queue_length: int = None,
        p95_runtime_seconds: float = None,
        total_tasks: int = None,
        max_concurrency: int = None,
        llm_total_cost: float = None,
        tasks_completed: int = None,
        **_: None,
    ) -> None:
        """
        Update DSLighting-specific metrics.

        Args:
            language: Language setting ('zh' or 'en')
            active_tasks: Number of currently active tasks
            queue_length: Number of tasks waiting in queue
            p95_runtime_seconds: 95th percentile runtime
            total_tasks: Total number of tasks (for progress calculation)
            max_concurrency: Maximum concurrency setting
            tasks_completed: Number of completed tasks
            **_: Reserved keyword arguments for backward compatibility
        """
        # Log at DEBUG level to avoid spamming logs
        logger.debug(f"update_dslighting_metrics called: language={language}, total_tasks={total_tasks}, tasks_completed={tasks_completed}")

        if language is not None:
            self._current_metrics["language"] = language
        if active_tasks is not None:
            self._current_metrics["active_tasks"] = active_tasks
        if queue_length is not None:
            self._current_metrics["queue_length"] = queue_length
        if p95_runtime_seconds is not None:
            self._current_metrics["p95_runtime_seconds"] = p95_runtime_seconds
        if total_tasks is not None:
            self._current_metrics["total_tasks"] = total_tasks
        if llm_total_cost is not None:
            self._current_metrics["llm_total_cost"] = llm_total_cost

        if max_concurrency is not None:
            self._current_metrics["max_concurrency"] = max_concurrency
        # Always update concurrency_utilization if max_concurrency is set
        if self._current_metrics.get("max_concurrency") is not None:
            max_conc = self._current_metrics["max_concurrency"]
            active = self._current_metrics.get("active_tasks", 0)
            if max_conc > 0:
                self._current_metrics["concurrency_utilization"] = (active / max_conc) * 100
            else:
                self._current_metrics["concurrency_utilization"] = 0.0

        if tasks_completed is not None:
            self._tasks_completed = tasks_completed
            # Calculate task progress and remaining tasks
            if total_tasks is not None and total_tasks > 0:
                completed_for_progress = max(0, min(tasks_completed, total_tasks))
                self._current_metrics["progress_percent"] = (completed_for_progress / total_tasks) * 100
                self._current_metrics["tasks_remaining"] = max(0, total_tasks - tasks_completed)
            elif self._current_metrics.get("total_tasks") is not None:
                # Use existing total_tasks if not provided
                total = self._current_metrics["total_tasks"]
                completed_for_progress = max(0, min(tasks_completed, total))
                self._current_metrics["progress_percent"] = (completed_for_progress / total) * 100 if total > 0 else 0.0
                self._current_metrics["tasks_remaining"] = max(0, total - tasks_completed)
            else:
                self._current_metrics["progress_percent"] = 0.0
                self._current_metrics["tasks_remaining"] = 0

        # Signal that metrics have been updated (for synchronization with file updater)
        self._metrics_updated.set()

        # NOTE: File monitor updates are handled by the background thread in _start_file_monitor_updater()
        # to avoid race conditions. We don't update file here to prevent competing writes.

    def record_task_completion(self) -> None:
        """Record a task completion for throughput calculation."""
        self._tasks_completed += 1

    # ==================== P0 LLM Service Metrics Methods ====================

    def record_llm_request(self, latency_ms: float, cost: float = 0.0,
                          input_tokens: int = 0, output_tokens: int = 0) -> None:
        """
        Record an LLM API request for metrics tracking.

        Args:
            latency_ms: Request latency in milliseconds
            cost: Cost of this request in USD
            input_tokens: Number of prompt/input tokens
            output_tokens: Number of completion/output tokens
        """
        current_time = time.time()

        # Track latency for percentile calculations
        self._llm_latencies.append(latency_ms)

        # Track request timestamp for RPM calculation
        self._llm_request_times.append(current_time)

        # Update cost tracking
        self._llm_realtime_cost += cost
        self._llm_total_requests += 1

        # Update token tracking (store in thousands)
        self._llm_input_tokens += input_tokens
        self._llm_output_tokens += output_tokens

        # Update current metrics
        self._current_metrics["llm_realtime_cost"] = self._llm_realtime_cost
        self._current_metrics["llm_input_tokens"] = self._llm_input_tokens / 1000.0
        self._current_metrics["llm_output_tokens"] = self._llm_output_tokens / 1000.0

        # Update RPM metrics immediately (will be written to file by monitoring loop)
        cutoff_time = current_time - 60
        rpm_count = sum(1 for t in self._llm_request_times if t >= cutoff_time)
        self._current_metrics["llm_current_rpm"] = rpm_count
        total_rate_limit = self._get_total_llm_rate_limit()
        self._current_metrics["llm_rate_limit"] = total_rate_limit
        if total_rate_limit > 0:
            self._current_metrics["llm_rate_limit_usage_percent"] = (rpm_count / total_rate_limit) * 100
        self._current_metrics["llm_p95_latency_ms"] = self._calculate_percentile(95)
        self._current_metrics["llm_p99_latency_ms"] = self._calculate_percentile(99)

        # Note: File monitor update is handled by the monitoring loop's background thread
        # to avoid race conditions. LLM metrics are now in _current_metrics and will be
        # written by _start_file_monitor_updater().

    def set_rate_limit(self, rpm: float) -> None:
        """
        Set the LLM API rate limit.

        Args:
            rpm: Requests per minute limit
        """
        self._llm_rate_limit = rpm
        self._current_metrics["llm_rate_limit"] = self._get_total_llm_rate_limit()

    def set_active_keys(self, active: int, total: int) -> None:
        """
        Set the number of active API keys.

        Args:
            active: Number of currently active keys
            total: Total number of configured keys
        """
        self._llm_active_keys = active
        self._llm_total_keys = total
        self._current_metrics["llm_active_api_keys"] = f"{active}/{total}"
        self._current_metrics["llm_rate_limit"] = self._get_total_llm_rate_limit()

    def increment_rate_limited_count(self) -> None:
        """Increment the count of rate-limited API keys."""
        self._llm_rate_limited_count += 1
        self._current_metrics["llm_rate_limited_keys"] = self._llm_rate_limited_count

    def reset_rate_limited_count(self) -> None:
        """Reset the rate-limited keys count to zero."""
        self._llm_rate_limited_count = 0
        self._current_metrics["llm_rate_limited_keys"] = 0

    def _update_llm_metrics(self) -> None:
        """Update LLM metrics from internal tracking state."""
        current_time = time.time()

        # Calculate current RPM (requests in the last 60 seconds)
        cutoff_time = current_time - 60
        rpm_count = sum(1 for t in self._llm_request_times if t >= cutoff_time)
        self._current_metrics["llm_current_rpm"] = rpm_count

        # Calculate rate limit usage percentage
        total_rate_limit = self._get_total_llm_rate_limit()
        if total_rate_limit > 0:
            usage_percent = (rpm_count / total_rate_limit) * 100
            self._current_metrics["llm_rate_limit_usage_percent"] = usage_percent

        # Calculate P95 latency
        self._current_metrics["llm_p95_latency_ms"] = self._calculate_percentile(95)

        # Calculate P99 latency
        self._current_metrics["llm_p99_latency_ms"] = self._calculate_percentile(99)

        # Update rate limit info
        self._current_metrics["llm_rate_limit"] = total_rate_limit
        self._current_metrics["llm_active_api_keys"] = f"{self._llm_active_keys}/{self._llm_total_keys}"
        self._current_metrics["llm_rate_limited_keys"] = self._llm_rate_limited_count

        # Update token metrics (in thousands)
        self._current_metrics["llm_input_tokens"] = self._llm_input_tokens / 1000.0
        self._current_metrics["llm_output_tokens"] = self._llm_output_tokens / 1000.0

        # NOTE: File monitor updates for LLM metrics are done in record_llm_request()
        # to avoid race conditions. We don't update file here.

    def calculate_progress_metrics(self) -> None:
        """
        Calculate P1 progress estimation metrics.

        Updates _current_metrics with:
        - estimated_time_remaining_seconds: ETA based on current throughput
        - theoretical_max_throughput: max_concurrency / avg_p95_runtime
        - actual_vs_theoretical_speed_percent: efficiency percentage
        - tasks_remaining: total_tasks - tasks_completed
        - progress_percent: (tasks_completed / total_tasks) * 100
        """
        total_tasks = self._current_metrics.get("total_tasks")
        max_concurrency = self._current_metrics.get("max_concurrency")
        p95_runtime = self._current_metrics.get("p95_runtime_seconds", 0.0)
        throughput = self._current_metrics.get("throughput_tasks_per_second", 0.0)

        # Calculate tasks_remaining
        if total_tasks is not None and total_tasks > 0:
            tasks_remaining = max(0, total_tasks - self._tasks_completed)
            self._current_metrics["tasks_remaining"] = tasks_remaining

            # Calculate progress_percent
            completed_for_progress = max(0, min(self._tasks_completed, total_tasks))
            self._current_metrics["progress_percent"] = (completed_for_progress / total_tasks) * 100
        else:
            self._current_metrics["tasks_remaining"] = None
            self._current_metrics["progress_percent"] = None

        # Calculate theoretical_max_throughput
        if max_concurrency is not None and max_concurrency > 0 and p95_runtime > 0:
            theoretical_max = max_concurrency / p95_runtime
            self._current_metrics["theoretical_max_throughput"] = theoretical_max
        else:
            self._current_metrics["theoretical_max_throughput"] = None

        # Calculate estimated_time_remaining_seconds (ETA)
        # Only calculate if we have meaningful throughput (> 0.001 tasks/s)
        if throughput > 0.001 and self._current_metrics.get("tasks_remaining") is not None:
            eta = self._current_metrics["tasks_remaining"] / throughput
            # Cap ETA at reasonable values (max 1 week in seconds)
            eta = min(eta, 604800)
            self._current_metrics["estimated_time_remaining_seconds"] = eta
        else:
            self._current_metrics["estimated_time_remaining_seconds"] = None

        # Calculate actual_vs_theoretical_speed_percent
        theoretical = self._current_metrics.get("theoretical_max_throughput")
        if throughput > 0 and theoretical is not None and theoretical > 0:
            self._current_metrics["actual_vs_theoretical_speed_percent"] = (throughput / theoretical) * 100
        else:
            self._current_metrics["actual_vs_theoretical_speed_percent"] = None

        # NOTE: File monitor updates are handled by the background thread in _start_file_monitor_updater()
        # to avoid race conditions. We don't update file here to prevent competing writes.

    def _get_total_llm_rate_limit(self) -> float:
        """Get effective total RPM limit across active API keys."""
        active_keys = max(1, int(self._llm_active_keys))
        return float(self._llm_rate_limit) * active_keys

    def _calculate_percentile(self, percentile: int) -> Optional[float]:
        """
        Calculate the given percentile from tracked latencies.

        Args:
            percentile: Percentile to calculate (e.g., 95 for P95)

        Returns:
            Percentile value in milliseconds, or None if no data
        """
        if not self._llm_latencies:
            return None

        sorted_latencies = sorted(self._llm_latencies)
        n = len(sorted_latencies)

        if n == 1:
            return sorted_latencies[0]

        # Use linear interpolation for better accuracy
        # percentile/100 * (n - 1) gives the position in 0-indexed array
        position = (percentile / 100.0) * (n - 1)
        lower_index = int(position)
        upper_index = min(lower_index + 1, n - 1)

        # Linear interpolation
        if lower_index == upper_index:
            return sorted_latencies[lower_index]

        fraction = position - lower_index
        return sorted_latencies[lower_index] + fraction * (sorted_latencies[upper_index] - sorted_latencies[lower_index])

    def get_llm_stats(self) -> Dict[str, Any]:
        """
        Get LLM metrics statistics.

        Returns:
            Dictionary with LLM metrics
        """
        return {
            "total_requests": self._llm_total_requests,
            "current_rpm": self._current_metrics.get("llm_current_rpm"),
            "rate_limit": self._get_total_llm_rate_limit(),
            "rate_limit_usage_percent": self._current_metrics.get("llm_rate_limit_usage_percent"),
            "active_keys": self._llm_active_keys,
            "rate_limited_keys": self._llm_rate_limited_count,
            "p95_latency_ms": self._current_metrics.get("llm_p95_latency_ms"),
            "p99_latency_ms": self._current_metrics.get("llm_p99_latency_ms"),
            "realtime_cost": self._llm_realtime_cost,
            "latency_count": len(self._llm_latencies),
        }

    def reset_llm_metrics(self) -> None:
        """Reset all LLM metrics to initial state."""
        self._llm_latencies.clear()
        self._llm_request_times.clear()
        self._llm_realtime_cost = 0.0
        self._llm_total_requests = 0
        self._llm_rate_limited_count = 0
        self._llm_input_tokens = 0
        self._llm_output_tokens = 0

        # Reset current metrics
        self._current_metrics["llm_current_rpm"] = None
        self._current_metrics["llm_rate_limit_usage_percent"] = None
        self._current_metrics["llm_p95_latency_ms"] = None
        self._current_metrics["llm_p99_latency_ms"] = None
        self._current_metrics["llm_realtime_cost"] = None
        self._current_metrics["llm_rate_limited_keys"] = None
        self._current_metrics["llm_input_tokens"] = None
        self._current_metrics["llm_output_tokens"] = None

    # ==================== P2 GPU Optimization Metrics Methods ====================

    def record_oom_retry(self) -> None:
        """
        Record an OOM (Out of Memory) retry occurrence.

        This method should be called by external code when an OOM event occurs
        and the system retries with reduced memory usage.
        """
        self._gpu_oom_retry_count += 1
        self._current_metrics["gpu_oom_retry_count"] = self._gpu_oom_retry_count
        logger.debug(f"OOM retry recorded. Total OOM retries: {self._gpu_oom_retry_count}")

    def record_oom_event(self) -> None:
        """
        Record an OOM (Out of Memory) event occurrence.

        Alias for record_oom_retry() for compatibility.
        """
        self.record_oom_retry()

    def calculate_gpu_idle_time_percent(self) -> float:
        """
        Calculate the percentage of time the GPU has been idle.

        GPU is considered idle when utilization < 10%.

        Returns:
            Percentage of time GPU was idle (0.0 to 100.0)
        """
        if self._gpu_total_samples == 0:
            return 0.0

        idle_percent = (self._gpu_idle_samples / self._gpu_total_samples) * 100.0
        self._current_metrics["gpu_idle_time_percent"] = idle_percent
        return idle_percent

    def calculate_gpu_memory_efficiency_percent(self) -> float:
        """
        Calculate GPU memory efficiency percentage.

        Memory efficiency is calculated as:
        - (effective_memory_used / total_memory_available) * 100

        This provides insight into how efficiently GPU memory is being utilized.

        Returns:
            Memory efficiency percentage (0.0 to 100.0)
        """
        if self._gpu_total_memory_mb <= 0:
            return 0.0

        # Calculate average memory used during active periods (when GPU is working)
        if len(self._gpu_active_memory_samples) > 0:
            avg_active_memory = sum(self._gpu_active_memory_samples) / len(self._gpu_active_memory_samples)
            efficiency = (avg_active_memory / self._gpu_total_memory_mb) * 100.0
        elif self._gpu_peak_memory_mb > 0:
            # Fall back to peak memory if no active samples
            efficiency = (self._gpu_peak_memory_mb / self._gpu_total_memory_mb) * 100.0
        else:
            efficiency = 0.0

        self._current_metrics["gpu_memory_efficiency_percent"] = efficiency
        return efficiency

    def update_gpu_metrics_from_history(self) -> None:
        """
        Update all P2 GPU optimization metrics from historical data.

        This method recalculates idle time percentage and memory efficiency
        based on all samples collected in the history.
        """
        # Calculate idle time percentage
        self.calculate_gpu_idle_time_percent()

        # Calculate memory efficiency
        self.calculate_gpu_memory_efficiency_percent()

        # Update peak memory in current metrics
        self._current_metrics["gpu_peak_memory_mb"] = self._gpu_peak_memory_mb

        # Update OOM retry count
        self._current_metrics["gpu_oom_retry_count"] = self._gpu_oom_retry_count

    def get_gpu_optimization_stats(self) -> Dict[str, Any]:
        """
        Get P2 GPU optimization metrics statistics.

        Returns:
            Dictionary with GPU optimization metrics
        """
        # Update metrics from history
        self.update_gpu_metrics_from_history()

        return {
            "oom_retry_count": self._gpu_oom_retry_count,
            "idle_time_percent": self._current_metrics.get("gpu_idle_time_percent"),
            "peak_memory_mb": self._gpu_peak_memory_mb,
            "total_memory_mb": self._gpu_total_memory_mb,
            "memory_efficiency_percent": self._current_metrics.get("gpu_memory_efficiency_percent"),
            "total_samples": self._gpu_total_samples,
            "idle_samples": self._gpu_idle_samples,
        }

    def reset_gpu_metrics(self) -> None:
        """Reset all P2 GPU optimization metrics to initial state."""
        self._gpu_oom_retry_count = 0
        self._gpu_idle_samples = 0
        self._gpu_total_samples = 0
        self._gpu_peak_memory_mb = 0.0
        self._gpu_idle_memory_samples.clear()
        self._gpu_active_memory_samples.clear()
        self._gpu_total_memory_mb = 0.0

        # Reset current metrics
        self._current_metrics["gpu_oom_retry_count"] = None
        self._current_metrics["gpu_idle_time_percent"] = None
        self._current_metrics["gpu_peak_memory_mb"] = None
        self._current_metrics["gpu_memory_efficiency_percent"] = None

    def reset_for_new_experiment(self, exp_name: str, run_id: str = None) -> None:
        """Reset monitoring data for a new experiment."""
        # Clear events for new reset cycle
        self._metrics_updated.clear()

        self._tasks_completed = 0
        self._history.clear()
        self._start_time = time.time()
        self._current_metrics["run_mode"] = exp_name  # Reuse run_mode field for exp_name (legacy compatibility)
        self._current_metrics["exp_name"] = exp_name  # Update exp_name in metrics
        # Also update instance variables for file path consistency
        if exp_name is not None:
            self._exp_name = exp_name
        if run_id is not None:
            self._run_id = run_id
        self._current_metrics["llm_total_cost"] = 0.0
        # Reset other cumulative metrics
        self._current_metrics["active_tasks"] = 0
        self._current_metrics["queue_length"] = 0
        self._current_metrics["throughput_tasks_per_second"] = 0.0
        self._current_metrics["p95_runtime_seconds"] = 0.0
        self._current_metrics["max_concurrency"] = None  # Will be set by scheduler
        self._current_metrics["total_tasks"] = None  # Will be set by scheduler
        self._current_metrics["tasks_remaining"] = None
        self._current_metrics["progress_percent"] = 0.0
        # Reset LLM metrics
        self.reset_llm_metrics()
        # Reset GPU metrics
        self.reset_gpu_metrics()
        logger.info(f"SystemMonitor reset for new experiment: {exp_name}")

        # Signal that metrics have been updated for the new experiment
        self._metrics_updated.set()

        # Immediately write reset state to file to prevent race condition with background updater
        self._write_current_metrics_to_file()

    def _write_current_metrics_to_file(self) -> None:
        """Write current metrics to file immediately (used for reset)"""
        try:
            from dslighting.utils.file_monitor import get_file_monitor
            file_monitor = get_file_monitor(self._exp_name, self._run_id)
            data = self._current_metrics.copy()
            data['tasks_completed'] = self._tasks_completed  # Include tasks_completed
            file_monitor.update(data)
        except Exception:
            pass

    def get_snapshot(self) -> SystemSnapshot:
        """Get the current system snapshot."""
        # Note: gpu_usage needs to be copied to avoid reference issues
        metrics_copy = self._current_metrics.copy()
        metrics_copy["gpu_usage"] = self._current_metrics["gpu_usage"].copy()
        return SystemSnapshot(
            timestamp=time.time(),
            **metrics_copy,
        )

    def get_history(self) -> List[SystemSnapshot]:
        """Get all historical snapshots."""
        return list(self._history)

    def analyze_bottleneck(self) -> Dict[str, Any]:
        """
        Analyze current metrics to identify the primary bottleneck and generate optimization suggestions.

        This method examines system metrics to determine:
        - primary_bottleneck: Main bottleneck ("LLM", "GPU", "CPU", "Memory", "I/O", or "None")
        - bottleneck_severity: 0-100 severity score based on how severe the bottleneck is
        - efficiency_percent: (actual_throughput / theoretical_max_throughput) * 100
        - optimization_suggestion: Dynamic suggestions for optimization

        Returns:
            Dictionary containing bottleneck analysis results
        """
        m = self._current_metrics

        # Extract metrics
        cpu_percent = m.get("cpu_usage_percent", 0.0)
        memory_percent = m.get("memory_usage_percent", 0.0)
        queue_length = m.get("queue_length", 0)
        active_tasks = m.get("active_tasks", 0)
        max_concurrency = m.get("max_concurrency", 1)
        throughput = m.get("throughput_tasks_per_second", 0.0)
        p95_runtime = m.get("p95_runtime_seconds", 0.0)
        gpu_usage = m.get("gpu_usage", {})

        # LLM metrics
        llm_rate_limit_usage = m.get("llm_rate_limit_usage_percent", 0.0)
        llm_rate_limited = m.get("llm_rate_limited_keys", 0)
        llm_p95_latency = m.get("llm_p95_latency_ms", 0.0)

        # Calculate theoretical maximum throughput
        # Based on max_concurrency and p95_runtime (tasks completing at P95 rate)
        if max_concurrency is not None and max_concurrency > 0 and p95_runtime is not None and p95_runtime > 0:
            theoretical_max = max_concurrency / p95_runtime
        else:
            # Fallback: estimate based on concurrency and assuming 1s per task
            theoretical_max = float(max_concurrency or 1)

        # Calculate efficiency percentage (round to 2 decimal places)
        if theoretical_max > 0:
            efficiency = round(min((throughput / theoretical_max) * 100, 100.0), 2)
        else:
            efficiency = 0.0

        # Determine GPU utilization
        gpu_utilization = 0.0
        gpu_memory_percent = 0.0
        if gpu_usage:
            total_util = 0.0
            total_mem = 0.0
            total_mem_capacity = 0.0
            for gpu_id, data in gpu_usage.items():
                total_util += data.get("utilization_percent", 0.0)
                total_mem += data.get("memory_used_mb", 0.0)
                total_mem_capacity += data.get("memory_total_mb", 1.0)
            gpu_utilization = total_util / len(gpu_usage) if gpu_usage else 0.0
            gpu_memory_percent = (total_mem / total_mem_capacity * 100) if total_mem_capacity > 0 else 0.0

        # Identify primary bottleneck
        bottleneck = "None"
        severity = 0.0
        suggestions = []

        # Check LLM bottlenecks first (highest priority for LLM-bound workloads)
        llm_high_latency = llm_p95_latency is not None and llm_p95_latency > 2000  # > 2 seconds P95
        llm_rate_critical = llm_rate_limit_usage is not None and llm_rate_limit_usage > 90.0
        llm_rate_warning = llm_rate_limit_usage is not None and llm_rate_limit_usage > 70.0

        if llm_rate_critical or (llm_high_latency and llm_rate_warning):
            bottleneck = "LLM"
            severity = round(min((llm_rate_limit_usage or 0) + (20 if llm_high_latency else 0), 100.0), 2)
            if llm_rate_critical:
                suggestions.append("LLM rate limit approaching critical (>90%), consider API key rotation")
            if llm_high_latency:
                suggestions.append(f"High LLM latency ({llm_p95_latency:.0f}ms P95), consider reducing concurrency")
            suggestions.append("Consider batching requests or using faster LLM model")
        elif llm_rate_warning:
            bottleneck = "LLM"
            severity = round((llm_rate_limit_usage or 0) * 0.6, 2)
            suggestions.append(f"LLM rate limit at {llm_rate_limit_usage:.0f}%, monitor closely")

        # Check GPU bottlenecks
        elif gpu_utilization is not None and gpu_utilization > 80.0:
            bottleneck = "GPU"
            severity = round(min(gpu_utilization * 0.8, 100.0), 2)
            if gpu_memory_percent is not None and gpu_memory_percent > 90.0:
                suggestions.append(f"GPU memory nearly full ({gpu_memory_percent:.0f}%), reduce batch size")
            else:
                suggestions.append("GPU utilization high, consider increasing batch size if memory allows")
            suggestions.append("GPU compute is the bottleneck")

        # Check CPU bottlenecks
        elif cpu_percent is not None and cpu_percent > 80.0:
            bottleneck = "CPU"
            severity = round(min(cpu_percent * 0.8, 100.0), 2)
            if active_tasks is not None and max_concurrency is not None and active_tasks < max_concurrency * 0.5:
                suggestions.append(f"Low concurrency utilization ({active_tasks}/{max_concurrency}), increase active tasks")
            else:
                suggestions.append("CPU saturated, consider offloading to GPU if applicable")
            suggestions.append("CPU compute is the bottleneck")

        # Check Memory bottlenecks
        elif memory_percent is not None and memory_percent > 85.0:
            bottleneck = "Memory"
            severity = round(min(memory_percent, 100.0), 2)
            suggestions.append(f"Memory usage high ({memory_percent:.0f}%), consider reducing cache size")
            suggestions.append("Monitor for potential out-of-memory conditions")

        # Check I/O bottlenecks (queue high but resources not saturated)
        elif queue_length is not None and queue_length > (max_concurrency or 1) * 2:
            cpu_ok = cpu_percent is None or cpu_percent < 60.0
            gpu_ok = gpu_utilization is None or gpu_utilization < 60.0
            if cpu_ok and gpu_ok:
                bottleneck = "I/O"
                severity = round(min((queue_length / ((max_concurrency or 1) * 4)) * 100, 100.0), 2)
                suggestions.append("High queue length with low resource utilization, check I/O waits")
                suggestions.append("Investigate disk I/O or network bottlenecks")

        # Generate optimization suggestions based on findings
        if bottleneck == "None":
            if efficiency < 50:
                suggestions.append("Low efficiency detected, consider tuning max_concurrency parameter")
                suggestions.append(f"Current throughput: {throughput:.2f} tasks/s, theoretical max: {theoretical_max:.2f}")
            elif efficiency > 90:
                suggestions.append("System running efficiently at optimal capacity")
            else:
                suggestions.append("System performing within expected parameters")

        # Add concurrency optimization suggestions
        if active_tasks is not None and max_concurrency is not None and active_tasks > 0 and max_concurrency > 0:
            utilization = (active_tasks / max_concurrency) * 100
            if utilization > 90:
                suggestions.append(f"Concurrency near max ({active_tasks}/{max_concurrency}), consider increasing to {min(max_concurrency * 2, 64)}")
            elif utilization < 30 and queue_length is not None and queue_length > 10:
                suggestions.append(f"Low concurrency utilization ({utilization:.0f}%), current settings may be too high")

        # Finalize suggestion string
        if suggestions:
            optimization_suggestion = "; ".join(suggestions[:3])  # Top 3 suggestions
        else:
            optimization_suggestion = "System operating normally"

        # Update current metrics
        self._current_metrics["primary_bottleneck"] = bottleneck
        self._current_metrics["bottleneck_severity"] = severity
        self._current_metrics["efficiency_percent"] = efficiency
        self._current_metrics["optimization_suggestion"] = optimization_suggestion

        return {
            "primary_bottleneck": bottleneck,
            "bottleneck_severity": severity,
            "efficiency_percent": efficiency,
            "optimization_suggestion": optimization_suggestion,
            "details": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_percent,
                "gpu_utilization_percent": gpu_utilization,
                "gpu_memory_percent": gpu_memory_percent,
                "queue_length": queue_length,
                "active_tasks": active_tasks,
                "max_concurrency": max_concurrency,
                "throughput_tasks_per_second": throughput,
                "theoretical_max_throughput": theoretical_max,
                "llm_rate_limit_usage_percent": llm_rate_limit_usage,
                "llm_p95_latency_ms": llm_p95_latency,
            }
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of monitored metrics over the entire history.

        Returns:
            Dictionary with statistics for each metric
        """
        if not self._history:
            return {
                "message": "No history available yet",
                "monitor_running": self._running,
            }

        snapshots = list(self._history)

        # Calculate statistics for each metric
        def calc_stats(values: List[float]) -> Dict[str, float]:
            if not values:
                return {"min": 0.0, "max": 0.0, "avg": 0.0}
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        cpu_values = [s.cpu_usage_percent for s in snapshots]
        memory_values = [s.memory_usage_percent for s in snapshots]
        throughput_values = [s.throughput_tasks_per_second for s in snapshots]

        summary = {
            "monitor_running": self._running,
            "duration_seconds": time.time() - self._start_time if self._start_time else 0.0,
            "snapshots_collected": len(snapshots),
            "tasks_completed": self._tasks_completed,
            "cpu_usage": calc_stats(cpu_values),
            "memory_usage": calc_stats(memory_values),
            "throughput": calc_stats(throughput_values),
            "current_snapshot": self.get_snapshot().__dict__,
        }

        # Add GPU summary if available
        if self._current_metrics["gpu_usage"]:
            gpu_summary = {}
            for gpu_id, gpu_data in self._current_metrics["gpu_usage"].items():
                gpu_summary[f"gpu_{gpu_id}"] = {
                    "utilization_percent": gpu_data["utilization_percent"],
                    "memory_used_percent": gpu_data["memory_used_percent"],
                }
            summary["gpu_usage"] = gpu_summary

        return summary

    def print_summary(self) -> None:
        """Print a formatted summary to the logger."""
        summary = self.get_summary()

        if "message" in summary:
            logger.info(f"Monitor: {summary['message']}")
            return

        logger.info("=" * 80)
        logger.info("System Monitor Summary")
        logger.info("=" * 80)
        logger.info(f"Running: {summary['monitor_running']}")
        logger.info(f"Duration: {summary['duration_seconds']:.1f}s")
        logger.info(f"Tasks completed: {summary['tasks_completed']}")
        logger.info("")

        logger.info("Resource Usage:")
        logger.info(f"  CPU:    {summary['cpu_usage']['avg']:.1f}% (min={summary['cpu_usage']['min']:.1f}%, max={summary['cpu_usage']['max']:.1f}%)")
        logger.info(f"  Memory: {summary['memory_usage']['avg']:.1f}% (min={summary['memory_usage']['min']:.1f}%, max={summary['memory_usage']['max']:.1f}%)")

        if "gpu_usage" in summary:
            logger.info("")
            logger.info("GPU Usage:")
            for gpu_name, gpu_data in summary["gpu_usage"].items():
                logger.info(f"  {gpu_name}: {gpu_data['utilization_percent']:.1f}% util, {gpu_data['memory_used_percent']:.1f}% memory")

        logger.info("")
        logger.info("Performance:")
        logger.info(f"  Throughput: {summary['throughput']['avg']:.4f} tasks/s")
        logger.info("=" * 80)


# Global monitor instance
_global_monitor: Optional[SystemMonitor] = None
_web_monitor_started = False  # Prevent duplicate Web server startup


def get_global_monitor() -> Optional[SystemMonitor]:
    """Get the global system monitor instance."""
    return _global_monitor


async def start_global_monitor(
    update_interval: float = 1.0,
    history_size: int = 1000,
    enable_gpu_monitoring: bool = True,
    auto_start_web: bool = True,
    enable_file_sharing: bool = True,  # Enable file sharing (cross-process monitoring)
    exp_name: Optional[str] = None,  # Experiment name for independent monitoring
    run_id: Optional[str] = None,  # Run ID for independent monitoring
) -> SystemMonitor:
    """
    Start the global system monitor.

    Args:
        update_interval: Seconds between metric collection
        history_size: Maximum number of snapshots to keep
        enable_gpu_monitoring: Whether to monitor GPU usage
        auto_start_web: Whether to automatically start web monitoring server
        enable_file_sharing: Whether to enable file-based metric sharing for cross-process monitoring
        exp_name: Optional experiment name for independent monitoring
        run_id: Optional run ID for independent monitoring

    Returns:
        The started SystemMonitor instance
    """
    global _global_monitor, _web_monitor_started

    if _global_monitor is None:
        _global_monitor = SystemMonitor(
            update_interval=update_interval,
            history_size=history_size,
            enable_gpu_monitoring=enable_gpu_monitoring,
        )

    await _global_monitor.start()

    # Store exp_name and run_id in the monitor instance for later use
    _global_monitor._exp_name = exp_name
    _global_monitor._run_id = run_id
    # Also update _current_metrics so it gets written to the file
    _global_monitor._current_metrics["exp_name"] = exp_name
    # Note: run_id is NOT added to _current_metrics because SystemSnapshot doesn't have this field
    # run_id is stored in _run_id instance variable and accessed directly in web_monitor

    # Start file sharing monitor (automatically write system resources to file)
    if enable_file_sharing:
        _start_file_monitor_updater(_global_monitor, update_interval, exp_name, run_id)

    # Auto-start Web monitoring server (only once)
    if auto_start_web and not _web_monitor_started:
        _start_web_monitor_in_background()
        _web_monitor_started = True

    return _global_monitor


def _start_file_monitor_updater(monitor: SystemMonitor, interval: float, exp_name: Optional[str] = None, run_id: Optional[str] = None) -> None:
    """Start background thread to periodically write system resources to file (for other processes to read)."""
    if exp_name is not None:
        monitor._exp_name = exp_name
    if run_id is not None:
        monitor._run_id = run_id

    if monitor._file_updater_thread is not None and monitor._file_updater_thread.is_alive():
        logger.debug(
            "[FileUpdater] Reusing existing thread for exp_name=%s, run_id=%s",
            monitor._exp_name,
            monitor._run_id,
        )
        return

    def update_file_loop():
        try:
            from dslighting.utils.file_monitor import get_file_monitor

            file_monitor = None
            current_key = (None, None)
            logger.info("[FileUpdater] Started background monitor writer thread")

            while monitor._running:
                try:
                    key = (monitor._exp_name, monitor._run_id)
                    if file_monitor is None or key != current_key:
                        file_monitor = get_file_monitor(monitor._exp_name, monitor._run_id)
                        current_key = key
                        logger.info(
                            "[FileUpdater] Writing metrics to exp_name=%s, run_id=%s, file=%s",
                            monitor._exp_name,
                            monitor._run_id,
                            file_monitor.file_path,
                        )

                    snapshot = monitor.get_snapshot()

                    # Write system resources to file
                    file_monitor.update({
                        'language': snapshot.language,
                        'cpu_usage_percent': snapshot.cpu_usage_percent,
                        'memory_usage_percent': snapshot.memory_usage_percent,
                        'memory_used_gb': snapshot.memory_used_gb,
                        'memory_total_gb': snapshot.memory_used_gb + snapshot.memory_available_gb,

                        # DSLighting-specific metrics
                        'active_tasks': snapshot.active_tasks,
                        'queue_length': snapshot.queue_length,
                        'p95_runtime_seconds': snapshot.p95_runtime_seconds,
                        'throughput_tasks_per_second': snapshot.throughput_tasks_per_second,
                        'tasks_completed': monitor._tasks_completed,
                        'total_tasks': snapshot.total_tasks,
                        'run_mode': monitor._exp_name,  # Using exp_name as run_mode
                        'exp_name': monitor._exp_name,
                        'max_concurrency': snapshot.max_concurrency,
                        'concurrency_utilization': snapshot.concurrency_utilization,
                        'llm_total_cost': snapshot.llm_total_cost,

                        # P0 LLM Service Metrics
                        'llm_current_rpm': snapshot.llm_current_rpm,
                        'llm_rate_limit': snapshot.llm_rate_limit,
                        'llm_rate_limit_usage_percent': snapshot.llm_rate_limit_usage_percent,
                        'llm_active_api_keys': snapshot.llm_active_api_keys,
                        'llm_rate_limited_keys': snapshot.llm_rate_limited_keys,
                        'llm_p95_latency_ms': snapshot.llm_p95_latency_ms,
                        'llm_p99_latency_ms': snapshot.llm_p99_latency_ms,
                        'llm_realtime_cost': snapshot.llm_realtime_cost,
                        'llm_input_tokens': snapshot.llm_input_tokens,
                        'llm_output_tokens': snapshot.llm_output_tokens,

                        # P1 Bottleneck Identification Metrics
                        'primary_bottleneck': snapshot.primary_bottleneck,
                        'bottleneck_severity': snapshot.bottleneck_severity,
                        'efficiency_percent': snapshot.efficiency_percent,
                        'optimization_suggestion': snapshot.optimization_suggestion,

                        # P1 Progress Estimation Metrics
                        'estimated_time_remaining_seconds': snapshot.estimated_time_remaining_seconds,
                        'theoretical_max_throughput': snapshot.theoretical_max_throughput,
                        'actual_vs_theoretical_speed_percent': snapshot.actual_vs_theoretical_speed_percent,
                        'tasks_remaining': snapshot.tasks_remaining,
                        'progress_percent': snapshot.progress_percent,

                        # P2 GPU Optimization Metrics
                        'gpu_oom_retry_count': snapshot.gpu_oom_retry_count,
                        'gpu_idle_time_percent': snapshot.gpu_idle_time_percent,
                        'gpu_peak_memory_mb': snapshot.gpu_peak_memory_mb,
                        'gpu_memory_efficiency_percent': snapshot.gpu_memory_efficiency_percent,
                    })
                    # Signal that first update is done
                    monitor._file_updater_first_update_done.set()
                except Exception as e:
                    logger.debug(f"File monitor update error: {e}")

                time.sleep(interval)
                logger.debug(f"[FileUpdater] After sleep, monitor._running={monitor._running}")

        except Exception as e:
            logger.debug(f"File monitor updater failed: {e}")

    # Start in background thread and store reference
    logger.info(
        "[FileUpdater] Starting thread for exp_name=%s, run_id=%s, monitor._running=%s",
        monitor._exp_name,
        monitor._run_id,
        monitor._running,
    )
    thread = threading.Thread(target=update_file_loop, daemon=True)
    thread.start()
    monitor._file_updater_thread = thread


def _start_web_monitor_in_background():
    """Start Web monitoring server in background (if available)"""

    def try_start_web():
        try:
            # Try to import Flask
            from flask import Flask, render_template_string, jsonify, Response
            from flask import stream_with_context

            # Use built-in WebMonitor (no external file dependency)
            from dslighting.monitoring.web_monitor import WebMonitor, find_available_port

            # Find available port
            port = find_available_port(8080)

            # Create and start Web server
            import webbrowser
            # Get language from current metrics (set via update_dslighting_metrics)
            # Note: _current_metrics["language"] defaults to None, so use or "zh" for fallback
            language = _global_monitor._current_metrics.get("language") or "zh"
            web_monitor = WebMonitor(host="127.0.0.1", port=port, language=language)
            web_monitor.monitor = _global_monitor

            # Auto-open browser
            threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()

            logger.info(f"Web monitor started: http://localhost:{port}")

            # Run server (blocking)
            web_monitor.run()
        except ImportError as e:
            logger.debug(f"Web monitoring not available (Flask not installed): {e}")
        except Exception as e:
            logger.warning(f"Web monitor startup failed: {e}")

    # Start in background thread
    web_thread = threading.Thread(target=try_start_web, daemon=True)
    web_thread.start()


async def stop_global_monitor() -> None:
    """Stop the global system monitor."""
    global _global_monitor

    if _global_monitor is not None:
        await _global_monitor.stop()
        _global_monitor = None
