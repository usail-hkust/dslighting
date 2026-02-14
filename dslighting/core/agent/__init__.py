"""
Agent module - DSLighting's main agent interface.

This module contains the main Agent class and supporting utilities
for task execution, benchmark management, and result processing.
"""

# Main Agent class (canonical API)
from dslighting.api.agent import Agent

# Task handling utilities
from .task_handler import (
    determine_workflow,
    create_task_definition,
)

# Benchmark management utilities
from .benchmark_manager import (
    get_default_benchmark_dir,
    initialize_benchmark,
)

# Result processing utilities
from .result_processor import (
    log_result,
    format_agent_repr,
    calculate_statistics,
)

__all__ = [
    # Main Agent class
    "Agent",

    # Task handling
    "determine_workflow",
    "create_task_definition",

    # Benchmark management
    "get_default_benchmark_dir",
    "initialize_benchmark",

    # Result processing
    "log_result",
    "format_agent_repr",
    "calculate_statistics",
]