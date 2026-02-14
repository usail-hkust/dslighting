#!/usr/bin/env python3
"""
DSLighting Real-time Monitoring Web Server

Features:
- Real-time system resource monitoring
- Task progress tracking
- Agent status
- Benchmark statistics
- Real-time data streaming

Usage:
    # Start monitoring server
    python -m dslighting.monitoring.web_monitor

    # Run benchmark in another terminal
    MAX_ITERATIONS=3 python benchmarks/run_dabench_full_fine_dag.py

    # Open browser
    http://localhost:8080
"""
import asyncio
import glob
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Dict, Optional

try:
    from flask import Flask, render_template, jsonify, Response
    from flask import stream_with_context
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not installed. Install: pip install flask")

from dslighting.monitoring.monitoring import start_global_monitor, get_global_monitor, SystemMonitor

# Get the template directory path
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


class WebMonitor:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080, language: str = "en", run_dir: Optional[str] = None):
        """
        Initialize the WebMonitor server.

        Args:
            host: Host address to bind to
            port: Port number to listen on
            language: UI language ('en' or 'zh')
            run_dir: Optional directory to copy monitoring data to
        """
        self.host = host
        self.port = port
        self.language = language
        self.run_dir = run_dir
        self.app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
        self.monitor: Optional[SystemMonitor] = None
        self._setup_routes()

    def _get_template_name(self) -> str:
        """Get the appropriate HTML template filename based on language."""
        return "monitor_zh.html" if self.language == "zh" else "monitor_en.html"

    def _setup_routes(self) -> None:
        """Configure Flask routes for the monitoring web server."""
        @self.app.route('/')
        def index():
            return render_template(self._get_template_name())

        @self.app.route('/stream')
        def stream():
            def generate():
                try:
                    while True:
                        snapshot = self._get_snapshot_data()
                        yield f"data: {json.dumps(snapshot)}\n\n"
                        time.sleep(1)
                except GeneratorExit:
                    pass
                except Exception as e:
                    print(f"Stream error: {e}")

            return Response(stream_with_context(generate()), mimetype="text/event-stream")

        @self.app.route('/api/snapshot')
        def api_snapshot():
            return jsonify(self._get_snapshot_data())

        @self.app.route('/api/summary')
        def api_summary():
            latest_monitor = get_global_monitor()
            if latest_monitor is not None and latest_monitor is not self.monitor:
                self.monitor = latest_monitor
            if not self.monitor:
                return jsonify({"error": "Monitor not started"})
            return jsonify(self.monitor.get_summary())

    def _get_snapshot_data(self) -> Dict:
        """Get current monitoring data snapshot for the web UI."""
        # The global monitor instance is recreated for each benchmark run.
        # Refresh reference here so the web page always follows the latest run.
        latest_monitor = get_global_monitor()
        if latest_monitor is not None and latest_monitor is not self.monitor:
            self.monitor = latest_monitor

        if not self.monitor:
            return {"status": "not_started", "message": "Monitor not started"}

        snapshot = self.monitor.get_snapshot()
        m = self.monitor._current_metrics
        history = self.monitor.get_history()
        cpu_values = [s.cpu_usage_percent for s in history]

        total_tasks = m.get('total_tasks')
        completed_raw = self.monitor._tasks_completed
        if total_tasks is not None and total_tasks > 0:
            completed = max(0, min(completed_raw, total_tasks))
        else:
            completed = max(0, completed_raw)
        progress = (completed / total_tasks * 100) if total_tasks else 0.0
        progress = max(0.0, min(progress, 100.0))

        start_time = datetime.now().strftime('%H:%M:%S')
        if self.monitor._start_time:
            try:
                start_time = datetime.fromtimestamp(self.monitor._start_time).strftime('%H:%M:%S')
            except (TypeError, ValueError, OSError):
                pass

        data = {
            "cpu": snapshot.cpu_usage_percent,
            "cpu_min": min(cpu_values) if cpu_values else 0,
            "cpu_max": max(cpu_values) if cpu_values else 0,
            "memory": snapshot.memory_usage_percent,
            "memory_used": snapshot.memory_used_gb,
            "memory_total": snapshot.memory_used_gb + snapshot.memory_available_gb,
            "active_tasks": m.get('active_tasks', snapshot.active_tasks),
            "queue_length": m.get('queue_length', snapshot.queue_length),
            "throughput": m.get('throughput_tasks_per_second', snapshot.throughput_tasks_per_second),
            "completed": completed,
            "total": total_tasks if total_tasks is not None else 0,
            "progress": progress,
            "gpus": [{"id": k, "utilization": v["utilization_percent"], "memory_used": v["memory_used_mb"], "memory_total": v["memory_total_mb"]} for k, v in (snapshot.gpu_usage or {}).items()],
            "exp_name": m.get('exp_name'),
            "start_time": start_time,
            "llm_current_rpm": m.get('llm_current_rpm'),
            "llm_rate_limit": m.get('llm_rate_limit', 60),
            "llm_rate_limit_usage_percent": m.get('llm_rate_limit_usage_percent'),
            "llm_active_api_keys": m.get('llm_active_api_keys'),
            "llm_rate_limited_keys": m.get('llm_rate_limited_keys', 0),
            "llm_p95_latency_ms": m.get('llm_p95_latency_ms'),
            "llm_p99_latency_ms": m.get('llm_p99_latency_ms'),
            "llm_realtime_cost": m.get('llm_realtime_cost'),
            "llm_input_tokens": m.get('llm_input_tokens'),
            "llm_output_tokens": m.get('llm_output_tokens'),
            "primary_bottleneck": m.get('primary_bottleneck'),
            "bottleneck_severity": m.get('bottleneck_severity'),
            "efficiency_percent": m.get('efficiency_percent'),
            "optimization_suggestion": m.get('optimization_suggestion'),
            "estimated_time_remaining_seconds": m.get('estimated_time_remaining_seconds'),
            "theoretical_max_throughput": m.get('theoretical_max_throughput'),
            "actual_vs_theoretical_speed_percent": m.get('actual_vs_theoretical_speed_percent'),
            "tasks_remaining": m.get('tasks_remaining'),
            "gpu_oom_retry_count": m.get('gpu_oom_retry_count', 0),
            "gpu_idle_time_percent": m.get('gpu_idle_time_percent'),
            "gpu_peak_memory_mb": m.get('gpu_peak_memory_mb'),
            "gpu_memory_efficiency_percent": m.get('gpu_memory_efficiency_percent'),
        }

        # Copy monitoring data to run_dir if configured
        if self.run_dir:
            self._copy_monitor_data_to_run_dir(data)

        return data

    def _copy_monitor_data_to_run_dir(self, current_data: Dict) -> None:
        """Copy monitoring data from /tmp/dslighting_monitor_*.json to run_dir."""
        if not self.run_dir or not os.path.isdir(self.run_dir):
            return

        try:
            # Create monitors subdirectory with timestamp
            monitors_dir = os.path.join(self.run_dir, "monitors")
            Path(monitors_dir).mkdir(parents=True, exist_ok=True)

            # Generate filename with current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = os.path.join(monitors_dir, f"{timestamp}_monitoring.json")

            # Find monitoring files in /tmp
            tmp_pattern = "/tmp/dslighting_monitor_*.json"
            tmp_files = glob.glob(tmp_pattern)

            # If tmp files exist, copy the matched one; otherwise write current data
            exp_name = current_data.get('exp_name')
            matched_file = None

            if tmp_files:
                if exp_name:
                    # Look for file with exp_name in filename
                    for f in tmp_files:
                        if exp_name in os.path.basename(f):
                            matched_file = f
                            break

                if matched_file:
                    shutil.copy2(matched_file, target_path)
                    return

            # Write current data directly
            self._write_monitor_file(target_path, current_data)

        except Exception as e:
            print(f"Warning: Failed to copy monitoring data to run_dir: {e}")

    def _write_monitor_file(self, path: str, data: Dict) -> None:
        """Write monitoring data to file."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to write monitoring file: {e}")

    async def start_monitor(self) -> None:
        """Start the global system monitor."""
        from dslighting.monitoring.monitoring import get_global_monitor, start_global_monitor, SystemMonitor

        # Check if global monitor already exists
        existing_monitor = get_global_monitor()
        if existing_monitor is not None:
            self.monitor = existing_monitor
            print("SystemMonitor: Using existing global monitor")
        else:
            # Start a new global monitor
            self.monitor = await start_global_monitor(
                update_interval=1.0,
                enable_gpu_monitoring=True,
                auto_start_web=False,  # Don't auto-start web monitor from here
            )
            print("SystemMonitor started")

    def run(self) -> None:
        """Run the web monitoring server."""
        print(f"DSLighting Web Monitor ({self.language})")
        print(f"Starting server on http://{self.host}:{self.port}")

        async def run_monitor():
            await self.start_monitor()

        def run_monitor_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_monitor())

        monitor_thread = Thread(target=run_monitor_thread, daemon=True)
        monitor_thread.start()

        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)


def find_available_port(start_port: int = 8080, max_attempts: int = 10) -> int:
    """
    Find an available port to bind to.

    Args:
        start_port: Starting port number to try
        max_attempts: Maximum number of ports to try

    Returns:
        Available port number
    """
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
            return port
        except OSError:
            continue
    return start_port


def main() -> None:
    """Main entry point for the web monitor."""
    print("DSLighting Web Monitor")
    print("=" * 50)

    if not FLASK_AVAILABLE:
        print("Flask not installed!")
        print("Install: pip install flask")
        return

    port = find_available_port(8080)
    language = os.getenv("DSLIGHTING_LANGUAGE", "en")
    run_dir = os.getenv("DSLIGHTING_RUN_DIR", None)

    print(f"Language: {language}")
    print(f"Port: {port}")
    if run_dir:
        print(f"Run Dir: {run_dir}")
    print()

    monitor = WebMonitor(host="0.0.0.0", port=port, language=language, run_dir=run_dir)

    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\nMonitor stopped")
