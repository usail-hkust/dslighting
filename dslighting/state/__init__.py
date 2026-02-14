"""
DSLighting 2.0 - State Layer

This layer manages memory and context for agents.

Components:
- JournalState: Search tree state that records all attempt history
- Experience: Meta-optimization experience across tasks
- ContextManager: Context management
- MemoryManager: Memory storage and retrieval (placeholder implementation)
"""

# Canonical state components
from dslighting.state.base import State
from dslighting.state.search.journal import JournalState, Node, MetricValue
from dslighting.state.autokaggle import AutoKaggleState, PhaseMemory, AttemptMemory
from dslighting.state.dsagent import DSAgentState
from dslighting.state.operator_library import OperatorLibrary

try:
    from dslighting.state.search.experience import Experience
except ImportError:
    # Experience depends on optional deps (e.g., numpy)
    Experience = None

try:
    from dslighting.state.context import ContextManager
except ImportError:
    ContextManager = None

# DSLighting MemoryManager (placeholder implementation)
from dslighting.state.memory import MemoryManager

__all__ = [
    "State",
    "JournalState",
    "Node",
    "MetricValue",
    "AutoKaggleState",
    "PhaseMemory",
    "AttemptMemory",
    "DSAgentState",
    "OperatorLibrary",
    "Experience",
    "MemoryManager",
    "ContextManager",
]
