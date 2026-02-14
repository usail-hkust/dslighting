"""
Result processing utilities for DSLighting Agent.

This module contains functions for result logging, formatting,
and statistics collection. Extracted from agent.py to improve
code organization.
"""

import logging
from typing import List
import time

from dslighting.core.interfaces import AgentResult

logger = logging.getLogger(__name__)


def log_result(result: AgentResult, logger_instance: logging.Logger = None):
    """
    Log result summary.

    Args:
        result: AgentResult to log
        logger_instance: Logger instance for output (uses module logger if None)
    """
    log = logger_instance or logger

    if result.success:
        log.info(
            f"✓ Task completed successfully | "
            f"Score: {result.score or 'N/A'} | "
            f"Cost: ${result.cost:.4f} | "
            f"Duration: {result.duration:.1f}s"
        )
    else:
        log.error(
            f"✗ Task failed | "
            f"Error: {result.error} | "
            f"Cost: ${result.cost:.4f}"
        )


def format_agent_repr(workflow_name: str, model_name: str) -> str:
    """
    Format Agent string representation.

    Args:
        workflow_name: Workflow name
        model_name: Model name

    Returns:
        Formatted string representation
    """
    return (
        f"Agent(workflow='{workflow_name}', "
        f"model='{model_name}', "
        f"results_count={0})"  # Will be filled by Agent class
    )


def calculate_statistics(results: List[AgentResult]) -> dict:
    """
    Calculate statistics from a list of results.

    Args:
        results: List of AgentResult objects

    Returns:
        Dictionary with statistics:
        - total_runs: Total number of runs
        - successful_runs: Number of successful runs
        - failed_runs: Number of failed runs
        - total_cost: Total cost across all runs
        - average_cost: Average cost per run
        - average_score: Average score (for successful runs)
        - total_duration: Total duration across all runs
    """
    if not results:
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_cost": 0.0,
            "average_cost": 0.0,
            "average_score": None,
            "total_duration": 0.0
        }

    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]

    total_cost = sum(r.cost for r in results)
    total_duration = sum(r.duration for r in results)

    successful_scores = [r.score for r in successful_results if r.score is not None]
    average_score = sum(successful_scores) / len(successful_scores) if successful_scores else None

    return {
        "total_runs": len(results),
        "successful_runs": len(successful_results),
        "failed_runs": len(failed_results),
        "total_cost": total_cost,
        "average_cost": total_cost / len(results),
        "average_score": average_score,
        "total_duration": total_duration
    }
