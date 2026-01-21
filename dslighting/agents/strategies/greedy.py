"""
Greedy Search Strategy

Simple greedy search - tries options and keeps the best.
"""

import asyncio
import itertools
from typing import Dict, Any, Callable, List
from .base import SearchStrategy


class GreedyStrategy(SearchStrategy):
    """
    Greedy search strategy.

    Evaluates configurations one by one and keeps the best.
    Simple but effective for small search spaces.
    """

    def __init__(self, max_evaluations: int = 10):
        """
        Initialize greedy strategy.

        Args:
            max_evaluations: Maximum number of configurations to evaluate
        """
        self.max_evaluations = max_evaluations

    async def search(
        self,
        search_space: Dict[str, list],
        evaluate_fn: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform greedy search.

        Args:
            search_space: Dictionary defining the search space
            evaluate_fn: Function to evaluate a configuration
            **kwargs: Additional arguments for evaluate_fn

        Returns:
            Best configuration found
        """
        # Generate all possible configurations
        configurations = self._generate_configurations(search_space)

        # Limit to max_evaluations
        configurations = configurations[:self.max_evaluations]

        best_config = None
        best_score = float('-inf')

        print(f"🔍 Greedy search: evaluating {len(configurations)} configurations...")

        for i, config in enumerate(configurations):
            print(f"  Evaluating configuration {i + 1}/{len(configurations)}: {config}")

            # Evaluate configuration
            try:
                score = await evaluate_fn(config, **kwargs)
                print(f"    Score: {score:.4f}")

                # Track best
                if score > best_score:
                    best_score = score
                    best_config = config
                    print(f"    ✓ New best!")
            except Exception as e:
                print(f"    ✗ Error: {str(e)[:100]}")
                continue

        print(f"\n✓ Best configuration: {best_config}")
        print(f"  Best score: {best_score:.4f}")

        return best_config

    def _generate_configurations(self, search_space: Dict[str, list]) -> List[Dict[str, Any]]:
        """
        Generate all possible configurations from search space.

        Args:
            search_space: Dictionary defining the search space

        Returns:
            List of configurations
        """
        # Get all keys and their possible values
        keys = list(search_space.keys())
        values = list(search_space.values())

        # Generate all combinations
        combinations = itertools.product(*values)

        # Convert to list of dictionaries
        configurations = [
            dict(zip(keys, combo))
            for combo in combinations
        ]

        return configurations
