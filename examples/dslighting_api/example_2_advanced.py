"""
Example 2: Advanced Usage of DSLighting API

This example demonstrates advanced features:
- Custom workflow selection
- LLM model configuration
- Batch processing
- Accessing underlying components

Usage:
    python examples/dslighting_api/example_2_advanced.py
"""

import dslighting


def main():
    """Run advanced DSLighting example."""
    print("=" * 60)
    print("DSLighting Advanced Usage Example")
    print("=" * 60)

    # Example 1: Custom workflow and model
    print("\n1. Custom workflow and model:")
    print("   agent = dslighting.Agent(")
    print("       workflow='autokaggle',")
    print("       model='gpt-4o',")
    print("       temperature=0.5,")
    print("       max_iterations=10")
    print("   )")
    print("   result = agent.run('data/competitions/titanic')")

    # Uncomment to run:
    # agent = dslighting.Agent(
    #     workflow="autokaggle",
    #     model="gpt-4o",
    #     temperature=0.5,
    #     max_iterations=10
    # )
    # result = agent.run("data/competitions/titanic")
    # print(f"   ✓ Score: {result.score}")
    # print(f"   ✓ Cost: ${result.cost:.4f}")

    # Example 2: Batch processing
    print("\n2. Batch processing multiple tasks:")
    print("   agent = dslighting.Agent()")
    print("   results = agent.run_batch([")
    print("       'data/competitions/titanic',")
    print("       'data/competitions/house-prices',")
    print("       'data/competitions/fraud'")
    print("   ])")
    print("   for i, r in enumerate(results):")
    print("       print(f'Task {i+1}: {r.score}')")

    # Uncomment to run:
    # agent = dslighting.Agent()
    # results = agent.run_batch([
    #     "data/competitions/titanic",
    #     "data/competitions/house-prices",
    #     "data/competitions/fraud"
    # ])
    # for i, r in enumerate(results):
    #     print(f"   Task {i+1}: score={r.score}, cost=${r.cost:.4f}")

    # Example 3: Access underlying DSAT components
    print("\n3. Access underlying DSAT components:")
    print("   agent = dslighting.Agent()")
    print("   config = agent.get_config()  # DSATConfig")
    print("   runner = agent.get_runner()  # DSATRunner")
    print("   print(f'Workflow: {config.workflow.name}')")
    print("   print(f'Model: {config.llm.model}')")

    # Uncomment to run:
    # agent = dslighting.Agent()
    # config = agent.get_config()
    # runner = agent.get_runner()
    # print(f"   ✓ Workflow: {config.workflow.name}")
    # print(f"   ✓ Model: {config.llm.model}")
    # print(f"   ✓ Temperature: {config.llm.temperature}")
    # print(f"   ✓ Runner type: {type(runner).__name__}")

    # Example 4: DataFrame input
    print("\n4. Direct DataFrame input:")
    print("   import pandas as pd")
    print("   df = pd.read_csv('my_data.csv')")
    print("   result = agent.run(df)")

    # Uncomment to run:
    # import pandas as pd
    # df = pd.read_csv("data/my_data.csv")
    # agent = dslighting.Agent()
    # result = agent.run(df, description="Predict the target column")
    # print(f"   ✓ Predictions saved to: {result.output}")

    # Example 5: Custom output path
    print("\n5. Custom output path:")
    print("   result = agent.run(")
    print("       'data/competitions/titanic',")
    print("       output_path='my_submission.csv'")
    print("   )")

    # Uncomment to run:
    # agent = dslighting.Agent()
    # result = agent.run(
    #     "data/competitions/titanic",
    #     output_path="my_submission.csv"
    # )
    # print(f"   ✓ Submission saved to: {result.output}")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
