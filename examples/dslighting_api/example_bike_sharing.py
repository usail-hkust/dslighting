"""
Example: Using DSLighting Python API with bike-sharing-demand dataset

This example demonstrates how to use the DSLighting Python API
with the bike-sharing-demand competition dataset using the aide workflow.

Dataset: bike-sharing-demand
Task: Predict bike rental demand based on temporal and weather conditions
Workflow: aide (All-round Intelligent Data Engineer)

Usage:
    python examples/dslighting_api/example_bike_sharing.py
"""

import dslighting


def example_1_simple():
    """Example 1: Simple one-liner with aide workflow."""
    print("=" * 70)
    print("Example 1: Simple Usage with AIDE Workflow")
    print("=" * 70)

    print("\n📝 Code:")
    print("```python")
    print("import dslighting")
    print("")
    print("# Run with aide workflow (default)")
    print("result = dslighting.run_agent('data/competitions/bike-sharing-demand')")
    print("print(f'Score: {result.score}')")
    print("```")

    print("\n💡 Note: This will:")
    print("  - Auto-detect Kaggle competition structure")
    print("  - Use 'aide' workflow (default)")
    print("  - Train a model to predict bike demand")
    print("  - Generate predictions and evaluate")

    # Uncomment to run:
    # result = dslighting.run_agent("data/competitions/bike-sharing-demand")
    # print(f"\n✓ Completed!")
    # print(f"  Score: {result.score}")
    # print(f"  Cost: ${result.cost:.4f}")
    # print(f"  Duration: {result.duration:.1f}s")


def example_2_explicit_workflow():
    """Example 2: Explicitly specify aide workflow."""
    print("\n" + "=" * 70)
    print("Example 2: Explicitly Specify AIDE Workflow")
    print("=" * 70)

    print("\n📝 Code:")
    print("```python")
    print("import dslighting")
    print("")
    print("# Create agent with aide workflow")
    print("agent = dslighting.Agent(workflow='aide')")
    print("")
    print("# Load the data")
    print("data = dslighting.load_data('data/competitions/bike-sharing-demand')")
    print("")
    print("# Run the agent")
    print("result = agent.run(data)")
    print("```")

    print("\n💡 AIDE Workflow Features:")
    print("  - Iterative code generation with debugging")
    print("  - Automatic feature engineering")
    print("  - Model selection and hyperparameter tuning")
    print("  - Good balance of performance and cost")

    # Uncomment to run:
    # agent = dslighting.Agent(workflow="aide")
    # data = dslighting.load_data("data/competitions/bike-sharing-demand")
    # result = agent.run(data)
    #
    # print(f"\n✓ Completed!")
    # print(f"  Score: {result.score}")
    # print(f"  Output saved to: {result.output}")


def example_3_custom_aide():
    """Example 3: Customized aide workflow configuration."""
    print("\n" + "=" * 70)
    print("Example 3: Customized AIDE Configuration")
    print("=" * 70)

    print("\n📝 Code:")
    print("```python")
    print("import dslighting")
    print("")
    print("# Create agent with custom aide configuration")
    print("agent = dslighting.Agent(")
    print("    workflow='aide',")
    print("    model='gpt-4o-mini',        # LLM model")
    print("    temperature=0.7,              # Creativity level")
    print("    max_iterations=5,             # Search iterations")
    print("    num_drafts=5                  # Number of code drafts")
    print(")")
    print("")
    print("# Run on bike-sharing-demand")
    print("result = agent.run('data/competitions/bike-sharing-demand')")
    print("```")

    print("\n💡 Customization Options:")
    print("  - model: Choose different LLM (gpt-4o, gpt-4o-mini, deepseek-chat, etc.)")
    print("  - temperature: Control randomness (0.0 = focused, 1.0 = creative)")
    print("  - max_iterations: How many search iterations to perform")
    print("  - num_drafts: Number of code drafts to generate")

    # Uncomment to run:
    # agent = dslighting.Agent(
    #     workflow="aide",
    #     model="gpt-4o-mini",
    #     temperature=0.7,
    #     max_iterations=5,
    #     num_drafts=5
    # )
    # result = agent.run("data/competitions/bike-sharing-demand")
    #
    # print(f"\n✓ Completed with custom configuration!")
    # print(f"  Score: {result.score}")
    # print(f"  Cost: ${result.cost:.4f}")


