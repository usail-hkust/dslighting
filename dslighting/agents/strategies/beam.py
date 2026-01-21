"""
Beam Search Strategy

Beam search - maintains top-k candidates at each step.
"""

import asyncio
from typing import Dict, Any, Callable, List, Tuple
from .base import SearchStrategy


class BeamSearchStrategy(SearchStrategy):
    """
    Beam search strategy.

    Maintains a beam of top-k candidates and explores from them.
    Good for balancing exploration and exploitation.
    """

    def __init__(self, beam_width: int = 5, max_steps: int = 10):
        """
        Initialize beam search strategy.

        Args:
            beam_width: Number of top candidates to keep (beam size)
            max_steps: Maximum number of expansion steps
        """
        self.beam_width = beam_width
        self.max_steps = max_steps

    async def search(
        self,
        search_space: Dict[str, list],
        evaluate_fn: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform beam search.

        Args:
            search_space: Dictionary defining the search space
            evaluate_fn: Function to evaluate a configuration
            **kwargs: Additional arguments for evaluate_fn

        Returns:
            Best configuration found
        """
        print(f"🔍 Beam search: width={self.beam_width}, steps={self.max_steps}")

        # Start with empty configuration
        beam = [({}, 0.0)]  # List of (config, score) tuples

        for step in range(self.max_steps):
            print(f"\n=== Step {step + 1}/{self.max_steps} ===")

            # Generate candidates by expanding beam
            candidates = []

            for config, score in beam:
                # Find next dimension to explore
                next_dim = self._get_next_dimension(search_space, config)

                if next_dim is None:
                    # Configuration is complete
                    candidates.append((config, score))
                    continue

                # Expand along this dimension
                for value in search_space[next_dim]:
                    new_config = config.copy()
                    new_config[next_dim] = value

                    # Evaluate new configuration
                    try:
                        new_score = await evaluate_fn(new_config, **kwargs)
                        candidates.append((new_config, new_score))
                        print(f"  Evaluated {new_config}: {new_score:.4f}")
                    except Exception as e:
                        print(f"  Error evaluating {new_config}: {str(e)[:100]}")
                        # Give poor score
                        candidates.append((new_config, float('-inf')))

            # Select top-k candidates
            candidates.sort(key=lambda x: x[1], reverse=True)
            beam = candidates[:self.beam_width]

            print(f"Top candidates in beam:")
            for i, (config, score) in enumerate(beam):
                print(f"  {i + 1}. {config} (score: {score:.4f})")

            # Check if we've explored all dimensions
            if all(len(config) == len(search_space) for config, _ in beam):
                print("\n✓ All dimensions explored")
                break

        # Return best from final beam
        best_config, best_score = max(beam, key=lambda x: x[1])

        print(f"\n✓ Best configuration: {best_config}")
        print(f"  Best score: {best_score:.4f}")

        return best_config

    def _get_next_dimension(self, search_space: Dict[str, list], config: Dict[str, Any]) -> str:
        """
        Get the next dimension to explore.

        Args:
            search_space: Full search space
            config: Current configuration

        Returns:
            Name of next dimension, or None if complete
        """
        for dim in search_space.keys():
            if dim not in config:
                return dim
        return None
