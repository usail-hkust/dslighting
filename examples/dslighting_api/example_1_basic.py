"""
Example 1: Basic Usage of DSLighting API

This example demonstrates the simplest way to use DSLighting:
- Load data with automatic type detection
- Run an agent with default settings
- Access results

Usage:
    python examples/dslighting_api/example_1_basic.py
"""

import dslighting


def main():
    """Run basic DSLighting example."""
    print("=" * 60)
    print("DSLighting Basic Usage Example")
    print("=" * 60)

    # Example 1: One-liner with run_agent
    print("\n1. Simple one-liner:")
    print("   result = dslighting.run_agent('data/competitions/titanic')")
    print("   (Uncomment to run)")

    # Uncomment to run:
    # result = dslighting.run_agent("data/competitions/titanic")
    # print(f"   ✓ Score: {result.score}")
    # print(f"   ✓ Cost: ${result.cost:.4f}")
    # print(f"   ✓ Duration: {result.duration:.1f}s")

    # Example 2: Load data first, then run
    print("\n2. Load data, then run:")
    print("   data = dslighting.load_data('data/competitions/titanic')")
    print("   agent = dslighting.Agent()")
    print("   result = agent.run(data)")

    # Uncomment to run:
    # data = dslighting.load_data("data/competitions/titanic")
    # print(f"   Detected task type: {data.task_detection.task_type}")
    # print(f"   Recommended workflow: {data.task_detection.recommended_workflow}")
    #
    # agent = dslighting.Agent()
    # result = agent.run(data)
    # print(f"   ✓ Success: {result.success}")
    # print(f"   ✓ Output: {result.output}")

    # Example 3: Question-answering task
    print("\n3. Question-answering task:")
    print("   result = dslighting.run_agent('What is 9*8-2?')")

    # Uncomment to run:
    # result = dslighting.run_agent("What is 9*8-2?")
    # print(f"   ✓ Answer: {result.output}")
    # print(f"   ✓ Cost: ${result.cost:.6f}")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
