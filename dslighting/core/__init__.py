"""
DSLighting Core Modules

Internal module; prefer importing from the package root (`dslighting`) for the single public entrypoint.
"""

# Core interfaces
from .interfaces import AgentResult, AgentInterface

# Re-export selected internal APIs
from .data import DataLoader, TaskContext
from .detection import TaskDetector
from .config import ConfigBuilder

__all__ = [
    "DataLoader",
    "TaskContext",
    "AgentResult",
    "AgentInterface",
    "TaskDetector",
    "ConfigBuilder",
]

# Note: DSLightingRunner/Runner should be imported from dslighting.runner directly
# to avoid circular dependencies between core and runtime modules