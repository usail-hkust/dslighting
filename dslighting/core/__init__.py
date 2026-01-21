"""
Core modules for DSLighting simplified API.
"""

from dslighting.core.agent import Agent, AgentResult
from dslighting.core.data_loader import DataLoader, TaskContext

# New unified API (recommended)
from dslighting.core.dataset import Dataset, load_dataset, DatasetInfo

# DSAT 继承 - 导出 types 和 config
try:
    from dslighting.core.types import *
    from dslighting.core.config import *
except ImportError:
    pass

__all__ = [
    # New unified API (recommended)
    "Dataset",
    "load_dataset",
    "DatasetInfo",

    # Legacy API (kept for backward compatibility)
    "DataLoader",
    "TaskContext",

    # Agent
    "Agent",
    "AgentResult",
]