def example_4_batch_with_aide():
    """Example 4: Batch processing multiple tasks with aide."""
    print("\n" + "=" * 70)
    print("Example 4: Batch Processing with AIDE")
    print("=" * 70)

    print("\n📝 Code:")
    print("```python")
    print("import dslighting")
    print("")
    print("# Create aide agent")
    print("agent = dslighting.Agent(workflow='aide')")
    print("")
    print("# Run on multiple tasks")
    print("tasks = [")
    print("    'data/competitions/bike-sharing-demand',")
    print("    'data/competitions/titanic',")
    print("    'data/competitions/house-prices'")
    print("]")
    print("")
    print("results = agent.run_batch(tasks)")
    print("")
    print("# Compare results")
    print("for i, result in enumerate(results):")
    print("    print(f'Task {i+1}: score={result.score}, cost=${result.cost:.4f}')")
    print("```")

    print("\n💡 Benefits:")
    print("  - Run multiple experiments sequentially")
    print("  - Compare performance across different datasets")
    print("  - Collect all results for analysis")


def example_5_access_results():
    """Example 5: Access detailed results and artifacts."""
    print("\n" + "=" * 70)
    print("Example 5: Access Detailed Results")
    print("=" * 70)

    print("\n📝 Code:")
    print("```python")
    print("import dslighting")
    print("")
    print("agent = dslighting.Agent(workflow='aide')")
    print("result = agent.run('data/competitions/bike-sharing-demand')")
    print("")
    print("# Access detailed information")
    print("print(f'Success: {result.success}')")
    print("print(f'Score: {result.score}')")
    print("print(f'Cost: ${result.cost:.4f}')")
    print("print(f'Duration: {result.duration:.1f}s')")
    print("print(f'Workspace: {result.workspace_path}')")
    print("print(f'Artifacts: {result.artifacts_path}')")
    print("")
    print("# Access underlying components for advanced usage")
    print("config = agent.get_config()")
    print("runner = agent.get_runner()")
    print("```")

    print("\n💡 Available Information:")
    print("  - result.success: Whether task completed successfully")
    print("  - result.output: Predictions or file path")
    print("  - result.score: Evaluation score")
    print("  - result.cost: Total LLM cost")
    print("  - result.duration: Execution time")
    print("  - result.workspace_path: Path to workspace directory")
    print("  - result.artifacts_path: Path to generated artifacts")
    print("  - result.metadata: Additional metadata")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("🚴 DSLighting Python API - Bike Sharing Demand Example")
    print("=" * 70)

    print("\n📊 Dataset: bike-sharing-demand")
    print("   Task: Predict bike rental demand")
    print("   Workflow: aide (All-round Intelligent Data Engineer)")

    # Run all examples
    example_1_simple()
    example_2_explicit_workflow()
    example_3_custom_aide()
    example_4_batch_with_aide()
    example_5_access_results()

    print("\n" + "=" * 70)
    print("✅ All examples displayed!")
    print("=" * 70)

    print("\n🚀 To run these examples:")
    print("   1. Uncomment the code in each example")
    print("   2. Make sure API_KEY is set in .env file")
    print("   3. Run: python examples/dslighting_api/example_bike_sharing.py")

    print("\n📚 More information:")
    print("   - Python API Guide: docs/python-api-guide.md")
    print("   - API Documentation: dslighting/README.md")
    print("   - AIDE Workflow: See documentation for details")

    print("\n💡 Quick Start:")
    print("   ```python")
    print("   import dslighting")
    print("   result = dslighting.run_agent('data/competitions/bike-sharing-demand')")
    print("   print(f'Score: {result.score}')")
    print("   ```")


if __name__ == "__main__":
    main()
