"""
Quick Start: Run DSLighting on bike-sharing-demand dataset

This is a ready-to-run example. Just uncomment the code and execute!

Usage:
    1. Set your API_KEY in .env file
    2. Uncomment the main() code below
    3. Run: python examples/dslighting_api/run_bike_sharing.py
"""

import dslighting


def main():
    """Run bike-sharing-demand prediction with DSLighting API."""

    print("=" * 70)
    print("🚴 DSLighting - Bike Sharing Demand Prediction")
    print("=" * 70)

    # ================================================================
    # STEP 1: Create Agent with AIDE workflow
    # ================================================================
    print("\n📝 Step 1: Creating Agent with AIDE workflow...")

    agent = dslighting.Agent(
        workflow="aide",           # Use AIDE workflow
        model="gpt-4o-mini",       # LLM model (you can change this)
        temperature=0.7,           # Temperature (0.0-1.0)
        max_iterations=5,          # Maximum iterations
        verbose=True               # Enable logging
    )

    print("✓ Agent created successfully!")
    print(f"  Workflow: {agent.config.workflow.name}")
    print(f"  Model: {agent.config.llm.model}")

    # ================================================================
    # STEP 2: Run on bike-sharing-demand dataset
    # ================================================================
    print("\n📝 Step 2: Running on bike-sharing-demand dataset...")

    result = agent.run("data/competitions/bike-sharing-demand")

    # ================================================================
    # STEP 3: Display results
    # ================================================================
    print("\n" + "=" * 70)
    print("📊 Results")
    print("=" * 70)

    print(f"\n✓ Success: {result.success}")
    print(f"✓ Score: {result.score}")
    print(f"✓ Cost: ${result.cost:.4f}")
    print(f"✓ Duration: {result.duration:.1f}s")

    if result.workspace_path:
        print(f"✓ Workspace: {result.workspace_path}")

    if result.artifacts_path:
        print(f"✓ Artifacts: {result.artifacts_path}")

    if result.error:
        print(f"✗ Error: {result.error}")

    # ================================================================
    # Additional Information
    # ================================================================
    print("\n" + "=" * 70)
    print("📚 Additional Information")
    print("=" * 70)

    print("\n💡 About AIDE Workflow:")
    print("  - Iterative code generation with automatic debugging")
    print("  - Feature engineering and model selection")
    print("  - Hyperparameter tuning")
    print("  - Good balance of performance and cost")

    print("\n📊 About bike-sharing-demand Dataset:")
    print("  - Task: Predict bike rental demand")
    print("  - Features: Temporal (hour, day, month) and weather conditions")
    print("  - Goal: Forecast bike rentals for future time periods")

    print("\n🔧 Advanced Usage:")
    print("  # Access underlying DSAT components")
    print("  config = agent.get_config()")
    print("  runner = agent.get_runner()")

    print("\n" + "=" * 70)
    print("✅ Completed!")
    print("=" * 70)


if __name__ == "__main__":
    # Uncomment the line below to run
    main()

    # Or run with one-liner:
    # import dslighting
    # result = dslighting.run_agent("data/competitions/bike-sharing-demand")
    # print(f"Score: {result.score}, Cost: ${result.cost:.4f}")
