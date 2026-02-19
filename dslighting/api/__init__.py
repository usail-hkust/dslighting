"""Layered API namespace for DSLighting.

Preferred import paths:
    - Stable public API: ``dslighting.api`` (or ``dslighting.api.public``)
    - Evolutionary internal API: ``dslighting.api.internal``
"""

from . import internal, public
from .internal import (
    TaskLoader,
    print_benchmark_banner,
    print_benchmark_info,
    validate_paths,
)
from .public import (
    Agent,
    AgentResult,
    DSBenchmark,
    DSLightingConfig,
    DataLoader,
    TaskContext,
    load_data,
    run_agent,
    setup,
)

__all__ = [
    "public",
    "internal",
    "Agent",
    "AgentResult",
    "DataLoader",
    "TaskContext",
    "run_agent",
    "load_data",
    "setup",
    "DSBenchmark",
    "DSLightingConfig",
    "TaskLoader",
    "print_benchmark_banner",
    "print_benchmark_info",
    "validate_paths",
]
