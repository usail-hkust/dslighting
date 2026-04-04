"""
Parallel Operator - Concurrent Orchestration

Executes multiple operators concurrently and aggregates results.
"""

import asyncio
import logging
from collections import Counter
from typing import List, Any, Dict, Literal, Callable, Optional, Tuple


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
                - "majority": Return most common result (>50% threshold)
        """
        self.operators = operators
        self.aggregation = aggregation
        self.logger = logging.getLogger(__name__)

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
            result, has_majority = self._majority_vote(successful_results)
            if not has_majority:
                self.logger.warning(
                    f"Majority aggregation: No majority (>50%) reached, "
                    f"using fallback result."
                )
            return result

        else:
            return successful_results[0]

    def _majority_vote(
        self,
        results: List[Any],
        *,
        key_func: Optional[Callable[[Any], Any]] = None,
        threshold: float = 0.5,
        min_count: Optional[int] = None
    ) -> Tuple[Any, bool]:
        """
        Perform majority voting on results.

        Majority rule: if >threshold (default: 50%) of results are the same,
        return that result. Uses a key function for comparison to handle
        unhashable types properly.

        Args:
            results: List of successful results to vote on
            key_func: Optional function to extract comparable key from results.
                      If None, uses the result directly (requires hashable types)
            threshold: Majority threshold (default: 0.5 for >50%)
            min_count: Minimum absolute count required (overrides threshold if set)

        Returns:
            Tuple of (majority_result, has_majority). has_majority is False
            if no clear majority exists.
        """
        if not results:
            return None, False

        if len(results) == 1:
            return results[0], True

        # Use key function to get comparable keys
        if key_func is not None:
            keys = [key_func(r) for r in results]
        else:
            keys = [self._majority_key(r) for r in results]

        # Count occurrences of each key
        key_counts = Counter(keys)

        # Find the most common result
        most_common_key, count = key_counts.most_common(1)[0]

        # Calculate percentage
        total = len(results)
        percentage = count / total

        # Determine if we have majority
        if min_count is not None:
            has_majority = count >= min_count
        else:
            has_majority = percentage > threshold

        # Find the actual result that matches the most common key
        majority_result = None
        for r, k in zip(results, keys):
            if k == most_common_key:
                majority_result = r
                break

        if has_majority:
            self.logger.debug(
                f"Majority vote: {count}/{total} results match "
                f"({percentage*100:.1f}%), threshold >{threshold*100:.0f}%"
            )
            return majority_result, True
        else:
            self.logger.warning(
                f"No majority result: {count}/{total} results match "
                f"({percentage*100:.1f}%), threshold >{threshold*100:.0f}%. "
                f"Returning first result."
            )
            return results[0], False

    def _majority_key(self, value: Any) -> Any:
        """Convert potentially unhashable results into stable majority-vote keys."""
        if isinstance(value, dict):
            return (
                "__dict__",
                tuple(
                    (key, self._majority_key(item))
                    for key, item in sorted(value.items(), key=lambda pair: repr(pair[0]))
                ),
            )
        if isinstance(value, list):
            return ("__list__", tuple(self._majority_key(item) for item in value))
        if isinstance(value, tuple):
            return ("__tuple__", tuple(self._majority_key(item) for item in value))
        if isinstance(value, set):
            return (
                "__set__",
                tuple(sorted((self._majority_key(item) for item in value), key=repr)),
            )

        try:
            hash(value)
            return value
        except TypeError:
            return ("__repr__", repr(value))

    async def __call__(self, **kwargs) -> Any:
        """Allow parallel to be called like a function."""
        return await self.execute(**kwargs)
