"""
ML-Master 2.0 Reproduction Example: Hierarchical Cognitive Caching

This example reproduces the ML-Master 2.0 approach described in the paper:
- Hierarchical Cognitive Caching (HCC)
- Hierarchical caching (multi-tier context organization)
- Context migration (dynamic promotion/consolidation/discarding)
- Phase-based exploration with parallel suggestions
- Phase consolidation and migration

Workflow:
1. Retrieve prior wisdom → construct initial context
2. Generate initial code through environment interaction
3. Propose hierarchical research plan (m directions × q suggestions each)
4. Execute suggestions in parallel (event subsequence E_tp-1:tp)
5. At phase boundary tp: consolidate phase, propose next plan
6. Repeat until completion or time budget
"""

import pandas as pd
import numpy as np
import time
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# Import DSLighting 2.0 Core Protocols
# ============================================================================

from dslighting import Action, Context, Tool


# ============================================================================
# ML-Master 2.0 Core Components
# ============================================================================

class ContextTier(Enum):
    """Context tiers for hierarchical caching"""
    EPHEMERAL = "ephemeral"      # Temporary, short-lived context
    WORKING = "working"           # Current working context
    STABLE = "stable"             # Stable, reusable context
    LONG_TERM = "long_term"       # Long-term wisdom/prior knowledge


@dataclass
class CachedContext:
    """A cached context entry with metadata"""
    tier: ContextTier
    content: Dict[str, Any]
    creation_time: float
    access_count: int = 0
    reuse_value: float = 0.0
    phase_id: int = -1


@dataclass
class ExplorationDirection:
    """An exploration direction with suggestions"""
    direction_id: int
    direction_name: str
    description: str
    suggestions: List[Dict[str, Any]]  # List of q suggestions
    results: List[Any] = field(default_factory=list)


@dataclass
class ResearchPlan:
    """A hierarchical research plan for a phase"""
    phase_id: int
    directions: List[ExplorationDirection]  # m directions
    time_budget: float = 60.0  # seconds


@dataclass
class PhaseResult:
    """Result after completing a phase"""
    phase_id: int
    completed_directions: int
    total_suggestions: int
    successful_suggestions: int
    best_result: Any = None
    consolidated_context: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


# ============================================================================
# Hierarchical Cognitive Cache (HCC)
# ============================================================================

