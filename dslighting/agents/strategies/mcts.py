"""
MCTS Strategy - Monte Carlo Tree Search

Monte Carlo Tree Search for intelligent configuration search.
"""

import asyncio
import math
import random
from typing import Dict, Any, Callable, List
from .base import SearchStrategy


class MCTSStrategy(SearchStrategy):
    """
    Monte Carlo Tree Search strategy.

    Uses MCTS to intelligently search the configuration space.
    Balances exploration and exploitation using UCB (Upper Confidence Bound).
    """

    def __init__(
        self,
        exploration_constant: float = 1.414,
        max_simulations: int = 100,
    ):
        """
        Initialize MCTS strategy.

        Args:
            exploration_constant: UCB exploration parameter (default: sqrt(2))
            max_simulations: Maximum number of MCTS simulations
        """
        self.exploration_constant = exploration_constant
        self.max_simulations = max_simulations

    async def search(
        self,
        search_space: Dict[str, list],
        evaluate_fn: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform MCTS search.

        Args:
            search_space: Dictionary defining the search space
            evaluate_fn: Function to evaluate a configuration
            **kwargs: Additional arguments for evaluate_fn

        Returns:
            Best configuration found
        """
        print(f"🔍 MCTS search: {self.max_simulations} simulations")

        # Initialize root node
        root = MCTSNode(config={})

        # Run simulations
        for sim in range(self.max_simulations):
            if sim % 10 == 0:
                print(f"  Simulation {sim}/{self.max_simulations}")

            # 1. Selection
            node = root
            path = [node]

            while not node.is_terminal(search_space) and node.is_fully_expanded(search_space):
                node = node.select_child(self.exploration_constant)
                path.append(node)

            # 2. Expansion
            if not node.is_terminal(search_space):
                node = node.expand(search_space)
                path.append(node)

            # 3. Evaluation (simulation)
            config = node.config
            try:
                score = await evaluate_fn(config, **kwargs)
            except Exception as e:
                score = float('-inf')

            # 4. Backpropagation
            for node in path:
                node.visits += 1
                node.value += score

        # Get best configuration from root
        best_config = root.get_best_child().config if root.children else root.config
        best_score = max((c.value / c.visits for c in root.children if c.visits > 0), default=0.0)

        print(f"\n✓ Best configuration: {best_config}")
        print(f"  Best score: {best_score:.4f}")

        return best_config


class MCTSNode:
    """Node in MCTS search tree."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCTS node.

        Args:
            config: Configuration at this node
        """
        self.config = config
        self.value = 0.0
        self.visits = 0
        self.children: List[MCTSNode] = []

    def is_fully_expanded(self, search_space: Dict[str, list]) -> bool:
        """Check if all children have been expanded."""
        if self.is_terminal(search_space):
            return True

        next_dim = self._get_next_dimension(search_space)
        return len(self.children) == len(search_space[next_dim])

    def is_terminal(self, search_space: Dict[str, list]) -> bool:
        """Check if this is a terminal node (complete configuration)."""
        return len(self.config) == len(search_space)

    def select_child(self, exploration_constant: float) -> 'MCTSNode':
        """
        Select best child using UCB (Upper Confidence Bound).

        Args:
            exploration_constant: Exploration parameter

        Returns:
            Selected child node
        """
        def ucb(node: MCTSNode) -> float:
            if node.visits == 0:
                return float('inf')

            exploitation = node.value / node.visits
            exploration = exploration_constant * math.sqrt(math.log(self.visits) / node.visits)

            return exploitation + exploration

        return max(self.children, key=ucb)

    def expand(self, search_space: Dict[str, list]) -> 'MCTSNode':
        """
        Expand node by adding a new child.

        Args:
            search_space: Full search space

        Returns:
            New child node
        """
        next_dim = self._get_next_dimension(search_space)

        # Find values that haven't been expanded yet
        expanded_values = [child.config[next_dim] for child in self.children]
        unexpanded_values = [v for v in search_space[next_dim] if v not in expanded_values]

        # Create new child with unexpanded value
        new_value = random.choice(unexpanded_values)
        new_config = self.config.copy()
        new_config[next_dim] = new_value

        new_child = MCTSNode(new_config)
        self.children.append(new_child)

        return new_child

    def get_best_child(self) -> 'MCTSNode':
        """Get child with highest average value."""
        def avg_value(node: MCTSNode) -> float:
            return node.value / node.visits if node.visits > 0 else float('-inf')

        return max(self.children, key=avg_value)

    def _get_next_dimension(self, search_space: Dict[str, list]) -> str:
        """Get next dimension to expand."""
        for dim in search_space.keys():
            if dim not in self.config:
                return dim
        return None
