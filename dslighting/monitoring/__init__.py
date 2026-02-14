"""
DSLighting Monitoring Module

Real-time system monitoring for DSLighting.

Components:
- SystemMonitor: Real-time system resource and performance monitoring
- WebMonitor: Web-based UI for monitoring
- SystemSnapshot: Data class for system metric snapshots

This module provides tools for monitoring system resources and performance
metrics in real-time, enabling visibility into optimization effectiveness.
"""

from dslighting.monitoring.monitoring import (
    SystemMonitor,
    SystemSnapshot,
    start_global_monitor,
    get_global_monitor,
    stop_global_monitor,
)

from dslighting.monitoring.web_monitor import (
    WebMonitor,
    find_available_port,
)

__all__ = [
    "SystemMonitor",
    "SystemSnapshot",
    "start_global_monitor",
    "get_global_monitor",
    "stop_global_monitor",
    "WebMonitor",
    "find_available_port",
]
