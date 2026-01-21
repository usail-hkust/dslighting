"""
Search Strategy Base Class

Abstract base class for all search strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Awaitable


class SearchStrategy(ABC):
    """
    Abstract base class for search strategies.

    All search strategies must implement the search method.
    """

    @abstractmethod
    async def search(
        self,
        search_space: Dict[str, list],
        evaluate_fn: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search the space for the best configuration.

        Args:
            search_space: Dictionary defining the search space
                Example: {
                    "algorithm": ["xgboost", "lightgbm"],
                    "n_estimators": [100, 200, 500],
                }
            evaluate_fn: Async function to evaluate a configuration
                Signature: async def evaluate_fn(config, **kwargs) -> float
            **kwargs: Additional arguments passed to evaluate_fn

        Returns:
            Best configuration found
        """
        pass
