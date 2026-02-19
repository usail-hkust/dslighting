"""Stable public API for DSLighting.

Import user-facing objects from this module when you need a compatibility
commitment across minor releases.
"""

from dslighting.api.agent import Agent
from dslighting.api.benchmark import DSBenchmark
from dslighting.api.convenience import load_data, run_agent, setup
from dslighting.config import DSLightingConfig
from dslighting.core.data import DataLoader, TaskContext
from dslighting.core.interfaces import AgentResult

__all__ = [
    "Agent",
    "AgentResult",
    "DataLoader",
    "TaskContext",
    "run_agent",
    "load_data",
    "setup",
    "DSBenchmark",
    "DSLightingConfig",
]
