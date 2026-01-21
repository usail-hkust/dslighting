"""
DSLighting 2.0 - State Layer

This layer manages memory and context for agents.

Components:
- JournalState: Search tree state that records all attempt history
- Experience: Meta-optimization experience across tasks
- ContextManager: Context management
- MemoryManager: Memory storage and retrieval (placeholder implementation)
"""

# Re-export DSAT state components
from dsat.services.states.journal import (
    JournalState,
    Node,
    MetricValue,
)

try:
    from dsat.services.states.experience import Experience
except ImportError:
    Experience = None

try:
    from dsat.utils.context import ContextManager
except ImportError:
    ContextManager = None

# DSLighting MemoryManager (placeholder implementation)
from dslighting.state.memory import MemoryManager

__all__ = [
    "JournalState",
    "Node",
    "MetricValue",
    "Experience",
    "MemoryManager",
    "ContextManager",
]
