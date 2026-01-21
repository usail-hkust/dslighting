"""
Parallel Operator - Concurrent Orchestration

Executes multiple operators concurrently and aggregates results.
"""

import asyncio
from typing import List, Any, Dict, Literal


class Parallel:
    """
    Parallel orchestration - execute operators concurrently.

    Example:
        parallel = Parallel([
            model1_op,
            model2_op,
            model3_op,
        ], aggregation="best")
        result = await parallel.execute(
            description=description,
            data_dir=data_dir
        )
    """

    def __init__(
        self,
        operators: List[Any],
        aggregation: Literal["first_success", "best", "all", "majority"] = "first_success"
    ):
        """
        Initialize parallel execution.

        Args:
            operators: List of operators to execute in parallel
            aggregation: How to combine results:
                - "first_success": Return first successful result
                - "best": Return result with best score
                - "all": Return all results
                - "majority": Return most common result
        """
        self.operators = operators
        self.aggregation = aggregation

    async def _execute_single(self, operator, **kwargs):
        """Execute a single operator and capture exceptions."""
        try:
            return await operator(**kwargs)
        except Exception as e:
            return {"error": str(e), "success": False}

    async def execute(self, **kwargs) -> Any:
        """
        Execute all operators in parallel.

        Args:
            **kwargs: Input arguments for all operators

        Returns:
            Aggregated result based on aggregation strategy
        """
        # Execute all operators concurrently
        tasks = [self._execute_single(op, **kwargs) for op in self.operators]
        results = await asyncio.gather(*tasks)

        # Filter out failed results
        successful_results = [r for r in results if not isinstance(r, dict) or not r.get("error")]

        if not successful_results:
            # All failed, return first error
            return results[0]

        # Aggregate based on strategy
        if self.aggregation == "first_success":
            return successful_results[0]

        elif self.aggregation == "best":
            # Find result with best score
            def get_score(result):
                if hasattr(result, 'score'):
                    return result.score
                elif isinstance(result, dict) and 'score' in result:
                    return result['score']
                return 0.0

            return max(successful_results, key=get_score)

        elif self.aggregation == "all":
            return successful_results

        elif self.aggregation == "majority":
            # For now, return first success (full voting requires more logic)
            return successful_results[0]

        else:
            return successful_results[0]

    async def __call__(self, **kwargs) -> Any:
        """Allow parallel to be called like a function."""
        return await self.execute(**kwargs)
