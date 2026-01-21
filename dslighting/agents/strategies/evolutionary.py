"""
Evolutionary Strategy

Evolutionary algorithm for configuration optimization.
"""

import asyncio
import random
import copy
from typing import Dict, Any, Callable, List
from .base import SearchStrategy


class EvolutionaryStrategy(SearchStrategy):
    """
    Evolutionary strategy.

    Uses population-based evolution to optimize configurations.
    Includes selection, mutation, and crossover operations.
    """

    def __init__(
        self,
        population_size: int = 10,
        generations: int = 5,
        mutation_rate: float = 0.2,
        elite_size: int = 2,
    ):
        """
        Initialize evolutionary strategy.

        Args:
            population_size: Size of population
            generations: Number of generations to evolve
            mutation_rate: Probability of mutation
            elite_size: Number of elite individuals to keep
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size

    async def search(
        self,
        search_space: Dict[str, list],
        evaluate_fn: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform evolutionary search.

        Args:
            search_space: Dictionary defining the search space
            evaluate_fn: Function to evaluate a configuration
            **kwargs: Additional arguments for evaluate_fn

        Returns:
            Best configuration found
        """
        print(f"🔍 Evolutionary search: population={self.population_size}, generations={self.generations}")

        # Initialize population
        population = self._initialize_population(search_space)

        best_config = None
        best_score = float('-inf')

        for gen in range(self.generations):
            print(f"\n=== Generation {gen + 1}/{self.generations} ===")

            # Evaluate population
            scored_population = []

            for individual in population:
                try:
                    score = await evaluate_fn(individual, **kwargs)
                    scored_population.append((individual, score))

                    if score > best_score:
                        best_score = score
                        best_config = individual
                        print(f"  ✓ New best! {individual}: {score:.4f}")

                except Exception as e:
                    # Give poor score to failed individuals
                    scored_population.append((individual, float('-inf')))

            # Sort by score
            scored_population.sort(key=lambda x: x[1], reverse=True)

            print(f"  Top 3 in generation {gen + 1}:")
            for i, (config, score) in enumerate(scored_population[:3]):
                print(f"    {i + 1}. {config}: {score:.4f}")

            # Selection and reproduction
            population = self._evolve_population(scored_population, search_space)

        print(f"\n✓ Best configuration: {best_config}")
        print(f"  Best score: {best_score:.4f}")

        return best_config

    def _initialize_population(self, search_space: Dict[str, list]) -> List[Dict[str, Any]]:
        """
        Initialize random population.

        Args:
            search_space: Search space definition

        Returns:
            List of random configurations
        """
        population = []

        for _ in range(self.population_size):
            individual = {}
            for dim, values in search_space.items():
                individual[dim] = random.choice(values)
            population.append(individual)

        return population

    def _evolve_population(
        self,
        scored_population: List[tuple],
        search_space: Dict[str, list]
    ) -> List[Dict[str, Any]]:
        """
        Evolve population to next generation.

        Args:
            scored_population: List of (config, score) tuples
            search_space: Search space definition

        Returns:
            New population
        """
        new_population = []

        # Elitism: keep top individuals
        elite = [config for config, score in scored_population[:self.elite_size]]
        new_population.extend(elite)

        # Generate offspring
        while len(new_population) < self.population_size:
            # Tournament selection
            parent = self._tournament_selection(scored_population)

            # Mutation
            if random.random() < self.mutation_rate:
                offspring = self._mutate(parent, search_space)
            else:
                offspring = parent.copy()

            new_population.append(offspring)

        return new_population

    def _tournament_selection(
        self,
        scored_population: List[tuple],
        tournament_size: int = 3
    ) -> Dict[str, Any]:
        """
        Select parent using tournament selection.

        Args:
            scored_population: List of (config, score) tuples
            tournament_size: Size of tournament

        Returns:
            Selected configuration
        """
        tournament = random.sample(scored_population, min(tournament_size, len(scored_population)))
        return max(tournament, key=lambda x: x[1])[0]

    def _mutate(
        self,
        config: Dict[str, Any],
        search_space: Dict[str, list]
    ) -> Dict[str, Any]:
        """
        Mutate configuration.

        Args:
            config: Configuration to mutate
            search_space: Search space definition

        Returns:
            Mutated configuration
        """
        mutated = config.copy()

        # Select random dimension to mutate
        dim = random.choice(list(search_space.keys()))
        mutated[dim] = random.choice(search_space[dim])

        return mutated
