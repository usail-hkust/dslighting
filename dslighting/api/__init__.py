"""
DSLighting 2.0 - User-Facing API Layer

This is the top layer that users interact with directly.

Components:
- Agent: High-level agent interface
- AgentResult: Result object from agent execution
- DataLoader: Data loading utilities
- Convenience functions: run_agent, load_data, setup
"""

# Import from core (the real implementation)
from ..core.agent import Agent, AgentResult
from ..core.data_loader import DataLoader, TaskContext
from .convenience import run_agent, load_data, setup

__all__ = [
    "Agent",
    "AgentResult",
    "DataLoader",
    "TaskContext",
    "run_agent",
    "load_data",
    "setup",
]