class HierarchicalCognitiveCache:
    """
    Hierarchical Cognitive Caching - organizes context into multiple tiers
    according to temporal stability and reuse value.
    """

    def __init__(self):
        # Multi-tier cache
        self.tiers = {
            ContextTier.EPHEMERAL: [],      # Temporary context (discarded quickly)
            ContextTier.WORKING: [],        # Current phase context
            ContextTier.STABLE: [],         # Reusable across phases
            ContextTier.LONG_TERM: []       # Prior wisdom (persistent)
        }

        # Phase history for consolidation
        self.phase_history: Dict[int, PhaseResult] = {}

        # Statistics
        self.stats = {
            "total_retrievals": 0,
            "cache_hits": 0,
            "migrations": 0
        }

    def store(self, tier: ContextTier, content: Dict[str, Any],
              phase_id: int = -1, reuse_value: float = 0.0) -> CachedContext:
        """Store context in a specific tier"""
        cached = CachedContext(
            tier=tier,
            content=content,
            creation_time=time.time(),
            phase_id=phase_id,
            reuse_value=reuse_value
        )

        self.tiers[tier].append(cached)
        return cached

    def retrieve(self, query: str, tier: ContextTier = None) -> List[CachedContext]:
        """Retrieve relevant context from cache"""
        self.stats["total_retrievals"] += 1

        if tier:
            tiers_to_search = [tier]
        else:
            # Search from stable to ephemeral (prioritize stable)
            tiers_to_search = [
                ContextTier.STABLE,
                ContextTier.WORKING,
                ContextTier.EPHEMERAL
            ]

        results = []
        for t in tiers_to_search:
            for cached in self.tiers[t]:
                if query.lower() in str(cached.content).lower():
                    cached.access_count += 1
                    results.append(cached)

        if results:
            self.stats["cache_hits"] += 1

        return results

    def migrate(self, phase_boundary: int) -> None:
        """
        Context migration: at phase boundary, promote/consolidate/discard context
        """
        self.stats["migrations"] += 1

        # 1. Promote high-reuse-value working context to stable
        working_to_promote = [
            c for c in self.tiers[ContextTier.WORKING]
            if c.reuse_value > 0.7
        ]
        for ctx in working_to_promote:
            ctx.tier = ContextTier.STABLE
            self.tiers[ContextTier.STABLE].append(ctx)
            self.tiers[ContextTier.WORKING].remove(ctx)

        # 2. Discard ephemeral context
        self.tiers[ContextTier.EPHEMERAL].clear()

        # 3. Consolidate phase results into long-term
        if phase_boundary in self.phase_history:
            phase_result = self.phase_history[phase_boundary]
            consolidated = {
                "phase_id": phase_boundary,
                "best_result": phase_result.best_result,
                "successful_approaches": phase_result.consolidated_context
            }
            self.store(
                tier=ContextTier.LONG_TERM,
                content=consolidated,
                phase_id=phase_boundary,
                reuse_value=1.0
            )

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of cache state"""
        return {
            "tier_sizes": {
                t.name: len(self.tiers[t])
                for t in ContextTier
            },
            "phase_history_size": len(self.phase_history),
            "stats": self.stats
        }


# ============================================================================
# ML-Master 2.0 Agent
# ============================================================================

class MLMaster2Agent:
    """
    ML-Master 2.0 Agent implementing HCC and phase-based exploration.
    """

    def __init__(self,
                 m_directions: int = 3,      # Number of exploration directions
                 q_suggestions: int = 2,     # Suggestions per direction
                 time_budget: float = 300.0,
                 max_phases: int = 5):
        self.m_directions = m_directions
        self.q_suggestions = q_suggestions
        self.time_budget = time_budget
        self.max_phases = max_phases

        # Initialize HCC
        self.cache = HierarchicalCognitiveCache()

        # Phase tracking
        self.current_phase = 0
        self.phase_results: List[PhaseResult] = []

        # Task context
        self.initial_context = {}
        self.task_complete = False

    def plan(self, ctx: Context) -> Action:
        """
        Plan method: given context, return next action
        Implements ML-Master 2.0 workflow
        """
        # Phase 0: Initialize context with prior wisdom
        if self.current_phase == 0:
            return Action(
                tool="initialize_context",
                args={"task": ctx.task}
            )

        # Generate initial code
        elif self.current_phase == 1:
            return Action(
                tool="generate_initial_code",
                args={"context": self.cache.retrieve("prior", ContextTier.LONG_TERM)}
            )

        # Phase 2+: Hierarchical research plan and parallel exploration
        else:
            phase_id = self.current_phase - 1

            # Generate research plan for this phase
            plan = self._generate_research_plan(phase_id, ctx)

            # Execute plan (parallel suggestions)
            phase_result = self._execute_research_plan(plan, ctx)

            # Store phase result
            self.phase_results.append(phase_result)
            self.cache.phase_history[phase_id] = phase_result

            # Context migration at phase boundary
            self.cache.migrate(phase_id)

            # Check completion
            if phase_id >= self.max_phases or self._is_task_complete(phase_result):
                self.task_complete = True
                return Action(
                    tool="finalize",
                    args={"phase_results": self.phase_results}
                )

            # Continue to next phase
            self.current_phase += 1
            return self.plan(ctx)

    def _generate_research_plan(self, phase_id: int,
                                 ctx: Context) -> ResearchPlan:
        """Generate hierarchical research plan (m directions × q suggestions)"""

        # Get relevant prior wisdom
        prior_wisdom = self.cache.retrieve(f"phase_{phase_id-1}", ContextTier.STABLE)

        # Generate m exploration directions
        directions = []

        # Direction 1: Feature Engineering
        direction1 = ExplorationDirection(
            direction_id=1,
            direction_name="feature_engineering",
            description="Explore different feature transformations",
            suggestions=[
                {
                    "suggestion_id": 1,
                    "name": "polynomial_features",
                    "description": "Add polynomial features",
                    "params": {"degree": 2}
                },
                {
                    "suggestion_id": 2,
                    "name": "interaction_features",
                    "description": "Add interaction features",
                    "params": {"interactions": True}
                }
            ][:self.q_suggestions]
        )

        # Direction 2: Model Selection
        direction2 = ExplorationDirection(
            direction_id=2,
            direction_name="model_selection",
            description="Explore different model architectures",
            suggestions=[
                {
                    "suggestion_id": 1,
                    "name": "random_forest",
                    "description": "Random Forest with tuning",
                    "params": {"n_estimators": 100}
                },
                {
                    "suggestion_id": 2,
                    "name": "gradient_boosting",
                    "description": "Gradient Boosting",
                    "params": {"learning_rate": 0.1}
                }
            ][:self.q_suggestions]
        )

        # Direction 3: Hyperparameter Tuning
        direction3 = ExplorationDirection(
            direction_id=3,
            direction_name="hyperparameter_tuning",
            description="Explore hyperparameter configurations",
            suggestions=[
                {
                    "suggestion_id": 1,
                    "name": "grid_search",
                    "description": "Grid search over parameters",
                    "params": {"cv": 5}
                },
                {
                    "suggestion_id": 2,
                    "name": "random_search",
                    "description": "Random search over parameters",
                    "params": {"n_iter": 20}
                }
            ][:self.q_suggestions]
        )

        directions = [direction1, direction2, direction3][:self.m_directions]

        return ResearchPlan(
            phase_id=phase_id,
            directions=directions,
            time_budget=self.time_budget / self.max_phases
        )

    def _execute_research_plan(self, plan: ResearchPlan,
                                ctx: Context) -> PhaseResult:
        """
        Execute research plan: parallel suggestions in each direction
        Corresponds to event subsequence E_tp-1:tp
        """
        print(f"\n{'='*70}")
        print(f"🔬 Phase {plan.phase_id}: Executing Research Plan")
        print(f"{'='*70}")
        print(f"Directions: {len(plan.directions)}")
        print(f"Suggestions per direction: {self.q_suggestions}")
        print(f"Time budget: {plan.time_budget:.1f}s\n")

        start_time = time.time()
        successful = 0
        all_results = []

        # Execute each direction
        for direction in plan.directions:
            print(f"\n📍 Direction {direction.direction_id}: {direction.direction_name}")
            print(f"   {direction.description}")

            # Execute suggestions in this direction (parallel simulation)
            for suggestion in direction.suggestions:
                print(f"\n   ↳ Suggestion {suggestion['suggestion_id']}: {suggestion['name']}")
                print(f"      {suggestion['description']}")

                # Execute suggestion (simulate with tool)
                result = self._execute_suggestion(suggestion, ctx)

                # Store result
                direction.results.append(result)
                all_results.append(result)

                if result.get("success", False):
                    successful += 1
                    print(f"      ✓ Success: Score = {result.get('score', 0):.4f}")
                else:
                    print(f"      ✗ Failed")

                # Store in working cache
                self.cache.store(
                    tier=ContextTier.WORKING,
                    content={
                        "direction": direction.direction_name,
                        "suggestion": suggestion,
                        "result": result
                    },
                    phase_id=plan.phase_id,
                    reuse_value=result.get("score", 0) / 10.0  # Normalize
                )

        # Find best result
        best_result = max(all_results, key=lambda x: x.get("score", -1))

        # Consolidate phase
        consolidated = self._consolidate_phase(all_results, plan.phase_id)

        execution_time = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"✅ Phase {plan.phase_id} Complete")
        print(f"   Total suggestions: {len(all_results)}")
        print(f"   Successful: {successful}")
        print(f"   Best score: {best_result.get('score', 0):.4f}")
        print(f"   Execution time: {execution_time:.1f}s")
        print(f"{'='*70}\n")

        return PhaseResult(
            phase_id=plan.phase_id,
            completed_directions=len(plan.directions),
            total_suggestions=len(all_results),
            successful_suggestions=successful,
            best_result=best_result,
            consolidated_context=consolidated,
            execution_time=execution_time
        )

    def _execute_suggestion(self, suggestion: Dict[str, Any],
                            ctx: Context) -> Dict[str, Any]:
        """Execute a single suggestion"""
        # Simulate execution with random results
        # In real implementation, this would interact with environment
        time.sleep(0.1)  # Simulate work

        success_prob = np.random.uniform(0.3, 0.9)
        success = np.random.random() < success_prob

        if success:
            score = np.random.uniform(0.6, 0.95)
        else:
            score = 0.0

        return {
            "suggestion": suggestion["name"],
            "success": success,
            "score": score,
            "execution_time": 0.1
        }

    def _consolidate_phase(self, results: List[Dict[str, Any]],
                           phase_id: int) -> Dict[str, Any]:
        """Consolidate phase results for long-term storage"""

        successful_results = [r for r in results if r.get("success", False)]

        if not successful_results:
            return {"phase_id": phase_id, "successful_approaches": []}

        # Extract patterns from successful approaches
        best_approaches = sorted(
            successful_results,
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:3]

        return {
            "phase_id": phase_id,
            "successful_approaches": [
                {
                    "suggestion": r["suggestion"],
                    "score": r["score"]
                }
                for r in best_approaches
            ],
            "avg_score": np.mean([r["score"] for r in successful_results])
        }

    def _is_task_complete(self, phase_result: PhaseResult) -> bool:
        """Check if task is complete"""
        # Example: complete if score > 0.9 or no successful suggestions
        best_score = phase_result.best_result.get("score", 0)
        return best_score > 0.9 or phase_result.successful_suggestions == 0

    def run(self, ctx: Context) -> Dict[str, Any]:
        """Run complete ML-Master 2.0 workflow"""
        print("\n" + "="*70)
        print("🚀 ML-Master 2.0: Hierarchical Cognitive Caching")
        print("="*70)
        print(f"Task: {ctx.task}")
        print(f"Directions per phase (m): {self.m_directions}")
        print(f"Suggestions per direction (q): {self.q_suggestions}")
        print(f"Max phases: {self.max_phases}")
        print(f"Time budget: {self.time_budget:.1f}s\n")

        # Phase 0: Initialize
        print("Phase 0: Initializing context with prior wisdom...")
        self.cache.store(
            tier=ContextTier.LONG_TERM,
            content={
                "task_type": "tabular_prediction",
                "common_approaches": [
                    "feature_engineering",
                    "model_ensembling",
                    "hyperparameter_tuning"
                ]
            },
            phase_id=-1,
            reuse_value=1.0
        )
        self.current_phase += 1

        # Phase 1: Generate initial code
        print("\nPhase 1: Generating initial code...")
        time.sleep(0.5)
        self.current_phase += 1

        # Main phase loop
        while not self.task_complete and self.current_phase <= self.max_phases + 1:
            action = self.plan(ctx)

            if action.tool == "finalize":
                break
            elif action.tool == "initialize_context":
                continue
            elif action.tool == "generate_initial_code":
                continue

        # Final summary
        print("\n" + "="*70)
        print("📊 ML-Master 2.0 Execution Summary")
        print("="*70)
        print(f"Total phases: {len(self.phase_results)}")

        for pr in self.phase_results:
            print(f"\nPhase {pr.phase_id}:")
            print(f"  Suggestions: {pr.total_suggestions}")
            print(f"  Successful: {pr.successful_suggestions}")
            print(f"  Best score: {pr.best_result.get('score', 0):.4f}")
            print(f"  Time: {pr.execution_time:.1f}s")

        # Cache summary
        cache_summary = self.cache.get_context_summary()
        print(f"\n📦 Hierarchical Cognitive Cache:")
        print(f"  Ephemeral: {cache_summary['tier_sizes']['EPHEMERAL']}")
        print(f"  Working: {cache_summary['tier_sizes']['WORKING']}")
        print(f"  Stable: {cache_summary['tier_sizes']['STABLE']}")
        print(f"  Long-term: {cache_summary['tier_sizes']['LONG_TERM']}")
        print(f"  Cache hits: {cache_summary['stats']['cache_hits']}")
        print(f"  Migrations: {cache_summary['stats']['migrations']}")

        print("\n" + "="*70)
        print("✅ ML-Master 2.0 workflow complete!")
        print("="*70 + "\n")

        return {
            "phase_results": self.phase_results,
            "cache_summary": cache_summary,
            "final_score": max(
                [pr.best_result.get("score", 0) for pr in self.phase_results],
                default=0.0
            )
        }


# ============================================================================
# Main Execution
# ============================================================================

def run_mlmaster2_example():
    """Run ML-Master 2.0 example"""

    # Create context
    ctx = Context(
        task="bike-sharing-demand prediction",
        data={"dataset": "bike-sharing-demand"},
        tools={}
    )

    # Create agent
    agent = MLMaster2Agent(
        m_directions=3,      # 3 exploration directions
        q_suggestions=2,     # 2 suggestions per direction
        time_budget=300.0,   # 5 minutes
        max_phases=3         # 3 phases
    )

    # Run agent
    result = agent.run(ctx)

    return result


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ML-Master 2.0 Reproduction Example")
    print("Hierarchical Cognitive Caching (HCC)")
    print("="*70 + "\n")

    result = run_mlmaster2_example()

    print("\n💡 Key Concepts Demonstrated:")
    print("  1. Hierarchical Caching: Multi-tier context organization")
    print("  2. Context Migration: Dynamic promotion/consolidation/discarding")
    print("  3. Phase-based Exploration: m directions × q suggestions")
    print("  4. Parallel Execution: Event subsequence E_tp-1:tp")
    print("  5. Phase Consolidation: Merge results at phase boundaries\n")
