"""
Orchestration Operators - Operator Composition Patterns

These operators provide composition patterns for combining multiple operators:
- Pipeline: Sequential execution
- Parallel: Concurrent execution with aggregation
- Conditional: Branching logic
"""

from .pipeline import Pipeline
from .parallel import Parallel
from .conditional import Conditional

__all__ = [
    "Pipeline",
    "Parallel",
    "Conditional",
]
