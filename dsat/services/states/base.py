"""
Defines the abstract base class for all state management services in DSAT.
"""
from abc import ABC

class State(ABC):
    """
    Abstract base class for state managers.

    This class serves as a common interface and type hint for different state
    management strategies used by various agent paradigms, such as journaling for
    tree-based search or linear phase logs for sequential workflows.
    """
    pass