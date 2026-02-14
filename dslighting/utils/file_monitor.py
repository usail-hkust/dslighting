"""
File Shared Monitor System

Multiple processes can share monitoring data via files.

WARNING: This module uses global singletons (_global_file_monitor) which may cause
issues in certain concurrent scenarios. While the FileSharedMonitor class itself
is thread-safe (uses internal locking), the global instance returned by
get_file_monitor() is shared across all callers. For isolated monitoring needs,
consider instantiating FileSharedMonitor directly with a custom file path instead
of relying on the global singleton.
"""
from __future__ import annotations

import json
import re
import time
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
import atexit


class FileSharedMonitor:
    """System for sharing monitoring data via files"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._lock = threading.Lock()
        self._last_data: Dict[str, Any] = {}

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def update(self, data: Dict[str, Any]) -> None:
        """Update monitoring data"""
        with self._lock:
            self._last_data = data
            data['_timestamp'] = time.time()

            try:
                # Ensure directory exists (handle race conditions)
                self.file_path.parent.mkdir(parents=True, exist_ok=True)

                # Atomic write
                temp_file = self.file_path.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(data, f)
                temp_file.replace(self.file_path)
            except FileNotFoundError:
                # Directory might have been deleted, try again after recreating
                try:
                    self.file_path.parent.mkdir(parents=True, exist_ok=True)
                    temp_file = self.file_path.with_suffix('.tmp')
                    with open(temp_file, 'w') as f:
                        json.dump(data, f)
                    temp_file.replace(self.file_path)
                except Exception as e:
                    pass  # Silently fail if we still can't write
            except Exception as e:
                print(f"Failed to write monitoring data: {e}")

    def read(self) -> Dict[str, Any]:
        """Read monitoring data"""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass

        # Return default values
        return self._get_default_data()

    def _get_default_data(self) -> Dict[str, Any]:
        """Get default data"""
        return {
            'language': 'zh',  # Default Chinese, optional 'en'
            'active_tasks': 0,
            'queue_length': 0,
            'p95_runtime_seconds': 0.0,
            'throughput_tasks_per_second': 0.0,
            'tasks_completed': 0,
            'total_tasks': 257,
            'llm_total_cost': 0.0,
            'max_concurrency': None,
            'concurrency_utilization': None,
            'exp_name': None,

            # P0 LLM Service Metrics
            'llm_current_rpm': None,
            'llm_rate_limit': None,
            'llm_rate_limit_usage_percent': None,
            'llm_active_api_keys': None,
            'llm_rate_limited_keys': None,
            'llm_p95_latency_ms': None,
            'llm_p99_latency_ms': None,
            'llm_realtime_cost': None,
            'llm_input_tokens': None,
            'llm_output_tokens': None,

            # P1 Bottleneck & Progress Metrics
            'primary_bottleneck': None,
            'bottleneck_severity': None,
            'efficiency_percent': None,
            'optimization_suggestion': None,
            'estimated_time_remaining_seconds': None,
            'theoretical_max_throughput': None,
            'actual_vs_theoretical_speed_percent': None,
            'tasks_remaining': None,
            'progress_percent': None,

            # P2 GPU Optimization Metrics
            'gpu_oom_retry_count': None,
            'gpu_idle_time_percent': None,
            'gpu_peak_memory_mb': None,
            'gpu_memory_efficiency_percent': None,
        }


# Global instance
_monitor_file = Path("/tmp/dslighting_monitor.json")
_global_file_monitor: Optional[FileSharedMonitor] = None
_global_monitors: Dict[str, FileSharedMonitor] = {}


def _get_monitor_file_path(exp_name: Optional[str] = None, run_id: Optional[str] = None) -> Path:
    """
    Generate monitor file path based on exp_name and run_id (UUID).

    Args:
        exp_name: Experiment name
        run_id: Run ID (8-char short UUID, auto-generated if None)

    Returns:
        Path to the monitor file
    """
    if exp_name is None and run_id is None:
        # Use default global monitor file
        return _monitor_file

    # Generate UUID if not provided
    if not run_id:
        run_id = str(uuid.uuid4())[:8]  # 8-char short UUID

    # Generate unique filename with exp_name and run_id
    if exp_name:
        # Sanitize exp_name for safe filename
        safe_name = re.sub(r'[^\w\-.]', '_', str(exp_name))
        filename = f"dslighting_monitor_{safe_name}_{run_id}.json"
    else:
        filename = f"dslighting_monitor_{run_id}.json"

    return Path("/tmp") / filename


def get_file_monitor(exp_name: Optional[str] = None, run_id: Optional[str] = None) -> FileSharedMonitor:
    """
    Get file monitor instance.

    Args:
        exp_name: Optional experiment name for independent monitoring
        run_id: Optional run ID for independent monitoring

    Returns:
        FileSharedMonitor instance

    Note:
        When exp_name and run_id are provided, returns an independent monitor
        for that specific experiment/run. Otherwise returns the global singleton.
    """
    global _global_file_monitor, _global_monitors

    # Use global monitor if no exp_name/run_id provided
    if exp_name is None and run_id is None:
        if _global_file_monitor is None:
            _global_file_monitor = FileSharedMonitor(_monitor_file)
        return _global_file_monitor

    # Generate unique key for this monitor
    monitor_key = f"{exp_name or ''}_{run_id or ''}"

    # Return cached monitor if exists
    if monitor_key in _global_monitors:
        return _global_monitors[monitor_key]

    # Create new independent monitor
    monitor_file = _get_monitor_file_path(exp_name, run_id)
    monitor = FileSharedMonitor(monitor_file)
    _global_monitors[monitor_key] = monitor

    return monitor


__all__ = [
    "FileSharedMonitor",
    "get_file_monitor",
]
