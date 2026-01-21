"""
Complete Example: Creating Custom Operators and Prompts in DSLighting

This example demonstrates:
1. Creating custom Operators (simple, LLM-based, complex)
2. Creating custom Prompts (templates, components)
3. Using them in a custom Agent
4. Running on a real dataset

Author: DSLighting Team
Date: 2026-01-18
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PART 1: Create Custom Operators
# ============================================================================

print("\n" + "=" * 70)
print("PART 1: Creating Custom Operators")
print("=" * 70)

from dslighting import Operator, LLMService, SandboxService

class DataSummaryOperator(Operator):
    """Generate data summary using simple analysis"""

    def __init__(self):
        super().__init__(name="data_summary")

    async def __call__(self, data_dir: Path) -> str:
        """Analyze data directory and generate summary"""
        import pandas as pd
        from pathlib import Path

        summary_lines = []
        summary_lines.append(f"## Data Directory: {data_dir}")
        summary_lines.append("")

        # List CSV files
        csv_files = list(Path(data_dir).glob("**/*.csv"))
        summary_lines.append(f"### Found {len(csv_files)} CSV files")

        for csv_file in csv_files[:5]:  # Limit to first 5
            try:
                df = pd.read_csv(csv_file)
                summary_lines.append(f"\n**{csv_file.name}**")
                summary_lines.append(f"- Shape: {df.shape}")
                summary_lines.append(f"- Columns: {', '.join(list(df.columns)[:5])}{'...' if len(df.columns) > 5 else ''}")
                summary_lines.append(f"- Missing: {df.isnull().sum().sum()} values")
            except Exception as e:
                summary_lines.append(f"\n**{csv_file.name}**")
                summary_lines.append(f"- Error: {str(e)[:50]}")

        return "\n".join(summary_lines)


class CodeQualityCheckOperator(Operator):
    """Check code quality using LLM"""

    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service=llm_service, name="code_quality_check")

    async def __call__(self, code: str) -> dict:
        """Check code quality and return suggestions"""
        prompt = f"""
Review the following Python code for quality issues:

```python
{code}
```

Please check:
1. Code style and formatting
2. Potential bugs or issues
3. Performance concerns
4. Best practices violations

Provide your review in the following format:

## Issues Found
[List any issues found]

## Suggestions
[Provide improvement suggestions]

## Overall Quality Score
[Rate from 1-10]
"""

        review = await self.llm_service.call(prompt)

        # Parse quality score
        import re
        score_match = re.search(r'Overall Quality Score.*?(\d+)', review, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 7

        return {
            "review": review,
            "score": score,
            "passes": score >= 7
        }


class IterativeRefinementOperator(Operator):
    """Iteratively refine code based on execution results"""

    def __init__(self, llm_service: LLMService, sandbox_service: SandboxService):
        super().__init__(
            llm_service=llm_service,
            name="iterative_refinement"
        )
        self.sandbox = sandbox_service

    async def __call__(
        self,
        code: str,
        feedback: str,
        max_refinements: int = 2
    ) -> dict:
        """Refine code iteratively based on feedback"""

        current_code = code
        refinement_history = []

        for iteration in range(max_refinements):
            print(f"  Refinement iteration {iteration + 1}/{max_refinements}")

            # Test current code
            result = self.sandbox.run_script(current_code)

            if result.success:
                print(f"  ✓ Code executed successfully")
                return {
                    "final_code": current_code,
                    "success": True,
                    "iterations": iteration + 1,
                    "history": refinement_history
                }

            # Generate refined code using LLM
            refine_prompt = f"""
The following code failed to execute. Please fix it.

Code:
```python
{current_code}
```

Error:
```
{result.stderr}
```

Feedback:
{feedback}

Please provide the fixed code. Return only the code in a ```python``` block.
"""

            refined_code = await self.llm_service.call(refine_prompt)

            # Parse refined code
            import re
            code_match = re.search(r'```python\n(.*?)```', refined_code, re.DOTALL)
            if code_match:
                new_code = code_match.group(1).strip()

                refinement_history.append({
                    "iteration": iteration + 1,
                    "old_code": current_code,
                    "new_code": new_code,
                    "error": result.stderr
                })

                current_code = new_code
            else:
                print(f"  ✗ Failed to parse refined code")
                break

        return {
            "final_code": current_code,
            "success": False,
            "iterations": max_refinements,
            "history": refinement_history
        }


# ============================================================================
# PART 2: Create Custom Prompts
# ============================================================================

print("\n" + "=" * 70)
print("PART 2: Creating Custom Prompts")
print("=" * 70)


class CustomPrompts:
    """Custom prompt templates for data science tasks"""

    @staticmethod
    def create_eda_prompt(data_summary: str) -> str:
        """Create prompt for exploratory data analysis"""
        return f"""
