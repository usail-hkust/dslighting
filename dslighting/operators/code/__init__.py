"""
Code Operators - Code Execution Operations

These operators handle code execution and testing.
"""

try:
    from dsat.operators.code.execute import ExecuteAndTestOperator
except ImportError:
    ExecuteAndTestOperator = None

__all__ = [
    "ExecuteAndTestOperator",
]
