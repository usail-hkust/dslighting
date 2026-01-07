from pydantic import BaseModel, Field

# 1. Pydantic model for the optimizer's structured output
class GraphOptimize(BaseModel):
    modification: str = Field(description="A brief, one-sentence summary of the change made to the workflow code.")
    graph: str = Field(description="The complete, runnable Python code for the new 'Workflow' class.")

# 2. Prompt templates
# --- FIX START: MAKE PROMPT MORE GENERIC AND STRATEGY-FOCUSED ---
WORKFLOW_OPTIMIZE_PROMPT = """
You are an expert AI workflow engineer. Your task is to iteratively optimize a Python-based AI workflow to improve its problem-solving score.

You will be given the code of a parent workflow, its performance score, and a history of modifications.
Your goal is to propose a single, small, logical modification to the workflow code. The new code must be a complete and runnable Python class named `Workflow`.

RULES:
1.  **Focus on Logic**: Your modifications should improve the problem-solving STRATEGY. Examples: add a data cleaning step, try a different model, change a prompt, add a self-correction loop, etc.
2.  **Adhere to the Standard Interface**: The workflow you generate MUST correctly implement the `solve` method: `async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path)`.
3.  **Use the Arguments Correctly**:
    - `description`: Contains the task goal and a COMPLETE data analysis report.
    - `io_instructions`: Contains CRITICAL I/O requirements.
    Your code's logic MUST use both arguments effectively.
4.  **DO NOT Hardcode Filenames**: Your generated workflow code should extract the required output filename from the `output_path.name` attribute provided to the `solve` method, or ensure that any internal prompts correctly instruct the final code-generation step to do so.
5.  **Make only ONE logical change.** (e.g., add one new operator call, change a prompt, add a loop).
6.  **Analyze the experience log.** Avoid modifications that have failed in the past. Learn from successful ones.
7.  **Ensure the `graph` output is the complete, final Python code**, including all necessary imports and the full class definition.
8.  **Inherit from DSATWorkflow**: The generated class MUST be `class Workflow(DSATWorkflow):`.

Your response MUST be a JSON object that adheres to the provided schema. Do not include any other text, markdown, or explanations.
"""
# --- FIX END ---

WORKFLOW_INPUT_TEMPLATE = """
# PARENT WORKFLOW CONTEXT

## Experience Log
{experience}

## Parent Score
{score:.4f}

## Parent Code
```python
{graph_code}
```

## Available Operators
{operator_description}
"""

# 3. Helper functions to assemble the final prompt
def get_operator_description() -> str:
    """Returns a formatted string of available operators for the prompt."""
    return """
    You can call operators from the `self.operators` dictionary inside the `solve` method. For example: `final_answer = await self.operators['ScEnsemble'](...)`

    - `ScEnsemble`: Performs self-consistency voting to find the best solution from a list.
      - `__call__(self, solutions: List[str], problem: str) -> str`
    - `Review`: Critically reviews a solution and returns structured feedback.
      - `__call__(self, problem: str, solution: str) -> ReviewResponse(is_correct: bool, feedback: str)`
    - `Revise`: Revises a solution based on feedback.
      - `__call__(self, problem: str, solution: str, feedback: str) -> str`
    """

# --- FIX: Update function signature ---
def get_graph_optimize_prompt(experience: str, score: float, graph_code: str) -> str:
    """Assembles the full prompt for the optimizer LLM."""
    main_prompt = WORKFLOW_OPTIMIZE_PROMPT # Use the updated prompt directly
    
    inputs = WORKFLOW_INPUT_TEMPLATE.format(
        experience=experience,
        score=score,
        graph_code=graph_code,
        operator_description=get_operator_description()
    )
    return main_prompt + "\n" + inputs