You are an expert data scientist performing Exploratory Data Analysis (EDA).

{data_summary}

Your task:
1. Load the data
2. Perform comprehensive EDA including:
   - Data types and missing values
   - Statistical summary
   - Correlation analysis
   - Distribution plots (describe them)
3. Provide insights and recommendations

Please provide:
- Analysis description
- Complete Python code using pandas and matplotlib
- Save visualizations to files

Output format:
## Analysis
[Your analysis description]

## Code
```python
import pandas as pd
import matplotlib.pyplot as plt

# Your code here
```
"""

    @staticmethod
    def create_modeling_prompt(
        data_summary: str,
        target_variable: str,
        task_type: str = "regression"
    ) -> str:
        """Create prompt for modeling task"""
        return f"""
You are an expert machine learning engineer building a {task_type} model.

{data_summary}

Target Variable: {target_variable}

Your task:
1. Preprocess the data (handle missing values, encode categories, etc.)
2. Feature engineering
3. Split data into train/validation sets
4. Train appropriate model(s)
5. Evaluate performance
6. Generate predictions for test set

Requirements:
- Use scikit-learn
- Handle categorical variables appropriately
- Save predictions to submission.csv
- Print evaluation metrics

Output format:
## Approach
[Your modeling approach]

## Code
```python
import pandas as pd
from sklearn.model_selection import train_test_split
# ... other imports

# Your code here
```
"""

    @staticmethod
    def create_debugging_prompt(
        code: str,
        error_message: str,
        context: str = ""
    ) -> str:
        """Create prompt for debugging code"""
        return f"""
The following code has an error. Please fix it.

Code:
```python
{code}
```

Error:
```
{error_message}
```

{context}

Instructions:
1. Analyze the error
2. Identify the root cause
3. Fix the code
4. Ensure the fix is robust

Return only the fixed code in a ```python``` block.
"""


# ============================================================================
# PART 3: Create Custom Agent using Custom Operators and Prompts
# ============================================================================

print("\n" + "=" * 70)
print("PART 3: Creating Custom Agent")
print("=" * 70)

from dslighting import BaseAgent, JournalState, Node, MetricValue


class MyCustomAgent(BaseAgent):
    """
    Custom Agent that uses:
    - Custom Operators (DataSummaryOperator, CodeQualityCheckOperator, etc.)
    - Custom Prompts (CustomPrompts)
    - Standard DSAT services and operators
    """

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # Standard DSAT services
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.data_analyzer = services.get("data_analyzer")
        self.state: JournalState = services["state"]

        # Standard DSAT operators
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

        # Custom operators
        self.data_summary_op = operators.get("data_summary")
        self.quality_check_op = operators.get("quality_check")
        self.refinement_op = operators.get("refinement")

        # Agent configuration
        self.max_iterations = agent_config.get("max_iterations", 5)
        self.quality_threshold = agent_config.get("quality_threshold", 7)

    async def solve(self, description, io_instructions, data_dir, output_path):
        """Solve task using custom operators and prompts"""

        print(f"\n{'='*70}")
        print(f"MyCustomAgent starting task")
        print(f"Description: {description[:100]}...")
        print(f"Data dir: {data_dir}")
        print(f"{'='*70}\n")

        # Step 1: Generate data summary using custom operator
        print("Step 1: Generating data summary...")
        if self.data_summary_op:
            data_summary = await self.data_summary_op(data_dir)
            print(f"✓ Data summary generated\n")
        else:
            data_summary = "Data summary not available"
            print(f"✗ Data summary operator not available\n")

        # Step 2: Generate initial code using custom prompt
        print("Step 2: Generating initial code...")
        if "model" in description.lower() or "predict" in description.lower():
            prompt = CustomPrompts.create_modeling_prompt(
                data_summary=data_summary,
                target_variable=io_instructions,
                task_type="regression"
            )
        else:
            prompt = CustomPrompts.create_eda_prompt(data_summary=data_summary)

        plan, code = await self.generate_op(system_prompt=prompt)
        print(f"✓ Initial code generated\n")
        print(f"Plan: {plan[:200]}...\n")

        # Step 3: Check code quality using custom operator
        print("Step 3: Checking code quality...")
        if self.quality_check_op:
            quality_result = await self.quality_check_op(code)
            print(f"✓ Quality score: {quality_result['score']}/10")
            print(f"  Passes threshold: {quality_result['passes']}\n")

            # If quality is low, use LLM to improve it
            if not quality_result['passes']:
                print("  Improving code quality...")
                improve_prompt = f"""
