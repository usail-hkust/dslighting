"""
Pipeline Operator - Sequential Orchestration

Executes operators in sequence, passing the output of one as input to the next.
"""

import asyncio
from typing import List, Any, Dict


class Pipeline:
    """
    Pipeline orchestration - execute operators sequentially.

    Example:
        pipeline = Pipeline([
            generate_op,
            execute_op,
            review_op,
        ])
        result = await pipeline.execute(
            plan_text=prompt,
            description=description,
            data_dir=data_dir
        )
    """

    def __init__(self, operators: List[Any]):
        """
        Initialize pipeline with a list of operators.

        Args:
            operators: List of operators to execute in sequence
        """
        self.operators = operators

    async def execute(self, **kwargs) -> Any:
        """
        Execute all operators in sequence.

        Args:
            **kwargs: Initial input arguments

        Returns:
            Output from the last operator
        """
        result = kwargs

        for i, operator in enumerate(self.operators):
            # Call operator with current result
            if hasattr(operator, '__call__'):
                result = await operator(**result)
            else:
                raise ValueError(f"Operator at index {i} is not callable")

        return result

    async def __call__(self, **kwargs) -> Any:
        """Allow pipeline to be called like a function."""
        return await self.execute(**kwargs)
