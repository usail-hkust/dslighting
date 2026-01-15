"""
Example 3: Migration from DSAT API to DSLighting API

This example shows how to migrate from the existing DSAT API
to the simplified DSLighting API.

Usage:
    python examples/dslighting_api/example_3_migration.py
"""

# ============================================================================
# OLD WAY: Using DSAT API directly
# ============================================================================

def old_dsat_api():
    """Example of old DSAT API usage (for comparison)."""
    print("\n" + "=" * 60)
    print("OLD: DSAT API")
    print("=" * 60)

    print("""
from dsat.config import DSATConfig, LLMConfig, WorkflowConfig
from dsat.runner import DSATRunner
from dsat.benchmark.mle import MLEBenchmark
import os

# 1. Create configuration
config = DSATConfig(
    llm=LLMConfig(
        model="gpt-4o-mini",
        api_key=os.getenv("API_KEY"),
        temperature=0.7
    ),
    workflow=WorkflowConfig(name="aide")
)

# 2. Create runner
runner = DSATRunner(config)

# 3. Setup benchmark
benchmark = MLEBenchmark(
    name="mle",
    data_dir="data/competitions",
    log_path="runs/results"
)

# 4. Get evaluation function
eval_fn = runner.get_eval_function()

# 5. Run evaluation
await benchmark.run_evaluation(eval_fn=eval_fn, model_name="gpt-4o-mini")

# Complexity: High
# - Need to understand DSATConfig, LLMConfig, WorkflowConfig
# - Need to create benchmark manually
# - Need to handle async/await
# - Many concepts to learn
    """)


# ============================================================================
# NEW WAY: Using DSLighting simplified API
# ============================================================================

def new_dslighting_api():
    """Example of new DSLighting API usage."""
    print("\n" + "=" * 60)
    print("NEW: DSLighting API")
    print("=" * 60)

    print("""
import dslighting

# Simple one-liner
result = dslighting.run_agent("data/competitions/titanic")

# Or with more control
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o-mini"
)
result = agent.run("data/competitions/titanic")

# Access results
print(f"Score: {result.score}")
print(f"Cost: ${result.cost}")

# Complexity: Low
# - Auto-detects task type
# - Sensible defaults
# - Simple, synchronous API
# - Easy to customize
    """)


# ============================================================================
# PROGRESSIVE MIGRATION
# ============================================================================

def progressive_migration():
    """Example of progressive migration paths."""
    print("\n" + "=" * 60)
    print("PROGRESSIVE MIGRATION")
    print("=" * 60)

    print("""
Path 1: Drop-in Replacement (Simple)
--------------------------------------
Use DSLighting for simple cases, keep DSAT for complex ones.

# Simple case - use DSLighting
import dslighting
result = dslighting.run_agent("data/competitions/titanic")

# Complex case - continue using DSAT
from dsat.config import DSATConfig
from dsat.runner import DSATRunner
# ... existing code


Path 2: Hybrid Approach (Balanced)
------------------------------------
Use DSLighting for setup, access DSATRunner for control.

import dslighting

# Setup with DSLighting
agent = dslighting.Agent(workflow="aide")
runner = agent.get_runner()

# Use DSATRunner directly for advanced control
eval_fn = runner.get_eval_function()
# ... custom evaluation logic


Path 3: Gradual Transition (Safe)
----------------------------------
Start new projects with DSLighting, keep old projects unchanged.

# New project
import dslighting
agent = dslighting.Agent()
result = agent.run(data)

# Old project - continue using DSAT
# No changes needed!
    """)


def main():
    """Run migration example."""
    print("=" * 60)
    print("DSLighting API Migration Guide")
    print("=" * 60)

    old_dsat_api()
    new_dslighting_api()
    progressive_migration()

    print("\n" + "=" * 60)
    print("Key Takeaways:")
    print("=" * 60)
    print("""
1. DSLighting API is simpler and more intuitive
2. Both APIs can coexist in the same project
3. Migration is optional - use what works best for you
4. DSLighting builds on DSAT - no functionality loss
5. Choose your migration path based on your needs
    """)


if __name__ == "__main__":
    main()