Improve the following code to make it production-ready:

```python
{code}
```

Focus on:
- Code style and readability
- Error handling
- Performance
- Best practices

Return only the improved code in a ```python``` block.
"""
                _, code = await self.generate_op(system_prompt=improve_prompt)
                print(f"  ✓ Code improved\n")

        # Step 4: Execute code
        print("Step 4: Executing code...")
        result = await self.execute_op(code=code, mode="script")

        if result.success:
            print(f"✓ Code executed successfully\n")
            print(f"Output preview:\n{result.stdout[:500]}...\n")

            # Step 5: Create node and add to state
            node = Node(plan=plan, code=code)
            node.absorb_exec_result(result)

            # Use review operator for scoring
            review = await self.review_op(prompt_context={
                "task": description,
                "code": code,
                "output": result.stdout
            })

            node.analysis = review.summary
            if review.metric_value:
                node.metric = MetricValue(
                    value=review.metric_value,
                    maximize=not review.lower_is_better
                )
            else:
                # Default metric based on execution success
                node.metric = MetricValue(value=1.0, maximize=True)

            self.state.append(node, parent=None)

            print(f"✓ Task completed!")
            print(f"  Analysis: {review.summary[:200]}...")
            if node.metric:
                print(f"  Metric: {node.metric.value}")

        else:
            print(f"✗ Code execution failed")
            print(f"  Error: {result.stderr}\n")

            # Step 6: Try to fix using refinement operator
            if self.refinement_op:
                print("Step 5: Attempting to fix errors...")
                feedback = f"The code failed with error: {result.stderr[:500]}"
                refinement_result = await self.refinement_op(
                    code=code,
                    feedback=feedback,
                    max_refinements=2
                )

                if refinement_result["success"]:
                    print(f"✓ Code fixed after {refinement_result['iterations']} iterations")
                    # Execute fixed code
                    result = await self.execute_op(
                        code=refinement_result["final_code"],
                        mode="script"
                    )

                    if result.success:
                        print(f"✓ Fixed code executed successfully")
                else:
                    print(f"✗ Could not fix code after {refinement_result['iterations']} attempts")


# ============================================================================
# PART 4: Run the Custom Agent
# ============================================================================

print("\n" + "=" * 70)
print("PART 4: Running Custom Agent")
print("=" * 70)


async def main():
    """Main execution function"""

    from dslighting import (
        LLMService,
        SandboxService,
        WorkspaceService,
        DataAnalyzer,
        JournalState,
        GenerateCodeAndPlanOperator,
        ReviewOperator,
        ExecuteAndTestOperator
    )

    # Create services
    workspace = WorkspaceService(run_name="custom_agent_demo")
    llm_service = LLMService(model="gpt-4o")  # Or "gpt-4o-mini" for faster testing
    sandbox_service = SandboxService(workspace=workspace, timeout=300)
    data_analyzer = DataAnalyzer()
    state = JournalState()

    # Create standard operators
    operators = {
        "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
        "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
        "review": ReviewOperator(llm_service=llm_service),
    }

    # Create custom operators
    operators["data_summary"] = DataSummaryOperator()
    operators["quality_check"] = CodeQualityCheckOperator(llm_service=llm_service)
    operators["refinement"] = IterativeRefinementOperator(
        llm_service=llm_service,
        sandbox_service=sandbox_service
    )

    # Create services dictionary
    services = {
        "llm": llm_service,
        "sandbox": sandbox_service,
        "workspace": workspace,
        "data_analyzer": data_analyzer,
        "state": state,
    }

    # Create custom agent
    agent = MyCustomAgent(
        operators=operators,
        services=services,
        agent_config={
            "max_iterations": 3,
            "quality_threshold": 7
        }
    )

    # Run on bike-sharing-demand dataset
    data_dir = Path("/Users/liufan/Applications/Github/dslighting/datasets/bike-sharing-demand")
    output_path = Path("submission.csv")

    await agent.solve(
        description="Predict bike sharing demand based on weather and time information",
        io_instructions="count",
        data_dir=data_dir,
        output_path=output_path
    )

    print("\n" + "=" * 70)
    print("Custom Agent execution completed!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DSLighting Custom Operators and Prompts Example")
    print("=" * 70)
    print("\nThis example demonstrates:")
    print("1. Creating custom Operators")
    print("2. Creating custom Prompts")
    print("3. Using them in a custom Agent")
    print("4. Running on real data")
    print("\n" + "=" * 70 + "\n")

    # Run the async main function
    asyncio.run(main())
